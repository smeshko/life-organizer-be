"""Tests for feedback schema validation."""

import pytest
from pydantic import ValidationError


@pytest.mark.unit
class TestFeedbackRequestSchema:
    """Tests for FeedbackRequest Pydantic schema validation."""

    def test_valid_feedback_request(self):
        """Test valid feedback request is accepted."""
        from life_organizer.schemas.feedback import FeedbackRequest

        req = FeedbackRequest(
            original_input="buy milk",
            wrong_category="note",
            correct_category="budget",
        )
        assert req.original_input == "buy milk"
        assert req.wrong_category.value == "note"
        assert req.correct_category.value == "budget"

    def test_case_insensitive_categories(self):
        """Test that uppercase category values are normalized to lowercase."""
        from life_organizer.schemas.feedback import FeedbackRequest

        req = FeedbackRequest(
            original_input="buy milk",
            wrong_category="NOTE",
            correct_category="BUDGET",
        )
        assert req.wrong_category.value == "note"
        assert req.correct_category.value == "budget"

    def test_missing_original_input(self):
        """Test that missing original_input raises validation error."""
        from life_organizer.schemas.feedback import FeedbackRequest

        with pytest.raises(ValidationError) as exc_info:
            FeedbackRequest(
                wrong_category="note",
                correct_category="budget",
            )
        assert "original_input" in str(exc_info.value)

    def test_missing_wrong_category(self):
        """Test that missing wrong_category raises validation error."""
        from life_organizer.schemas.feedback import FeedbackRequest

        with pytest.raises(ValidationError) as exc_info:
            FeedbackRequest(
                original_input="buy milk",
                correct_category="budget",
            )
        assert "wrong_category" in str(exc_info.value)

    def test_missing_correct_category(self):
        """Test that missing correct_category raises validation error."""
        from life_organizer.schemas.feedback import FeedbackRequest

        with pytest.raises(ValidationError) as exc_info:
            FeedbackRequest(
                original_input="buy milk",
                wrong_category="note",
            )
        assert "correct_category" in str(exc_info.value)

    def test_invalid_wrong_category(self):
        """Test that invalid wrong_category value raises validation error."""
        from life_organizer.schemas.feedback import FeedbackRequest

        with pytest.raises(ValidationError) as exc_info:
            FeedbackRequest(
                original_input="buy milk",
                wrong_category="shopping",
                correct_category="budget",
            )
        assert "wrong_category" in str(exc_info.value)

    def test_invalid_correct_category(self):
        """Test that invalid correct_category value raises validation error."""
        from life_organizer.schemas.feedback import FeedbackRequest

        with pytest.raises(ValidationError) as exc_info:
            FeedbackRequest(
                original_input="buy milk",
                wrong_category="note",
                correct_category="invalid",
            )
        assert "correct_category" in str(exc_info.value)

    def test_same_wrong_and_correct_category(self):
        """Test that same wrong_category and correct_category raises validation error."""
        from life_organizer.schemas.feedback import FeedbackRequest

        with pytest.raises(ValidationError) as exc_info:
            FeedbackRequest(
                original_input="buy milk",
                wrong_category="note",
                correct_category="note",
            )
        errors = exc_info.value.errors()
        assert any("must differ" in str(e["msg"]).lower() for e in errors)

    def test_empty_original_input(self):
        """Test that empty original_input raises validation error."""
        from life_organizer.schemas.feedback import FeedbackRequest

        with pytest.raises(ValidationError) as exc_info:
            FeedbackRequest(
                original_input="",
                wrong_category="note",
                correct_category="budget",
            )
        assert "original_input" in str(exc_info.value)

    def test_whitespace_only_original_input(self):
        """Test that whitespace-only original_input raises validation error."""
        from life_organizer.schemas.feedback import FeedbackRequest

        with pytest.raises(ValidationError) as exc_info:
            FeedbackRequest(
                original_input="   ",
                wrong_category="note",
                correct_category="budget",
            )
        assert "original_input" in str(exc_info.value)


@pytest.mark.unit
class TestFeedbackResponseSchema:
    """Tests for FeedbackResponse Pydantic schema."""

    def test_valid_feedback_response(self):
        """Test valid feedback response creation."""
        from life_organizer.schemas.feedback import FeedbackResponse

        resp = FeedbackResponse(success=True, message="Feedback recorded")
        assert resp.success is True
        assert resp.message == "Feedback recorded"
