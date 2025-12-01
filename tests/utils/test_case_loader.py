"""Utility for loading test cases from JSON fixtures."""

import json
from pathlib import Path
from typing import Any


class TestCase:
    """Represents a single test case for prompt validation."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Initialize test case from dict.

        Args:
            data: Test case data from JSON
        """
        self.id = data["id"]
        self.description = data.get("description", "")
        self.input = data["input"]
        self.expected = data["expected"]

    def __repr__(self) -> str:
        """Return string representation."""
        return f"TestCase(id={self.id!r}, input={self.input!r})"

    @property
    def is_multi_transaction(self) -> bool:
        """Check if this test case expects multiple transactions."""
        return self.expected.get("multi_transaction", False)

    @property
    def expected_transaction_count(self) -> int:
        """Get expected number of transactions."""
        if self.is_multi_transaction:
            return self.expected.get("expected_count", 1)
        return 1


def load_test_cases(fixture_file: str = "budget_prompt_test_cases.json") -> list[TestCase]:
    """Load test cases from JSON fixture file.

    Args:
        fixture_file: Name of the fixture file (default: budget_prompt_test_cases.json)

    Returns:
        List of TestCase objects

    Raises:
        FileNotFoundError: If fixture file doesn't exist
        json.JSONDecodeError: If JSON is invalid
        KeyError: If required fields are missing
    """
    fixtures_dir = Path(__file__).parent.parent / "fixtures"
    fixture_path = fixtures_dir / fixture_file

    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture file not found: {fixture_path}")

    with fixture_path.open(encoding="utf-8") as f:
        data = json.load(f)

    # Validate structure
    if "test_cases" not in data:
        raise KeyError("Fixture must contain 'test_cases' key")

    # Create TestCase objects
    test_cases = []
    for case_data in data["test_cases"]:
        # Validate required fields
        required_fields = ["id", "input", "expected"]
        missing_fields = [f for f in required_fields if f not in case_data]
        if missing_fields:
            raise KeyError(
                f"Test case missing required fields: {missing_fields}. Case data: {case_data}"
            )

        test_cases.append(TestCase(case_data))

    return test_cases


def get_test_case_by_id(
    test_case_id: str, fixture_file: str = "budget_prompt_test_cases.json"
) -> TestCase | None:
    """Get a specific test case by ID.

    Args:
        test_case_id: The test case ID to find
        fixture_file: Name of the fixture file

    Returns:
        TestCase if found, None otherwise
    """
    test_cases = load_test_cases(fixture_file)
    for case in test_cases:
        if case.id == test_case_id:
            return case
    return None
