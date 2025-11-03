"""Orchestrator for routing classification requests to keyword or LLM classifiers."""

import logging

import anthropic

from life_organizer.schemas.classification import ClassifiedInput
from life_organizer.services.classifier import KeywordClassifier
from life_organizer.services.claude_classifier import ClaudeClassifier

logger = logging.getLogger(__name__)


class ClassifierOrchestrator:
    """
    Routes classification requests to appropriate classifier based on confidence.

    Strategy: Try keyword classifier first (fast, deterministic). If confidence
    is below threshold, invoke LLM classifier for more accurate result. On LLM
    failure, gracefully fallback to keyword result.
    """

    CONFIDENCE_THRESHOLD = 0.75

    def __init__(
        self,
        keyword_classifier: KeywordClassifier,
        llm_classifier: ClaudeClassifier,
    ) -> None:
        """
        Initialize orchestrator with classifier instances.

        Args:
            keyword_classifier: Fast keyword-based classifier
            llm_classifier: Accurate LLM-based classifier
        """
        self.keyword_classifier = keyword_classifier
        self.llm_classifier = llm_classifier
        logger.info(
            f"Initialized ClassifierOrchestrator with threshold: {self.CONFIDENCE_THRESHOLD}"
        )

    async def classify(self, text: str) -> ClassifiedInput:
        """
        Classify input using keyword classifier with LLM fallback.

        Args:
            text: User input to classify

        Returns:
            ClassifiedInput with category, confidence, and classifier source
        """
        # Try keyword classifier first
        keyword_result = self.keyword_classifier.classify(text)

        # High confidence - use keyword result
        if keyword_result.confidence >= self.CONFIDENCE_THRESHOLD:
            logger.info(
                f"Keyword classifier high confidence ({keyword_result.confidence:.2f}) "
                f"for '{text[:50]}...' - using keyword result"
            )
            return keyword_result

        # Low confidence - invoke LLM classifier
        logger.info(
            f"Keyword classifier low confidence ({keyword_result.confidence:.2f}) "
            f"for '{text[:50]}...' - trying LLM fallback"
        )

        try:
            llm_result = await self.llm_classifier.classify(text)
            logger.info(
                f"LLM classifier succeeded with confidence {llm_result.confidence:.2f} "
                f"for '{text[:50]}...'"
            )
            return llm_result

        except anthropic.APIError as e:
            logger.warning(
                f"LLM classifier failed ({type(e).__name__}: {e}) - falling back to keyword result"
            )
            return keyword_result

        except Exception as e:
            logger.error(
                f"Unexpected error in LLM classifier ({type(e).__name__}: {e}) - "
                f"falling back to keyword result"
            )
            return keyword_result
