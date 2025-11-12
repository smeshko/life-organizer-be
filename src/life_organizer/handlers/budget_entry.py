"""Budget entry handler for expenses, income, and savings transactions."""

import datetime
import logging
from decimal import Decimal
from typing import Literal, cast

from life_organizer.db.models.budget import BudgetTransaction
from life_organizer.db.session import async_session_factory
from life_organizer.handlers.base import BaseHandler
from life_organizer.schemas.classification import ClassifiedInput
from life_organizer.schemas.enums import ActionType, Category
from life_organizer.schemas.responses import ProcessingResponse

logger = logging.getLogger(__name__)

# Type alias for transaction types
TransactionType = Literal["Expenses", "Income", "Savings"]

# Constants
EUR_TO_BGN_RATE = 1.955


def _convert_to_bgn(amount: float, currency: str) -> float:
    """Convert amount to BGN.

    Args:
        amount: Amount in source currency
        currency: Currency code (EUR, BGN, USD)

    Returns:
        Amount in BGN
    """
    if currency == "EUR":
        return round(amount * EUR_TO_BGN_RATE, 2)
    elif currency == "BGN":
        return round(amount, 2)
    elif currency == "USD":
        # Rough approximation: 1 USD ≈ 1.8 BGN
        return round(amount * 1.8, 2)
    else:
        # Unknown currency, assume BGN
        logger.warning(f"Unknown currency '{currency}', assuming BGN")
        return round(amount, 2)


class BudgetEntryHandler(BaseHandler):
    """Handler for budget entries (expenses, income, savings).

    Processes LLM-classified budget entries with pre-extracted structured data.
    Performs currency conversion and persists transactions to the database.

    All extraction, classification, and date parsing is done by the LLM classifier.
    This handler validates, transforms, and persists the data to PostgreSQL.

    Handles:
    - Expenses: "spent 120eur at next"
    - Income: "received 250bgn rent"
    - Savings: "saved 1220 in ibkr"
    """

    def can_handle(self, classified_input: ClassifiedInput) -> bool:
        """Determine if this handler can process the input.

        Args:
            classified_input: Classified user input

        Returns:
            True if category is BUDGET (used for all budget entries)
        """
        return classified_input.category == Category.BUDGET

    def requires_app_action(self) -> bool:
        """Determine if this handler requires iOS app involvement.

        Returns:
            False (backend handles database persistence directly)
        """
        return False

    async def execute(self, classified_inputs: list[ClassifiedInput]) -> list[ProcessingResponse]:
        """Process budget entries from LLM-extracted data and persist to database.

        Args:
            classified_inputs: List of classifications with extracted_data containing:
                - amount (float): Transaction amount
                - currency (str): Currency code (EUR, BGN, USD)
                - transaction_type (str): Expenses, Income, or Savings
                - category (str): Budget category name
                - date (str): ISO format date (YYYY-MM-DD)
                - merchant (str, optional): Merchant/description

        Returns:
            List of ProcessingResponse objects (one per input) with success status.
        """
        results: list[ProcessingResponse] = []
        transactions_to_commit: list[BudgetTransaction] = []

        # Single database session for all transactions
        async with async_session_factory() as db:
            try:
                # Process each classified input
                for classified_input in classified_inputs:
                    try:
                        # VALIDATION PHASE
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

                        # Extract and validate data
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

                        # Validate transaction type enum
                        if transaction_type_raw not in ("Expenses", "Income", "Savings"):
                            raise ValueError(
                                f"Invalid transaction_type: {transaction_type_raw}. "
                                f"Must be Expenses, Income, or Savings"
                            )
                        transaction_type = cast("TransactionType", transaction_type_raw)

                        # TRANSFORMATION PHASE
                        amount_bgn = _convert_to_bgn(amount, currency)

                        # Extract other fields
                        category = str(classified_input.extracted_data["category"])
                        date_iso = str(classified_input.extracted_data["date"])
                        merchant = classified_input.extracted_data.get("merchant")
                        details = str(merchant) if merchant else None

                        # Create transaction model (not yet persisted)
                        transaction = BudgetTransaction(
                            amount=Decimal(str(amount)),
                            currency=currency,
                            amount_bgn=Decimal(str(amount_bgn)),
                            date=datetime.date.fromisoformat(date_iso),
                            transaction_type=transaction_type,
                            category=category,
                            details=details,
                        )

                        # Add to session (still transient)
                        db.add(transaction)
                        transactions_to_commit.append(transaction)

                        # Create success response
                        results.append(
                            ProcessingResponse(
                                success=True,
                                action_type=ActionType.BACKEND_HANDLED,
                                message=f"Logged {transaction_type.lower()}: {amount_bgn} BGN in {category}",
                            )
                        )

                    except (ValueError, KeyError) as e:
                        # Validation error for this transaction
                        logger.warning(f"Budget entry validation error: {e}")
                        results.append(
                            ProcessingResponse(
                                success=False,
                                action_type=ActionType.BACKEND_HANDLED,
                                message=f"Could not process budget entry: {e!s}",
                            )
                        )

                    except Exception as e:
                        # Unexpected error for this transaction
                        logger.error(f"Unexpected error processing transaction: {e}")
                        results.append(
                            ProcessingResponse(
                                success=False,
                                action_type=ActionType.BACKEND_HANDLED,
                                message=f"An error occurred processing your budget entry: {e!s}",
                            )
                        )

                # ATOMIC COMMIT - all valid transactions or none
                if transactions_to_commit:
                    await db.commit()
                    logger.info(f"Persisted {len(transactions_to_commit)} budget transaction(s)")
                else:
                    logger.warning("No valid transactions to commit")

            except Exception as db_error:
                # Database error - rollback all
                logger.error(f"Failed to persist budget transactions: {db_error}")
                await db.rollback()

                # Update all success responses to failure
                for i, result in enumerate(results):
                    if result.success:
                        results[i] = ProcessingResponse(
                            success=False,
                            action_type=ActionType.BACKEND_HANDLED,
                            message="Failed to save budget transaction to database",
                        )

        return results  # Always return list of ProcessingResponse
