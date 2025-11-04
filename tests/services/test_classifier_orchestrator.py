"""Unit tests for ClassifierOrchestrator service."""

from unittest.mock import AsyncMock, Mock

import anthropic
import pytest

from life_organizer.schemas.classification import ClassifiedInput
from life_organizer.schemas.enums import Category
from life_organizer.services.classifier_orchestrator import ClassifierOrchestrator


@pytest.fixture
def mock_keyword_classifier() -> Mock:
    """Create mocked KeywordClassifier."""
    classifier = Mock()
    return classifier


@pytest.fixture
def mock_llm_classifier() -> AsyncMock:
    """Create mocked ClaudeClassifier."""
    classifier = AsyncMock()
    return classifier


@pytest.fixture
def orchestrator(
    mock_keyword_classifier: Mock, mock_llm_classifier: AsyncMock
) -> ClassifierOrchestrator:
    """Create orchestrator with mocked classifiers."""
    return ClassifierOrchestrator(
        keyword_classifier=None,  # Temporarily disabled in Phase 1
        llm_classifier=mock_llm_classifier,
    )


class TestClassifierOrchestrator:
    """Test suite for ClassifierOrchestrator routing logic."""

    @pytest.mark.skip(
        reason="Keyword routing removed in Phase 1, will be updated in Phase 3 (T007)"
    )
    @pytest.mark.asyncio
    async def test_high_confidence_uses_keyword(
        self,
        orchestrator: ClassifierOrchestrator,
        mock_keyword_classifier: Mock,
        mock_llm_classifier: AsyncMock,
    ) -> None:
        """Test that high confidence (≥75%) uses keyword result without LLM."""
        # Mock keyword result with high confidence
        keyword_result = ClassifiedInput(
            category=Category.BUDGET,
            confidence=0.85,
            extracted_data={"amount": 45.0},
            raw_input="Spent 45 EUR",
            classifier_source="keyword",
        )
        mock_keyword_classifier.classify.return_value = keyword_result

        # Classify
        result = await orchestrator.classify("Spent 45 EUR")

        # Assertions
        assert result == keyword_result
        assert result.classifier_source == "keyword"
        mock_keyword_classifier.classify.assert_called_once_with("Spent 45 EUR")
        mock_llm_classifier.classify.assert_not_called()

    @pytest.mark.skip(
        reason="Keyword routing removed in Phase 1, will be updated in Phase 3 (T007)"
    )
    @pytest.mark.asyncio
    async def test_low_confidence_uses_llm(
        self,
        orchestrator: ClassifierOrchestrator,
        mock_keyword_classifier: Mock,
        mock_llm_classifier: AsyncMock,
    ) -> None:
        """Test that low confidence (<75%) invokes LLM classifier."""
        # Mock keyword result with low confidence
        keyword_result = ClassifiedInput(
            category=Category.UNKNOWN,
            confidence=0.45,
            extracted_data={},
            raw_input="ambiguous input",
            classifier_source="keyword",
        )
        mock_keyword_classifier.classify.return_value = keyword_result

        # Mock LLM result
        llm_result = ClassifiedInput(
            category=Category.REMINDER,
            confidence=0.9,
            extracted_data={"action": "check status"},
            raw_input="ambiguous input",
            classifier_source="llm",
        )
        mock_llm_classifier.classify.return_value = llm_result

        # Classify
        result = await orchestrator.classify("ambiguous input")

        # Assertions
        assert result == llm_result
        assert result.classifier_source == "llm"
        mock_keyword_classifier.classify.assert_called_once()
        mock_llm_classifier.classify.assert_called_once_with("ambiguous input")

    @pytest.mark.skip(
        reason="Keyword routing removed in Phase 1, will be updated in Phase 3 (T007)"
    )
    @pytest.mark.asyncio
    async def test_llm_timeout_fallback_to_keyword(
        self,
        orchestrator: ClassifierOrchestrator,
        mock_keyword_classifier: Mock,
        mock_llm_classifier: AsyncMock,
    ) -> None:
        """Test that LLM timeout falls back to keyword result."""
        # Mock keyword result with low confidence
        keyword_result = ClassifiedInput(
            category=Category.UNKNOWN,
            confidence=0.5,
            extracted_data={},
            raw_input="test input",
            classifier_source="keyword",
        )
        mock_keyword_classifier.classify.return_value = keyword_result

        # Mock LLM timeout
        mock_llm_classifier.classify.side_effect = anthropic.APITimeoutError("Request timed out")

        # Classify
        result = await orchestrator.classify("test input")

        # Should fallback to keyword result
        assert result == keyword_result
        assert result.classifier_source == "keyword"
        mock_llm_classifier.classify.assert_called_once()

    @pytest.mark.skip(
        reason="Keyword routing removed in Phase 1, will be updated in Phase 3 (T007)"
    )
    @pytest.mark.asyncio
    async def test_llm_rate_limit_fallback_to_keyword(
        self,
        orchestrator: ClassifierOrchestrator,
        mock_keyword_classifier: Mock,
        mock_llm_classifier: AsyncMock,
    ) -> None:
        """Test that LLM rate limit error falls back to keyword result."""
        keyword_result = ClassifiedInput(
            category=Category.UNKNOWN,
            confidence=0.6,
            extracted_data={},
            raw_input="test",
            classifier_source="keyword",
        )
        mock_keyword_classifier.classify.return_value = keyword_result

        # Create mock response for rate limit error
        mock_response = Mock()
        mock_response.status_code = 429
        mock_llm_classifier.classify.side_effect = anthropic.RateLimitError(
            message="Rate limit exceeded", response=mock_response, body={}
        )

        result = await orchestrator.classify("test")

        assert result == keyword_result
        assert result.classifier_source == "keyword"

    @pytest.mark.skip(
        reason="Keyword routing removed in Phase 1, will be updated in Phase 3 (T007)"
    )
    @pytest.mark.asyncio
    async def test_llm_auth_error_fallback_to_keyword(
        self,
        orchestrator: ClassifierOrchestrator,
        mock_keyword_classifier: Mock,
        mock_llm_classifier: AsyncMock,
    ) -> None:
        """Test that LLM authentication error falls back to keyword result."""
        keyword_result = ClassifiedInput(
            category=Category.UNKNOWN,
            confidence=0.55,
            extracted_data={},
            raw_input="test",
            classifier_source="keyword",
        )
        mock_keyword_classifier.classify.return_value = keyword_result

        # Create mock response for auth error
        mock_response = Mock()
        mock_response.status_code = 401
        mock_llm_classifier.classify.side_effect = anthropic.AuthenticationError(
            message="Invalid API key", response=mock_response, body={}
        )

        result = await orchestrator.classify("test")

        assert result == keyword_result

    @pytest.mark.skip(
        reason="Keyword routing removed in Phase 1, will be updated in Phase 3 (T007)"
    )
    @pytest.mark.asyncio
    async def test_llm_generic_error_fallback_to_keyword(
        self,
        orchestrator: ClassifierOrchestrator,
        mock_keyword_classifier: Mock,
        mock_llm_classifier: AsyncMock,
    ) -> None:
        """Test that unexpected LLM errors fall back to keyword result."""
        keyword_result = ClassifiedInput(
            category=Category.UNKNOWN,
            confidence=0.65,
            extracted_data={},
            raw_input="test",
            classifier_source="keyword",
        )
        mock_keyword_classifier.classify.return_value = keyword_result

        mock_llm_classifier.classify.side_effect = Exception("Unexpected error")

        result = await orchestrator.classify("test")

        assert result == keyword_result

    @pytest.mark.skip(
        reason="Keyword routing removed in Phase 1, will be updated in Phase 3 (T007)"
    )
    @pytest.mark.asyncio
    async def test_threshold_boundary_75_percent(
        self,
        orchestrator: ClassifierOrchestrator,
        mock_keyword_classifier: Mock,
        mock_llm_classifier: AsyncMock,
    ) -> None:
        """Test exact 75% confidence threshold uses keyword (≥, not >)."""
        keyword_result = ClassifiedInput(
            category=Category.BUDGET,
            confidence=0.75,  # Exactly 75%
            extracted_data={},
            raw_input="test",
            classifier_source="keyword",
        )
        mock_keyword_classifier.classify.return_value = keyword_result

        result = await orchestrator.classify("test")

        # Should NOT invoke LLM at exactly 75%
        assert result == keyword_result
        mock_llm_classifier.classify.assert_not_called()

    @pytest.mark.asyncio
    async def test_threshold_boundary_just_below_75(
        self,
        orchestrator: ClassifierOrchestrator,
        mock_keyword_classifier: Mock,
        mock_llm_classifier: AsyncMock,
    ) -> None:
        """Test just below 75% threshold invokes LLM."""
        keyword_result = ClassifiedInput(
            category=Category.UNKNOWN,
            confidence=0.74,  # Just below threshold
            extracted_data={},
            raw_input="test",
            classifier_source="keyword",
        )
        mock_keyword_classifier.classify.return_value = keyword_result

        llm_result = ClassifiedInput(
            category=Category.REMINDER,
            confidence=0.88,
            extracted_data={"action": "test"},
            raw_input="test",
            classifier_source="llm",
        )
        mock_llm_classifier.classify.return_value = llm_result

        result = await orchestrator.classify("test")

        # Should invoke LLM just below 75%
        assert result == llm_result
        mock_llm_classifier.classify.assert_called_once()
