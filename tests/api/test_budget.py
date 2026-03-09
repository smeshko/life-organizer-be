"""Tests for POST /api/v1/budget endpoint."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from life_organizer.schemas.classification import ClassifiedInput
from life_organizer.schemas.enums import ActionType, Category
from life_organizer.schemas.responses import ProcessingResponse


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

        request = ClassifyRequest(input="coffee 4.50")
        result = await process_budget(request)

        assert len(result) == 1
        assert result[0].success is True
        mock_claude.parse_budget_text.assert_awaited_once_with("coffee 4.50")
        mock_budget.create_entries.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_422_empty_input(self) -> None:
        """Empty input should return 422."""
        from life_organizer.api.routes.budget import process_budget
        from life_organizer.schemas.requests import ClassifyRequest

        request = ClassifyRequest(input=" ")

        with pytest.raises(HTTPException) as exc_info:
            await process_budget(request)

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

        request = ClassifyRequest(input="coffee 5")

        with pytest.raises(HTTPException) as exc_info:
            await process_budget(request)

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

        request = ClassifyRequest(input="a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q")

        with pytest.raises(HTTPException) as exc_info:
            await process_budget(request)

        assert exc_info.value.status_code == 422
