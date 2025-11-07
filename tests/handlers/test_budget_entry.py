"""Tests for BudgetEntryHandler using LLM-extracted data."""

import pytest
from fastapi import HTTPException

from life_organizer.handlers.budget_entry import BudgetEntryHandler, _convert_to_bgn
from life_organizer.schemas.classification import ClassifiedInput
from life_organizer.schemas.enums import ActionType, Category


@pytest.fixture
def handler() -> BudgetEntryHandler:
    """Create a budget entry handler instance."""
    return BudgetEntryHandler()


def _classified_input(
    extracted_data: dict[str, object], raw_input: str = "test input"
) -> ClassifiedInput:
    """Helper to build ClassifiedInput objects for tests."""
    return ClassifiedInput(
        category=Category.BUDGET,
        confidence=0.95,
        extracted_data=extracted_data,
        raw_input=raw_input,
        classifier_source="llm",
    )


class TestBudgetEntryHandlerExecute:
    """Integration-style tests for execute() using LLM extracted data."""

    @pytest.mark.asyncio
    async def test_expense_in_eur_converts_to_bgn(self, handler: BudgetEntryHandler) -> None:
        """Expense entries in EUR should be converted to BGN."""
        classified = _classified_input(
            {
                "amount": 120.0,
                "currency": "EUR",
                "transaction_type": "Expenses",
                "category": "Clothes",
                "merchant": "next",
                "date": "2025-11-04",
            },
            raw_input="spent 120eur at next",
        )

        result = await handler.execute(classified)

        assert result.success is True
        assert result.action_type == ActionType.APP_ACTION_REQUIRED
        assert result.app_action is not None
        action = result.app_action
        assert action.amount == pytest.approx(234.6)
        assert action.transaction_type == "Expenses"
        assert action.category == "Clothes"
        assert action.details == "next"
        assert action.date == "2025-11-04"
        assert result.message == "Logged expenses: 234.6 BGN in Clothes"

    @pytest.mark.asyncio
    async def test_income_entry_passes_through_fields(self, handler: BudgetEntryHandler) -> None:
        """Income entries should keep amount, date, and category from extracted data."""
        classified = _classified_input(
            {
                "amount": 250.0,
                "currency": "BGN",
                "transaction_type": "Income",
                "category": "Rent",
                "merchant": "tenant",
                "date": "2025-10-31",
            },
            raw_input="received 250 bgn rent",
        )

        result = await handler.execute(classified)

        assert result.success is True
        assert result.app_action is not None
        action = result.app_action
        assert action.amount == 250.0
        assert action.transaction_type == "Income"
        assert action.category == "Rent"
        assert action.details == "tenant"
        assert action.date == "2025-10-31"
        assert result.message == "Logged income: 250.0 BGN in Rent"

    @pytest.mark.asyncio
    async def test_savings_entry_without_merchant(self, handler: BudgetEntryHandler) -> None:
        """Savings entries with no merchant should produce None details."""
        classified = _classified_input(
            {
                "amount": 1220.0,
                "currency": "BGN",
                "transaction_type": "Savings",
                "category": "Savings",
                "date": "2025-11-04",
            },
            raw_input="saved 1220 in ibkr",
        )

        result = await handler.execute(classified)

        assert result.success is True
        assert result.app_action is not None
        action = result.app_action
        assert action.amount == 1220.0
        assert action.transaction_type == "Savings"
        assert action.category == "Savings"
        assert action.details is None
        assert action.date == "2025-11-04"
        assert result.message == "Logged savings: 1220.0 BGN in Savings"

    @pytest.mark.asyncio
    async def test_missing_required_fields_raises_exception(
        self, handler: BudgetEntryHandler
    ) -> None:
        """Missing required extracted fields should raise HTTPException."""
        classified = _classified_input(
            {
                "amount": 50.0,
                "currency": "BGN",
                # transaction_type missing
                "category": "Groceries",
                "date": "2025-11-04",
            }
        )

        with pytest.raises(HTTPException) as exc_info:
            await handler.execute(classified)

        assert exc_info.value.status_code == 422
        assert "Missing required fields: transaction_type" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_invalid_transaction_type_raises_exception(
        self, handler: BudgetEntryHandler
    ) -> None:
        """Unexpected transaction_type should raise HTTPException."""
        classified = _classified_input(
            {
                "amount": 45.0,
                "currency": "BGN",
                "transaction_type": "Gift",
                "category": "Other",
                "date": "2025-11-04",
            }
        )

        with pytest.raises(HTTPException) as exc_info:
            await handler.execute(classified)

        assert exc_info.value.status_code == 422
        assert "Invalid transaction_type" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_non_positive_amount_raises_exception(self, handler: BudgetEntryHandler) -> None:
        """Amounts that are zero or negative should be rejected."""
        classified = _classified_input(
            {
                "amount": 0,
                "currency": "BGN",
                "transaction_type": "Expenses",
                "category": "Groceries",
                "date": "2025-11-04",
            }
        )

        with pytest.raises(HTTPException) as exc_info:
            await handler.execute(classified)

        assert exc_info.value.status_code == 422
        assert "Amount must be positive" in exc_info.value.detail


class TestConvertToBGN:
    """Unit tests for currency conversion helper."""

    def test_eur_to_bgn(self) -> None:
        """120 EUR should convert to 234.60 BGN."""
        assert _convert_to_bgn(120.0, "EUR") == pytest.approx(234.6)

    def test_bgn_passthrough(self) -> None:
        """BGN amounts should remain unchanged."""
        assert _convert_to_bgn(95.0, "BGN") == pytest.approx(95.0)

    def test_usd_conversion(self) -> None:
        """USD amounts use approximate conversion rate."""
        assert _convert_to_bgn(10.0, "USD") == pytest.approx(18.0)

    def test_unknown_currency_defaults_to_bgn(self) -> None:
        """Unknown currencies are treated as BGN."""
        assert _convert_to_bgn(42.0, "JPY") == pytest.approx(42.0)
