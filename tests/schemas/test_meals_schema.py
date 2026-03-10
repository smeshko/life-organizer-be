"""Tests for meal suggestion Pydantic schemas."""

import pytest
from pydantic import ValidationError

from life_organizer.schemas.meals import (
    MealSuggestion,
    MealSuggestRequest,
    MealSuggestResponse,
)


@pytest.mark.unit
class TestMealSuggestRequest:
    """Tests for MealSuggestRequest schema."""

    def test_empty_request_defaults_to_none(self) -> None:
        """Empty request should default requirements to None."""
        req = MealSuggestRequest()
        assert req.requirements is None

    def test_with_requirements(self) -> None:
        """Request with requirements should store them."""
        req = MealSuggestRequest(requirements="I have chicken thighs")
        assert req.requirements == "I have chicken thighs"

    def test_requirements_none_explicitly(self) -> None:
        """Explicitly setting requirements to None should work."""
        req = MealSuggestRequest(requirements=None)
        assert req.requirements is None


@pytest.mark.unit
class TestMealSuggestion:
    """Tests for MealSuggestion schema."""

    def test_valid_suggestion(self) -> None:
        """Valid suggestion with all required fields should be created."""
        suggestion = MealSuggestion(
            name="Spaghetti Bolognese",
            ingredients=["pasta", "tomato sauce", "ground beef"],
            instructions="Cook pasta. Make sauce. Combine.",
            prep_time=30,
            cuisine="Italian",
            tags=["dinner", "pasta"],
        )
        assert suggestion.name == "Spaghetti Bolognese"
        assert len(suggestion.ingredients) == 3
        assert suggestion.prep_time == 30
        assert suggestion.cuisine == "Italian"
        assert suggestion.tags == ["dinner", "pasta"]

    def test_missing_name_raises(self) -> None:
        """Missing name should raise ValidationError."""
        with pytest.raises(ValidationError):
            MealSuggestion(
                ingredients=["pasta"],
                instructions="Cook it.",
                prep_time=10,
                cuisine="Italian",
                tags=[],
            )

    def test_missing_ingredients_raises(self) -> None:
        """Missing ingredients should raise ValidationError."""
        with pytest.raises(ValidationError):
            MealSuggestion(
                name="Test",
                instructions="Cook it.",
                prep_time=10,
                cuisine="Italian",
                tags=[],
            )

    def test_missing_instructions_raises(self) -> None:
        """Missing instructions should raise ValidationError."""
        with pytest.raises(ValidationError):
            MealSuggestion(
                name="Test",
                ingredients=["pasta"],
                prep_time=10,
                cuisine="Italian",
                tags=[],
            )

    def test_missing_prep_time_raises(self) -> None:
        """Missing prep_time should raise ValidationError."""
        with pytest.raises(ValidationError):
            MealSuggestion(
                name="Test",
                ingredients=["pasta"],
                instructions="Cook it.",
                cuisine="Italian",
                tags=[],
            )

    def test_prep_time_must_be_int(self) -> None:
        """prep_time must be an integer."""
        with pytest.raises(ValidationError):
            MealSuggestion(
                name="Test",
                ingredients=["pasta"],
                instructions="Cook it.",
                prep_time="thirty",
                cuisine="Italian",
                tags=[],
            )

    def test_ingredients_must_be_list_of_strings(self) -> None:
        """ingredients must be a list of strings."""
        with pytest.raises(ValidationError):
            MealSuggestion(
                name="Test",
                ingredients="pasta",
                instructions="Cook it.",
                prep_time=10,
                cuisine="Italian",
                tags=[],
            )

    def test_tags_must_be_list_of_strings(self) -> None:
        """tags must be a list of strings."""
        with pytest.raises(ValidationError):
            MealSuggestion(
                name="Test",
                ingredients=["pasta"],
                instructions="Cook it.",
                prep_time=10,
                cuisine="Italian",
                tags="dinner",
            )


@pytest.mark.unit
class TestMealSuggestResponse:
    """Tests for MealSuggestResponse schema."""

    def test_valid_response(self) -> None:
        """Valid response with list of suggestions."""
        suggestion = MealSuggestion(
            name="Test",
            ingredients=["a"],
            instructions="Do it.",
            prep_time=10,
            cuisine="Italian",
            tags=["dinner"],
        )
        response = MealSuggestResponse(suggestions=[suggestion])
        assert len(response.suggestions) == 1
        assert response.suggestions[0].name == "Test"

    def test_empty_suggestions_list(self) -> None:
        """Empty suggestions list should be valid."""
        response = MealSuggestResponse(suggestions=[])
        assert response.suggestions == []

    def test_missing_suggestions_raises(self) -> None:
        """Missing suggestions field should raise ValidationError."""
        with pytest.raises(ValidationError):
            MealSuggestResponse()
