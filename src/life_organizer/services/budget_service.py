"""Budget service for persisting parsed budget transactions to the database."""

import datetime
import logging
from decimal import Decimal
from typing import Any, Literal, TypedDict, Union, cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from life_organizer.db.models.budget import BudgetTransaction
from life_organizer.schemas.budget import ExpenseCategory, IncomeCategory, SavingsCategory
from life_organizer.schemas.classification import ClassifiedInput
from life_organizer.schemas.enums import ActionType
from life_organizer.schemas.responses import ProcessingResponse

logger = logging.getLogger(__name__)

# Type alias for transaction types
TransactionType = Literal["Expenses", "Income", "Savings"]


class PaginatedResult(TypedDict):
    """Type for paginated transaction query results."""

    items: list[Any]
    total: int
    page: int
    page_size: int


# Constants
USD_TO_EUR_RATE = 0.92


def _convert_to_eur(amount: float, currency: str) -> float:
    """Convert amount to EUR.

    Args:
        amount: Amount in source currency
        currency: Currency code (EUR, USD)

    Returns:
        Amount in EUR
    """
    if currency == "EUR":
        return round(amount, 2)
    elif currency == "USD":
        return round(amount * USD_TO_EUR_RATE, 2)
    else:
        logger.warning(f"Unknown currency '{currency}', assuming EUR")
        return round(amount, 2)


