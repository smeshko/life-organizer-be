"""Assertion helpers for prompt validation tests.

These helpers provide flexible comparison logic for validating LLM outputs,
allowing for reasonable tolerances and variations in non-critical fields.
"""

from typing import Any


def assert_amount_match(
    actual: float, expected: float, tolerance: float = 0.01, field_name: str = "amount"
) -> None:
    """Assert that two amounts match within tolerance.

    Args:
        actual: Actual amount from LLM
        expected: Expected amount
        tolerance: Acceptable difference (default: 0.01)
        field_name: Name of the field for error messages

    Raises:
        AssertionError: If amounts don't match within tolerance
    """
    diff = abs(actual - expected)
    assert diff <= tolerance, (
        f"{field_name}: expected {expected}, got {actual} (diff: {diff}, tolerance: {tolerance})"
    )


def assert_currency_match(actual: str, expected: str, field_name: str = "currency") -> None:
    """Assert that currency codes match (case-insensitive).

    Args:
        actual: Actual currency from LLM
        expected: Expected currency
        field_name: Name of the field for error messages

    Raises:
        AssertionError: If currencies don't match
    """
    assert actual.upper() == expected.upper(), (
        f"{field_name}: expected {expected!r}, got {actual!r}"
    )


def assert_category_match(actual: str, expected: str, field_name: str = "category") -> None:
    """Assert that category matches exactly (case-sensitive).

    Args:
        actual: Actual category from LLM
        expected: Expected category
        field_name: Name of the field for error messages

    Raises:
        AssertionError: If categories don't match
    """
    assert actual == expected, (
        f"{field_name}: expected {expected!r}, got {actual!r} "
        f"(category names must match exactly, including casing)"
    )


def assert_merchant_match(
    actual: str | None,
    expected: str | None,
    flexible: bool = True,
    field_name: str = "merchant",
) -> None:
    """Assert that merchant names match.

    Args:
        actual: Actual merchant from LLM
        expected: Expected merchant
        flexible: If True, use case-insensitive comparison (default: True)
        field_name: Name of the field for error messages

    Raises:
        AssertionError: If merchants don't match
    """
    if expected is None:
        # If None expected, actual can be anything (including None)
        return

    if actual is None:
        raise AssertionError(f"{field_name}: expected {expected!r}, got None")

    if flexible:
        assert actual.lower() == expected.lower(), (
            f"{field_name}: expected {expected!r}, got {actual!r} (case-insensitive comparison)"
        )
    else:
        assert actual == expected, f"{field_name}: expected {expected!r}, got {actual!r}"


def assert_transaction_type_match(
    actual: str, expected: str, field_name: str = "transaction_type"
) -> None:
    """Assert that transaction types match exactly.

    Args:
        actual: Actual transaction type from LLM
        expected: Expected transaction type
        field_name: Name of the field for error messages

    Raises:
        AssertionError: If transaction types don't match
    """
    assert actual == expected, f"{field_name}: expected {expected!r}, got {actual!r}"


def assert_confidence_threshold(
    actual: float,
    min_threshold: float = 0.7,
    max_threshold: float | None = None,
    field_name: str = "confidence",
) -> None:
    """Assert that confidence meets threshold requirements.

    Args:
        actual: Actual confidence from LLM
        min_threshold: Minimum acceptable confidence
        max_threshold: Maximum acceptable confidence (optional)
        field_name: Name of the field for error messages

    Raises:
        AssertionError: If confidence doesn't meet thresholds
    """
    if max_threshold is not None:
        assert min_threshold <= actual <= max_threshold, (
            f"{field_name}: expected between {min_threshold} and {max_threshold}, got {actual}"
        )
    else:
        assert actual >= min_threshold, f"{field_name}: expected >= {min_threshold}, got {actual}"


def assert_date_format(actual: str, field_name: str = "date") -> None:
    """Assert that date is in ISO format (YYYY-MM-DD).

    Args:
        actual: Actual date from LLM
        field_name: Name of the field for error messages

    Raises:
        AssertionError: If date is not in ISO format
    """
    import re

    iso_pattern = r"^\d{4}-\d{2}-\d{2}$"
    assert re.match(iso_pattern, actual), (
        f"{field_name}: expected ISO format (YYYY-MM-DD), got {actual!r}"
    )


def assert_extracted_data_matches(
    actual_data: dict[str, Any],
    expected_data: dict[str, Any],
    amount_tolerance: float = 0.01,
) -> None:
    """Assert that extracted data matches expected values with appropriate flexibility.

    This is a high-level assertion that uses the appropriate comparison method
    for each field type.

    Args:
        actual_data: Actual extracted_data from LLM
        expected_data: Expected extracted_data
        amount_tolerance: Tolerance for amount comparisons

    Raises:
        AssertionError: If any field doesn't match
    """
    # Amount
    if "amount" in expected_data:
        assert "amount" in actual_data, "Missing 'amount' field in extracted_data"
        assert_amount_match(actual_data["amount"], expected_data["amount"], amount_tolerance)

    # Currency
    if "currency" in expected_data:
        assert "currency" in actual_data, "Missing 'currency' field in extracted_data"
        assert_currency_match(actual_data["currency"], expected_data["currency"])

    # Transaction type
    if "transaction_type" in expected_data:
        assert "transaction_type" in actual_data, (
            "Missing 'transaction_type' field in extracted_data"
        )
        assert_transaction_type_match(
            actual_data["transaction_type"], expected_data["transaction_type"]
        )

    # Category (case-sensitive)
    if "category" in expected_data:
        assert "category" in actual_data, "Missing 'category' field in extracted_data"
        assert_category_match(actual_data["category"], expected_data["category"])

    # Merchant (flexible)
    if "merchant" in expected_data:
        assert_merchant_match(actual_data.get("merchant"), expected_data["merchant"], flexible=True)

    # Date format validation
    if "date" in actual_data:
        assert_date_format(actual_data["date"])

    # Note: Confidence thresholds are handled in the test function
    # (confidence is in the parent object, not extracted_data)
