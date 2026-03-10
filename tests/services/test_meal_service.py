"""Tests for MealService meal suggestion orchestration."""

import datetime
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from life_organizer.schemas.meals import MealSuggestion
from life_organizer.services.meal_service import MealService


def _make_suggestion_dicts() -> list[dict]:
    """Create sample suggestion dicts as returned by ClaudeService."""
    return [
        {
            "name": "Chicken Stir Fry",
            "ingredients": ["chicken breast", "bell peppers", "soy sauce", "rice"],
            "instructions": "Cut chicken. Stir fry with veggies. Serve over rice.",
            "prep_time": 25,
            "cuisine": "Asian",
            "tags": ["quick", "healthy"],
        },
        {
            "name": "Spaghetti Bolognese",
            "ingredients": ["spaghetti", "ground beef", "tomato paste", "onions"],
            "instructions": "Cook pasta. Make sauce. Combine.",
            "prep_time": 35,
            "cuisine": "Italian",
            "tags": ["comfort", "pasta"],
        },
        {
            "name": "Greek Salad",
            "ingredients": ["lettuce", "cucumber", "tomatoes", "feta cheese", "olives"],
            "instructions": "Chop veggies. Add feta. Drizzle olive oil.",
            "prep_time": 15,
            "cuisine": "Mediterranean",
            "tags": ["quick", "healthy", "salad"],
        },
    ]


def _make_meal_history_row(recipe_name: str, cooked_date: datetime.date) -> MagicMock:
    """Create a mock MealHistory row."""
    row = MagicMock()
    row.recipe_name = recipe_name
    row.cooked_date = cooked_date
    return row


def _make_feedback_row(recipe_name: str) -> MagicMock:
    """Create a mock RecipeFeedback row."""
    row = MagicMock()
    row.recipe_name = recipe_name
    row.liked = True
    return row


def _make_session_factory(history_rows: list, feedback_rows: list) -> AsyncMock:
    """Create a mock async session factory returning configured session."""
    mock_session = AsyncMock()

    # Track call order for two separate queries
    call_count = 0

    async def mock_execute(stmt):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        if call_count == 1:
            result.scalars.return_value.all.return_value = history_rows
        else:
            result.scalars.return_value.all.return_value = feedback_rows
        return result

    mock_session.execute = AsyncMock(side_effect=mock_execute)

    @asynccontextmanager
    async def session_ctx() -> AsyncGenerator[AsyncMock]:
        yield mock_session

    return MagicMock(side_effect=session_ctx)


@pytest.mark.unit
class TestMealServiceGetSuggestions:
    """Tests for MealService.get_suggestions method."""

    @pytest.mark.asyncio
    async def test_successful_suggestion_flow(self) -> None:
        """Full flow: queries DB for history + feedback, calls Claude, returns suggestions."""
        today = datetime.date.today()
        history_rows = [
            _make_meal_history_row("Pasta Carbonara", today - datetime.timedelta(days=2)),
        ]
        feedback_rows = [
            _make_feedback_row("Chicken Curry"),
        ]

        session_factory = _make_session_factory(history_rows, feedback_rows)
        service = MealService(session_factory=session_factory)

        mock_claude = MagicMock()
        mock_claude.suggest_meals = AsyncMock(return_value=_make_suggestion_dicts())

        results = await service.get_suggestions(requirements=None, claude_service=mock_claude)

        assert len(results) == 3
        assert all(isinstance(s, MealSuggestion) for s in results)
        assert results[0].name == "Chicken Stir Fry"

        # Verify claude was called with correct history and liked recipes
        mock_claude.suggest_meals.assert_awaited_once()
        call_kwargs = mock_claude.suggest_meals.call_args.kwargs
        assert call_kwargs["requirements"] is None
        assert "Pasta Carbonara" in call_kwargs["history"]
        assert "Chicken Curry" in call_kwargs["liked_recipes"]

    @pytest.mark.asyncio
    async def test_empty_meal_history(self) -> None:
        """No recent meals should pass empty history list."""
        session_factory = _make_session_factory([], [_make_feedback_row("Curry")])
        service = MealService(session_factory=session_factory)

        mock_claude = MagicMock()
        mock_claude.suggest_meals = AsyncMock(return_value=_make_suggestion_dicts())

        results = await service.get_suggestions(requirements=None, claude_service=mock_claude)

        assert len(results) == 3
        call_kwargs = mock_claude.suggest_meals.call_args.kwargs
        assert call_kwargs["history"] == []

    @pytest.mark.asyncio
    async def test_empty_recipe_feedback(self) -> None:
        """No liked recipes should pass empty liked_recipes list."""
        session_factory = _make_session_factory(
            [_make_meal_history_row("Pasta", datetime.date.today())], []
        )
        service = MealService(session_factory=session_factory)

        mock_claude = MagicMock()
        mock_claude.suggest_meals = AsyncMock(return_value=_make_suggestion_dicts())

        results = await service.get_suggestions(requirements=None, claude_service=mock_claude)

        assert len(results) == 3
        call_kwargs = mock_claude.suggest_meals.call_args.kwargs
        assert call_kwargs["liked_recipes"] == []

    @pytest.mark.asyncio
    async def test_requirements_passed_through(self) -> None:
        """Requirements string should be passed to claude_service."""
        session_factory = _make_session_factory([], [])
        service = MealService(session_factory=session_factory)

        mock_claude = MagicMock()
        mock_claude.suggest_meals = AsyncMock(return_value=_make_suggestion_dicts())

        await service.get_suggestions(
            requirements="I have chicken thighs", claude_service=mock_claude
        )

        call_kwargs = mock_claude.suggest_meals.call_args.kwargs
        assert call_kwargs["requirements"] == "I have chicken thighs"

    @pytest.mark.asyncio
    async def test_claude_api_failure_propagates(self) -> None:
        """Claude API failure should propagate as HTTPException."""
        session_factory = _make_session_factory([], [])
        service = MealService(session_factory=session_factory)

        mock_claude = MagicMock()
        mock_claude.suggest_meals = AsyncMock(
            side_effect=HTTPException(status_code=500, detail="Failed to parse meal suggestions")
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.get_suggestions(requirements=None, claude_service=mock_claude)

        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_malformed_suggestion_dict_raises_http_exception(self) -> None:
        """Malformed suggestion dicts from Claude should raise HTTPException 500."""
        session_factory = _make_session_factory([], [])
        service = MealService(session_factory=session_factory)

        mock_claude = MagicMock()
        # Return dicts missing required fields to trigger ValidationError
        mock_claude.suggest_meals = AsyncMock(
            return_value=[{"name": "Test"}]  # missing ingredients, instructions, etc.
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.get_suggestions(requirements=None, claude_service=mock_claude)

        assert exc_info.value.status_code == 500
        assert "Failed to parse meal suggestions" in str(exc_info.value.detail)
