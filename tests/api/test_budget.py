"""Tests for budget API endpoints."""

import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import anthropic
import pytest
from fastapi import HTTPException
from starlette.requests import Request

from life_organizer.schemas.classification import ClassifiedInput
from life_organizer.schemas.enums import ActionType, Category
from life_organizer.schemas.responses import ProcessingResponse


def _make_mock_request() -> Request:
    """Create a minimal Starlette Request for slowapi compatibility."""
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/budget/",
        "headers": [],
        "query_string": b"",
    }
    request = Request(scope)
    request._receive = MagicMock()
    return request


def _make_classified_input() -> ClassifiedInput:
    """Create a sample ClassifiedInput for testing."""
    return ClassifiedInput(
        category=Category.BUDGET,
        confidence=0.95,
        extracted_data={
            "amount": 4.50,
            "currency": "EUR",
            "transaction_type": "Expenses",
            "category": "Eat out",
            "merchant": "coffee shop",
            "date": "2026-03-09",
        },
        raw_input="coffee 4.50",
        classifier_source="llm",
    )


def _make_processing_response(success: bool = True) -> ProcessingResponse:
    """Create a sample ProcessingResponse for testing."""
    return ProcessingResponse(
        success=success,
        action_type=ActionType.BACKEND_HANDLED,
        message="Logged expenses: 4.5 EUR in Eat out" if success else "Processing failed",
    )


class TestProcessBudget:
    """Tests for POST /api/v1/budget endpoint."""

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.budget.budget_service")
    @patch("life_organizer.api.routes.budget.claude_service")
    async def test_200_valid_input(self, mock_claude: AsyncMock, mock_budget: AsyncMock) -> None:
        """Valid input should return 200 with processing results."""
        from life_organizer.api.routes.budget import process_budget
        from life_organizer.schemas.requests import ClassifyRequest

        mock_claude.parse_budget_text = AsyncMock(return_value=[_make_classified_input()])
        mock_budget.create_entries = AsyncMock(return_value=[_make_processing_response()])

        body = ClassifyRequest(input="coffee 4.50")
        result = await process_budget(_make_mock_request(), body)

        assert len(result) == 1
        assert result[0].success is True
        mock_claude.parse_budget_text.assert_awaited_once_with("coffee 4.50")
        mock_budget.create_entries.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_422_empty_input(self) -> None:
        """Empty input should return 422."""
        from life_organizer.api.routes.budget import process_budget
        from life_organizer.schemas.requests import ClassifyRequest

        body = ClassifyRequest(input=" ")

        with pytest.raises(HTTPException) as exc_info:
            await process_budget(_make_mock_request(), body)

        assert exc_info.value.status_code == 422
        assert "empty" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.budget.budget_service")
    @patch("life_organizer.api.routes.budget.claude_service")
    async def test_500_processing_error(
        self, mock_claude: AsyncMock, mock_budget: AsyncMock
    ) -> None:
        """Unexpected processing error should return 500."""
        from life_organizer.api.routes.budget import process_budget
        from life_organizer.schemas.requests import ClassifyRequest

        mock_claude.parse_budget_text = AsyncMock(side_effect=RuntimeError("Unexpected failure"))

        body = ClassifyRequest(input="coffee 5")

        with pytest.raises(HTTPException) as exc_info:
            await process_budget(_make_mock_request(), body)

        assert exc_info.value.status_code == 500
        assert "Processing error" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.budget.budget_service")
    @patch("life_organizer.api.routes.budget.claude_service")
    async def test_422_transaction_limit(
        self, mock_claude: AsyncMock, mock_budget: AsyncMock
    ) -> None:
        """HTTPException 422 from claude_service should propagate."""
        from life_organizer.api.routes.budget import process_budget
        from life_organizer.schemas.requests import ClassifyRequest

        mock_claude.parse_budget_text = AsyncMock(
            side_effect=HTTPException(status_code=422, detail="Too many transactions")
        )

        body = ClassifyRequest(input="a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q")

        with pytest.raises(HTTPException) as exc_info:
            await process_budget(_make_mock_request(), body)

        assert exc_info.value.status_code == 422


