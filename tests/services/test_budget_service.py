"""Tests for BudgetService budget entry persistence."""

import datetime
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


def _mock_session_factory() -> tuple[MagicMock, AsyncMock]:
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


def _make_mock_transaction(
    id: int = 1,
    amount: float = 50.0,
    currency: str = "EUR",
    amount_eur: float | None = 50.0,
    date: datetime.date = datetime.date(2026, 1, 15),
    transaction_type: str = "Expenses",
    category: str = "Groceries",
    details: str | None = "Kaufland",
) -> MagicMock:
    """Create a mock BudgetTransaction object."""
    mock = MagicMock()
    mock.id = id
    mock.amount = amount
    mock.currency = currency
    mock.amount_eur = amount_eur
    mock.date = date
    mock.transaction_type = transaction_type
    mock.category = category
    mock.details = details
    return mock


def _mock_execute_results(
    *results: tuple[str, object],
) -> AsyncMock:
    """Create a mock session.execute that returns different result types.

    Each result is a tuple of (type, value) where type is 'scalar' or 'scalars'.
    - ('scalar', 5) -> result.scalar() returns 5
    - ('scalars', [item1, item2]) -> result.scalars().all() returns [item1, item2]
    """
    mocks = []
    for result_type, value in results:
        result_mock = MagicMock()
        if result_type == "scalar":
            result_mock.scalar.return_value = value
        elif result_type == "scalars":
            scalars_mock = MagicMock()
            scalars_mock.all.return_value = value
            result_mock.scalars.return_value = scalars_mock
        mocks.append(result_mock)

    return AsyncMock(side_effect=mocks)


class TestQueryTransactions:
    """Tests for BudgetService.query_transactions method."""

    @pytest.mark.asyncio
    async def test_no_filters_returns_first_page(self) -> None:
        """Default call with no filters returns first page."""
        mock_factory, mock_session = _mock_session_factory()
        service = BudgetService(session_factory=mock_factory)

        transactions = [_make_mock_transaction(id=i) for i in range(3)]
        mock_session.execute = _mock_execute_results(
            ("scalar", 3),
            ("scalars", transactions),
        )

        result = await service.query_transactions(
            start_date=None,
            end_date=None,
            transaction_type=None,
            category=None,
            page=1,
            page_size=50,
        )

        assert result["total"] == 3
        assert result["page"] == 1
        assert result["page_size"] == 50
        assert len(result["items"]) == 3

    @pytest.mark.asyncio
    async def test_date_range_filter(self) -> None:
        """Date range filter passes conditions to query."""
        mock_factory, mock_session = _mock_session_factory()
        service = BudgetService(session_factory=mock_factory)

        mock_session.execute = _mock_execute_results(
            ("scalar", 1),
            ("scalars", [_make_mock_transaction()]),
        )

        result = await service.query_transactions(
            start_date=datetime.date(2026, 1, 1),
            end_date=datetime.date(2026, 1, 31),
            transaction_type=None,
            category=None,
            page=1,
            page_size=50,
        )

        assert result["total"] == 1
        assert len(result["items"]) == 1
        assert mock_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_transaction_type_filter(self) -> None:
        """Transaction type filter works correctly."""
        mock_factory, mock_session = _mock_session_factory()
        service = BudgetService(session_factory=mock_factory)

        mock_session.execute = _mock_execute_results(
            ("scalar", 2),
            ("scalars", [_make_mock_transaction(id=1), _make_mock_transaction(id=2)]),
        )

        result = await service.query_transactions(
            start_date=None,
            end_date=None,
            transaction_type="Expenses",
            category=None,
            page=1,
            page_size=50,
        )

        assert result["total"] == 2
        assert len(result["items"]) == 2

    @pytest.mark.asyncio
    async def test_category_filter(self) -> None:
        """Category filter works correctly."""
        mock_factory, mock_session = _mock_session_factory()
        service = BudgetService(session_factory=mock_factory)

        mock_session.execute = _mock_execute_results(
            ("scalar", 1),
            ("scalars", [_make_mock_transaction(category="Groceries")]),
        )

        result = await service.query_transactions(
            start_date=None,
            end_date=None,
            transaction_type=None,
            category="Groceries",
            page=1,
            page_size=50,
        )

        assert result["total"] == 1
        assert len(result["items"]) == 1

    @pytest.mark.asyncio
    async def test_combined_filters(self) -> None:
        """All filters combined (AND'd together)."""
        mock_factory, mock_session = _mock_session_factory()
        service = BudgetService(session_factory=mock_factory)

        mock_session.execute = _mock_execute_results(
            ("scalar", 1),
            ("scalars", [_make_mock_transaction()]),
        )

        result = await service.query_transactions(
            start_date=datetime.date(2026, 1, 1),
            end_date=datetime.date(2026, 1, 31),
            transaction_type="Expenses",
            category="Groceries",
            page=1,
            page_size=50,
        )

        assert result["total"] == 1
        assert len(result["items"]) == 1

    @pytest.mark.asyncio
    async def test_pagination_offset(self) -> None:
        """Page 2 returns correct offset."""
        mock_factory, mock_session = _mock_session_factory()
        service = BudgetService(session_factory=mock_factory)

        mock_session.execute = _mock_execute_results(
            ("scalar", 120),
            ("scalars", [_make_mock_transaction(id=i) for i in range(50, 100)]),
        )

        result = await service.query_transactions(
            start_date=None,
            end_date=None,
            transaction_type=None,
            category=None,
            page=2,
            page_size=50,
        )

        assert result["total"] == 120
        assert result["page"] == 2
        assert len(result["items"]) == 50

    @pytest.mark.asyncio
    async def test_empty_result_page(self) -> None:
        """Page beyond data returns empty items with correct total."""
        mock_factory, mock_session = _mock_session_factory()
        service = BudgetService(session_factory=mock_factory)

        mock_session.execute = _mock_execute_results(
            ("scalar", 5),
            ("scalars", []),
        )

        result = await service.query_transactions(
            start_date=None,
            end_date=None,
            transaction_type=None,
            category=None,
            page=999,
            page_size=50,
        )

        assert result["total"] == 5
        assert result["items"] == []
        assert result["page"] == 999


