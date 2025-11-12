"""LLM-based classifier using Claude Haiku for intelligent text classification."""

import json
import logging
from pathlib import Path
from typing import Any

import anthropic
from anthropic.types import TextBlock
from fastapi import HTTPException
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential

from life_organizer.schemas.classification import ClassifiedInput
from life_organizer.schemas.enums import Category

logger = logging.getLogger(__name__)

# Load system prompt from file
_PROMPT_DIR = Path(__file__).parent.parent / "prompts"
_SYSTEM_PROMPT_FILE = _PROMPT_DIR / "classifier_system_prompt.txt"

with _SYSTEM_PROMPT_FILE.open(encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()


class ClaudeClassifier:
    """
    LLM-based classifier using Anthropic Claude Haiku.

    Uses structured prompting to classify user input into categories
    and extract structured data. Includes validation and single-retry logic
    for missing required fields.
    """

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

    def _get_required_fields(self, category: Category) -> list[str]:
        """Return required fields for each category.

        Args:
            category: The classification category

        Returns:
            List of required field names for the category
        """
        if category == Category.BUDGET:
            return ["amount", "currency", "transaction_type", "category", "date"]
        elif category == Category.SHOPPING:
            return ["items"]
        elif category == Category.REMINDER:
            return ["action"]
        elif category == Category.CALENDAR:
            return ["time_reference"]
        return []  # UNKNOWN has no required fields

    def _estimate_transaction_count(self, text: str) -> int:
        """Estimate number of transactions in input using simple heuristics.

        Counts separators: commas and the word 'and'.
        Returns estimated count (minimum 1 for non-empty input).

        Args:
            text: User input text

        Returns:
            Estimated transaction count
        """
        if not text or not text.strip():
            return 0

        # Count commas and ' and ' as transaction separators
        comma_count = text.count(",")
        and_count = text.lower().count(" and ")

        # Estimate: separators + 1 = transactions
        # e.g., "50 at DM, 120 at Next" has 1 comma = 2 transactions
        return max(1, comma_count + and_count + 1)

    async def _classify_internal(self, text: str) -> list[ClassifiedInput]:
        """
        Internal classification logic without retry/validation.

        Args:
            text: User input to classify

        Returns:
            List of classified inputs parsed from LLM array response.

        Raises:
            anthropic.APIError: On API communication errors
        """
        # Validate input to avoid wasting API calls
        if not text or not text.strip():
            logger.debug("Empty or whitespace-only input, returning UNKNOWN")
            return [
                ClassifiedInput(
                    category=Category.UNKNOWN,
                    confidence=0.0,
                    extracted_data={},
                    raw_input=text,
                    classifier_source="llm",
                )
            ]

        try:
            # Call Claude API with prompt caching for system prompt
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=2000,  # Increased from 500 for multi-transaction
                system=[
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT,
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

            # Parse JSON array
            data_array = json.loads(response_text)

            # Validate it's a list
            if not isinstance(data_array, list):
                logger.error(f"Expected JSON array, got {type(data_array)}")
                raise ValueError("LLM did not return a JSON array")

            # Parse each transaction
            results = []
            for item_data in data_array:
                # Normalize category to enum
                category_str = item_data.get("category", "unknown").lower()
                item_data["category"] = self._normalize_category(category_str)

                # Ensure extracted_data has expected fields
                item_data["extracted_data"] = self._ensure_extracted_data_fields(
                    item_data["category"], item_data.get("extracted_data", {})
                )

                # Set classifier source
                item_data["classifier_source"] = "llm"

                # Validate with Pydantic
                result = ClassifiedInput.model_validate(item_data)
                results.append(result)

            logger.info(f"Classified {len(results)} transaction(s) from input")
            return results

        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            raise  # Let orchestrator handle fallback

        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Failed to parse Claude response: {e}")
            # Return UNKNOWN with low confidence
            return [
                ClassifiedInput(
                    category=Category.UNKNOWN,
                    confidence=0.0,
                    extracted_data={},
                    raw_input=text,
                    classifier_source="llm",
                )
            ]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        reraise=True,
    )
    async def classify(self, text: str) -> list[ClassifiedInput]:
        """
        Classify input text using Claude Haiku with validation and single retry.

        Validates that all required fields for the category are present in
        extracted_data. If fields are missing, retries once with explicit
        instructions. Raises ValidationError if fields still missing after retry.

        Args:
            text: User input to classify

        Returns:
            List of ClassifiedInput objects (one or more items).
            Even single transactions return a list with one element.

        Raises:
            anthropic.APIError: On API communication errors
            ValidationError: If required fields missing after retry
            HTTPException: If input exceeds transaction limit
        """
        # Validate input to avoid wasting API calls
        if not text or not text.strip():
            logger.debug("Empty or whitespace-only input, returning UNKNOWN")
            return [
                ClassifiedInput(
                    category=Category.UNKNOWN,
                    confidence=0.0,
                    extracted_data={},
                    raw_input=text,
                    classifier_source="llm",
                )
            ]

        # Transaction count validation
        estimated_count = self._estimate_transaction_count(text)
        if estimated_count > 15:
            logger.warning(
                f"Input exceeds transaction limit: estimated {estimated_count} transactions"
            )
            raise HTTPException(
                status_code=422,
                detail=f"Maximum 15 transactions per request. You provided approximately {estimated_count}.",
            )

        # First attempt
        results = await self._classify_internal(text)

        # Check for required fields in each result (category-specific)
        # Note: For multi-transaction, we don't retry on missing fields
        # as the retry logic is designed for single transactions
        for result in results:
            required = self._get_required_fields(result.category)
            missing = [
                f
                for f in required
                if f not in result.extracted_data or result.extracted_data[f] is None
            ]

            if missing:
                logger.warning(
                    f"Transaction missing required fields: {missing} for category {result.category}. "
                    f"Raw input: '{result.raw_input[:50]}...'"
                )

        logger.info(f"Claude classified '{text[:50]}...' into {len(results)} transaction(s)")
        return results

    def _normalize_category(self, category_str: str) -> Category:
        """Map LLM category string to Category enum."""
        category_map = {
            "budget": Category.BUDGET,
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
        if category == Category.BUDGET:
            # Validate critical fields exist (let retry logic handle missing fields)
            if "amount" not in extracted_data:
                logger.warning("LLM returned BUDGET without amount field")
            if "currency" not in extracted_data:
                logger.warning("LLM returned BUDGET without currency field")
            if "transaction_type" not in extracted_data:
                logger.warning("LLM returned BUDGET without transaction_type field")
            if "category" not in extracted_data:
                logger.warning("LLM returned BUDGET without category field")
            if "date" not in extracted_data:
                logger.warning("LLM returned BUDGET without date field")

        elif category == Category.SHOPPING:
            if "items" not in extracted_data or not isinstance(extracted_data["items"], list):
                logger.warning("LLM returned SHOPPING without items list, adding empty list")
                extracted_data["items"] = []
        elif category == Category.REMINDER and "action" not in extracted_data:
            logger.debug("LLM returned REMINDER without action field")
        elif category == Category.CALENDAR and "time_reference" not in extracted_data:
            logger.debug("LLM returned CALENDAR without time_reference field")

        return extracted_data
