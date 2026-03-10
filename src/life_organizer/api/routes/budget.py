"""Budget API endpoints for logging and exporting budget transactions."""

import datetime
import logging
import math

from fastapi import APIRouter, HTTPException, Query, Request, Response, UploadFile
from sqlalchemy import select

from life_organizer.config import get_settings
from life_organizer.db.models.budget import BudgetTransaction
from life_organizer.db.session import async_session_factory
from life_organizer.rate_limit import limiter
from life_organizer.schemas.budget import (
    AggregationPeriod,
    AggregationResponse,
    AvailableYearsResponse,
    CategoryAggregation,
    PaginatedTransactionsResponse,
    TransactionItem,
)
from life_organizer.schemas.requests import ClassifyRequest
from life_organizer.schemas.responses import ProcessingResponse
from life_organizer.services.budget_service import BudgetService
from life_organizer.services.claude_service import ClaudeService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
settings = get_settings()
claude_service = ClaudeService(api_key=settings.claude_api_key)
budget_service = BudgetService(session_factory=async_session_factory)


@router.post(
    "/",
    response_model=list[ProcessingResponse],
    response_description="List of transaction processing results (always an array, even for single transaction)",
    responses={
        200: {
            "description": "Successfully processed transaction(s)",
            "content": {
                "application/json": {
                    "examples": {
                        "single_transaction": {
                            "summary": "Single Transaction",
                            "value": [
                                {
                                    "success": True,
                                    "action_type": "backend_handled",
                                    "message": "Logged expenses: 4.5 EUR in Eat out",
                                }
                            ],
                        },
                        "multi_transaction": {
                            "summary": "Multiple Transactions",
                            "value": [
                                {
                                    "success": True,
                                    "action_type": "backend_handled",
                                    "message": "Logged expenses: 12.0 EUR in Eat out",
                                },
                                {
                                    "success": True,
                                    "action_type": "backend_handled",
                                    "message": "Logged expenses: 4.5 EUR in Eat out",
                                },
                            ],
                        },
                        "partial_failure": {
                            "summary": "Partial Success",
                            "value": [
                                {
                                    "success": True,
                                    "action_type": "backend_handled",
                                    "message": "Logged expenses: 50.0 EUR in Groceries",
                                },
                                {
                                    "success": False,
                                    "action_type": "backend_handled",
                                    "message": "Could not process budget entry: Missing required fields: amount",
                                },
                            ],
                        },
                    }
                }
            },
        },
        422: {
            "description": "Validation error (empty input, too many transactions)",
        },
        500: {"description": "Server error during processing"},
    },
)
@limiter.limit("10/minute")
async def process_budget(
    request: Request,  # noqa: ARG001 - required by slowapi rate limiter
    body: ClassifyRequest,
) -> list[ProcessingResponse]:
    """Process natural language budget input and persist transactions.

    Parses natural language input into structured budget transactions using Claude LLM,
    then validates and persists them to the database.

    Supports multi-transaction parsing from a single input.
    For example: "lunch 12 eur, coffee 4.50"

    **Important:** The response is ALWAYS an array, even for single transactions.

    Args:
        request: Starlette Request object (required by slowapi rate limiter)
        body: ClassifyRequest with text input (category field is ignored)

    Returns:
        List of ProcessingResponse objects (one per detected transaction)

    Raises:
        HTTPException 422: Input validation failed or transaction limit exceeded
        HTTPException 429: Rate limit exceeded
        HTTPException 500: Server error during processing
    """
    try:
        # Input validation
        if not body.input.strip():
            raise HTTPException(
                status_code=422,
                detail="Input cannot be empty or whitespace only",
            )

        # Parse budget text using Claude
        classified_list = await claude_service.parse_budget_text(body.input)

        # Persist entries
        return await budget_service.create_entries(classified_list)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Budget processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing error: {e!s}") from e


