"""Budget entry handler for expenses, income, and savings transactions."""

import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

from dateutil import parser as date_parser

from life_organizer.handlers.base import BaseHandler
from life_organizer.schemas.actions import LogBudgetEntryAction
from life_organizer.schemas.budget import ExpenseCategory, IncomeCategory, SavingsCategory
from life_organizer.schemas.classification import ClassifiedInput
from life_organizer.schemas.enums import ActionType, Category
from life_organizer.schemas.responses import ActionResult

logger = logging.getLogger(__name__)

# Type alias for transaction types
TransactionType = Literal["Expenses", "Income", "Savings"]

# Constants
EUR_TO_BGN_RATE = 1.955

# Currency normalization map
CURRENCY_MAP = {
    "eur": "EUR",
    "euro": "EUR",
    "euros": "EUR",
    "€": "EUR",
    "bgn": "BGN",
    "lev": "BGN",
    "leva": "BGN",
}


def _load_merchant_category_map() -> dict[str, str]:
    """Load merchant to category mapping from JSON file.

    Returns:
        dict mapping merchant names to budget categories
    """
    config_path = (
        Path(__file__).parent.parent.parent.parent / "config" / "merchant_category_map.json"
    )
    with config_path.open() as f:
        return json.load(f)  # type: ignore[no-any-return]


def _load_transaction_type_keywords() -> dict[str, list[str]]:
    """Load transaction type keywords from JSON file.

    Returns:
        dict with 'income' and 'savings' keyword lists
    """
    config_path = (
        Path(__file__).parent.parent.parent.parent / "config" / "transaction_type_keywords.json"
    )
    with config_path.open() as f:
        return json.load(f)  # type: ignore[no-any-return]


# Merchant to category mapping (high-confidence keyword matches)
MERCHANT_CATEGORY_MAP = _load_merchant_category_map()
TRANSACTION_TYPE_KEYWORDS = _load_transaction_type_keywords()


class BudgetEntryHandler(BaseHandler):
    """Handler for budget entries (expenses, income, savings).

    Processes natural language financial transactions, extracts structured data,
    converts currencies, classifies transaction types and categories, and generates
    app actions for iOS to populate the Excel budget sheet.

    Handles:
    - Expenses: "spent 120eur at next"
    - Income: "received 250bgn rent"
    - Savings: "saved 1220 in ibkr"
    """

    def can_handle(self, classified_input: ClassifiedInput) -> bool:
        """Determine if this handler can process the input.

        Args:
            classified_input: Classified user input

        Returns:
            True if category is EXPENSE (used for all budget entries)
        """
        return classified_input.category == Category.EXPENSE

    def requires_app_action(self) -> bool:
        """Determine if this handler requires iOS app involvement.

        Returns:
            True (always delegates to iOS for Excel population)
        """
        return True

    async def execute(self, classified_input: ClassifiedInput) -> ActionResult:
        """Process budget entry and generate app action.

        Args:
            classified_input: Classified user input with extracted data

        Returns:
            ActionResult with LogBudgetEntryAction for iOS app
        """
        try:
            # 1. Extract amount and currency
            amount, currency = _extract_amount_currency(classified_input)

            # 2. Convert to BGN
            amount_bgn = _convert_to_bgn(amount, currency)

            # 3. Classify transaction type
            transaction_type = _classify_transaction_type(classified_input)

            # 4. Classify category
            category = await _classify_category(
                classified_input,
                transaction_type,
            )

            # 5. Parse date
            date_iso = _parse_date(classified_input)

            # 6. Extract details
            details = _extract_details(classified_input)

            # 7. Generate app action
            action = LogBudgetEntryAction(
                amount=amount_bgn,
                date=date_iso,
                transaction_type=transaction_type,
                category=category,
                details=details,
            )

            # 8. Return result
            return ActionResult(
                success=True,
                action_type=ActionType.APP_ACTION_REQUIRED,
                message=f"Logged {transaction_type.lower()}: {amount_bgn} BGN in {category}",
                app_action=action,
            )

        except ValueError as e:
            # Invalid amount or parsing error
            return ActionResult(
                success=False,
                action_type=ActionType.CONFIRMATION_NEEDED,
                message=f"Could not parse budget entry: {e!s}",
            )

        except Exception as e:
            # Unexpected error
            logger.exception("Budget entry handler error: %s", e)
            return ActionResult(
                success=False,
                action_type=ActionType.CONFIRMATION_NEEDED,
                message="An error occurred processing your budget entry",
            )


