"""Unit tests for ClaudeClassifier service."""

import json
from unittest.mock import AsyncMock, Mock

import anthropic
import pytest
from anthropic.types import TextBlock

from life_organizer.schemas.enums import Category
from life_organizer.services.claude_classifier import ClaudeClassifier


@pytest.fixture
def mock_anthropic_client() -> AsyncMock:
    """Create mocked AsyncAnthropic client."""
    client = AsyncMock()
    return client


@pytest.fixture
def claude_classifier(mock_anthropic_client: AsyncMock) -> ClaudeClassifier:
    """Create ClaudeClassifier with mocked client."""
    classifier = ClaudeClassifier(api_key="test-api-key")
    classifier.client = mock_anthropic_client
    return classifier


class TestClaudeClassifier:
    """Test suite for ClaudeClassifier service."""

    @pytest.mark.asyncio
    async def test_classify_expense_success(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ) -> None:
        """Test successful budget classification with comprehensive data extraction."""
        # Mock successful API response with all required fields
        mock_response = Mock()
        mock_response.content = [
            TextBlock(
                type="text",
                text=json.dumps(
                    {
                        "category": "budget",
                        "confidence": 0.95,
                        "extracted_data": {
                            "amount": 45.0,
                            "currency": "EUR",
                            "transaction_type": "Expenses",
                            "category": "Eat out",
                            "merchant": "restaurant",
                            "date": "2025-11-04",
                        },
                        "raw_input": "Spent 45 EUR at restaurant",
                    }
                ),
            )
        ]
        mock_anthropic_client.messages.create.return_value = mock_response

        # Classify
        result = await claude_classifier.classify("Spent 45 EUR at restaurant")

        # Assertions
        assert result.category == Category.BUDGET
        assert result.confidence == 0.95
        assert result.classifier_source == "llm"
        assert result.extracted_data["amount"] == 45.0
        assert result.extracted_data["currency"] == "EUR"
        assert result.extracted_data["transaction_type"] == "Expenses"
        assert result.extracted_data["category"] == "Eat out"
        assert result.extracted_data["merchant"] == "restaurant"
        assert result.extracted_data["date"] == "2025-11-04"

    @pytest.mark.asyncio
    async def test_classify_shopping_success(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ) -> None:
        """Test successful shopping classification with items list."""
        mock_response = Mock()
        mock_response.content = [
            TextBlock(
                type="text",
                text=json.dumps(
                    {
                        "category": "shopping",
                        "confidence": 0.9,
                        "extracted_data": {"items": ["milk", "eggs", "bread"]},
                        "raw_input": "Buy milk, eggs and bread",
                    }
                ),
            )
        ]
        mock_anthropic_client.messages.create.return_value = mock_response

        result = await claude_classifier.classify("Buy milk, eggs and bread")

        assert result.category == Category.SHOPPING
        assert result.confidence == 0.9
        assert result.classifier_source == "llm"
        assert "milk" in result.extracted_data["items"]
        assert "eggs" in result.extracted_data["items"]

    @pytest.mark.asyncio
    async def test_classify_reminder_success(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ) -> None:
        """Test successful reminder classification with action field."""
        mock_response = Mock()
        mock_response.content = [
            TextBlock(
                type="text",
                text=json.dumps(
                    {
                        "category": "reminder",
                        "confidence": 0.85,
                        "extracted_data": {"action": "call dentist"},
                        "raw_input": "Call dentist tomorrow",
                    }
                ),
            )
        ]
        mock_anthropic_client.messages.create.return_value = mock_response

        result = await claude_classifier.classify("Call dentist tomorrow")

        assert result.category == Category.REMINDER
        assert result.confidence == 0.85
        assert result.classifier_source == "llm"
        assert result.extracted_data["action"] == "call dentist"

    @pytest.mark.asyncio
    async def test_classify_calendar_success(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ) -> None:
        """Test successful calendar classification with time reference."""
        mock_response = Mock()
        mock_response.content = [
            TextBlock(
                type="text",
                text=json.dumps(
                    {
                        "category": "calendar",
                        "confidence": 0.88,
                        "extracted_data": {"time_reference": "Monday 3pm"},
                        "raw_input": "Meeting on Monday at 3pm",
                    }
                ),
            )
        ]
        mock_anthropic_client.messages.create.return_value = mock_response

        result = await claude_classifier.classify("Meeting on Monday at 3pm")

        assert result.category == Category.CALENDAR
        assert result.confidence == 0.88
        assert result.classifier_source == "llm"
        assert result.extracted_data["time_reference"] == "Monday 3pm"

    @pytest.mark.asyncio
    async def test_classify_unknown_success(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ) -> None:
        """Test successful unknown classification for ambiguous input."""
        mock_response = Mock()
        mock_response.content = [
            TextBlock(
                type="text",
                text=json.dumps(
                    {
                        "category": "unknown",
                        "confidence": 0.3,
                        "extracted_data": {},
                        "raw_input": "Hello there",
                    }
                ),
            )
        ]
        mock_anthropic_client.messages.create.return_value = mock_response

        result = await claude_classifier.classify("Hello there")

        assert result.category == Category.UNKNOWN
        assert result.confidence == 0.3
        assert result.classifier_source == "llm"

    @pytest.mark.asyncio
    async def test_api_timeout_error(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ) -> None:
        """Test that API timeout errors propagate to orchestrator."""
        mock_anthropic_client.messages.create.side_effect = anthropic.APITimeoutError(
            "Request timed out"
        )

        with pytest.raises(anthropic.APITimeoutError):
            await claude_classifier.classify("Test input")

    @pytest.mark.asyncio
    async def test_api_connection_error(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ) -> None:
        """Test that API connection errors propagate."""
        # Create a mock request for the error
        mock_request = Mock()
        mock_anthropic_client.messages.create.side_effect = anthropic.APIConnectionError(
            message="Connection failed", request=mock_request
        )

        with pytest.raises(anthropic.APIConnectionError):
            await claude_classifier.classify("Test input")

    @pytest.mark.asyncio
    async def test_rate_limit_error(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ) -> None:
        """Test that rate limit errors propagate."""
        # Create a mock response for the error
        mock_response = Mock()
        mock_response.status_code = 429
        mock_anthropic_client.messages.create.side_effect = anthropic.RateLimitError(
            message="Rate limit exceeded", response=mock_response, body={}
        )

        with pytest.raises(anthropic.RateLimitError):
            await claude_classifier.classify("Test input")

    @pytest.mark.asyncio
    async def test_authentication_error(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ) -> None:
        """Test that authentication errors propagate."""
        # Create a mock response for the error
        mock_response = Mock()
        mock_response.status_code = 401
        mock_anthropic_client.messages.create.side_effect = anthropic.AuthenticationError(
            message="Invalid API key", response=mock_response, body={}
        )

        with pytest.raises(anthropic.AuthenticationError):
            await claude_classifier.classify("Test input")

    @pytest.mark.asyncio
    async def test_malformed_json_response(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ) -> None:
        """Test handling of malformed JSON response."""
        mock_response = Mock()
        mock_response.content = [TextBlock(type="text", text="This is not valid JSON {")]
        mock_anthropic_client.messages.create.return_value = mock_response

        result = await claude_classifier.classify("Test input")

        # Should return UNKNOWN with low confidence
        assert result.category == Category.UNKNOWN
        assert result.confidence == 0.0
        assert result.classifier_source == "llm"

    @pytest.mark.asyncio
    async def test_missing_category_field(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ) -> None:
        """Test handling of response with missing category field."""
        mock_response = Mock()
        mock_response.content = [
            TextBlock(
                type="text",
                text=json.dumps(
                    {
                        "confidence": 0.8,
                        "extracted_data": {},
                        "raw_input": "Test",
                    }
                ),
            )
        ]
        mock_anthropic_client.messages.create.return_value = mock_response

        result = await claude_classifier.classify("Test")

        # Should return UNKNOWN due to missing category
        assert result.category == Category.UNKNOWN

    @pytest.mark.asyncio
    async def test_unrecognized_category(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ) -> None:
        """Test that unrecognized categories map to UNKNOWN."""
        mock_response = Mock()
        mock_response.content = [
            TextBlock(
                type="text",
                text=json.dumps(
                    {
                        "category": "invalid_category",
                        "confidence": 0.8,
                        "extracted_data": {},
                        "raw_input": "Test",
                    }
                ),
            )
        ]
        mock_anthropic_client.messages.create.return_value = mock_response

        result = await claude_classifier.classify("Test")

        assert result.category == Category.UNKNOWN
