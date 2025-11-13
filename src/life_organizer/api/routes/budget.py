"""Budget export endpoint for TSV format."""

import datetime
import math

from fastapi import APIRouter, Query, Response
from sqlalchemy import select

from life_organizer.db.models.budget import BudgetTransaction
from life_organizer.db.session import async_session_factory

router = APIRouter()


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
    - Amount: Amount in BGN as integer (rounded up)
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
            # Round up amount to integer
            amount_int = math.ceil(float(transaction.amount_bgn))

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
