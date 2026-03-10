"""Tests for MealService meal suggestion orchestration."""

import datetime
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from life_organizer.db.models.meals import MealHistory, Recipe, RecipeFeedback
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


def _make_mock_session() -> AsyncMock:
    """Create a mock async session for save_feedback tests."""
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    return session


@pytest.mark.unit
class TestMealServiceSaveFeedback:
    """Tests for MealService.save_feedback method."""

    @pytest.mark.asyncio
    async def test_positive_feedback_no_recipe_id_creates_liked_recipe(self) -> None:
        """Liked LLM-generated recipe (no recipe_id) should create Recipe with source='liked'."""
        session = _make_mock_session()
        service = MealService(session_factory=MagicMock())

        # Mock execute to return no existing recipe for the lookup query
        lookup_result = MagicMock()
        lookup_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=lookup_result)

        # Mock flush to set id on the new recipe
        async def mock_flush() -> None:
            for call in session.add.call_args_list:
                obj = call[0][0]
                if isinstance(obj, Recipe):
                    obj.id = 42

        session.flush = AsyncMock(side_effect=mock_flush)

        await service.save_feedback(
            recipe_id=None,
            recipe_name="Greek Lemon Chicken",
            liked=True,
            notes="great",
            session=session,
        )

        # Verify Recipe created with source='liked' and stats initialized
        added_objects = [call[0][0] for call in session.add.call_args_list]
        recipes = [o for o in added_objects if isinstance(o, Recipe)]
        assert len(recipes) == 1
        assert recipes[0].source == "liked"
        assert recipes[0].name == "Greek Lemon Chicken"
        assert recipes[0].times_made == 1
        assert recipes[0].last_made == datetime.date.today()

        # Verify feedback and history reference the new recipe id
        feedbacks = [o for o in added_objects if isinstance(o, RecipeFeedback)]
        histories = [o for o in added_objects if isinstance(o, MealHistory)]
        assert len(feedbacks) == 1
        assert feedbacks[0].recipe_id == 42
        assert feedbacks[0].liked is True
        assert feedbacks[0].notes == "great"
        assert len(histories) == 1
        assert histories[0].recipe_id == 42
        assert histories[0].recipe_name == "Greek Lemon Chicken"

    @pytest.mark.asyncio
    async def test_positive_feedback_no_recipe_id_reuses_existing_liked_recipe(self) -> None:
        """Repeated liked feedback for same name should reuse existing recipe, not create duplicate."""
        session = _make_mock_session()
        service = MealService(session_factory=MagicMock())

        # Mock an existing liked recipe returned by the lookup query
        existing_recipe = MagicMock()
        existing_recipe.id = 10
        existing_recipe.name = "Greek Lemon Chicken"
        existing_recipe.source = "liked"
        existing_recipe.times_made = 2
        existing_recipe.last_made = datetime.date(2026, 1, 1)

        lookup_result = MagicMock()
        lookup_result.scalar_one_or_none.return_value = existing_recipe
        session.execute = AsyncMock(return_value=lookup_result)

        await service.save_feedback(
            recipe_id=None,
            recipe_name="Greek Lemon Chicken",
            liked=True,
            notes="still great",
            session=session,
        )

        # Verify no new Recipe was added
        added_objects = [call[0][0] for call in session.add.call_args_list]
        recipes = [o for o in added_objects if isinstance(o, Recipe)]
        assert len(recipes) == 0

        # Verify existing recipe was updated
        assert existing_recipe.times_made == 3
        assert existing_recipe.last_made == datetime.date.today()

        # Verify feedback and history reference the existing recipe's id
        feedbacks = [o for o in added_objects if isinstance(o, RecipeFeedback)]
        histories = [o for o in added_objects if isinstance(o, MealHistory)]
        assert len(feedbacks) == 1
        assert feedbacks[0].recipe_id == 10
        assert feedbacks[0].liked is True
        assert feedbacks[0].notes == "still great"
        assert feedbacks[0].recipe_name == "Greek Lemon Chicken"
        assert len(histories) == 1
        assert histories[0].recipe_id == 10
        assert histories[0].recipe_name == "Greek Lemon Chicken"

    @pytest.mark.asyncio
    async def test_positive_feedback_with_existing_recipe_id(self) -> None:
        """Feedback for known recipe should increment times_made and update last_made."""
        session = _make_mock_session()
        service = MealService(session_factory=MagicMock())

        mock_recipe = MagicMock()
        mock_recipe.id = 5
        mock_recipe.times_made = 3
        mock_recipe.last_made = None

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_recipe
        session.execute = AsyncMock(return_value=result_mock)

        mock_recipe.name = "Spaghetti Bolognese"  # DB name differs from request

        await service.save_feedback(
            recipe_id=5,
            recipe_name="Spaghetti",
            liked=True,
            notes=None,
            session=session,
        )

        assert mock_recipe.times_made == 4
        assert mock_recipe.last_made == datetime.date.today()

        added_objects = [call[0][0] for call in session.add.call_args_list]
        feedbacks = [o for o in added_objects if isinstance(o, RecipeFeedback)]
        histories = [o for o in added_objects if isinstance(o, MealHistory)]
        assert len(feedbacks) == 1
        assert feedbacks[0].recipe_id == 5
        # Verify resolved name from DB is used, not the request name
        assert feedbacks[0].recipe_name == "Spaghetti Bolognese"
        assert len(histories) == 1
        assert histories[0].recipe_id == 5
        assert histories[0].recipe_name == "Spaghetti Bolognese"

    @pytest.mark.asyncio
    async def test_negative_feedback_no_recipe_id_does_not_create_recipe(self) -> None:
        """Negative feedback without recipe_id should NOT create a Recipe."""
        session = _make_mock_session()
        service = MealService(session_factory=MagicMock())

        await service.save_feedback(
            recipe_id=None,
            recipe_name="Bad Soup",
            liked=False,
            notes="too salty",
            session=session,
        )

        added_objects = [call[0][0] for call in session.add.call_args_list]
        recipes = [o for o in added_objects if isinstance(o, Recipe)]
        assert len(recipes) == 0

        feedbacks = [o for o in added_objects if isinstance(o, RecipeFeedback)]
        assert len(feedbacks) == 1
        assert feedbacks[0].liked is False
        assert feedbacks[0].recipe_id is None

        histories = [o for o in added_objects if isinstance(o, MealHistory)]
        assert len(histories) == 1
        assert histories[0].recipe_name == "Bad Soup"

    @pytest.mark.asyncio
    async def test_negative_feedback_with_existing_recipe_id(self) -> None:
        """Negative feedback with recipe_id should still increment times_made."""
        session = _make_mock_session()
        service = MealService(session_factory=MagicMock())

        mock_recipe = MagicMock()
        mock_recipe.id = 7
        mock_recipe.name = "Ok Pasta"
        mock_recipe.times_made = 1
        mock_recipe.last_made = None

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_recipe
        session.execute = AsyncMock(return_value=result_mock)

        await service.save_feedback(
            recipe_id=7,
            recipe_name="Ok Pasta",
            liked=False,
            notes=None,
            session=session,
        )

        assert mock_recipe.times_made == 2
        assert mock_recipe.last_made == datetime.date.today()

        added_objects = [call[0][0] for call in session.add.call_args_list]
        feedbacks = [o for o in added_objects if isinstance(o, RecipeFeedback)]
        assert feedbacks[0].liked is False

    @pytest.mark.asyncio
    async def test_nonexistent_recipe_id_raises_404(self) -> None:
        """Non-existent recipe_id should raise HTTPException 404."""
        session = _make_mock_session()
        service = MealService(session_factory=MagicMock())

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        with pytest.raises(HTTPException) as exc_info:
            await service.save_feedback(
                recipe_id=999,
                recipe_name="Missing",
                liked=True,
                notes=None,
                session=session,
            )

        assert exc_info.value.status_code == 404
        assert "Recipe not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_database_failure_no_partial_writes(self) -> None:
        """Database failure should propagate without partial writes."""
        session = _make_mock_session()
        service = MealService(session_factory=MagicMock())

        # Mock execute to return no existing recipe for the lookup query
        lookup_result = MagicMock()
        lookup_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=lookup_result)

        session.flush = AsyncMock(side_effect=Exception("DB connection lost"))

        with pytest.raises(Exception, match="DB connection lost"):
            await service.save_feedback(
                recipe_id=None,
                recipe_name="Test",
                liked=True,
                notes=None,
                session=session,
            )