def _make_mock_upload_file(
    content_type: str = "image/png", content: bytes = b"fake-image-bytes"
) -> MagicMock:
    """Create a mock UploadFile for testing."""
    mock_file = MagicMock()
    mock_file.content_type = content_type
    mock_file.read = AsyncMock(return_value=content)
    return mock_file


class TestProcessBudgetImages:
    """Tests for POST /api/v1/budget/images endpoint."""

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.budget.budget_service")
    @patch("life_organizer.api.routes.budget.claude_service")
    async def test_200_single_image(self, mock_claude: AsyncMock, mock_budget: AsyncMock) -> None:
        """Valid single image upload should return 200 with processing results."""
        from life_organizer.api.routes.budget import process_budget_images

        mock_claude.parse_budget_images = AsyncMock(return_value=[_make_classified_input()])
        mock_budget.create_entries = AsyncMock(return_value=[_make_processing_response()])

        result = await process_budget_images(
            _make_mock_request(),
            files=[_make_mock_upload_file()],
        )

        assert len(result) == 1
        assert result[0].success is True
        mock_claude.parse_budget_images.assert_awaited_once()
        mock_budget.create_entries.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.budget.budget_service")
    @patch("life_organizer.api.routes.budget.claude_service")
    async def test_200_multiple_images(
        self, mock_claude: AsyncMock, mock_budget: AsyncMock
    ) -> None:
        """Multiple image upload should return 200 with combined results."""
        from life_organizer.api.routes.budget import process_budget_images

        classified_inputs = [_make_classified_input(), _make_classified_input()]
        responses = [_make_processing_response(), _make_processing_response()]

        mock_claude.parse_budget_images = AsyncMock(return_value=classified_inputs)
        mock_budget.create_entries = AsyncMock(return_value=responses)

        result = await process_budget_images(
            _make_mock_request(),
            files=[_make_mock_upload_file(), _make_mock_upload_file(), _make_mock_upload_file()],
        )

        assert len(result) == 2
        # Verify all 3 images were read
        args = mock_claude.parse_budget_images.call_args
        assert len(args[0][0]) == 3  # 3 image byte lists passed

    @pytest.mark.asyncio
    async def test_400_non_image_file(self) -> None:
        """Non-image file should return 400."""
        from life_organizer.api.routes.budget import process_budget_images

        mock_file = _make_mock_upload_file(content_type="text/plain")

        with pytest.raises(HTTPException) as exc_info:
            await process_budget_images(
                _make_mock_request(),
                files=[mock_file],
            )

        assert exc_info.value.status_code == 400
        assert "Invalid file type" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.budget.budget_service")
    @patch("life_organizer.api.routes.budget.claude_service")
    async def test_422_no_transactions_found(
        self, mock_claude: AsyncMock, mock_budget: AsyncMock
    ) -> None:
        """Image with no transactions should return 422."""
        from life_organizer.api.routes.budget import process_budget_images

        mock_claude.parse_budget_images = AsyncMock(return_value=[])

        with pytest.raises(HTTPException) as exc_info:
            await process_budget_images(
                _make_mock_request(),
                files=[_make_mock_upload_file()],
            )

        assert exc_info.value.status_code == 422
        assert "No transactions found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.budget.budget_service")
    @patch("life_organizer.api.routes.budget.claude_service")
    async def test_500_claude_api_error(
        self, mock_claude: AsyncMock, mock_budget: AsyncMock
    ) -> None:
        """Claude API error should return 500."""
        from life_organizer.api.routes.budget import process_budget_images

        mock_claude.parse_budget_images = AsyncMock(
            side_effect=anthropic.APIError(
                message="Service unavailable",
                request=MagicMock(),
                body=None,
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await process_budget_images(
                _make_mock_request(),
                files=[_make_mock_upload_file()],
            )

        assert exc_info.value.status_code == 500
        assert "Processing error" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.budget.budget_service")
    @patch("life_organizer.api.routes.budget.claude_service")
    async def test_text_endpoint_still_works(
        self, mock_claude: AsyncMock, mock_budget: AsyncMock
    ) -> None:
        """Regression test: text endpoint should still work after adding image endpoint."""
        from life_organizer.api.routes.budget import process_budget
        from life_organizer.schemas.requests import ClassifyRequest

        mock_claude.parse_budget_text = AsyncMock(return_value=[_make_classified_input()])
        mock_budget.create_entries = AsyncMock(return_value=[_make_processing_response()])

        body = ClassifyRequest(input="coffee 4.50")
        result = await process_budget(_make_mock_request(), body)

        assert len(result) == 1
        assert result[0].success is True
        mock_claude.parse_budget_text.assert_awaited_once_with("coffee 4.50")


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
    """Create a mock BudgetTransaction for route tests."""
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


class TestGetTransactions:
    """Tests for GET /api/v1/budget/transactions endpoint."""

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.budget.budget_service")
    async def test_200_no_filters(self, mock_budget: AsyncMock) -> None:
        """Default call with no filters returns paginated response."""
        from life_organizer.api.routes.budget import get_transactions

        mock_budget.query_transactions = AsyncMock(
            return_value={
                "items": [_make_mock_transaction()],
                "total": 1,
                "page": 1,
                "page_size": 50,
            }
        )

        result = await get_transactions()

        assert result.total == 1
        assert result.page == 1
        assert result.page_size == 50
        assert len(result.items) == 1
        assert result.items[0].category == "Groceries"

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.budget.budget_service")
    async def test_200_with_date_range(self, mock_budget: AsyncMock) -> None:
        """Date filtering works correctly."""
        from life_organizer.api.routes.budget import get_transactions

        mock_budget.query_transactions = AsyncMock(
            return_value={
                "items": [_make_mock_transaction()],
                "total": 1,
                "page": 1,
                "page_size": 50,
            }
        )

        result = await get_transactions(
            start_date=datetime.date(2026, 1, 1),
            end_date=datetime.date(2026, 1, 31),
        )

        assert result.total == 1
        call_kwargs = mock_budget.query_transactions.call_args[1]
        assert call_kwargs["start_date"] == datetime.date(2026, 1, 1)
        assert call_kwargs["end_date"] == datetime.date(2026, 1, 31)

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.budget.budget_service")
    async def test_200_with_transaction_type(self, mock_budget: AsyncMock) -> None:
        """Transaction type filtering works correctly."""
        from life_organizer.api.routes.budget import get_transactions

        mock_budget.query_transactions = AsyncMock(
            return_value={
                "items": [_make_mock_transaction()],
                "total": 1,
                "page": 1,
                "page_size": 50,
            }
        )

        result = await get_transactions(transaction_type="Expenses")

        assert result.total == 1
        call_kwargs = mock_budget.query_transactions.call_args[1]
        assert call_kwargs["transaction_type"] == "Expenses"

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.budget.budget_service")
    async def test_200_with_category(self, mock_budget: AsyncMock) -> None:
        """Category filtering works correctly."""
        from life_organizer.api.routes.budget import get_transactions

        mock_budget.query_transactions = AsyncMock(
            return_value={
                "items": [_make_mock_transaction(category="Groceries")],
                "total": 1,
                "page": 1,
                "page_size": 50,
            }
        )

        result = await get_transactions(category="Groceries")

        assert result.total == 1
        assert result.items[0].category == "Groceries"

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.budget.budget_service")
    async def test_200_combined_filters(self, mock_budget: AsyncMock) -> None:
        """All filters combined work correctly."""
        from life_organizer.api.routes.budget import get_transactions

        mock_budget.query_transactions = AsyncMock(
            return_value={
                "items": [_make_mock_transaction()],
                "total": 1,
                "page": 1,
                "page_size": 50,
            }
        )

        result = await get_transactions(
            start_date=datetime.date(2026, 1, 1),
            end_date=datetime.date(2026, 1, 31),
            transaction_type="Expenses",
            category="Groceries",
        )

        assert result.total == 1
        call_kwargs = mock_budget.query_transactions.call_args[1]
        assert call_kwargs["start_date"] == datetime.date(2026, 1, 1)
        assert call_kwargs["end_date"] == datetime.date(2026, 1, 31)
        assert call_kwargs["transaction_type"] == "Expenses"
        assert call_kwargs["category"] == "Groceries"

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.budget.budget_service")
    async def test_200_pagination(self, mock_budget: AsyncMock) -> None:
        """Page 2 returns correct offset."""
        from life_organizer.api.routes.budget import get_transactions

        mock_budget.query_transactions = AsyncMock(
            return_value={
                "items": [_make_mock_transaction(id=i) for i in range(50, 100)],
                "total": 120,
                "page": 2,
                "page_size": 50,
            }
        )

        result = await get_transactions(page=2, page_size=50)

        assert result.total == 120
        assert result.page == 2
        assert len(result.items) == 50

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.budget.budget_service")
    async def test_200_empty_page(self, mock_budget: AsyncMock) -> None:
        """Page beyond data returns empty items."""
        from life_organizer.api.routes.budget import get_transactions

        mock_budget.query_transactions = AsyncMock(
            return_value={
                "items": [],
                "total": 5,
                "page": 999,
                "page_size": 50,
            }
        )

        result = await get_transactions(page=999)

        assert result.total == 5
        assert result.items == []
        assert result.page == 999

    @pytest.mark.asyncio
    async def test_422_invalid_page(self) -> None:
        """page param has ge=1 constraint for FastAPI validation."""
        import inspect

        from life_organizer.api.routes.budget import get_transactions

        sig = inspect.signature(get_transactions)
        page_param = sig.parameters["page"]
        query_info = page_param.default
        assert query_info.metadata[0].ge == 1  # type: ignore[union-attr]

    @pytest.mark.asyncio
    async def test_422_invalid_page_size(self) -> None:
        """page_size param has ge=1, le=200 constraints for FastAPI validation."""
        import inspect

        from life_organizer.api.routes.budget import get_transactions

        sig = inspect.signature(get_transactions)
        page_size_param = sig.parameters["page_size"]
        query_info = page_size_param.default
        metadata_values = {type(m).__name__: m for m in query_info.metadata}  # type: ignore[union-attr]
        assert metadata_values["Ge"].ge == 1  # type: ignore[union-attr]
        assert metadata_values["Le"].le == 200  # type: ignore[union-attr]

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.budget.budget_service")
    async def test_amount_eur_none_handled(self, mock_budget: AsyncMock) -> None:
        """Transactions with amount_eur=None (legacy) are handled correctly."""
        from life_organizer.api.routes.budget import get_transactions

        mock_budget.query_transactions = AsyncMock(
            return_value={
                "items": [_make_mock_transaction(amount_eur=None)],
                "total": 1,
                "page": 1,
                "page_size": 50,
            }
        )

        result = await get_transactions()

        assert result.items[0].amount_eur is None


class TestGetTransactionAggregations:
    """Tests for GET /api/v1/budget/transactions/aggregate endpoint."""

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.budget.budget_service")
    async def test_200_year_only(self, mock_budget: AsyncMock) -> None:
        """Year-only returns full year aggregations."""
        from life_organizer.api.routes.budget import get_transaction_aggregations

        mock_budget.aggregate_transactions = AsyncMock(
            return_value={
                "period": {"year": 2025, "month": None},
                "aggregations": [
                    {"category": "Groceries", "total_eur": 450.0, "count": 23},
                ],
            }
        )

        result = await get_transaction_aggregations(year=2025, month=None, transaction_type=None)

        assert result.period.year == 2025
        assert result.period.month is None
        assert len(result.aggregations) == 1
        assert result.aggregations[0].category == "Groceries"
        assert result.aggregations[0].total_eur == 450.0
        assert result.aggregations[0].count == 23

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.budget.budget_service")
    async def test_200_year_and_month(self, mock_budget: AsyncMock) -> None:
        """Year + month returns monthly aggregations."""
        from life_organizer.api.routes.budget import get_transaction_aggregations

        mock_budget.aggregate_transactions = AsyncMock(
            return_value={
                "period": {"year": 2026, "month": 1},
                "aggregations": [
                    {"category": "Groceries", "total_eur": 150.0, "count": 8},
                ],
            }
        )

        result = await get_transaction_aggregations(year=2026, month=1)

        assert result.period.year == 2026
        assert result.period.month == 1

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.budget.budget_service")
    async def test_200_with_transaction_type(self, mock_budget: AsyncMock) -> None:
        """Transaction type filter works."""
        from life_organizer.api.routes.budget import get_transaction_aggregations

        mock_budget.aggregate_transactions = AsyncMock(
            return_value={
                "period": {"year": 2026, "month": None},
                "aggregations": [
                    {"category": "Salary Ivo", "total_eur": 3000.0, "count": 1},
                ],
            }
        )

        result = await get_transaction_aggregations(
            year=2026, month=None, transaction_type="Income"
        )

        assert len(result.aggregations) == 1
        call_kwargs = mock_budget.aggregate_transactions.call_args[1]
        assert call_kwargs["year"] == 2026
        assert call_kwargs["transaction_type"] == "Income"

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.budget.budget_service")
    async def test_200_empty_aggregations(self, mock_budget: AsyncMock) -> None:
        """No matching transactions returns empty aggregations array."""
        from life_organizer.api.routes.budget import get_transaction_aggregations

        mock_budget.aggregate_transactions = AsyncMock(
            return_value={
                "period": {"year": 2020, "month": None},
                "aggregations": [],
            }
        )

        result = await get_transaction_aggregations(year=2020, month=None, transaction_type=None)

        assert result.aggregations == []

    @pytest.mark.asyncio
    async def test_422_year_required(self) -> None:
        """year param is required (no default value)."""
        import inspect

        from life_organizer.api.routes.budget import get_transaction_aggregations

        sig = inspect.signature(get_transaction_aggregations)
        year_param = sig.parameters["year"]
        # Required params have Query(...) with no default — the default is the Query itself
        query_info = year_param.default
        # Verify ge and le constraints exist
        metadata_values = {type(m).__name__: m for m in query_info.metadata}
        assert metadata_values["Ge"].ge == 2000
        assert metadata_values["Le"].le == 2100

    @pytest.mark.asyncio
    async def test_422_month_constraints(self) -> None:
        """month param has ge=1, le=12 constraints."""
        import inspect

        from life_organizer.api.routes.budget import get_transaction_aggregations

        sig = inspect.signature(get_transaction_aggregations)
        month_param = sig.parameters["month"]
        query_info = month_param.default
        metadata_values = {type(m).__name__: m for m in query_info.metadata}
        assert metadata_values["Ge"].ge == 1
        assert metadata_values["Le"].le == 12


class TestGetAvailableYears:
    """Tests for GET /api/v1/budget/years endpoint."""

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.budget.budget_service")
    async def test_200_returns_years(self, mock_budget: AsyncMock) -> None:
        """Returns sorted year list."""
        from life_organizer.api.routes.budget import get_available_years

        mock_budget.get_available_years = AsyncMock(return_value=[2024, 2025, 2026])

        result = await get_available_years()

        assert result.years == [2024, 2025, 2026]

    @pytest.mark.asyncio
    @patch("life_organizer.api.routes.budget.budget_service")
    async def test_200_empty(self, mock_budget: AsyncMock) -> None:
        """No transactions returns empty list."""
        from life_organizer.api.routes.budget import get_available_years

        mock_budget.get_available_years = AsyncMock(return_value=[])

        result = await get_available_years()

        assert result.years == []