# Private helper functions


def _extract_amount_currency(classified_input: ClassifiedInput) -> tuple[float, str]:
    """Extract amount and currency from classified input.

    Args:
        classified_input: Classified user input with extracted_data

    Returns:
        Tuple of (amount, currency)
        Currency is "EUR" or "BGN", defaults to "BGN"

    Raises:
        ValueError: If amount cannot be extracted
    """
    # Check extracted_data first
    if "amount" in classified_input.extracted_data:
        amount_val = classified_input.extracted_data["amount"]
        currency_val = classified_input.extracted_data.get("currency", "BGN")
        # Type narrowing for mypy
        if not isinstance(amount_val, (int, float, str)):
            msg = f"Invalid amount type in extracted_data: {type(amount_val)}"
            raise ValueError(msg)
        if not isinstance(currency_val, str):
            msg = f"Invalid currency type in extracted_data: {type(currency_val)}"
            raise ValueError(msg)
        return (float(amount_val), currency_val)

    # Fallback: regex on raw_input
    pattern = r"(\d+(?:[.,]\d{1,2})?)\s*(eur|euro|euros|€|bgn|lev|leva)?"
    match = re.search(pattern, classified_input.raw_input.lower())

    if not match:
        msg = f"No amount found in input: {classified_input.raw_input}"
        raise ValueError(msg)

    amount_str = match.group(1).replace(",", ".")
    amount = float(amount_str)

    currency_raw = match.group(2)
    currency = CURRENCY_MAP.get(currency_raw.lower(), "BGN") if currency_raw else "BGN"

    return (amount, currency)


def _convert_to_bgn(amount: float, currency: str) -> float:
    """Convert amount to BGN using fixed EUR rate.

    Args:
        amount: Amount to convert
        currency: Source currency ("EUR" or "BGN")

    Returns:
        Amount in BGN, rounded to 2 decimal places
    """
    if currency == "EUR":
        return round(amount * EUR_TO_BGN_RATE, 2)
    return amount  # Already BGN or default


def _parse_date(classified_input: ClassifiedInput) -> str:
    """Parse date from classified input.

    Supports:
    - Relative: "today", "yesterday"
    - Day names: "Monday", "Tuesday", etc. (most recent occurrence)
    - Absolute: "Nov 3", "2025-11-03", "November 3"

    Args:
        classified_input: Classified user input

    Returns:
        Date in ISO format (YYYY-MM-DD)
    """
    text = classified_input.raw_input.lower()

    # Check for relative dates
    if "yesterday" in text:
        date = datetime.now() - timedelta(days=1)
        return date.strftime("%Y-%m-%d")

    if "today" in text:
        return datetime.now().strftime("%Y-%m-%d")

    # Check for day names (monday, tuesday, etc.)
    day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for day_name in day_names:
        if day_name in text:
            # Find most recent occurrence of this day
            today = datetime.now()
            target_day = day_names.index(day_name)
            days_ahead = target_day - today.weekday()
            if days_ahead > 0:
                days_ahead -= 7  # Get last week's occurrence
            date = today + timedelta(days=days_ahead)
            return date.strftime("%Y-%m-%d")

    # Try parsing absolute dates with dateutil (only if clear date pattern exists)
    try:
        # Month name patterns (helps avoid parsing random numbers as years)
        date_keywords = [
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
            "jan",
            "feb",
            "mar",
            "apr",
            "jun",
            "jul",
            "aug",
            "sep",
            "oct",
            "nov",
            "dec",
        ]

        # Check for ISO date format (YYYY-MM-DD) or month names
        has_date_pattern = re.search(r"\d{4}-\d{2}-\d{2}", text) is not None or any(
            keyword in text for keyword in date_keywords
        )

        if has_date_pattern:
            parsed_date = date_parser.parse(text, fuzzy=True, default=datetime.now())

            # Sanity check: year should be reasonable (avoid "7" or "1220" becoming years)
            current_year = datetime.now().year
            if current_year - 1 <= parsed_date.year <= current_year + 1:
                result: str = parsed_date.strftime("%Y-%m-%d")
                return result
    except Exception:
        pass

    # Default to today
    return datetime.now().strftime("%Y-%m-%d")


