"""Orchestrator for routing classification requests to LLM classifier."""

import logging

from life_organizer.schemas.classification import ClassifiedInput
from life_organizer.services.claude_classifier import ClaudeClassifier

logger = logging.getLogger(__name__)


class ClassifierOrchestrator:
    """
    Orchestrates classification routing to LLM classifier.

    Routes all classification requests directly to the LLM classifier with
    comprehensive extraction and validation. Provides a consistent interface
    for potential future enhancements (e.g., category-specific classifiers).
    """

    def __init__(
        self,
        llm_classifier: ClaudeClassifier,
    ) -> None:
        """
        Initialize orchestrator with LLM classifier.

        Args:
            llm_classifier: Claude-based classifier for all classification requests
        """
        self.llm_classifier = llm_classifier
        logger.info("ClassifierOrchestrator initialized with LLM classifier")

    async def classify(self, text: str) -> ClassifiedInput:
        """
        Classify user input using LLM classifier.

        Args:
            text: Raw user input to classify

        Returns:
            ClassifiedInput with category, confidence, and extracted data

        Raises:
            anthropic.APIError: If LLM API fails
            ValidationError: If required fields missing after retry
        """
        logger.info(f"Classifying input: '{text[:50]}...'")

        # Route directly to LLM classifier
        result = await self.llm_classifier.classify(text)

        logger.info(
            f"Classification complete: {result.category} (confidence: {result.confidence:.2f})"
        )

        return result
