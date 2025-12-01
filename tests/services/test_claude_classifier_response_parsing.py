"""Unit tests for ClaudeClassifier response parsing and validation logic.

NOTE: These tests use mocked LLM responses and do NOT validate system prompt behavior.
They verify that the classifier code correctly parses, validates, and handles various
response formats from the LLM.

For actual prompt validation with real LLM calls, see:
- tests/integration/test_budget_prompt_validation.py
"""

import json
from unittest.mock import AsyncMock, Mock

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
    confidence: float = 0.95,
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
        "confidence": confidence,
        "extracted_data": extracted_data,
        "raw_input": raw_input,
    }


@pytest.fixture
def mock_anthropic_client() -> AsyncMock:
    """Create a mocked Anthropic client."""
    client = AsyncMock()
    return client


@pytest.fixture
def claude_classifier(mock_anthropic_client: AsyncMock) -> ClaudeClassifier:
    """Create a ClaudeClassifier with mocked client."""
    classifier = ClaudeClassifier(api_key="test-api-key")
    classifier.client = mock_anthropic_client
    return classifier


class TestCategoryRobustness:
    """Test category selection robustness and fallback behavior."""

    @pytest.mark.asyncio
    async def test_home_improvements_full_name(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ):
        """Test that 'Home Improvements' maps to exact enum 'Home improvements' (not 'Home')."""
        # Mock LLM response with correct full category name
        _set_llm_response(
            mock_anthropic_client,
            _budget_payload(
                amount=423.0,
                currency="BGN",
                transaction_type="Expenses",
                category="Home improvements",  # Exact enum value
                merchant="home improvements",
                raw_input="423 BGN for Home Improvements",
            ),
        )

        results = await claude_classifier.classify(
            "423 BGN for Home Improvements", category="budget"
        )

        assert len(results) == 1
        result = results[0]
        assert result.category == Category.BUDGET
        assert result.extracted_data["category"] == "Home improvements"  # Not "Home"
        assert result.extracted_data["transaction_type"] == "Expenses"
        assert result.extracted_data["amount"] == 423.0

    @pytest.mark.asyncio
    async def test_generic_salary_fallback(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ):
        """Test that generic 'salary' maps to 'Salary Ivo' (not invalid 'Salary')."""
        _set_llm_response(
            mock_anthropic_client,
            _budget_payload(
                amount=7700.0,
                currency="BGN",
                transaction_type="Income",
                category="Salary Ivo",  # Fallback to default
                merchant="salary",
                raw_input="7700bgn salary",
                confidence=0.65,  # Lower confidence for fallback
            ),
        )

        results = await claude_classifier.classify("7700bgn salary", category="budget")

        assert len(results) == 1
        result = results[0]
        assert result.extracted_data["category"] == "Salary Ivo"  # Not "Salary"
        assert result.extracted_data["transaction_type"] == "Income"
        assert result.confidence >= 0.5 and result.confidence <= 0.7

    @pytest.mark.asyncio
    async def test_medical_synonym_mapping(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ):
        """Test that 'doctor's visit' maps to 'Medical' (not 'Healthcare')."""
        _set_llm_response(
            mock_anthropic_client,
            _budget_payload(
                amount=150.0,
                currency="BGN",
                transaction_type="Expenses",
                category="Medical",  # Correct enum, not "Healthcare"
                merchant="doctor's visit",
                raw_input="150 for a doctor's visit",
            ),
        )

        results = await claude_classifier.classify("150 for a doctor's visit", category="budget")

        assert len(results) == 1
        result = results[0]
        assert result.extracted_data["category"] == "Medical"  # Not "Healthcare"
        assert result.extracted_data["merchant"] == "doctor's visit"
        assert result.extracted_data["transaction_type"] == "Expenses"

    @pytest.mark.asyncio
    async def test_ambiguous_expense_fallback(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ):
        """Test that ambiguous expenses use 'Other' fallback with lower confidence."""
        _set_llm_response(
            mock_anthropic_client,
            _budget_payload(
                amount=50.0,
                currency="BGN",
                transaction_type="Expenses",
                category="Other",
                merchant=None,
                raw_input="50 for something",
                confidence=0.6,  # Lower confidence for fallback
            ),
        )

        results = await claude_classifier.classify("50 for something", category="budget")

        assert len(results) == 1
        result = results[0]
        assert result.extracted_data["category"] == "Other"
        assert result.confidence >= 0.5 and result.confidence <= 0.7

    @pytest.mark.asyncio
    async def test_case_sensitivity_preserved(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ):
        """Test that category casing is preserved exactly (lowercase 'i' in 'improvements')."""
        _set_llm_response(
            mock_anthropic_client,
            _budget_payload(
                amount=500.0,
                currency="BGN",
                transaction_type="Expenses",
                category="Home improvements",  # Lowercase 'i'
                merchant="contractor",
                raw_input="500 for home improvements",
            ),
        )

        results = await claude_classifier.classify("500 for home improvements", category="budget")

        assert len(results) == 1
        result = results[0]
        # Exact match required - "Home improvements" not "Home Improvements"
        assert result.extracted_data["category"] == "Home improvements"

    @pytest.mark.asyncio
    async def test_healthcare_to_medical_synonym(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ):
        """Test that 'healthcare' synonym maps to 'Medical'."""
        _set_llm_response(
            mock_anthropic_client,
            _budget_payload(
                amount=100.0,
                currency="BGN",
                transaction_type="Expenses",
                category="Medical",
                merchant="healthcare visit",
                raw_input="100 for healthcare visit",
            ),
        )

        results = await claude_classifier.classify("100 for healthcare visit", category="budget")

        assert len(results) == 1
        assert results[0].extracted_data["category"] == "Medical"

    @pytest.mark.asyncio
    async def test_home_renovation_synonym(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ):
        """Test that 'home renovation' maps to 'Home improvements'."""
        _set_llm_response(
            mock_anthropic_client,
            _budget_payload(
                amount=2000.0,
                currency="BGN",
                transaction_type="Expenses",
                category="Home improvements",
                merchant="home renovation",
                raw_input="2000 for home renovation",
            ),
        )

        results = await claude_classifier.classify("2000 for home renovation", category="budget")

        assert len(results) == 1
        assert results[0].extracted_data["category"] == "Home improvements"

    @pytest.mark.asyncio
    async def test_wage_to_salary_ivo(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ):
        """Test that 'wage' maps to 'Salary Ivo' income category."""
        _set_llm_response(
            mock_anthropic_client,
            _budget_payload(
                amount=5000.0,
                currency="BGN",
                transaction_type="Income",
                category="Salary Ivo",
                merchant="wage payment",
                raw_input="5000 wage payment",
                confidence=0.65,
            ),
        )

        results = await claude_classifier.classify("5000 wage payment", category="budget")

        assert len(results) == 1
        result = results[0]
        assert result.extracted_data["category"] == "Salary Ivo"
        assert result.extracted_data["transaction_type"] == "Income"

    @pytest.mark.asyncio
    async def test_multi_transaction_mixed_categories(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ):
        """Test multiple transactions with different categories including 'Home improvements'."""
        # Mock multi-transaction response matching the original failed example
        payloads = [
            _budget_payload(
                amount=74.0,
                currency="BGN",
                transaction_type="Expenses",
                category="Groceries",
                merchant="Metro cash and Carry",
                raw_input="74 BGN at Metro",
            ),
            _budget_payload(
                amount=58.0,
                currency="USD",
                transaction_type="Expenses",
                category="Subscriptions",
                merchant="Craft",
                raw_input="58 USD for Craft subscription",
            ),
            _budget_payload(
                amount=423.0,
                currency="BGN",
                transaction_type="Expenses",
                category="Home improvements",  # Full name, not "Home"
                merchant="Home Improvements",
                raw_input="423 BGN for Home Improvements",
            ),
            _budget_payload(
                amount=72.0,
                currency="USD",
                transaction_type="Expenses",
                category="Subscriptions",
                merchant="Dynamous",
                raw_input="72 USD for Dynamous subscription",
            ),
        ]

        mock_response = Mock()
        mock_response.content = [TextBlock(type="text", text=json.dumps(payloads))]
        mock_anthropic_client.messages.create.return_value = mock_response

        results = await claude_classifier.classify(
            "74 BGN at Metro, 58 USD for Craft subscription, 423 BGN for Home Improvements, 72 USD for Dynamous subscription",
            category="budget",
        )

        assert len(results) == 4
        assert results[0].extracted_data["category"] == "Groceries"
        assert results[1].extracted_data["category"] == "Subscriptions"
        assert results[2].extracted_data["category"] == "Home improvements"  # Not "Home"
        assert results[3].extracted_data["category"] == "Subscriptions"

    @pytest.mark.asyncio
    async def test_multi_transaction_with_fallback(
        self, claude_classifier: ClaudeClassifier, mock_anthropic_client: AsyncMock
    ):
        """Test that fallback doesn't affect specific category detection in multi-transaction."""
        payloads = [
            _budget_payload(
                amount=50.0,
                currency="BGN",
                transaction_type="Expenses",
                category="Groceries",
                merchant="Billa",
                raw_input="50 at Billa",
                confidence=0.95,
            ),
            _budget_payload(
                amount=30.0,
                currency="BGN",
                transaction_type="Expenses",
                category="Other",  # Fallback for ambiguous
                merchant=None,
                raw_input="30 for something",
                confidence=0.6,
            ),
            _budget_payload(
                amount=150.0,
                currency="BGN",
                transaction_type="Expenses",
                category="Medical",  # Specific category after fallback
                merchant="doctor",
                raw_input="150 for doctor",
                confidence=0.90,
            ),
        ]

        mock_response = Mock()
        mock_response.content = [TextBlock(type="text", text=json.dumps(payloads))]
        mock_anthropic_client.messages.create.return_value = mock_response

        results = await claude_classifier.classify(
            "50 at Billa, 30 for something, 150 for doctor", category="budget"
        )

        assert len(results) == 3
        assert results[0].extracted_data["category"] == "Groceries"
        assert results[0].confidence > 0.9
        assert results[1].extracted_data["category"] == "Other"  # Fallback
        assert results[1].confidence >= 0.5 and results[1].confidence <= 0.7
        assert results[2].extracted_data["category"] == "Medical"
        assert results[2].confidence > 0.8
