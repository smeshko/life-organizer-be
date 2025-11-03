"""LLM-based classifier using Claude Haiku for intelligent text classification."""

import json
import logging
from typing import Any

import anthropic
from anthropic.types import TextBlock
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential

from life_organizer.schemas.classification import ClassifiedInput
from life_organizer.schemas.enums import Category

logger = logging.getLogger(__name__)


class ClaudeClassifier:
    """
    LLM-based classifier using Anthropic Claude Haiku.

    Uses structured prompting to classify user input into categories
    and extract structured data. Designed as fallback for low-confidence
    keyword classifications.
    """

    SYSTEM_PROMPT = """You are a classification assistant for a life organizer app.

Classify user input into ONE category and extract relevant structured data.

**Categories:**
- expense: Financial transactions (purchases, bills, payments)
- shopping: Items to buy or shopping lists
- reminder: Tasks, actions to remember
- calendar: Events, appointments, time-based activities
- unknown: Unclear or unclassifiable input

**Return ONLY valid JSON matching this schema:**
{
  "category": "expense" | "shopping" | "reminder" | "calendar" | "unknown",
  "confidence": 0.0-1.0,
  "extracted_data": {
    // For expense: {"amount": number, "currency": "EUR"|"USD", "merchant_hint": string}
    // For shopping: {"items": [string, ...]}
    // For reminder: {"action": string}
    // For calendar: {"time_reference": string}
  },
  "raw_input": "original input text"
}

**Examples:**

Input: "Spent 45 EUR at restaurant"
Output: {"category": "expense", "confidence": 0.95, "extracted_data": {"amount": 45.0, "currency": "EUR", "merchant_hint": "restaurant"}, "raw_input": "Spent 45 EUR at restaurant"}

Input: "Buy milk and eggs"
Output: {"category": "shopping", "confidence": 0.9, "extracted_data": {"items": ["milk", "eggs"]}, "raw_input": "Buy milk and eggs"}

Input: "Call dentist tomorrow"
Output: {"category": "reminder", "confidence": 0.85, "extracted_data": {"action": "call dentist"}, "raw_input": "Call dentist tomorrow"}

Return ONLY the JSON, no additional text."""

    def __init__(self, api_key: str, model: str = "claude-haiku-4-5") -> None:
        """
        Initialize Claude classifier.

        Args:
            api_key: Anthropic API key
            model: Claude model identifier (default: claude-haiku-4-5)
        """
        self.client = anthropic.AsyncAnthropic(api_key=api_key, timeout=10.0)
        self.model = model
        logger.info(f"Initialized ClaudeClassifier with model: {model}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        reraise=True,
    )
    async def classify(self, text: str) -> ClassifiedInput:
        """
        Classify input text using Claude Haiku.

        Args:
            text: User input to classify

        Returns:
            ClassifiedInput with category, confidence, and extracted data

        Raises:
            anthropic.APIError: On API communication errors
        """
        # Validate input to avoid wasting API calls
        if not text or not text.strip():
            logger.debug("Empty or whitespace-only input, returning UNKNOWN")
            return ClassifiedInput(
                category=Category.UNKNOWN,
                confidence=0.0,
                extracted_data={},
                raw_input=text,
                classifier_source="llm",
            )

        try:
            # Call Claude API with prompt caching for system prompt
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=500,
                system=[
                    {
                        "type": "text",
                        "text": self.SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[{"role": "user", "content": text}],
            )

            # Extract response text
            first_block = message.content[0]
            if not isinstance(first_block, TextBlock):
                logger.error(f"Unexpected response block type: {type(first_block)}")
                raise ValueError(f"Expected TextBlock, got {type(first_block)}")
            response_text = first_block.text
            logger.debug(f"Claude response: {response_text}")

            # Strip markdown code fences if present
            response_text = response_text.strip()
            if response_text.startswith("```"):
                # Remove first line (```json or ```)
                lines = response_text.split("\n", 1)
                if len(lines) > 1:
                    response_text = lines[1]
                # Remove last line (```)
                if response_text.endswith("```"):
                    response_text = response_text.rsplit("```", 1)[0]
                response_text = response_text.strip()

            # Parse JSON
            data = json.loads(response_text)

            # Normalize category to enum
            category_str = data.get("category", "unknown").lower()
            data["category"] = self._normalize_category(category_str)

            # Ensure extracted_data has expected fields
            data["extracted_data"] = self._ensure_extracted_data_fields(
                data["category"], data.get("extracted_data", {})
            )

            # Set classifier source
            data["classifier_source"] = "llm"

            # Validate with Pydantic
            result = ClassifiedInput.model_validate(data)
            logger.info(
                f"Claude classified '{text[:50]}...' as {result.category} "
                f"(confidence: {result.confidence:.2f})"
            )
            return result

        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            raise  # Let orchestrator handle fallback

        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Failed to parse Claude response: {e}")
            # Return UNKNOWN with low confidence
            return ClassifiedInput(
                category=Category.UNKNOWN,
                confidence=0.0,
                extracted_data={},
                raw_input=text,
                classifier_source="llm",
            )

    def _normalize_category(self, category_str: str) -> Category:
        """Map LLM category string to Category enum."""
        category_map = {
            "expense": Category.EXPENSE,
            "shopping": Category.SHOPPING,
            "reminder": Category.REMINDER,
            "calendar": Category.CALENDAR,
            "unknown": Category.UNKNOWN,
        }
        return category_map.get(category_str.lower(), Category.UNKNOWN)

    def _ensure_extracted_data_fields(
        self,
        category: Category,
        extracted_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Ensure extracted_data has expected fields for category."""
        # Validate and add defaults for category-specific fields
        if category == Category.EXPENSE:
            if "amount" not in extracted_data:
                logger.warning("LLM returned EXPENSE without amount field")
        elif category == Category.SHOPPING:
            if "items" not in extracted_data or not isinstance(extracted_data["items"], list):
                logger.warning("LLM returned SHOPPING without items list, adding empty list")
                extracted_data["items"] = []
        elif category == Category.REMINDER and "action" not in extracted_data:
            logger.debug("LLM returned REMINDER without action field")
        elif category == Category.CALENDAR and "time_reference" not in extracted_data:
            logger.debug("LLM returned CALENDAR without time_reference field")

        return extracted_data