@router.post(
    "/images",
    response_model=list[ProcessingResponse],
    response_description="List of transaction processing results from screenshot extraction",
    responses={
        200: {
            "description": "Successfully extracted and processed transaction(s) from screenshots",
            "content": {
                "application/json": {
                    "examples": {
                        "single_image": {
                            "summary": "Single Screenshot",
                            "value": [
                                {
                                    "success": True,
                                    "action_type": "backend_handled",
                                    "message": "Logged expenses: 4.5 EUR in Eat out",
                                },
                                {
                                    "success": True,
                                    "action_type": "backend_handled",
                                    "message": "Logged expenses: 12.0 EUR in Groceries",
                                },
                            ],
                        },
                    }
                }
            },
        },
        400: {"description": "Invalid file type (non-image file uploaded)"},
        422: {"description": "No transactions found in the provided image(s)"},
        500: {"description": "Server error during processing"},
    },
)
@limiter.limit("10/minute")
async def process_budget_images(
    request: Request,  # noqa: ARG001 - required by slowapi rate limiter
    files: list[UploadFile],
) -> list[ProcessingResponse]:
    """Process Revolut screenshot images and persist extracted transactions.

    Accepts one or more image files, extracts transactions using Claude Vision,
    then validates and persists them to the database.

    Args:
        request: Starlette Request object (required by slowapi rate limiter)
        files: List of uploaded image files (PNG, JPEG, GIF, WebP)

    Returns:
        List of ProcessingResponse objects (one per extracted transaction)

    Raises:
        HTTPException 400: Non-image file uploaded
        HTTPException 422: No transactions found in images
        HTTPException 429: Rate limit exceeded
        HTTPException 500: Server error during processing
    """
    _ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp"}
    _MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB per image (Anthropic limit)

    try:
        # Validate files were provided
        if not files:
            raise HTTPException(
                status_code=400,
                detail="No files provided. Upload at least one image.",
            )

        # Validate file types
        for file in files:
            if not file.content_type or file.content_type not in _ALLOWED_IMAGE_TYPES:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid file type. Only image files are accepted.",
                )

        # Read image bytes with their media types
        image_data: list[tuple[bytes, str]] = []
        for file in files:
            content = await file.read()
            if len(content) > _MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size is {_MAX_FILE_SIZE // (1024 * 1024)} MB.",
                )
            image_data.append((content, file.content_type or "image/png"))

        # Parse images using Claude Vision
        classified_list = await claude_service.parse_budget_images(image_data)

        # No transactions found
        if not classified_list:
            raise HTTPException(
                status_code=422,
                detail="No transactions found in the provided image(s).",
            )

        # Persist entries
        return await budget_service.create_entries(classified_list)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Budget image processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing error: {e!s}") from e


@router.get(
    "/export",
    response_class=Response,
    responses={
        200: {
            "description": "TSV export of budget transactions",
            "content": {
                "text/tab-separated-values": {
                    "example": "2025-11-13\tExpenses\tGroceries\t98\tKaufland\n2025-11-13\tIncome\tSalary Ivo\t3000\tNovember salary\n"
                }
            },
        },
    },
)
async def export_budget(
    start_date: datetime.date = Query(
        ...,
        description="Starting date for export (inclusive). Format: YYYY-MM-DD",
        example="2025-11-01",
    ),
) -> Response:
    """Export budget transactions as TSV format for Excel copy/paste.

    Returns tab-separated values with the following columns:
    - Date: Transaction date (YYYY-MM-DD)
    - Type: Transaction type (Expenses, Income, or Savings)
    - Category: Transaction category
    - Amount: Amount in EUR as integer (rounded up), falls back to BGN for historical records
    - Details: Merchant or description (empty if null)

    Transactions are filtered by start_date (inclusive) and sorted by date ascending.

    Args:
        start_date: Starting date for filtering transactions

    Returns:
        Response with TSV content and text/tab-separated-values media type
    """
    async with async_session_factory() as db:
        # Query transactions from start_date onwards, ordered by date
        stmt = (
            select(BudgetTransaction)
            .where(BudgetTransaction.date >= start_date)
            .order_by(BudgetTransaction.date.asc())
        )
        result = await db.execute(stmt)
        transactions = result.scalars().all()

        # Build TSV content (no header row)
        lines = []

        for transaction in transactions:
            # Use amount_eur for new transactions, fallback to amount_bgn for historical
            amount_value = (
                transaction.amount_eur if transaction.amount_eur else transaction.amount_bgn
            )
            amount_int = math.ceil(float(amount_value))

            # Handle null details
            details = transaction.details or ""

            # Format row
            line = (
                f"{transaction.date}\t"
                f"{transaction.transaction_type}\t"
                f"{transaction.category}\t"
                f"{amount_int}\t"
                f"{details}"
            )
            lines.append(line)

        # Join with newlines
        tsv_content = "\n".join(lines)

        return Response(
            content=tsv_content,
            media_type="text/tab-separated-values",
        )


