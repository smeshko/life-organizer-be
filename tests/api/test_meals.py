"""Tests for POST /api/v1/meals/suggest endpoint."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from life_organizer.schemas.meals import MealSuggestion


def _make_mock_request() -> Request:
    """Create a minimal Starlette Request for slowapi compatibility."""
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/meals/suggest",
        "headers": [],
        "query_string": b"",
    }
    request = Request(scope)
    request._receive = MagicMock()
    return request


def _make_suggestions() -> list[MealSuggestion]:
    """Create sample MealSuggestion objects for testing."""
    return [
        MealSuggestion(
            name="Chicken Stir Fry",
            ingredients=["chicken breast", "bell peppers", "soy sauce", "rice"],
            instructions="Cut chicken. Stir fry with veggies. Serve over rice.",
            prep_time=25,
            cuisine="Asian",
            tags=["quick", "healthy"],
        ),
        MealSuggestion(
            name="Spaghetti Bolognese",
            ingredients=["spaghetti", "ground beef", "tomato paste", "onions"],
            instructions="Cook pasta. Make sauce. Combine.",
            prep_time=35,
            cuisine="Italian",
            tags=["comfort", "pasta"],
        ),
        MealSuggestion(
            name="Greek Salad",
            ingredients=["lettuce", "cucumber", "tomatoes", "feta cheese", "olives"],
            instructions="Chop veggies. Add feta. Drizzle olive oil.",
            prep_time=15,
            cuisine="Mediterranean",
            tags=["quick", "healthy", "salad"],
        ),
    ]


@pytest.mark.unit
class TestSuggestMeals:
    """Tests for POST /api/v1/meals/suggest endpoint."""

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.meals.meal_service")
    @patch("life_organizer.api.routes.meals.claude_service")
    async def test_200_no_body(self, mock_claude: AsyncMock, mock_meal: AsyncMock) -> None:
        """No body or empty body should return 200 with 3 suggestions."""
        from life_organizer.api.routes.meals import suggest_meals
        from life_organizer.schemas.meals import MealSuggestRequest

        mock_meal.get_suggestions = AsyncMock(return_value=_make_suggestions())

        result = await suggest_meals(_make_mock_request(), MealSuggestRequest())

        assert len(result.suggestions) == 3
        assert result.suggestions[0].name == "Chicken Stir Fry"
        mock_meal.get_suggestions.assert_awaited_once()
        call_kwargs = mock_meal.get_suggestions.call_args.kwargs
        assert call_kwargs["requirements"] is None
        assert call_kwargs["claude_service"] is mock_claude

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.meals.meal_service")
    @patch("life_organizer.api.routes.meals.claude_service")
    async def test_200_with_requirements(
        self, mock_claude: AsyncMock, mock_meal: AsyncMock
    ) -> None:
        """Request with requirements should pass them to meal_service."""
        from life_organizer.api.routes.meals import suggest_meals
        from life_organizer.schemas.meals import MealSuggestRequest

        mock_meal.get_suggestions = AsyncMock(return_value=_make_suggestions())

        body = MealSuggestRequest(requirements="I have chicken thighs")
        result = await suggest_meals(_make_mock_request(), body)

        assert len(result.suggestions) == 3
        call_kwargs = mock_meal.get_suggestions.call_args.kwargs
        assert call_kwargs["requirements"] == "I have chicken thighs"

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.meals.meal_service")
    @patch("life_organizer.api.routes.meals.claude_service")
    async def test_500_claude_api_failure(
        self, mock_claude: AsyncMock, mock_meal: AsyncMock
    ) -> None:
        """Claude API failure should return 500."""
        from life_organizer.api.routes.meals import suggest_meals
        from life_organizer.schemas.meals import MealSuggestRequest

        mock_meal.get_suggestions = AsyncMock(
            side_effect=HTTPException(status_code=500, detail="Failed to parse meal suggestions")
        )

        with pytest.raises(HTTPException) as exc_info:
            await suggest_meals(_make_mock_request(), MealSuggestRequest())

        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.meals.meal_service")
    @patch("life_organizer.api.routes.meals.claude_service")
    async def test_500_unexpected_error(self, mock_claude: AsyncMock, mock_meal: AsyncMock) -> None:
        """Unexpected error should return 500 with processing error message."""
        from life_organizer.api.routes.meals import suggest_meals
        from life_organizer.schemas.meals import MealSuggestRequest

        mock_meal.get_suggestions = AsyncMock(side_effect=RuntimeError("Unexpected"))

        with pytest.raises(HTTPException) as exc_info:
            await suggest_meals(_make_mock_request(), MealSuggestRequest())

        assert exc_info.value.status_code == 500
        assert "Internal server error" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.meals.meal_service")
    @patch("life_organizer.api.routes.meals.claude_service")
    async def test_get_suggestions_called_with_correct_args(
        self, mock_claude: AsyncMock, mock_meal: AsyncMock
    ) -> None:
        """Verify meal_service.get_suggestions is called with correct arguments."""
        from life_organizer.api.routes.meals import suggest_meals
        from life_organizer.schemas.meals import MealSuggestRequest

        mock_meal.get_suggestions = AsyncMock(return_value=_make_suggestions())

        body = MealSuggestRequest(requirements="vegetarian only")
        await suggest_meals(_make_mock_request(), body)

        mock_meal.get_suggestions.assert_awaited_once_with(
            requirements="vegetarian only",
            claude_service=mock_claude,
        )


@pytest.mark.unit
class TestMealFeedback:
    """Tests for POST /api/v1/meals/feedback endpoint."""

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.meals.meal_service")
    async def test_201_liked_no_recipe_id(self, mock_meal: AsyncMock) -> None:
        """Liked feedback without recipe_id should return 201."""
        from life_organizer.api.routes.meals import submit_meal_feedback
        from life_organizer.schemas.meals import MealFeedbackRequest

        mock_meal.save_feedback = AsyncMock()
        body = MealFeedbackRequest(recipe_name="Greek Lemon Chicken", liked=True, notes="great")
        mock_db = AsyncMock()

        result = await submit_meal_feedback(body, mock_db)

        assert result.success is True
        assert result.message == "Feedback recorded"
        mock_meal.save_feedback.assert_awaited_once_with(
            recipe_id=None,
            recipe_name="Greek Lemon Chicken",
            liked=True,
            notes="great",
            session=mock_db,
        )

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.meals.meal_service")
    async def test_201_disliked(self, mock_meal: AsyncMock) -> None:
        """Disliked feedback should return 201."""
        from life_organizer.api.routes.meals import submit_meal_feedback
        from life_organizer.schemas.meals import MealFeedbackRequest

        mock_meal.save_feedback = AsyncMock()
        body = MealFeedbackRequest(recipe_name="Bad Soup", liked=False)
        mock_db = AsyncMock()

        result = await submit_meal_feedback(body, mock_db)

        assert result.success is True
        mock_meal.save_feedback.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.meals.meal_service")
    async def test_201_with_recipe_id(self, mock_meal: AsyncMock) -> None:
        """Feedback with existing recipe_id should return 201."""
        from life_organizer.api.routes.meals import submit_meal_feedback
        from life_organizer.schemas.meals import MealFeedbackRequest

        mock_meal.save_feedback = AsyncMock()
        body = MealFeedbackRequest(recipe_id=5, recipe_name="Spaghetti", liked=True)
        mock_db = AsyncMock()

        result = await submit_meal_feedback(body, mock_db)

        assert result.success is True
        call_kwargs = mock_meal.save_feedback.call_args.kwargs
        assert call_kwargs["recipe_id"] == 5

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.meals.meal_service")
    async def test_404_nonexistent_recipe(self, mock_meal: AsyncMock) -> None:
        """Non-existent recipe_id should return 404."""
        from life_organizer.api.routes.meals import submit_meal_feedback
        from life_organizer.schemas.meals import MealFeedbackRequest

        mock_meal.save_feedback = AsyncMock(
            side_effect=HTTPException(status_code=404, detail="Recipe not found")
        )
        body = MealFeedbackRequest(recipe_id=999, recipe_name="Missing", liked=True)
        mock_db = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await submit_meal_feedback(body, mock_db)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.meals.meal_service")
    async def test_500_unexpected_error(self, mock_meal: AsyncMock) -> None:
        """Unexpected service error should return 500."""
        from life_organizer.api.routes.meals import submit_meal_feedback
        from life_organizer.schemas.meals import MealFeedbackRequest

        mock_meal.save_feedback = AsyncMock(side_effect=RuntimeError("DB down"))
        body = MealFeedbackRequest(recipe_name="Test", liked=True)
        mock_db = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await submit_meal_feedback(body, mock_db)

        assert exc_info.value.status_code == 500
        assert "Internal server error" in str(exc_info.value.detail)
