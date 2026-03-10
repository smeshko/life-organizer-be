"""Tests for POST /api/v1/budget and POST /api/v1/budget/images endpoints."""

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
