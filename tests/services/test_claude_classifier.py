"""Unit tests for ClaudeClassifier service."""

import json
from unittest.mock import AsyncMock, Mock

import anthropic
import pytest
from anthropic.types import TextBlock

from life_organizer.schemas.enums import Category
from life_organizer.services.claude_classifier import ClaudeClassifier


def _set_llm_response(mock_client: AsyncMock, payload: dict) -> None:
    """Helper to configure mocked Anthropic client responses."""
    mock_response = Mock()
    # Always return an array, even for single transactions (classifier expects array)
    mock_response.content = [TextBlock(type="text", text=json.dumps([payload]))]
    mock_client.messages.create.return_value = mock_response


def _budget_payload(
    *,
    amount: float = 120.0,
    currency: str = "EUR",
    transaction_type: str = "Expenses",
    category: str = "Groceries",
    merchant: str | None = "billa",
    date: str = "2025-11-04",
    raw_input: str = "example input",
) -> dict:
    """Build a default budget payload with overrides."""
    extracted_data: dict[str, object] = {
        "amount": amount,
        "currency": currency,
        "transaction_type": transaction_type,
        "category": category,
        "date": date,
    }
    if merchant is not None:
        extracted_data["merchant"] = merchant

    return {
        "category": "budget",
        "confidence": 0.95,
        "extracted_data": extracted_data,
        "raw_input": raw_input,
    }


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


class TestClaudeClassifierExtraction:
    """Extraction-focused tests verifying structured data handling."""

    @pytest.mark.asyncio
    async def test_extract_transaction_type_expense(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ) -> None:
        _set_llm_response(
            mock_anthropic_client,
            _budget_payload(transaction_type="Expenses", raw_input="spent 120eur at next"),
        )

        results = await claude_classifier.classify("spent 120eur at next")

        # Classifier always returns a list
        assert len(results) == 1
        result = results[0]
        assert result.category == Category.BUDGET
        assert result.extracted_data["transaction_type"] == "Expenses"

    @pytest.mark.asyncio
    async def test_extract_transaction_type_income(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ) -> None:
        _set_llm_response(
            mock_anthropic_client,
            _budget_payload(
                transaction_type="Income",
                category="Salary",
                merchant="company",
                raw_input="received salary 2500",
            ),
        )

        results = await claude_classifier.classify("received salary 2500")

        # Classifier always returns a list
        assert len(results) == 1
        result = results[0]
        assert result.category == Category.BUDGET
        assert result.extracted_data["transaction_type"] == "Income"
        assert result.extracted_data["category"] == "Salary"

    @pytest.mark.asyncio
    async def test_extract_transaction_type_savings(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ) -> None:
        _set_llm_response(
            mock_anthropic_client,
            _budget_payload(
                transaction_type="Savings",
                category="Savings",
                merchant=None,
                raw_input="saved 1220 in ibkr",
            ),
        )

        results = await claude_classifier.classify("saved 1220 in ibkr")

        # Classifier always returns a list
        assert len(results) == 1
        result = results[0]

        assert result.category == Category.BUDGET
        assert result.extracted_data["transaction_type"] == "Savings"
        assert "merchant" not in result.extracted_data

    @pytest.mark.asyncio
    async def test_extract_budget_category(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ) -> None:
        _set_llm_response(
            mock_anthropic_client,
            _budget_payload(
                category="Clothes", merchant="next", raw_input="bought clothes at next"
            ),
        )

        results = await claude_classifier.classify("bought clothes at next")

        # Classifier always returns a list
        assert len(results) == 1
        result = results[0]

        assert result.extracted_data["category"] == "Clothes"
        assert result.extracted_data["merchant"] == "next"

    @pytest.mark.asyncio
    async def test_extract_merchant_details(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ) -> None:
        _set_llm_response(
            mock_anthropic_client,
            _budget_payload(merchant="coffee shop", raw_input="15 coffee with friends"),
        )

        results = await claude_classifier.classify("15 coffee with friends")

        # Classifier always returns a list
        assert len(results) == 1
        result = results[0]

        assert result.extracted_data["merchant"] == "coffee shop"

    @pytest.mark.asyncio
    async def test_extract_date_relative(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ) -> None:
        _set_llm_response(
            mock_anthropic_client,
            _budget_payload(
                date="2025-11-03", merchant="banitsa", raw_input="7 for banitsa yesterday"
            ),
        )

        results = await claude_classifier.classify("7 for banitsa yesterday")

        # Classifier always returns a list
        assert len(results) == 1
        result = results[0]

        assert result.extracted_data["date"] == "2025-11-03"

    @pytest.mark.asyncio
    async def test_extract_date_day_name(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ) -> None:
        _set_llm_response(
            mock_anthropic_client,
            _budget_payload(
                date="2025-11-03",
                transaction_type="Income",
                category="Rent",
                merchant="tenant",
                raw_input="received rent on Monday",
            ),
        )

        results = await claude_classifier.classify("received rent on Monday")

        # Classifier always returns a list
        assert len(results) == 1
        result = results[0]

        assert result.extracted_data["date"] == "2025-11-03"
        assert result.extracted_data["transaction_type"] == "Income"

    @pytest.mark.asyncio
    async def test_extract_date_specific(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ) -> None:
        _set_llm_response(
            mock_anthropic_client,
            _budget_payload(date="2025-01-05", raw_input="spent 30 on Jan 5th"),
        )

        results = await claude_classifier.classify("spent 30 on Jan 5th")

        # Classifier always returns a list
        assert len(results) == 1
        result = results[0]

        assert result.extracted_data["date"] == "2025-01-05"

    @pytest.mark.asyncio
    async def test_shopping_category_success(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ) -> None:
        payload = {
            "category": "shopping",
            "confidence": 0.9,
            "extracted_data": {"items": ["milk", "eggs", "bread"]},
            "raw_input": "Buy milk, eggs and bread",
        }
        _set_llm_response(mock_anthropic_client, payload)

        results = await claude_classifier.classify("Buy milk, eggs and bread")

        # Classifier always returns a list
        assert len(results) == 1
        result = results[0]

        assert result.category == Category.SHOPPING
        assert result.extracted_data["items"] == ["milk", "eggs", "bread"]

    @pytest.mark.asyncio
    async def test_calendar_category_success(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ) -> None:
        payload = {
            "category": "calendar",
            "confidence": 0.88,
            "extracted_data": {"time_reference": "Monday 3pm"},
            "raw_input": "Meeting on Monday at 3pm",
        }
        _set_llm_response(mock_anthropic_client, payload)

        results = await claude_classifier.classify("Meeting on Monday at 3pm")

        # Classifier always returns a list
        assert len(results) == 1
        result = results[0]

        assert result.category == Category.CALENDAR
        assert result.extracted_data["time_reference"] == "Monday 3pm"

    @pytest.mark.asyncio
    async def test_unknown_category_success(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ) -> None:
        payload = {
            "category": "unknown",
            "confidence": 0.3,
            "extracted_data": {},
            "raw_input": "Hello there",
        }
        _set_llm_response(mock_anthropic_client, payload)

        results = await claude_classifier.classify("Hello there")

        # Classifier always returns a list
        assert len(results) == 1
        result = results[0]

        assert result.category == Category.UNKNOWN
        assert result.confidence == 0.3


