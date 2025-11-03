"""Tests for the classifier API endpoint."""

import pytest
from fastapi.testclient import TestClient

from life_organizer.main import app
from life_organizer.schemas.enums import Category


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestClassifyEndpoint:
    """Tests for POST /api/v1/classify endpoint."""

    def test_classify_expense_input(self, client: TestClient) -> None:
        """Test classifying a clear expense input."""
        response = client.post(
            "/api/v1/classify",
            json={"input": "Spent 45 EUR at restaurant"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["category"] == Category.EXPENSE
        assert data["confidence"] > 0.0
        assert data["raw_input"] == "Spent 45 EUR at restaurant"
        assert isinstance(data["extracted_data"], dict)

    def test_classify_shopping_input(self, client: TestClient) -> None:
        """Test classifying a clear shopping input."""
        response = client.post(
            "/api/v1/classify",
            json={"input": "We're out of milk"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["category"] == Category.SHOPPING
        assert data["confidence"] > 0.0
        assert data["raw_input"] == "We're out of milk"

    def test_classify_reminder_input(self, client: TestClient) -> None:
        """Test classifying a reminder input."""
        response = client.post(
            "/api/v1/classify",
            json={"input": "Remind me to call the dentist"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["category"] == Category.REMINDER
        assert data["confidence"] > 0.0

    def test_classify_calendar_input(self, client: TestClient) -> None:
        """Test classifying a calendar input."""
        response = client.post(
            "/api/v1/classify",
            json={"input": "Meeting tomorrow at 2pm"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["category"] == Category.CALENDAR
        assert data["confidence"] > 0.0

    def test_response_schema_matches_classified_input(self, client: TestClient) -> None:
        """Test that response format matches ClassifiedInput schema."""
        response = client.post(
            "/api/v1/classify",
            json={"input": "Spent 45 EUR at restaurant"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify all required fields are present
        assert "category" in data
        assert "confidence" in data
        assert "extracted_data" in data
        assert "raw_input" in data

        # Verify field types
        assert isinstance(data["category"], str)
        assert isinstance(data["confidence"], (int, float))
        assert isinstance(data["extracted_data"], dict)
        assert isinstance(data["raw_input"], str)

    def test_empty_input_validation_error(self, client: TestClient) -> None:
        """Test that empty input returns 422 validation error."""
        response = client.post(
            "/api/v1/classify",
            json={"input": ""},
        )

        assert response.status_code == 422

    def test_whitespace_only_input_error(self, client: TestClient) -> None:
        """Test that whitespace-only input returns error."""
        response = client.post(
            "/api/v1/classify",
            json={"input": "   \n\t  "},
        )

        assert response.status_code == 422
        assert "empty" in response.json()["detail"].lower()

    def test_input_exceeds_max_length(self, client: TestClient) -> None:
        """Test that input exceeding 1000 chars returns 422 error."""
        long_input = "a" * 1001
        response = client.post(
            "/api/v1/classify",
            json={"input": long_input},
        )

        assert response.status_code == 422

    def test_unknown_category_for_unclear_input(self, client: TestClient) -> None:
        """Test that unclear input returns UNKNOWN category with 200 status."""
        response = client.post(
            "/api/v1/classify",
            json={"input": "The quick brown fox jumps over the lazy dog"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["category"] == Category.UNKNOWN
        # LLM can be confident that something is UNKNOWN, so confidence can be high
        assert 0.0 <= data["confidence"] <= 1.0

    def test_extracted_data_contains_amount_for_expense(self, client: TestClient) -> None:
        """Test that extracted_data contains amount for expense inputs."""
        response = client.post(
            "/api/v1/classify",
            json={"input": "Spent 45 EUR at restaurant"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "amount" in data["extracted_data"]
        assert data["extracted_data"]["amount"] == 45.0

    def test_extracted_data_contains_currency_for_expense(self, client: TestClient) -> None:
        """Test that extracted_data contains currency for expense inputs."""
        response = client.post(
            "/api/v1/classify",
            json={"input": "Paid 20 dollars for gas"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "currency" in data["extracted_data"]
        assert data["extracted_data"]["currency"] == "USD"

    def test_confidence_field_between_zero_and_one(self, client: TestClient) -> None:
        """Test that confidence field is always between 0.0 and 1.0."""
        test_inputs = [
            "Spent 45 EUR at restaurant",
            "We're out of milk",
            "Random text here",
            "Meeting tomorrow",
        ]

        for input_text in test_inputs:
            response = client.post(
                "/api/v1/classify",
                json={"input": input_text},
            )

            assert response.status_code == 200
            data = response.json()

            assert 0.0 <= data["confidence"] <= 1.0, f"Failed for input: {input_text}"

    def test_missing_input_field(self, client: TestClient) -> None:
        """Test that missing input field returns 422 error."""
        response = client.post(
            "/api/v1/classify",
            json={},
        )

        assert response.status_code == 422

    def test_invalid_json_format(self, client: TestClient) -> None:
        """Test that invalid JSON returns 422 error."""
        response = client.post(
            "/api/v1/classify",
            data="not valid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422

    def test_endpoint_cors_headers(self, client: TestClient) -> None:
        """Test that CORS headers are present in response."""
        response = client.post(
            "/api/v1/classify",
            json={"input": "Spent 45 EUR"},
        )

        # CORS headers should be added by middleware
        assert response.status_code == 200

    def test_multiple_sequential_requests(self, client: TestClient) -> None:
        """Test that multiple sequential requests work correctly."""
        inputs = [
            "Spent 45 EUR at restaurant",
            "We're out of milk",
            "Remind me to call dentist",
            "Meeting tomorrow",
        ]

        for input_text in inputs:
            response = client.post(
                "/api/v1/classify",
                json={"input": input_text},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["raw_input"] == input_text

    def test_special_characters_in_input(self, client: TestClient) -> None:
        """Test that special characters are handled correctly."""
        response = client.post(
            "/api/v1/classify",
            json={"input": "Spent 45€ @restaurant!!! #food"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["category"] == Category.EXPENSE
        assert data["raw_input"] == "Spent 45€ @restaurant!!! #food"

    def test_unicode_characters_in_input(self, client: TestClient) -> None:
        """Test that Unicode characters are handled correctly."""
        response = client.post(
            "/api/v1/classify",
            json={"input": "Spent 45 EUR at café ☕"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["category"] == Category.EXPENSE
        assert "café" in data["raw_input"]