@router.get(
    "/transactions",
    response_model=PaginatedTransactionsResponse,
    response_description="Paginated list of budget transactions",
    responses={
        200: {
            "description": "Successfully retrieved transactions",
            "content": {
                "application/json": {
                    "examples": {
                        "paginated_result": {
                            "summary": "Paginated Transactions",
                            "value": {
                                "items": [
                                    {
                                        "id": 1,
                                        "amount": 50.0,
                                        "currency": "EUR",
                                        "amount_eur": 50.0,
                                        "date": "2026-01-15",
                                        "transaction_type": "Expenses",
                                        "category": "Groceries",
                                        "details": "Kaufland",
                                    }
                                ],
                                "total": 1,
                                "page": 1,
                                "page_size": 50,
                            },
                        },
                    }
                }
            },
        },
        422: {"description": "Validation error (invalid query parameters)"},
    },
)
async def get_transactions(
    start_date: datetime.date | None = Query(
        default=None,
        description="Filter transactions on or after this date (YYYY-MM-DD)",
    ),
    end_date: datetime.date | None = Query(
        default=None,
        description="Filter transactions on or before this date (YYYY-MM-DD)",
    ),
    transaction_type: str | None = Query(
        default=None,
        description="Filter by transaction type (Expenses, Income, or Savings)",
    ),
    category: str | None = Query(
        default=None,
        description="Filter by category name",
    ),
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(
        default=50, ge=1, le=200, description="Number of items per page (max 200)"
    ),
) -> PaginatedTransactionsResponse:
    """Query budget transactions with optional filters and pagination.

    Returns a paginated list of transactions ordered by date descending.
    All filters are AND'd together when multiple are provided.
    """
    result = await budget_service.query_transactions(
        start_date=start_date,
        end_date=end_date,
        transaction_type=transaction_type,
        category=category,
        page=page,
        page_size=page_size,
    )

    items = [
        TransactionItem(
            id=t.id,
            amount=float(t.amount),
            currency=t.currency,
            amount_eur=float(t.amount_eur) if t.amount_eur is not None else None,
            date=t.date,
            transaction_type=t.transaction_type,
            category=t.category,
            details=t.details,
        )
        for t in result["items"]
    ]

    return PaginatedTransactionsResponse(
        items=items,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


@router.get(
    "/transactions/aggregate",
    response_model=AggregationResponse,
    response_description="Category-level spending aggregations for the specified period",
    responses={
        200: {
            "description": "Successfully retrieved aggregations",
            "content": {
                "application/json": {
                    "examples": {
                        "monthly": {
                            "summary": "Monthly Aggregation",
                            "value": {
                                "period": {"year": 2026, "month": 1},
                                "aggregations": [
                                    {
                                        "category": "Groceries",
                                        "total_eur": 450.00,
                                        "count": 23,
                                    }
                                ],
                            },
                        },
                        "yearly": {
                            "summary": "Yearly Aggregation",
                            "value": {
                                "period": {"year": 2025, "month": None},
                                "aggregations": [],
                            },
                        },
                    }
                }
            },
        },
        422: {"description": "Validation error (invalid query parameters)"},
    },
)
async def get_transaction_aggregations(
    year: int = Query(
        ...,
        ge=2000,
        le=2100,
        description="Year to aggregate (required)",
    ),
    month: int | None = Query(
        default=None,
        ge=1,
        le=12,
        description="Month (1-12) to aggregate, or omit for full year",
    ),
    transaction_type: str | None = Query(
        default=None,
        description="Filter by transaction type (Expenses, Income, or Savings)",
    ),
) -> AggregationResponse:
    """Get spending totals grouped by category for a given period.

    Returns category-level aggregations sorted by total_eur descending.
    If month is omitted, aggregates the full year.
    If transaction_type is omitted, aggregates all types.
    """
    result = await budget_service.aggregate_transactions(
        year=year, month=month, transaction_type=transaction_type
    )

    aggregations = [
        CategoryAggregation(
            category=a["category"],
            total_eur=a["total_eur"],
            count=a["count"],
        )
        for a in result["aggregations"]
    ]

    return AggregationResponse(
        period=AggregationPeriod(year=year, month=month),
        aggregations=aggregations,
    )


@router.get(
    "/years",
    response_model=AvailableYearsResponse,
    response_description="List of years with transaction data",
    responses={
        200: {
            "description": "Successfully retrieved available years",
            "content": {
                "application/json": {
                    "examples": {
                        "with_data": {
                            "summary": "Years With Data",
                            "value": {"years": [2024, 2025, 2026]},
                        },
                        "empty": {
                            "summary": "No Transactions",
                            "value": {"years": []},
                        },
                    }
                }
            },
        },
    },
)
async def get_available_years() -> AvailableYearsResponse:
    """Get distinct years from all budget transactions.

    Returns a sorted list of years (ascending) that have at least one transaction.
    Returns an empty list if no transactions exist.
    """
    years = await budget_service.get_available_years()
    return AvailableYearsResponse(years=years)