class TestAggregateTransactions:
    """Tests for BudgetService.aggregate_transactions method."""

    @pytest.mark.asyncio
    async def test_year_only_aggregation(self) -> None:
        """Year-only aggregation returns full year results."""
        mock_factory, mock_session = _mock_session_factory()
        service = BudgetService(session_factory=mock_factory)

        result_mock = MagicMock()
        result_mock.all.return_value = [
            ("Groceries", 450.0, 23),
            ("Eat out", 200.0, 15),
        ]
        mock_session.execute = AsyncMock(return_value=result_mock)

        result = await service.aggregate_transactions(year=2025, month=None, transaction_type=None)

        assert result["period"]["year"] == 2025
        assert result["period"]["month"] is None
        assert len(result["aggregations"]) == 2
        assert result["aggregations"][0]["category"] == "Groceries"
        assert result["aggregations"][0]["total_eur"] == 450.0
        assert result["aggregations"][0]["count"] == 23

    @pytest.mark.asyncio
    async def test_year_and_month_aggregation(self) -> None:
        """Year + month aggregation returns monthly results."""
        mock_factory, mock_session = _mock_session_factory()
        service = BudgetService(session_factory=mock_factory)

        result_mock = MagicMock()
        result_mock.all.return_value = [
            ("Groceries", 150.0, 8),
        ]
        mock_session.execute = AsyncMock(return_value=result_mock)

        result = await service.aggregate_transactions(year=2026, month=1, transaction_type=None)

        assert result["period"]["year"] == 2026
        assert result["period"]["month"] == 1
        assert len(result["aggregations"]) == 1

    @pytest.mark.asyncio
    async def test_transaction_type_filter(self) -> None:
        """Transaction type filter returns only matching type."""
        mock_factory, mock_session = _mock_session_factory()
        service = BudgetService(session_factory=mock_factory)

        result_mock = MagicMock()
        result_mock.all.return_value = [
            ("Salary Ivo", 3000.0, 1),
        ]
        mock_session.execute = AsyncMock(return_value=result_mock)

        result = await service.aggregate_transactions(year=2026, month=1, transaction_type="Income")

        assert len(result["aggregations"]) == 1
        assert result["aggregations"][0]["category"] == "Salary Ivo"

    @pytest.mark.asyncio
    async def test_no_matching_transactions(self) -> None:
        """No matching transactions returns empty aggregations list."""
        mock_factory, mock_session = _mock_session_factory()
        service = BudgetService(session_factory=mock_factory)

        result_mock = MagicMock()
        result_mock.all.return_value = []
        mock_session.execute = AsyncMock(return_value=result_mock)

        result = await service.aggregate_transactions(year=2020, month=None, transaction_type=None)

        assert result["aggregations"] == []

    @pytest.mark.asyncio
    async def test_sorted_by_total_descending(self) -> None:
        """Multiple categories sorted by total_eur descending."""
        mock_factory, mock_session = _mock_session_factory()
        service = BudgetService(session_factory=mock_factory)

        result_mock = MagicMock()
        result_mock.all.return_value = [
            ("Groceries", 500.0, 20),
            ("Eat out", 300.0, 10),
            ("Transport", 100.0, 5),
        ]
        mock_session.execute = AsyncMock(return_value=result_mock)

        result = await service.aggregate_transactions(
            year=2026, month=None, transaction_type="Expenses"
        )

        assert len(result["aggregations"]) == 3
        totals = [a["total_eur"] for a in result["aggregations"]]
        assert totals == [500.0, 300.0, 100.0]

    @pytest.mark.asyncio
    async def test_legacy_records_use_amount_bgn_fallback(self) -> None:
        """Legacy records (amount_eur=None) use amount_bgn fallback via coalesce."""
        mock_factory, mock_session = _mock_session_factory()
        service = BudgetService(session_factory=mock_factory)

        # The coalesce happens in SQL, so the result already reflects the fallback
        result_mock = MagicMock()
        result_mock.all.return_value = [
            ("Groceries", 250.0, 5),
        ]
        mock_session.execute = AsyncMock(return_value=result_mock)

        result = await service.aggregate_transactions(year=2024, month=None, transaction_type=None)

        assert len(result["aggregations"]) == 1
        assert result["aggregations"][0]["total_eur"] == 250.0
        # Verify execute was called (the coalesce is in the SQL query)
        mock_session.execute.assert_awaited_once()


