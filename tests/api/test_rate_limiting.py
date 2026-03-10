"""Tests for rate limiting on LLM-hitting endpoints."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from life_organizer.db.session import get_db
from life_organizer.main import app
from life_organizer.rate_limit import limiter


@pytest.fixture(autouse=True)
def _reset_limiter():
    """Reset rate limiter state between tests."""
    limiter.reset()
    yield
    limiter.reset()


def _make_client() -> TestClient:
    """Create a TestClient for the app."""
    return TestClient(app)


@pytest.mark.unit
class TestBudgetRateLimiting:
    """Tests for rate limiting on POST /api/v1/budget."""

    @patch("life_organizer.api.routes.budget.budget_service")
    @patch("life_organizer.api.routes.budget.claude_service")
    def test_10_requests_within_limit_succeed(self, mock_claude: AsyncMock, mock_budget: AsyncMock):
        """10 requests to POST /api/v1/budget within 1 minute all succeed."""
        mock_claude.parse_budget_text = AsyncMock(return_value=[])
        mock_budget.create_entries = AsyncMock(return_value=[])

        client = _make_client()
        for i in range(10):
            response = client.post("/api/v1/budget/", json={"input": f"coffee {i}"})
            assert response.status_code == 200, (
                f"Request {i + 1} failed with {response.status_code}"
            )

    @patch("life_organizer.api.routes.budget.budget_service")
    @patch("life_organizer.api.routes.budget.claude_service")
    def test_11th_request_returns_429(self, mock_claude: AsyncMock, mock_budget: AsyncMock):
        """11th request to POST /api/v1/budget within 1 minute returns 429."""
        mock_claude.parse_budget_text = AsyncMock(return_value=[])
        mock_budget.create_entries = AsyncMock(return_value=[])

        client = _make_client()
        for i in range(10):
            response = client.post("/api/v1/budget/", json={"input": f"coffee {i}"})
            assert response.status_code == 200

        response = client.post("/api/v1/budget/", json={"input": "coffee 11"})
        assert response.status_code == 429

    @patch("life_organizer.api.routes.budget.budget_service")
    @patch("life_organizer.api.routes.budget.claude_service")
    def test_429_response_has_retry_after_header(
        self, mock_claude: AsyncMock, mock_budget: AsyncMock
    ):
        """429 response includes a Retry-After header."""
        mock_claude.parse_budget_text = AsyncMock(return_value=[])
        mock_budget.create_entries = AsyncMock(return_value=[])

        client = _make_client()
        for i in range(10):
            client.post("/api/v1/budget/", json={"input": f"coffee {i}"})

        response = client.post("/api/v1/budget/", json={"input": "coffee 11"})
        assert response.status_code == 429
        assert "retry-after" in response.headers

    @patch("life_organizer.api.routes.budget.budget_service")
    @patch("life_organizer.api.routes.budget.claude_service")
    def test_429_response_has_error_message(self, mock_claude: AsyncMock, mock_budget: AsyncMock):
        """429 response body contains a clear error message."""
        mock_claude.parse_budget_text = AsyncMock(return_value=[])
        mock_budget.create_entries = AsyncMock(return_value=[])

        client = _make_client()
        for i in range(10):
            client.post("/api/v1/budget/", json={"input": f"coffee {i}"})

        response = client.post("/api/v1/budget/", json={"input": "coffee 11"})
        assert response.status_code == 429
        body = response.json()
        assert "error" in body
        assert "rate limit" in body["error"].lower()


@pytest.mark.unit
class TestMealsSuggestRateLimiting:
    """Tests for rate limiting on POST /api/v1/meals/suggest."""

    @patch("life_organizer.api.routes.meals.meal_service")
    @patch("life_organizer.api.routes.meals.claude_service")
    def test_10_requests_within_limit_succeed(self, mock_claude: AsyncMock, mock_meal: AsyncMock):
        """10 requests to POST /api/v1/meals/suggest within 1 minute all succeed."""
        from life_organizer.schemas.meals import MealSuggestion

        mock_meal.get_suggestions = AsyncMock(
            return_value=[
                MealSuggestion(
                    name="Test",
                    ingredients=["a"],
                    instructions="Do.",
                    prep_time=10,
                    cuisine="Italian",
                    tags=[],
                )
            ]
        )

        client = _make_client()
        for i in range(10):
            response = client.post("/api/v1/meals/suggest", json={})
            assert response.status_code == 200, (
                f"Request {i + 1} failed with {response.status_code}"
            )

    @patch("life_organizer.api.routes.meals.meal_service")
    @patch("life_organizer.api.routes.meals.claude_service")
    def test_11th_request_returns_429(self, mock_claude: AsyncMock, mock_meal: AsyncMock):
        """11th request to POST /api/v1/meals/suggest within 1 minute returns 429."""
        from life_organizer.schemas.meals import MealSuggestion

        mock_meal.get_suggestions = AsyncMock(
            return_value=[
                MealSuggestion(
                    name="Test",
                    ingredients=["a"],
                    instructions="Do.",
                    prep_time=10,
                    cuisine="Italian",
                    tags=[],
                )
            ]
        )

        client = _make_client()
        for _i in range(10):
            response = client.post("/api/v1/meals/suggest", json={})
            assert response.status_code == 200

        response = client.post("/api/v1/meals/suggest", json={})
        assert response.status_code == 429

    @patch("life_organizer.api.routes.meals.meal_service")
    @patch("life_organizer.api.routes.meals.claude_service")
    def test_429_response_has_retry_after_header(
        self, mock_claude: AsyncMock, mock_meal: AsyncMock
    ):
        """429 response includes a Retry-After header."""
        from life_organizer.schemas.meals import MealSuggestion

        mock_meal.get_suggestions = AsyncMock(
            return_value=[
                MealSuggestion(
                    name="Test",
                    ingredients=["a"],
                    instructions="Do.",
                    prep_time=10,
                    cuisine="Italian",
                    tags=[],
                )
            ]
        )

        client = _make_client()
        for _i in range(10):
            client.post("/api/v1/meals/suggest", json={})

        response = client.post("/api/v1/meals/suggest", json={})
        assert response.status_code == 429
        assert "retry-after" in response.headers

    @patch("life_organizer.api.routes.meals.meal_service")
    @patch("life_organizer.api.routes.meals.claude_service")
    def test_429_response_has_error_message(self, mock_claude: AsyncMock, mock_meal: AsyncMock):
        """429 response body contains a clear error message."""
        from life_organizer.schemas.meals import MealSuggestion

        mock_meal.get_suggestions = AsyncMock(
            return_value=[
                MealSuggestion(
                    name="Test",
                    ingredients=["a"],
                    instructions="Do.",
                    prep_time=10,
                    cuisine="Italian",
                    tags=[],
                )
            ]
        )

        client = _make_client()
        for _i in range(10):
            client.post("/api/v1/meals/suggest", json={})

        response = client.post("/api/v1/meals/suggest", json={})
        assert response.status_code == 429
        body = response.json()
        assert "error" in body
        assert "rate limit" in body["error"].lower()


@pytest.mark.unit
class TestNonLLMEndpointsNotRateLimited:
    """Tests that non-LLM endpoints are NOT rate limited."""

    def test_health_endpoint_not_rate_limited(self):
        """GET /api/v1/health is NOT rate limited."""
        client = _make_client()
        for i in range(15):
            response = client.get("/api/v1/health")
            assert response.status_code == 200, f"Health request {i + 1} was rate limited"

    def test_feedback_endpoint_not_rate_limited(self):
        """POST /api/v1/feedback is NOT rate limited."""
        mock_db = AsyncMock()

        async def override_get_db() -> AsyncGenerator[AsyncMock]:
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        try:
            client = _make_client()
            payload = {
                "original_input": "test input",
                "wrong_category": "budget",
                "correct_category": "unknown",
            }
            for i in range(15):
                response = client.post("/api/v1/feedback/", json=payload)
                assert response.status_code == 201, (
                    f"Feedback request {i + 1} failed with {response.status_code}"
                )
        finally:
            app.dependency_overrides.clear()

    @patch("life_organizer.api.routes.budget.async_session_factory")
    def test_budget_export_not_rate_limited(self, mock_session_factory: MagicMock):
        """GET /api/v1/budget/export is NOT rate limited."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        @asynccontextmanager
        async def mock_context_manager() -> AsyncGenerator[AsyncMock]:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(return_value=mock_result)
            yield mock_session

        client = _make_client()
        for i in range(15):
            mock_session_factory.return_value = mock_context_manager()
            response = client.get("/api/v1/budget/export?start_date=2026-01-01")
            assert response.status_code == 200, (
                f"Export request {i + 1} failed with {response.status_code}"
            )
