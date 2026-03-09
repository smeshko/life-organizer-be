"""Tests for feedback schema validation and API endpoint."""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from life_organizer.db.session import get_db
from life_organizer.main import app

FEEDBACK_URL = "/api/v1/feedback"


async def _mock_get_db() -> AsyncGenerator[AsyncMock]:
    """Mock database session for endpoint tests."""
    session = AsyncMock()
    yield session


@pytest.fixture
def client():
    """TestClient with mocked database dependency."""
    app.dependency_overrides[get_db] = _mock_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.mark.unit
class TestFeedbackRequestSchema:
    """Tests for FeedbackRequest Pydantic schema validation."""

    def test_valid_feedback_request(self):
        """Test valid feedback request is accepted."""
        from life_organizer.schemas.feedback import FeedbackRequest

        req = FeedbackRequest(
            original_input="buy milk",
            wrong_category="unknown",
            correct_category="budget",
        )
        assert req.original_input == "buy milk"
        assert req.wrong_category.value == "unknown"
        assert req.correct_category.value == "budget"

    def test_case_insensitive_categories(self):
        """Test that uppercase category values are normalized to lowercase."""
        from life_organizer.schemas.feedback import FeedbackRequest

        req = FeedbackRequest(
            original_input="buy milk",
            wrong_category="UNKNOWN",
            correct_category="BUDGET",
        )
        assert req.wrong_category.value == "unknown"
        assert req.correct_category.value == "budget"

    def test_missing_original_input(self):
        """Test that missing original_input raises validation error."""
        from life_organizer.schemas.feedback import FeedbackRequest

        with pytest.raises(ValidationError) as exc_info:
            FeedbackRequest(
                wrong_category="unknown",
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
                wrong_category="unknown",
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
                wrong_category="unknown",
                correct_category="invalid",
            )
        assert "correct_category" in str(exc_info.value)

    def test_same_wrong_and_correct_category(self):
        """Test that same wrong_category and correct_category raises validation error."""
        from life_organizer.schemas.feedback import FeedbackRequest

        with pytest.raises(ValidationError) as exc_info:
            FeedbackRequest(
                original_input="buy milk",
                wrong_category="budget",
                correct_category="budget",
            )
        errors = exc_info.value.errors()
        assert any("must differ" in str(e["msg"]).lower() for e in errors)

    def test_empty_original_input(self):
        """Test that empty original_input raises validation error."""
        from life_organizer.schemas.feedback import FeedbackRequest

        with pytest.raises(ValidationError) as exc_info:
            FeedbackRequest(
                original_input="",
                wrong_category="unknown",
                correct_category="budget",
            )
        assert "original_input" in str(exc_info.value)

    def test_whitespace_only_original_input(self):
        """Test that whitespace-only original_input raises validation error."""
        from life_organizer.schemas.feedback import FeedbackRequest

        with pytest.raises(ValidationError) as exc_info:
            FeedbackRequest(
                original_input="   ",
                wrong_category="unknown",
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


@pytest.mark.unit
class TestFeedbackRoute:
    """Tests for the feedback route handler logic."""

    @pytest.mark.asyncio
    async def test_submit_feedback_creates_model_and_adds_to_session(self):
        """Test that submit_feedback creates a MisclassificationFeedback and adds to db."""
        from life_organizer.api.routes.feedback import submit_feedback
        from life_organizer.schemas.feedback import FeedbackRequest

        mock_db = AsyncMock()

        request = FeedbackRequest(
            original_input="buy milk",
            wrong_category="unknown",
            correct_category="budget",
        )

        response = await submit_feedback(request=request, db=mock_db)

        assert response.success is True
        assert response.message == "Feedback recorded"
        mock_db.add.assert_called_once()

        # Verify the model passed to db.add has correct values
        added_model = mock_db.add.call_args[0][0]
        assert added_model.original_input == "buy milk"
        assert added_model.wrong_category == "unknown"
        assert added_model.correct_category == "budget"


@pytest.mark.unit
class TestFeedbackEndpoint:
    """Integration tests for POST /api/v1/feedback endpoint."""

    def test_submit_feedback_success(self, client):
        """Test happy path: valid payload returns 201 with success response."""
        response = client.post(
            FEEDBACK_URL,
            json={
                "original_input": "buy milk",
                "wrong_category": "unknown",
                "correct_category": "budget",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Feedback recorded"

    def test_submit_feedback_case_insensitive(self, client):
        """Test uppercase category values are accepted and normalized."""
        response = client.post(
            FEEDBACK_URL,
            json={
                "original_input": "should be budget",
                "wrong_category": "UNKNOWN",
                "correct_category": "BUDGET",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True

    def test_missing_original_input_returns_422(self, client):
        """Test missing original_input field returns 422."""
        response = client.post(
            FEEDBACK_URL,
            json={
                "wrong_category": "unknown",
                "correct_category": "budget",
            },
        )
        assert response.status_code == 422

    def test_missing_wrong_category_returns_422(self, client):
        """Test missing wrong_category field returns 422."""
        response = client.post(
            FEEDBACK_URL,
            json={
                "original_input": "buy milk",
                "correct_category": "budget",
            },
        )
        assert response.status_code == 422

    def test_missing_correct_category_returns_422(self, client):
        """Test missing correct_category field returns 422."""
        response = client.post(
            FEEDBACK_URL,
            json={
                "original_input": "buy milk",
                "wrong_category": "unknown",
            },
        )
        assert response.status_code == 422

    def test_invalid_wrong_category_returns_422(self, client):
        """Test invalid wrong_category value returns 422."""
        response = client.post(
            FEEDBACK_URL,
            json={
                "original_input": "buy milk",
                "wrong_category": "shopping",
                "correct_category": "budget",
            },
        )
        assert response.status_code == 422

    def test_invalid_correct_category_returns_422(self, client):
        """Test invalid correct_category value returns 422."""
        response = client.post(
            FEEDBACK_URL,
            json={
                "original_input": "buy milk",
                "wrong_category": "unknown",
                "correct_category": "invalid",
            },
        )
        assert response.status_code == 422

    def test_same_categories_returns_422(self, client):
        """Test wrong_category == correct_category returns 422."""
        response = client.post(
            FEEDBACK_URL,
            json={
                "original_input": "buy milk",
                "wrong_category": "budget",
                "correct_category": "budget",
            },
        )
        assert response.status_code == 422

    def test_empty_original_input_returns_422(self, client):
        """Test empty original_input returns 422."""
        response = client.post(
            FEEDBACK_URL,
            json={
                "original_input": "",
                "wrong_category": "unknown",
                "correct_category": "budget",
            },
        )
        assert response.status_code == 422

    def test_whitespace_only_input_returns_422(self, client):
        """Test whitespace-only original_input returns 422."""
        response = client.post(
            FEEDBACK_URL,
            json={
                "original_input": "   ",
                "wrong_category": "unknown",
                "correct_category": "budget",
            },
        )
        assert response.status_code == 422

    def test_empty_body_returns_422(self, client):
        """Test completely empty JSON body returns 422."""
        response = client.post(FEEDBACK_URL, json={})
        assert response.status_code == 422
