"""Tests for BudgetService budget entry persistence."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from life_organizer.schemas.classification import ClassifiedInput
from life_organizer.schemas.enums import ActionType, Category
from life_organizer.services.budget_service import BudgetService, _convert_to_eur


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


def _mock_session_factory() -> MagicMock:
    """Create a mock async session factory."""
    mock_session = AsyncMock()
    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)
    return mock_factory, mock_session


class TestBudgetServiceCreateEntries:
    """Tests for BudgetService.create_entries method."""

    @pytest.mark.asyncio
    async def test_single_expense_in_eur(self) -> None:
        """Single EUR expense should succeed and commit to DB."""
        mock_factory, mock_session = _mock_session_factory()
        service = BudgetService(session_factory=mock_factory)

        classified = _classified_input(
            {
                "amount": 120.0,
                "currency": "EUR",
                "transaction_type": "Expenses",
                "category": "Clothes",
                "merchant": "next",
                "date": "2026-03-09",
            }
        )

        results = await service.create_entries([classified])

        assert len(results) == 1
        assert results[0].success is True
        assert results[0].action_type == ActionType.BACKEND_HANDLED
        assert results[0].message == "Logged expenses: 120.0 EUR in Clothes"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_income_entry(self) -> None:
        """Income entry should produce correct message format."""
        mock_factory, _mock_session = _mock_session_factory()
        service = BudgetService(session_factory=mock_factory)

        classified = _classified_input(
            {
                "amount": 250.0,
                "currency": "EUR",
                "transaction_type": "Income",
                "category": "Rent",
                "merchant": "tenant",
                "date": "2026-03-09",
            }
        )

        results = await service.create_entries([classified])

        assert len(results) == 1
        assert results[0].success is True
        assert results[0].message == "Logged income: 250.0 EUR in Rent"

    @pytest.mark.asyncio
    async def test_savings_entry_without_merchant(self) -> None:
        """Savings entry without merchant should have details=None."""
        mock_factory, mock_session = _mock_session_factory()
        service = BudgetService(session_factory=mock_factory)

        classified = _classified_input(
            {
                "amount": 1220.0,
                "currency": "EUR",
                "transaction_type": "Savings",
                "category": "Savings",
                "date": "2026-03-09",
            }
        )

        results = await service.create_entries([classified])

        assert len(results) == 1
        assert results[0].success is True
        assert results[0].message == "Logged savings: 1220.0 EUR in Savings"

        # Verify the transaction was created with details=None
        call_args = mock_session.add.call_args[0][0]
        assert call_args.details is None

    @pytest.mark.asyncio
    async def test_missing_required_fields(self) -> None:
        """Missing required fields should return failure response."""
        mock_factory, _mock_session = _mock_session_factory()
        service = BudgetService(session_factory=mock_factory)

        classified = _classified_input(
            {
                "amount": 50.0,
                "currency": "EUR",
                "category": "Groceries",
                "date": "2026-03-09",
            }
        )

        results = await service.create_entries([classified])

        assert len(results) == 1
        assert results[0].success is False
        assert "Missing required fields: transaction_type" in results[0].message

    @pytest.mark.asyncio
    async def test_invalid_transaction_type(self) -> None:
        """Invalid transaction type should return failure response."""
        mock_factory, _mock_session = _mock_session_factory()
        service = BudgetService(session_factory=mock_factory)

        classified = _classified_input(
            {
                "amount": 45.0,
                "currency": "EUR",
                "transaction_type": "Gift",
                "category": "Other",
                "date": "2026-03-09",
            }
        )

        results = await service.create_entries([classified])

        assert len(results) == 1
        assert results[0].success is False
        assert "Invalid transaction_type" in results[0].message

    @pytest.mark.asyncio
    async def test_non_positive_amount(self) -> None:
        """Zero or negative amount should be rejected."""
        mock_factory, _mock_session = _mock_session_factory()
        service = BudgetService(session_factory=mock_factory)

        classified = _classified_input(
            {
                "amount": 0,
                "currency": "EUR",
                "transaction_type": "Expenses",
                "category": "Groceries",
                "date": "2026-03-09",
            }
        )

        results = await service.create_entries([classified])

        assert len(results) == 1
        assert results[0].success is False
        assert "Amount must be positive" in results[0].message

    @pytest.mark.asyncio
    async def test_invalid_expense_category(self) -> None:
        """Invalid expense category should return failure with enum list."""
        mock_factory, _mock_session = _mock_session_factory()
        service = BudgetService(session_factory=mock_factory)

        classified = _classified_input(
            {
                "amount": 39.0,
                "currency": "EUR",
                "transaction_type": "Expenses",
                "category": "Bills",
                "merchant": "water utilities",
                "date": "2026-03-09",
            }
        )

        results = await service.create_entries([classified])

        assert len(results) == 1
        assert results[0].success is False
        assert "Invalid expense category: Bills" in results[0].message
        assert "Must be one of:" in results[0].message

    @pytest.mark.asyncio
    async def test_invalid_income_category(self) -> None:
        """Invalid income category should return failure with enum list."""
        mock_factory, _mock_session = _mock_session_factory()
        service = BudgetService(session_factory=mock_factory)

        classified = _classified_input(
            {
                "amount": 250.0,
                "currency": "EUR",
                "transaction_type": "Income",
                "category": "Freelance",
                "merchant": "client",
                "date": "2026-03-09",
            }
        )

        results = await service.create_entries([classified])

        assert len(results) == 1
        assert results[0].success is False
        assert "Invalid income category: Freelance" in results[0].message

    @pytest.mark.asyncio
    async def test_invalid_savings_category(self) -> None:
        """Invalid savings category should return failure."""
        mock_factory, _mock_session = _mock_session_factory()
        service = BudgetService(session_factory=mock_factory)

        classified = _classified_input(
            {
                "amount": 100.0,
                "currency": "EUR",
                "transaction_type": "Savings",
                "category": "Emergency Fund",
                "date": "2026-03-09",
            }
        )

        results = await service.create_entries([classified])

        assert len(results) == 1
        assert results[0].success is False
        assert "Invalid savings category: Emergency Fund" in results[0].message

    @pytest.mark.asyncio
    async def test_multiple_transactions_mixed(self) -> None:
        """Multiple transactions with mix of valid and invalid should return partial results."""
        mock_factory, mock_session = _mock_session_factory()
        service = BudgetService(session_factory=mock_factory)

        valid = _classified_input(
            {
                "amount": 50.0,
                "currency": "EUR",
                "transaction_type": "Expenses",
                "category": "Groceries",
                "date": "2026-03-09",
            }
        )
        invalid = _classified_input(
            {
                "amount": 50.0,
                "currency": "EUR",
                "transaction_type": "Gift",
                "category": "Other",
                "date": "2026-03-09",
            }
        )

        results = await service.create_entries([valid, invalid])

        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is False
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_db_error_rolls_back_all(self) -> None:
        """Database error on commit should rollback and update all to failure."""
        mock_factory, mock_session = _mock_session_factory()
        mock_session.commit = AsyncMock(side_effect=Exception("DB connection lost"))
        service = BudgetService(session_factory=mock_factory)

        classified = _classified_input(
            {
                "amount": 50.0,
                "currency": "EUR",
                "transaction_type": "Expenses",
                "category": "Groceries",
                "date": "2026-03-09",
            }
        )

        results = await service.create_entries([classified])

        assert len(results) == 1
        assert results[0].success is False
        assert "Failed to save budget transaction" in results[0].message
        mock_session.rollback.assert_awaited_once()


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