class TestClaudeClassifierRetryLogic:
    """Tests covering validation and retry behavior."""

    # Note: Retry tests disabled as retry logic was removed for multi-transaction support
    # The classifier now gracefully handles missing fields without retrying


class TestClaudeClassifierErrorHandling:
    """Tests covering error propagation and malformed responses."""

    @pytest.mark.asyncio
    async def test_api_timeout_error(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ) -> None:
        mock_anthropic_client.messages.create.side_effect = anthropic.APITimeoutError(
            "Request timed out"
        )

        with pytest.raises(anthropic.APITimeoutError):
            await claude_classifier.classify("Test input")

    @pytest.mark.asyncio
    async def test_api_connection_error(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ) -> None:
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
        mock_response = Mock()
        mock_response.content = [TextBlock(type="text", text="This is not valid JSON {")]
        mock_anthropic_client.messages.create.return_value = mock_response

        results = await claude_classifier.classify("Test input")

        # Classifier always returns a list
        assert len(results) == 1
        result = results[0]

        assert result.category == Category.UNKNOWN
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_missing_category_field(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ) -> None:
        payload = {
            "confidence": 0.8,
            "extracted_data": {},
            "raw_input": "Test",
        }
        _set_llm_response(mock_anthropic_client, payload)

        results = await claude_classifier.classify("Test")

        # Classifier always returns a list
        assert len(results) == 1
        result = results[0]

        assert result.category == Category.UNKNOWN

    @pytest.mark.asyncio
    async def test_unrecognized_category_maps_to_unknown(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ) -> None:
        payload = {
            "category": "invalid_category",
            "confidence": 0.8,
            "extracted_data": {},
            "raw_input": "Test",
        }
        _set_llm_response(mock_anthropic_client, payload)

        results = await claude_classifier.classify("Test")

        # Classifier always returns a list
        assert len(results) == 1
        result = results[0]

        assert result.category == Category.UNKNOWN

    @pytest.mark.asyncio
    async def test_extracted_data_as_array_unrolls_to_multiple_transactions(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ) -> None:
        """Test handling when LLM incorrectly returns extracted_data as array of transactions.

        This is an edge case where the LLM misunderstands the format and returns:
        [
          {
            "category": "budget",
            "extracted_data": [
              {"amount": 50, "currency": "EUR", ...},
              {"amount": 5, "currency": "EUR", ...}
            ]
          }
        ]

        Instead of the correct format:
        [
          {"category": "budget", "extracted_data": {"amount": 50, ...}},
          {"category": "budget", "extracted_data": {"amount": 5, ...}}
        ]

        The classifier should "unroll" this into separate ClassifiedInput objects.
        """
        # Simulate LLM returning incorrect format with extracted_data as array
        incorrect_payload = {
            "category": "budget",
            "confidence": 0.95,
            "extracted_data": [
                {
                    "amount": 50.0,
                    "currency": "EUR",
                    "transaction_type": "Expenses",
                    "category": "Body care",
                    "merchant": "dm",
                    "date": "2025-11-04",
                },
                {
                    "amount": 5.0,
                    "currency": "EUR",
                    "transaction_type": "Expenses",
                    "category": "Eat out",
                    "merchant": "bakery",
                    "date": "2025-11-04",
                },
            ],
            "raw_input": "spent 50 at dm and 5 at bakery",
        }

        # Mock the response
        mock_response = Mock()
        mock_response.content = [TextBlock(type="text", text=json.dumps([incorrect_payload]))]
        mock_anthropic_client.messages.create.return_value = mock_response

        # Execute
        results = await claude_classifier.classify("spent 50 at dm and 5 at bakery")

        # Should unroll into 2 separate transactions
        assert len(results) == 2

        # First transaction
        assert results[0].category == Category.BUDGET
        assert results[0].extracted_data["amount"] == 50.0
        assert results[0].extracted_data["currency"] == "EUR"
        assert results[0].extracted_data["merchant"] == "dm"

        # Second transaction
        assert results[1].category == Category.BUDGET
        assert results[1].extracted_data["amount"] == 5.0
        assert results[1].extracted_data["currency"] == "EUR"
        assert results[1].extracted_data["merchant"] == "bakery"
