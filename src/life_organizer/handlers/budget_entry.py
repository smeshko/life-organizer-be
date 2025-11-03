"""Budget entry handler for expenses, income, and savings transactions."""

import re
from datetime import datetime, timedelta

from dateutil import parser as date_parser

from life_organizer.schemas.classification import ClassifiedInput

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

    # Try parsing absolute dates with dateutil
    try:
        parsed_date = date_parser.parse(text, fuzzy=True, default=datetime.now())
        result: str = parsed_date.strftime("%Y-%m-%d")
        return result
    except Exception:
        # Default to today
        return datetime.now().strftime("%Y-%m-%d")


def _classify_transaction_type(classified_input: ClassifiedInput) -> str:
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
        if isinstance(trans_type, str):
            return trans_type

    # Income keywords (highest priority)
    income_keywords = ["received", "got", "earned", "salary", "rent", "income"]
    if any(keyword in text for keyword in income_keywords):
        return "Income"

    # Savings keywords
    savings_keywords = ["saved", "invested", "saving", "deposit"]
    if any(keyword in text for keyword in savings_keywords):
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
