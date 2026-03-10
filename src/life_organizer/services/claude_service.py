"""Claude LLM service for parsing budget text into structured transactions."""

import datetime
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

# Load budget system prompt at module level
_PROMPT_DIR = Path(__file__).parent.parent / "prompts"
_BUDGET_PROMPT_FILE = _PROMPT_DIR / "budget_system_prompt_v2.txt"

_BUDGET_VISION_PROMPT_FILE = _PROMPT_DIR / "budget_vision_prompt_v1.txt"

try:
    with _BUDGET_PROMPT_FILE.open(encoding="utf-8") as f:
        _BUDGET_PROMPT = f.read()
    logger.debug("Loaded budget system prompt v2")
except FileNotFoundError:
    logger.error(f"Prompt file not found: {_BUDGET_PROMPT_FILE}")
    raise

try:
    with _BUDGET_VISION_PROMPT_FILE.open(encoding="utf-8") as f:
        _BUDGET_VISION_PROMPT = f.read()
    logger.debug("Loaded budget vision prompt v1")
except FileNotFoundError:
    logger.error(f"Prompt file not found: {_BUDGET_VISION_PROMPT_FILE}")
    raise


class ClaudeService:
    """Service for parsing natural language budget text using Claude LLM."""

    def __init__(self, api_key: str, model: str = "claude-haiku-4-5") -> None:
        """Initialize Claude service.

        Args:
            api_key: Anthropic API key
            model: Claude model identifier
        """
        self.client = anthropic.AsyncAnthropic(api_key=api_key, timeout=10.0)
        self.model = model
        logger.info(f"Initialized ClaudeService with model: {model}")

    def _get_system_prompt_with_current_date(self) -> str:
        """Get budget system prompt with today's date injected.

        Returns:
            System prompt with current date replacing placeholders
        """
        today = datetime.date.today()
        today_iso = today.isoformat()
        today_long = today.strftime("%B %-d, %Y")

        yesterday = today - datetime.timedelta(days=1)
        yesterday_iso = yesterday.isoformat()

        prompt = _BUDGET_PROMPT
        prompt = prompt.replace("November 4, 2025", today_long)
        prompt = prompt.replace("2025-11-04", today_iso)
        prompt = prompt.replace("2025-11-03", yesterday_iso)

        return prompt

    def _estimate_transaction_count(self, text: str) -> int:
        """Estimate number of transactions in input using simple heuristics.

        Args:
            text: User input text

        Returns:
            Estimated transaction count
        """
        if not text or not text.strip():
            return 0

        comma_count = text.count(",")
        and_count = text.lower().count(" and ")

        return max(1, comma_count + and_count + 1)

    def _ensure_extracted_data_fields(
        self,
        extracted_data: Any,
    ) -> dict[str, Any]:
        """Ensure extracted_data has expected fields for budget category.

        Args:
            extracted_data: Raw extracted data from LLM (may be dict or list)

        Returns:
            Validated dict of extracted data fields
        """
        result_dict: dict[str, Any]
        if not isinstance(extracted_data, dict):
            if isinstance(extracted_data, list) and len(extracted_data) > 0:
                logger.warning(
                    f"extracted_data is a list with {len(extracted_data)} items, taking first item"
                )
                result_dict = extracted_data[0] if isinstance(extracted_data[0], dict) else {}
            else:
                logger.warning(
                    f"extracted_data is not a dict: {type(extracted_data)}, converting to empty dict"
                )
                result_dict = {}
        else:
            result_dict = extracted_data

        # Log warnings for missing critical fields
        for field in ("amount", "currency", "transaction_type", "category", "date"):
            if field not in result_dict:
                logger.warning(f"LLM returned BUDGET without {field} field")

        return result_dict

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        reraise=True,
    )
    async def parse_budget_text(self, text: str) -> list[ClassifiedInput]:
        """Parse natural language budget text into structured ClassifiedInput objects.

        Args:
            text: Natural language budget text (e.g., "coffee 4.50, lunch 12 eur")

        Returns:
            List of ClassifiedInput objects with parsed budget data

        Raises:
            HTTPException: If input exceeds transaction limit (422)
            anthropic.APIError: On API communication errors (after 3 retries)
        """
        # Empty input check
        if not text or not text.strip():
            logger.debug("Empty or whitespace-only input, returning BUDGET with confidence 0.0")
            return [
                ClassifiedInput(
                    category=Category.BUDGET,
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
                detail=(
                    f"Maximum 15 transactions per request. "
                    f"You provided approximately {estimated_count}."
                ),
            )

        try:
            # Get system prompt with current date
            system_prompt = self._get_system_prompt_with_current_date()

            # Call Claude API with prompt caching
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=[
                    {
                        "type": "text",
                        "text": system_prompt,
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
            logger.debug(
                f"Raw LLM response: {response_text[:200]}..."
                if len(response_text) > 200
                else f"Raw LLM response: {response_text}"
            )

            # Strip markdown code fences if present
            response_text = response_text.strip()
            if response_text.startswith("```"):
                lines = response_text.split("\n", 1)
                if len(lines) > 1:
                    response_text = lines[1]
                if response_text.endswith("```"):
                    response_text = response_text.rsplit("```", 1)[0]
                response_text = response_text.strip()

            # Parse JSON array
            data_array = json.loads(response_text)
            logger.debug(
                f"Parsed {len(data_array) if isinstance(data_array, list) else 0} "
                f"transaction(s) from LLM response"
            )

            if not isinstance(data_array, list):
                logger.error(f"Expected JSON array, got {type(data_array)}")
                raise ValueError("LLM did not return a JSON array")

            # Parse each transaction
            results: list[ClassifiedInput] = []
            for item_data in data_array:
                # Normalize category to BUDGET (always budget now)
                item_data["category"] = Category.BUDGET

                # Check if extracted_data is incorrectly a list (LLM mistake)
                extracted_data_raw = item_data.get("extracted_data", {})
                if isinstance(extracted_data_raw, list) and len(extracted_data_raw) > 1:
                    logger.warning(
                        f"LLM returned extracted_data as array with "
                        f"{len(extracted_data_raw)} items. "
                        f"Unrolling into {len(extracted_data_raw)} separate transactions."
                    )
                    for tx_idx, transaction_data in enumerate(extracted_data_raw):
                        if not isinstance(transaction_data, dict):
                            logger.warning(f"Skipping non-dict item at index {tx_idx}")
                            continue

                        unrolled_item = {
                            "category": Category.BUDGET,
                            "confidence": item_data.get("confidence", 0.8),
                            "extracted_data": self._ensure_extracted_data_fields(transaction_data),
                            "raw_input": item_data.get("raw_input", ""),
                            "classifier_source": "llm",
                        }

                        result = ClassifiedInput.model_validate(unrolled_item)
                        results.append(result)
                    continue

                # Normal case: extracted_data is a dict or single-item list
                item_data["extracted_data"] = self._ensure_extracted_data_fields(extracted_data_raw)
                item_data["classifier_source"] = "llm"

                result = ClassifiedInput.model_validate(item_data)
                results.append(result)

            logger.info(f"Parsed {len(results)} transaction(s) from input")
            return results

        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            raise

        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Failed to parse Claude response: {e}")
            return [
                ClassifiedInput(
                    category=Category.UNKNOWN,
                    confidence=0.0,
                    extracted_data={},
                    raw_input=text,
                    classifier_source="llm",
                )
            ]
