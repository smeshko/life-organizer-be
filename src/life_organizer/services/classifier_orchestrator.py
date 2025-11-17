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

    async def classify(self, text: str, category: str | None = None) -> list[ClassifiedInput]:
        """
        Classify user input using LLM classifier.

        Args:
            text: Raw user input to classify
            category: Optional category for prompt selection (defaults to "budget")

        Returns:
            List of ClassifiedInput objects (one or more transactions).
            Even single transactions return a list with one element.

        Raises:
            anthropic.APIError: If LLM API fails
            ValidationError: If required fields missing after retry
        """
        logger.info(f"Classifying input with category: {category or 'default (budget)'}")

        # Route directly to LLM classifier (now returns list)
        results = await self.llm_classifier.classify(text, category=category)

        logger.info(f"Classification complete: {len(results)} transaction(s)")

        return results