class TestGetAvailableYears:
    """Tests for BudgetService.get_available_years method."""

    @pytest.mark.asyncio
    async def test_returns_sorted_years(self) -> None:
        """Returns distinct years sorted ascending."""
        mock_factory, mock_session = _mock_session_factory()
        service = BudgetService(session_factory=mock_factory)

        scalars_mock = MagicMock()
        scalars_mock.all.return_value = [2024.0, 2025.0, 2026.0]
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        mock_session.execute = AsyncMock(return_value=result_mock)

        years = await service.get_available_years()

        assert years == [2024, 2025, 2026]
        assert all(isinstance(y, int) for y in years)

    @pytest.mark.asyncio
    async def test_no_transactions_returns_empty(self) -> None:
        """No transactions returns empty list."""
        mock_factory, mock_session = _mock_session_factory()
        service = BudgetService(session_factory=mock_factory)

        scalars_mock = MagicMock()
        scalars_mock.all.return_value = []
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        mock_session.execute = AsyncMock(return_value=result_mock)

        years = await service.get_available_years()

        assert years == []


def _make_mock_plan(
    id: int = 1,
    year: int = 2026,
    month: int = 1,
    transaction_type: str = "Expenses",
    category: str = "Groceries",
    planned_amount: float = 400.0,
) -> MagicMock:
    """Create a mock BudgetPlan object."""
    mock = MagicMock()
    mock.id = id
    mock.year = year
    mock.month = month
    mock.transaction_type = transaction_type
    mock.category = category
    mock.planned_amount = planned_amount
    return mock


