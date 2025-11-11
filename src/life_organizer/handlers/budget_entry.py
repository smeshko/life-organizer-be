"""Budget entry handler for expenses, income, and savings transactions."""

import datetime
import logging
from decimal import Decimal
from typing import Literal, cast

from fastapi import HTTPException

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

    async def execute(self, classified_input: ClassifiedInput) -> ProcessingResponse:
        """Process budget entry from LLM-extracted data and persist to database.

        Args:
            classified_input: Classification with extracted_data containing:
                - amount (float): Transaction amount
                - currency (str): Currency code (EUR, BGN, USD)
                - transaction_type (str): Expenses, Income, or Savings
                - category (str): Budget category name
                - date (str): ISO format date (YYYY-MM-DD)
                - merchant (str, optional): Merchant/description

        Returns:
            ProcessingResponse with backend_handled status after database persistence

        Raises:
            ValueError: If required fields are missing or invalid
        """
        try:
            # Validate required fields are present
            required_fields = ["amount", "currency", "transaction_type", "category", "date"]
            missing = [f for f in required_fields if f not in classified_input.extracted_data]
            if missing:
                raise ValueError(f"Missing required fields: {', '.join(missing)}")

            # Extract from LLM-provided data (all parsing done by LLM)
            amount_raw = classified_input.extracted_data["amount"]
            amount = float(amount_raw) if isinstance(amount_raw, (int, float, str)) else 0.0
            currency = str(classified_input.extracted_data["currency"])
            transaction_type_raw = str(classified_input.extracted_data["transaction_type"])
            category = str(classified_input.extracted_data["category"])
            date_iso = str(classified_input.extracted_data["date"])  # Already ISO format from LLM

            # Validate and cast transaction type
            if transaction_type_raw not in ("Expenses", "Income", "Savings"):
                raise ValueError(
                    f"Invalid transaction_type: {transaction_type_raw}. "
                    f"Must be Expenses, Income, or Savings"
                )
            transaction_type = cast("TransactionType", transaction_type_raw)

            # Validate amount is positive
            if amount <= 0:
                raise ValueError(f"Amount must be positive, got {amount}")

            # Only calculation that stays in handler: currency conversion
            amount_bgn = _convert_to_bgn(amount, currency)

            # Extract optional merchant field
            merchant = classified_input.extracted_data.get("merchant")
            details = str(merchant) if merchant else None

            # Persist transaction to database
            async with async_session_factory() as db:
                try:
                    # Create database record
                    transaction = BudgetTransaction(
                        amount=Decimal(str(amount)),  # Original amount
                        currency=currency,
                        amount_bgn=Decimal(str(amount_bgn)),  # Converted amount
                        date=datetime.date.fromisoformat(date_iso),
                        transaction_type=transaction_type,
                        category=category,
                        details=details,
                    )
                    db.add(transaction)
                    await db.commit()
                    logger.info(f"Persisted budget transaction: {transaction}")
                except Exception as db_error:
                    # Log error and raise to fail the request
                    logger.error(f"Failed to persist budget transaction: {db_error}")
                    await db.rollback()
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to save budget transaction to database",
                    ) from db_error

            # Return success result
            return ProcessingResponse(
                success=True,
                action_type=ActionType.BACKEND_HANDLED,
                message=f"Logged {transaction_type.lower()}: {amount_bgn} BGN in {category}",
            )

        except (ValueError, KeyError) as e:
            # Invalid amount, missing field, or validation error
            logger.warning(f"Budget entry validation error: {e}")
            raise HTTPException(
                status_code=422,
                detail=f"Could not process budget entry: {e!s}",
            ) from e

        except Exception as e:
            # Unexpected error
            logger.exception("Budget entry handler error: %s", e)
            raise HTTPException(
                status_code=500,
                detail="An error occurred processing your budget entry",
            ) from e
