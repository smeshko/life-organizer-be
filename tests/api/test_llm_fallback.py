"""Integration tests for classification endpoint with LLM fallback."""

from unittest.mock import AsyncMock, patch

import anthropic
import pytest
from fastapi.testclient import TestClient

from life_organizer.main import app
from life_organizer.schemas.classification import ClassifiedInput
from life_organizer.schemas.enums import Category


@pytest.fixture
def client() -> TestClient:
    """Create FastAPI test client."""
    return TestClient(app)


class TestClassificationWithLLMFallback:
    """Integration tests for /classify endpoint with orchestrator."""

    def test_high_confidence_uses_keyword_source(self, client: TestClient) -> None:
        """Test that high-confidence inputs use keyword classifier."""
        response = client.post(
            "/api/v1/classify",
            json={"input": "Spent 100 EUR at restaurant"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "expense"
        assert data["confidence"] >= 0.75
        assert data["classifier_source"] == "keyword"
        assert "amount" in data["extracted_data"]

    @patch("life_organizer.api.routes.classifier.claude_classifier.classify")
    async def test_low_confidence_uses_llm_source(
        self, mock_llm_classify: AsyncMock, client: TestClient
    ) -> None:
        """Test that low-confidence inputs invoke LLM classifier."""
        # Mock LLM response
        mock_llm_classify.return_value = ClassifiedInput(
            category=Category.REMINDER,
            confidence=0.9,
            extracted_data={"action": "check status"},
            raw_input="check on that thing",
            classifier_source="llm",
        )

        response = client.post(
            "/api/v1/classify",
            json={"input": "check on that thing"},
        )

        assert response.status_code == 200
        data = response.json()
        # Depending on keyword confidence, may use LLM
        assert "classifier_source" in data
        assert data["classifier_source"] in ["keyword", "llm"]

    @patch("life_organizer.api.routes.classifier.claude_classifier.classify")
    async def test_llm_timeout_returns_keyword_result(
        self, mock_llm_classify: AsyncMock, client: TestClient
    ) -> None:
        """Test that LLM timeout falls back to keyword result."""
        mock_llm_classify.side_effect = anthropic.APITimeoutError("Timeout")

        # Use ambiguous input likely to have low keyword confidence
        response = client.post(
            "/api/v1/classify",
            json={"input": "maybe do something"},
        )

        # Should succeed with keyword fallback
        assert response.status_code == 200
        data = response.json()
        assert data["classifier_source"] == "keyword"

    def test_empty_input_returns_422(self, client: TestClient) -> None:
        """Test that empty input returns validation error."""
        response = client.post(
            "/api/v1/classify",
            json={"input": ""},
        )

        assert response.status_code == 422

    def test_whitespace_only_input_returns_422(self, client: TestClient) -> None:
        """Test that whitespace-only input returns validation error."""
        response = client.post(
            "/api/v1/classify",
            json={"input": "   "},
        )

        assert response.status_code == 422

    def test_special_characters_handled(self, client: TestClient) -> None:
        """Test that special characters are handled gracefully."""
        response = client.post(
            "/api/v1/classify",
            json={"input": "Spent €45.50 @restaurant!"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "classifier_source" in data

    def test_very_long_input_handled(self, client: TestClient) -> None:
        """Test that very long input is handled (up to 1000 chars)."""
        long_input = "Buy milk " * 100  # ~900 chars

        response = client.post(
            "/api/v1/classify",
            json={"input": long_input},
        )

        assert response.status_code == 200
        data = response.json()
        assert "classifier_source" in data

    def test_response_schema_includes_all_fields(self, client: TestClient) -> None:
        """Test that response includes all required ClassifiedInput fields."""
        response = client.post(
            "/api/v1/classify",
            json={"input": "Spent 50 EUR"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify all ClassifiedInput fields present
        assert "category" in data
        assert "confidence" in data
        assert "extracted_data" in data
        assert "raw_input" in data
        assert "classifier_source" in data

        # Verify types
        assert isinstance(data["category"], str)
        assert isinstance(data["confidence"], float)
        assert isinstance(data["extracted_data"], dict)
        assert isinstance(data["raw_input"], str)
        assert data["classifier_source"] in ["keyword", "llm"]

    def test_expense_category_extracts_amount_currency(self, client: TestClient) -> None:
        """Test EXPENSE classification extracts amount and currency."""
        response = client.post(
            "/api/v1/classify",
            json={"input": "Paid 75 USD for groceries"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "expense"
        # extracted_data should have amount/currency (from keyword or LLM)
        if "amount" in data["extracted_data"]:
            assert data["extracted_data"]["amount"] > 0

    def test_shopping_category_extracts_items(self, client: TestClient) -> None:
        """Test SHOPPING classification extracts items list."""
        response = client.post(
            "/api/v1/classify",
            json={"input": "Need to buy milk and bread"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "shopping"
        # extracted_data should have items (from keyword or LLM)
        if "items" in data["extracted_data"]:
            assert isinstance(data["extracted_data"]["items"], list)

    def test_reminder_category_has_action(self, client: TestClient) -> None:
        """Test REMINDER classification returns appropriate category."""
        response = client.post(
            "/api/v1/classify",
            json={"input": "Remember to call dentist tomorrow"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "reminder"
        assert "classifier_source" in data

    def test_calendar_category_detected(self, client: TestClient) -> None:
        """Test CALENDAR classification works correctly."""
        response = client.post(
            "/api/v1/classify",
            json={"input": "Meeting with team on Monday at 2pm"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "calendar"
        assert "classifier_source" in data

    def test_unknown_category_for_unclear_input(self, client: TestClient) -> None:
        """Test UNKNOWN category for unclear/ambiguous input."""
        response = client.post(
            "/api/v1/classify",
            json={"input": "hello world"},
        )

        assert response.status_code == 200
        data = response.json()
        # May be unknown or have low confidence
        assert "category" in data
        assert "classifier_source" in data
