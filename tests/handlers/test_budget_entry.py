"""Tests for BudgetEntryHandler using LLM-extracted data."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from life_organizer.handlers.budget_entry import BudgetEntryHandler, _convert_to_eur
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
    @patch("life_organizer.handlers.budget_entry.async_session_factory")
    async def test_expense_in_eur_persisted(
        self, mock_session_factory: MagicMock, handler: BudgetEntryHandler
    ) -> None:
        """Expense entries in EUR should be persisted to database."""
        # Mock database session
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session

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

        # Handler always returns a list, even for single transaction
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].success is True
        assert result[0].action_type == ActionType.BACKEND_HANDLED
        assert result[0].message == "Logged expenses: 120.0 EUR in Clothes"

        # Verify database operations were called
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("life_organizer.handlers.budget_entry.async_session_factory")
    async def test_income_entry_passes_through_fields(
        self, mock_session_factory: MagicMock, handler: BudgetEntryHandler
    ) -> None:
        """Income entries should keep amount, date, and category from extracted data."""
        # Mock database session
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session

        classified = _classified_input(
            {
                "amount": 250.0,
                "currency": "EUR",
                "transaction_type": "Income",
                "category": "Rent",
                "merchant": "tenant",
                "date": "2025-10-31",
            },
            raw_input="received 250 eur rent",
        )

        result = await handler.execute(classified)

        # Handler always returns a list, even for single transaction
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].success is True
        assert result[0].action_type == ActionType.BACKEND_HANDLED
        assert result[0].message == "Logged income: 250.0 EUR in Rent"

        # Verify database operations were called
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("life_organizer.handlers.budget_entry.async_session_factory")
    async def test_savings_entry_without_merchant(
        self, mock_session_factory: MagicMock, handler: BudgetEntryHandler
    ) -> None:
        """Savings entries with no merchant should persist with None details."""
        # Mock database session
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session

        classified = _classified_input(
            {
                "amount": 1220.0,
                "currency": "EUR",
                "transaction_type": "Savings",
                "category": "Savings",
                "date": "2025-11-04",
            },
            raw_input="saved 1220 in ibkr",
        )

        result = await handler.execute(classified)

        # Handler always returns a list, even for single transaction
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].success is True
        assert result[0].action_type == ActionType.BACKEND_HANDLED
        assert result[0].message == "Logged savings: 1220.0 EUR in Savings"

        # Verify database operations were called
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_missing_required_fields_returns_failure(
        self, handler: BudgetEntryHandler
    ) -> None:
        """Missing required extracted fields should return failure response."""
        classified = _classified_input(
            {
                "amount": 50.0,
                "currency": "EUR",
                # transaction_type missing
                "category": "Groceries",
                "date": "2025-11-04",
            }
        )

        result = await handler.execute(classified)

        # Handler always returns a list, even for single transaction
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].success is False
        assert result[0].action_type == ActionType.BACKEND_HANDLED
        assert "Missing required fields: transaction_type" in result[0].message

    @pytest.mark.asyncio
    async def test_invalid_transaction_type_returns_failure(
        self, handler: BudgetEntryHandler
    ) -> None:
        """Unexpected transaction_type should return failure response."""
        classified = _classified_input(
            {
                "amount": 45.0,
                "currency": "EUR",
                "transaction_type": "Gift",
                "category": "Other",
                "date": "2025-11-04",
            }
        )

        result = await handler.execute(classified)

        # Handler always returns a list, even for single transaction
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].success is False
        assert result[0].action_type == ActionType.BACKEND_HANDLED
        assert "Invalid transaction_type" in result[0].message

    @pytest.mark.asyncio
    async def test_non_positive_amount_returns_failure(self, handler: BudgetEntryHandler) -> None:
        """Amounts that are zero or negative should be rejected."""
        classified = _classified_input(
            {
                "amount": 0,
                "currency": "EUR",
                "transaction_type": "Expenses",
                "category": "Groceries",
                "date": "2025-11-04",
            }
        )

        result = await handler.execute(classified)

        # Handler always returns a list, even for single transaction
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].success is False
        assert result[0].action_type == ActionType.BACKEND_HANDLED
        assert "Amount must be positive" in result[0].message

    @pytest.mark.asyncio
    async def test_invalid_expense_category_returns_failure(
        self, handler: BudgetEntryHandler
    ) -> None:
        """Invalid expense category should be rejected with clear error message."""
        classified = _classified_input(
            {
                "amount": 39.0,
                "currency": "EUR",
                "transaction_type": "Expenses",
                "category": "Bills",  # Invalid - not in ExpenseCategory enum
                "merchant": "water utilities",
                "date": "2025-11-13",
            }
        )

        result = await handler.execute(classified)

        # Handler always returns a list, even for single transaction
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].success is False
        assert result[0].action_type == ActionType.BACKEND_HANDLED
        assert "Invalid expense category: Bills" in result[0].message
        assert "Must be one of:" in result[0].message

    @pytest.mark.asyncio
    async def test_invalid_income_category_returns_failure(
        self, handler: BudgetEntryHandler
    ) -> None:
        """Invalid income category should be rejected with clear error message."""
        classified = _classified_input(
            {
                "amount": 250.0,
                "currency": "EUR",
                "transaction_type": "Income",
                "category": "Freelance",  # Invalid - not in IncomeCategory enum
                "merchant": "client",
                "date": "2025-11-13",
            }
        )

        result = await handler.execute(classified)

        # Handler always returns a list, even for single transaction
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].success is False
        assert result[0].action_type == ActionType.BACKEND_HANDLED
        assert "Invalid income category: Freelance" in result[0].message
        assert "Must be one of:" in result[0].message


class TestConvertToEUR:
    """Unit tests for currency conversion helper."""

    def test_eur_passthrough(self) -> None:
        """EUR amounts should remain unchanged."""
        assert _convert_to_eur(120.0, "EUR") == pytest.approx(120.0)

    def test_usd_to_eur(self) -> None:
        """100 USD should convert to 92.00 EUR."""
        assert _convert_to_eur(100.0, "USD") == pytest.approx(92.0)

    def test_unknown_currency_defaults_to_eur(self) -> None:
        """Unknown currencies are treated as EUR."""
        assert _convert_to_eur(42.0, "JPY") == pytest.approx(42.0)
