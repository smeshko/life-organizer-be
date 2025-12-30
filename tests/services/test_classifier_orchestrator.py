"""Unit tests for ClassifierOrchestrator service."""

from unittest.mock import AsyncMock, Mock

import anthropic
import pytest
from pydantic import ValidationError

from life_organizer.schemas.classification import ClassifiedInput
from life_organizer.schemas.enums import Category
from life_organizer.services.classifier_orchestrator import ClassifierOrchestrator


@pytest.fixture
def mock_llm_classifier() -> AsyncMock:
    """Create mocked ClaudeClassifier."""
    classifier = AsyncMock()
    return classifier


@pytest.fixture
def orchestrator(mock_llm_classifier: AsyncMock) -> ClassifierOrchestrator:
    """Create orchestrator with mocked LLM classifier."""
    return ClassifierOrchestrator(
        llm_classifier=mock_llm_classifier,
    )


class TestClassifierOrchestrator:
    """Test suite for ClassifierOrchestrator LLM-only routing."""

    @pytest.mark.asyncio
    async def test_successful_classification(
        self,
        orchestrator: ClassifierOrchestrator,
        mock_llm_classifier: AsyncMock,
    ) -> None:
        """Test successful LLM classification."""
        # Mock LLM result (now returns a list)
        llm_result = ClassifiedInput(
            category=Category.BUDGET,
            confidence=0.95,
            extracted_data={
                "amount": 120.0,
                "currency": "EUR",
                "transaction_type": "Expenses",
                "category": "Clothes",
                "merchant": "next",
                "date": "2025-11-04",
            },
            raw_input="spent 120eur at next",
            classifier_source="llm",
        )
        mock_llm_classifier.classify.return_value = [llm_result]

        # Classify
        results = await orchestrator.classify("spent 120eur at next")

        # Assertions
        assert len(results) == 1
        assert results[0] == llm_result
        assert results[0].category == Category.BUDGET
        assert results[0].confidence == 0.95
        assert results[0].classifier_source == "llm"
        mock_llm_classifier.classify.assert_called_once_with("spent 120eur at next", category=None)

    @pytest.mark.asyncio
    async def test_llm_api_error_propagates(
        self,
        orchestrator: ClassifierOrchestrator,
        mock_llm_classifier: AsyncMock,
    ) -> None:
        """Test that LLM API errors propagate (no fallback)."""
        # Mock LLM API error
        mock_llm_classifier.classify.side_effect = anthropic.APITimeoutError("Request timed out")

        # Should raise the error instead of returning a result
        with pytest.raises(anthropic.APITimeoutError):
            await orchestrator.classify("test input")

        mock_llm_classifier.classify.assert_called_once()

    @pytest.mark.asyncio
    async def test_rate_limit_error_propagates(
        self,
        orchestrator: ClassifierOrchestrator,
        mock_llm_classifier: AsyncMock,
    ) -> None:
        """Test that rate limit errors propagate."""
        # Create mock response for rate limit error
        mock_response = Mock()
        mock_response.status_code = 429
        mock_llm_classifier.classify.side_effect = anthropic.RateLimitError(
            message="Rate limit exceeded", response=mock_response, body={}
        )

        # Should raise the error
        with pytest.raises(anthropic.RateLimitError):
            await orchestrator.classify("test")

        mock_llm_classifier.classify.assert_called_once()

    @pytest.mark.asyncio
    async def test_validation_error_propagates(
        self,
        orchestrator: ClassifierOrchestrator,
        mock_llm_classifier: AsyncMock,
    ) -> None:
        """Test that ValidationError from missing fields propagates."""
        # Mock classifier raising ValidationError (from retry logic)
        mock_llm_classifier.classify.side_effect = ValidationError.from_exception_data(
            "ValidationError",
            [
                {
                    "type": "missing",
                    "loc": ("extracted_data", "amount"),
                    "msg": "Field required",
                    "input": {},
                }
            ],
        )

        # Should raise ValidationError
        with pytest.raises(ValidationError):
            await orchestrator.classify("incomplete input")

        mock_llm_classifier.classify.assert_called_once()

    @pytest.mark.asyncio
    async def test_unknown_category_classification(
        self,
        orchestrator: ClassifierOrchestrator,
        mock_llm_classifier: AsyncMock,
    ) -> None:
        """Test classification returns UNKNOWN for unclear input."""
        # Mock LLM returning UNKNOWN (now returns a list)
        unknown_result = ClassifiedInput(
            category=Category.UNKNOWN,
            confidence=0.2,
            extracted_data={},
            raw_input="gibberish xyz 123",
            classifier_source="llm",
        )
        mock_llm_classifier.classify.return_value = [unknown_result]

        # Classify
        results = await orchestrator.classify("gibberish xyz 123")

        # Assertions
        assert len(results) == 1
        assert results[0].category == Category.UNKNOWN
        assert results[0].confidence < 0.5
        mock_llm_classifier.classify.assert_called_once()