def _classify_transaction_type(classified_input: ClassifiedInput) -> TransactionType:
    """Classify transaction type based on keywords.

    Priority: Income > Savings > Expenses (default)

    Args:
        classified_input: Classified user input

    Returns:
        One of: "Income", "Savings", "Expenses"
    """
    text = classified_input.raw_input.lower()

    # Check extracted_data first (if classifier detected type)
    if "transaction_type" in classified_input.extracted_data:
        trans_type = classified_input.extracted_data["transaction_type"]
        if isinstance(trans_type, str) and trans_type in ("Expenses", "Income", "Savings"):
            return trans_type  # type: ignore[return-value]

    # Income keywords (highest priority)
    if any(keyword in text for keyword in TRANSACTION_TYPE_KEYWORDS["income"]):
        return "Income"

    # Savings keywords
    if any(keyword in text for keyword in TRANSACTION_TYPE_KEYWORDS["savings"]):
        return "Savings"

    # Default to Expenses
    return "Expenses"


def _extract_details(classified_input: ClassifiedInput) -> str | None:
    """Extract merchant/details from input.

    Removes amount, currency, and date patterns to get remaining context.

    Args:
        classified_input: Classified user input

    Returns:
        Extracted details or None if empty
    """
    text = classified_input.raw_input.lower()

    # Remove amount/currency pattern
    text = re.sub(r"\d+(?:[.,]\d{1,2})?\s*(eur|euro|euros|€|bgn|lev|leva)?", "", text)

    # Remove relative dates
    text = re.sub(r"\b(today|yesterday|tomorrow)\b", "", text)

    # Remove day names
    day_pattern = r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b"
    text = re.sub(day_pattern, "", text)

    # Remove common words
    text = re.sub(r"\b(spent|paid|received|saved|at|for|in|to|from|the|a|an|i|my)\b", "", text)

    # Clean up whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text if text else None


def _get_categories_for_type(transaction_type: str) -> list[str]:
    """Get available category names for transaction type.

    Args:
        transaction_type: One of "Expenses", "Income", "Savings"

    Returns:
        List of category names
    """
    if transaction_type == "Expenses":
        return [cat.value for cat in ExpenseCategory]
    if transaction_type == "Income":
        return [cat.value for cat in IncomeCategory]
    if transaction_type == "Savings":
        return [cat.value for cat in SavingsCategory]
    return ["Other"]


async def _classify_category(
    classified_input: ClassifiedInput,
    transaction_type: str,  # noqa: ARG001 - Will be used in Phase 2 for LLM fallback
) -> str:
    """Classify budget category using hybrid approach.

    Uses keyword mapping for high-confidence cases, LLM fallback for ambiguous.

    Args:
        classified_input: Classified user input
        transaction_type: One of "Expenses", "Income", "Savings" (used for LLM fallback in Phase 2)

    Returns:
        Category name string
    """
    details = _extract_details(classified_input)
    if not details:
        return "Other"

    # Check merchant keyword map (case-insensitive)
    details_lower = details.lower()
    for merchant, category in MERCHANT_CATEGORY_MAP.items():
        if merchant.lower() in details_lower:
            return category

    # LLM fallback would go here (Phase 2 integration)
    # For Phase 1, we just fallback to "Other" for unmapped merchants

    # Fallback to "Other"
    return "Other"