class BudgetService:
    """Service for validating and persisting budget transactions.

    Accepts parsed ClassifiedInput objects from ClaudeService and persists
    them as BudgetTransaction records in the database.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        """Initialize BudgetService.

        Args:
            session_factory: Async session factory for database access
        """
        self.session_factory = session_factory

    async def create_entries(
        self, classified_inputs: list[ClassifiedInput]
    ) -> list[ProcessingResponse]:
        """Validate and persist budget entries from parsed ClassifiedInput objects.

        Processes each input independently. Valid transactions are committed atomically.
        If the database commit fails, all success responses are updated to failures.

        Args:
            classified_inputs: List of parsed budget classifications

        Returns:
            List of ProcessingResponse objects (one per input)
        """
        results: list[ProcessingResponse] = []
        transactions_to_commit: list[BudgetTransaction] = []

        async with self.session_factory() as db:
            try:
                for classified_input in classified_inputs:
                    try:
                        # Validate required fields
                        required_fields = [
                            "amount",
                            "currency",
                            "transaction_type",
                            "category",
                            "date",
                        ]
                        missing = [
                            f for f in required_fields if f not in classified_input.extracted_data
                        ]
                        if missing:
                            raise ValueError(f"Missing required fields: {', '.join(missing)}")

                        # Extract and validate amount
                        amount_raw = classified_input.extracted_data["amount"]
                        amount = (
                            float(amount_raw) if isinstance(amount_raw, (int, float, str)) else 0.0
                        )
                        if amount <= 0:
                            raise ValueError(f"Amount must be positive, got {amount}")

                        currency = str(classified_input.extracted_data["currency"])
                        transaction_type_raw = str(
                            classified_input.extracted_data["transaction_type"]
                        )

                        # Validate transaction type
                        if transaction_type_raw not in ("Expenses", "Income", "Savings"):
                            raise ValueError(
                                f"Invalid transaction_type: {transaction_type_raw}. "
                                f"Must be Expenses, Income, or Savings"
                            )
                        transaction_type = cast("TransactionType", transaction_type_raw)

                        # Validate category against appropriate enum
                        category_raw = str(classified_input.extracted_data["category"])
                        category_enum: Union[ExpenseCategory, IncomeCategory, SavingsCategory]
                        if transaction_type == "Expenses":
                            try:
                                category_enum = ExpenseCategory(category_raw)
                            except ValueError:
                                raise ValueError(
                                    f"Invalid expense category: {category_raw}. "
                                    f"Must be one of: "
                                    f"{', '.join([c.value for c in ExpenseCategory])}"
                                ) from None
                        elif transaction_type == "Income":
                            try:
                                category_enum = IncomeCategory(category_raw)
                            except ValueError:
                                raise ValueError(
                                    f"Invalid income category: {category_raw}. "
                                    f"Must be one of: "
                                    f"{', '.join([c.value for c in IncomeCategory])}"
                                ) from None
                        elif transaction_type == "Savings":
                            try:
                                category_enum = SavingsCategory(category_raw)
                            except ValueError:
                                raise ValueError(
                                    f"Invalid savings category: {category_raw}. "
                                    f"Must be one of: "
                                    f"{', '.join([c.value for c in SavingsCategory])}"
                                ) from None

                        # Convert to EUR
                        amount_eur = _convert_to_eur(amount, currency)

                        # Extract other fields
                        category = category_enum.value
                        date_iso = str(classified_input.extracted_data["date"])
                        merchant = classified_input.extracted_data.get("merchant")
                        details = str(merchant) if merchant else None

                        # Create transaction model
                        transaction = BudgetTransaction(
                            amount=Decimal(str(amount)),
                            currency=currency,
                            amount_bgn=Decimal("0"),
                            amount_eur=Decimal(str(amount_eur)),
                            date=datetime.date.fromisoformat(date_iso),
                            transaction_type=transaction_type,
                            category=category,
                            details=details,
                        )

                        db.add(transaction)
                        transactions_to_commit.append(transaction)

                        results.append(
                            ProcessingResponse(
                                success=True,
                                action_type=ActionType.BACKEND_HANDLED,
                                message=(
                                    f"Logged {transaction_type.lower()}: "
                                    f"{amount_eur} EUR in {category}"
                                ),
                            )
                        )

                    except (ValueError, KeyError) as e:
                        logger.warning(f"Budget entry validation error: {e}")
                        results.append(
                            ProcessingResponse(
                                success=False,
                                action_type=ActionType.BACKEND_HANDLED,
                                message=f"Could not process budget entry: {e!s}",
                            )
                        )

                    except Exception as e:
                        logger.error(f"Unexpected error processing transaction: {e}")
                        results.append(
                            ProcessingResponse(
                                success=False,
                                action_type=ActionType.BACKEND_HANDLED,
                                message=(f"An error occurred processing your budget entry: {e!s}"),
                            )
                        )

                # Atomic commit
                if transactions_to_commit:
                    await db.commit()
                    logger.info(f"Persisted {len(transactions_to_commit)} budget transaction(s)")
                else:
                    logger.warning("No valid transactions to commit")

            except Exception as db_error:
                logger.error(f"Failed to persist budget transactions: {db_error}")
                await db.rollback()

                for i, result in enumerate(results):
                    if result.success:
                        results[i] = ProcessingResponse(
                            success=False,
                            action_type=ActionType.BACKEND_HANDLED,
                            message="Failed to save budget transaction to database",
                        )

        return results

    async def query_transactions(
        self,
        start_date: datetime.date | None,
        end_date: datetime.date | None,
        transaction_type: str | None,
        category: str | None,
        page: int,
        page_size: int,
    ) -> PaginatedResult:
        """Query transactions with optional filters and pagination.

        Args:
            start_date: Filter transactions on or after this date
            end_date: Filter transactions on or before this date
            transaction_type: Filter by transaction type (Expenses, Income, Savings)
            category: Filter by category name
            page: Page number (1-based)
            page_size: Number of items per page

        Returns:
            Dict with items, total, page, and page_size
        """
        async with self.session_factory() as db:
            # Build base filter conditions
            conditions = []
            if start_date is not None:
                conditions.append(BudgetTransaction.date >= start_date)
            if end_date is not None:
                conditions.append(BudgetTransaction.date <= end_date)
            if transaction_type is not None:
                conditions.append(BudgetTransaction.transaction_type == transaction_type)
            if category is not None:
                conditions.append(BudgetTransaction.category == category)

            # Count query
            count_stmt = select(func.count()).select_from(BudgetTransaction)
            for condition in conditions:
                count_stmt = count_stmt.where(condition)
            count_result = await db.execute(count_stmt)
            total = count_result.scalar() or 0

            # Items query with pagination
            items_stmt = (
                select(BudgetTransaction)
                .order_by(BudgetTransaction.date.desc(), BudgetTransaction.id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            for condition in conditions:
                items_stmt = items_stmt.where(condition)
            items_result = await db.execute(items_stmt)
            transactions = items_result.scalars().all()

            return {
                "items": list(transactions),
                "total": total,
                "page": page,
                "page_size": page_size,
            }

    async def get_available_years(self) -> list[int]:
        """Get distinct years from all transactions, sorted ascending.

        Returns:
            List of integer years, or empty list if no transactions exist
        """
        async with self.session_factory() as db:
            stmt = select(func.distinct(func.extract("year", BudgetTransaction.date))).order_by(
                func.extract("year", BudgetTransaction.date).asc()
            )
            result = await db.execute(stmt)
            return [int(row) for row in result.scalars().all()]
