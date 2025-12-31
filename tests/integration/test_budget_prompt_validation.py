"""Integration tests for budget prompt validation using real Claude Haiku API calls.

These tests validate that the system prompt produces correct outputs for known test cases.
Unlike mock-based unit tests, these make real API calls to Claude to verify prompt behavior.

Requirements:
- ANTHROPIC_API_KEY or CLAUDE_API_KEY environment variable must be set
- Tests are marked with @pytest.mark.integration
- Run with: pytest -m integration

Cost: ~$0.001-0.002 per test case (Claude Haiku pricing)
"""

import pytest

from life_organizer.schemas.enums import Category
from life_organizer.services.claude_classifier import ClaudeClassifier
from tests.config.prompt_validation_config import (
    PromptValidationConfig,
    get_anthropic_api_key,
    skip_if_no_api_key,
)
from tests.utils.assertion_helpers import (
    assert_confidence_threshold,
    assert_extracted_data_matches,
)
from tests.utils.test_case_loader import TestCase, load_test_cases


@pytest.fixture
def real_classifier():
    """Create a ClaudeClassifier with real API key for integration testing.

    Raises:
        pytest.skip: If API key is not available
    """
    api_key = get_anthropic_api_key()
    if not api_key:
        pytest.skip("API key not available")

    return ClaudeClassifier(api_key=api_key)


@pytest.fixture
def budget_test_cases():
    """Load budget prompt test cases from fixtures."""
    return load_test_cases("budget_prompt_test_cases.json")


@pytest.mark.integration
@pytest.mark.asyncio
@skip_if_no_api_key()
class TestBudgetPromptValidation:
    """Integration tests for budget prompt using real LLM calls."""

    async def test_simple_expense_dm(self, real_classifier: ClaudeClassifier):
        """Test simple expense extraction - 50 at DM."""
        result = await real_classifier.classify("50 at DM", category="budget")

        assert len(result) == 1
        transaction = result[0]

        assert transaction.category == Category.BUDGET
        assert_extracted_data_matches(
            transaction.extracted_data,
            {
                "amount": 50.0,
                "currency": "EUR",
                "transaction_type": "Expenses",
                "category": "Body care",
            },
            amount_tolerance=PromptValidationConfig.AMOUNT_TOLERANCE,
        )
        assert_confidence_threshold(transaction.confidence, min_threshold=0.7)

    async def test_home_improvements_full_name(self, real_classifier: ClaudeClassifier):
        """Test that 'Home Improvements' maps to exact enum 'Home improvements' (not 'Home')."""
        result = await real_classifier.classify("423 EUR for Home Improvements", category="budget")

        assert len(result) == 1
        transaction = result[0]

        assert transaction.category == Category.BUDGET
        assert_extracted_data_matches(
            transaction.extracted_data,
            {
                "amount": 423.0,
                "currency": "EUR",
                "transaction_type": "Expenses",
                "category": "Home improvements",  # Exact match required
            },
        )
        assert_confidence_threshold(transaction.confidence, min_threshold=0.7)

    async def test_salary_ivo_fallback(self, real_classifier: ClaudeClassifier):
        """Test that generic 'salary' maps to 'Salary Ivo' (not invalid 'Salary')."""
        result = await real_classifier.classify("7700eur salary", category="budget")

        assert len(result) == 1
        transaction = result[0]

        assert transaction.category == Category.BUDGET
        assert_extracted_data_matches(
            transaction.extracted_data,
            {
                "amount": 7700.0,
                "currency": "EUR",
                "transaction_type": "Income",
                "category": "Salary Ivo",  # Maps via synonym
            },
        )
        # Synonym mapping produces high confidence
        assert_confidence_threshold(transaction.confidence, min_threshold=0.7)

    async def test_medical_synonym_healthcare(self, real_classifier: ClaudeClassifier):
        """Test that 'doctor visit' maps to 'Medical' (not 'Healthcare')."""
        result = await real_classifier.classify("150 for a doctor's visit", category="budget")

        assert len(result) == 1
        transaction = result[0]

        assert transaction.category == Category.BUDGET
        assert_extracted_data_matches(
            transaction.extracted_data,
            {
                "amount": 150.0,
                "currency": "EUR",
                "transaction_type": "Expenses",
                "category": "Medical",  # Not "Healthcare"
            },
        )
        assert_confidence_threshold(transaction.confidence, min_threshold=0.7)

    async def test_multi_transaction_simple(self, real_classifier: ClaudeClassifier):
        """Test multiple transactions separated by comma."""
        result = await real_classifier.classify("50 at DM, 120 at Next", category="budget")

        assert len(result) == 2

        # First transaction: DM
        assert result[0].category == Category.BUDGET
        assert_extracted_data_matches(
            result[0].extracted_data,
            {
                "amount": 50.0,
                "currency": "EUR",
                "category": "Body care",
            },
        )

        # Second transaction: Next
        assert result[1].category == Category.BUDGET
        assert_extracted_data_matches(
            result[1].extracted_data,
            {
                "amount": 120.0,
                "currency": "EUR",
                "category": "Clothes",
            },
        )


@pytest.mark.integration
@pytest.mark.asyncio
@skip_if_no_api_key()
@pytest.mark.parametrize("test_case", load_test_cases("budget_prompt_test_cases.json"))
async def test_budget_golden_dataset(test_case: TestCase, real_classifier: ClaudeClassifier):
    """Parameterized test that runs all test cases from golden dataset.

    This test uses pytest's parametrize to run each test case from the fixture file.
    Each test case is validated against its expected output using real LLM calls.

    Args:
        test_case: TestCase object from fixture
        real_classifier: Real ClaudeClassifier with API key
    """
    # Call real LLM
    result = await real_classifier.classify(test_case.input, category="budget")

    # Handle multi-transaction cases
    if test_case.is_multi_transaction:
        expected_count = test_case.expected.get("expected_count", 0)
        assert len(result) == expected_count, (
            f"Expected {expected_count} transactions, got {len(result)}"
        )

        # Validate each transaction
        expected_transactions = test_case.expected.get("transactions", [])
        for i, expected_tx in enumerate(expected_transactions):
            assert result[i].category == Category.BUDGET
            assert_extracted_data_matches(
                result[i].extracted_data,
                expected_tx,
                amount_tolerance=PromptValidationConfig.AMOUNT_TOLERANCE,
            )
        return

    # Handle single-transaction cases
    # Basic assertions
    assert len(result) >= 1, f"Expected at least 1 result, got {len(result)}"
    transaction = result[0]
    assert transaction.category == Category.BUDGET

    # Validate extracted data
    expected_data = test_case.expected.get("extracted_data", {})
    assert_extracted_data_matches(
        transaction.extracted_data,
        expected_data,
        amount_tolerance=PromptValidationConfig.AMOUNT_TOLERANCE,
    )

    # Validate confidence thresholds
    min_conf = expected_data.get("min_confidence", 0.7)
    max_conf = expected_data.get("max_confidence")
    assert_confidence_threshold(
        transaction.confidence, min_threshold=min_conf, max_threshold=max_conf
    )