class TestGetPlan:
    """Tests for BudgetService.get_plan method."""

    @pytest.mark.asyncio
    async def test_no_entries_returns_empty_list(self) -> None:
        """Year with no plans returns empty list."""
        mock_factory, mock_session = _mock_session_factory()
        service = BudgetService(session_factory=mock_factory)

        scalars_mock = MagicMock()
        scalars_mock.all.return_value = []
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        mock_session.execute = AsyncMock(return_value=result_mock)

        result = await service.get_plan(2026)

        assert result == []
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_all_entries_for_year(self) -> None:
        """Returns all BudgetPlan rows for the year."""
        mock_factory, mock_session = _mock_session_factory()
        service = BudgetService(session_factory=mock_factory)

        plans = [
            _make_mock_plan(id=1, month=1, category="Groceries"),
            _make_mock_plan(id=2, month=2, category="Groceries"),
            _make_mock_plan(id=3, month=1, category="Eat out"),
        ]
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = plans
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        mock_session.execute = AsyncMock(return_value=result_mock)

        result = await service.get_plan(2026)

        assert len(result) == 3
        assert result[0].category == "Groceries"

    @pytest.mark.asyncio
    async def test_ordered_by_type_category_month(self) -> None:
        """Verify query is executed (ordering is in SQL)."""
        mock_factory, mock_session = _mock_session_factory()
        service = BudgetService(session_factory=mock_factory)

        plans = [
            _make_mock_plan(id=1, transaction_type="Expenses", category="Eat out", month=1),
            _make_mock_plan(id=2, transaction_type="Expenses", category="Groceries", month=1),
            _make_mock_plan(id=3, transaction_type="Income", category="Salary Ivo", month=1),
        ]
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = plans
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        mock_session.execute = AsyncMock(return_value=result_mock)

        result = await service.get_plan(2026)

        assert len(result) == 3
        mock_session.execute.assert_awaited_once()


class TestUpsertPlan:
    """Tests for BudgetService.upsert_plan method."""

    @pytest.mark.asyncio
    async def test_insert_new_entries(self) -> None:
        """New entries are inserted, returns correct count."""
        mock_factory, mock_session = _mock_session_factory()
        service = BudgetService(session_factory=mock_factory)

        mock_session.execute = AsyncMock()

        entries: list[dict[str, object]] = [
            {
                "transaction_type": "Expenses",
                "category": "Groceries",
                "month": 1,
                "planned_amount": 400.0,
            },
            {
                "transaction_type": "Expenses",
                "category": "Groceries",
                "month": 2,
                "planned_amount": 450.0,
            },
        ]

        count = await service.upsert_plan(2026, entries)

        assert count == 2
        mock_session.execute.assert_awaited_once()
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_existing_entries(self) -> None:
        """Upsert returns correct count when updating existing entries."""
        mock_factory, mock_session = _mock_session_factory()
        service = BudgetService(session_factory=mock_factory)

        mock_session.execute = AsyncMock()

        entries: list[dict[str, object]] = [
            {
                "transaction_type": "Expenses",
                "category": "Groceries",
                "month": 1,
                "planned_amount": 500.0,
            },
        ]

        count = await service.upsert_plan(2026, entries)

        assert count == 1
        mock_session.execute.assert_awaited_once()
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_atomic_commit(self) -> None:
        """All entries committed together in single execute."""
        mock_factory, mock_session = _mock_session_factory()
        service = BudgetService(session_factory=mock_factory)

        mock_session.execute = AsyncMock()

        entries: list[dict[str, object]] = [
            {
                "transaction_type": "Expenses",
                "category": "Groceries",
                "month": m,
                "planned_amount": 400.0,
            }
            for m in range(1, 13)
        ]

        count = await service.upsert_plan(2026, entries)

        assert count == 12
        # Single execute call for all 12 entries (bulk upsert)
        mock_session.execute.assert_awaited_once()
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_db_error_rolls_back(self) -> None:
        """Database error triggers rollback."""
        mock_factory, mock_session = _mock_session_factory()
        mock_session.execute = AsyncMock(side_effect=Exception("DB connection lost"))
        service = BudgetService(session_factory=mock_factory)

        entries: list[dict[str, object]] = [
            {
                "transaction_type": "Expenses",
                "category": "Groceries",
                "month": 1,
                "planned_amount": 400.0,
            },
        ]

        with pytest.raises(Exception, match="DB connection lost"):
            await service.upsert_plan(2026, entries)

        mock_session.rollback.assert_awaited_once()
