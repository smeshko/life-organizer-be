"""Orchestrator for routing classification requests to keyword or LLM classifiers."""

import logging

import anthropic

from life_organizer.schemas.classification import ClassifiedInput

# from life_organizer.services.classifier import KeywordClassifier  # Removed in Phase 1
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
        keyword_classifier: object | None,  # Temporarily accepting None until Phase 2
        llm_classifier: ClaudeClassifier,
    ) -> None:
        """
        Initialize orchestrator with classifier instances.

        Args:
            keyword_classifier: Fast keyword-based classifier (temporarily disabled)
            llm_classifier: Accurate LLM-based classifier
        """
        self.keyword_classifier = keyword_classifier  # Will be removed in Phase 2
        self.llm_classifier = llm_classifier
        logger.info(
            f"Initialized ClassifierOrchestrator with threshold: {self.CONFIDENCE_THRESHOLD}"
        )

    async def classify(self, text: str) -> ClassifiedInput:
        """
        Classify input using LLM classifier.

        Temporarily routes directly to LLM. Full refactoring in Phase 2.

        Args:
            text: User input to classify

        Returns:
            ClassifiedInput with category, confidence, and classifier source
        """
        # Temporarily route directly to LLM - will be properly refactored in Phase 2
        try:
            llm_result = await self.llm_classifier.classify(text)
            logger.info(
                f"LLM classifier succeeded with confidence {llm_result.confidence:.2f} "
                f"for '{text[:50]}...'"
            )
            return llm_result

        except anthropic.APIError as e:
            logger.error(f"LLM classifier API error ({type(e).__name__}: {e})")
            raise

        except (ValueError, TypeError, RuntimeError, Exception) as e:
            logger.error(f"Unexpected error in LLM classifier ({type(e).__name__}: {e})")
            raise
