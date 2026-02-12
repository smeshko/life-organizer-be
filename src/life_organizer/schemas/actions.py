"""App action schemas for iOS client actions."""

from typing import Literal

from pydantic import BaseModel, Field


class BaseAppAction(BaseModel):
    """Base model for iOS app actions that the backend requests.

    When the backend cannot handle an action directly, it returns an app action
    that tells the iOS client what to do.

    Subclasses define specific action types with their required fields.
    The iOS app uses the 'type' field to determine which action to perform.

    Attributes:
        type: Action type discriminator
    """

    type: str = Field(..., description="Action type discriminator")


class LogBudgetEntryAction(BaseAppAction):
    """Action to log a budget entry (expense/income/savings) in Excel sheet.

    The iOS app receives this action and populates the budget tracking Excel sheet
    with the transaction details. All amounts are in EUR.

    Attributes:
        type: Always "log_budget_entry"
        amount: Amount in EUR
        date: Transaction date in ISO format (YYYY-MM-DD)
        transaction_type: One of "Expenses", "Income", "Savings"
        category: Budget category name (from predefined categories)
        details: Optional merchant/description (e.g., "next", "dm", "ibkr")
    """

    type: Literal["log_budget_entry"] = "log_budget_entry"
    amount: float = Field(..., description="Amount in EUR", gt=0)
    date: str = Field(..., description="Date in ISO format (YYYY-MM-DD)")
    transaction_type: Literal["Expenses", "Income", "Savings"] = Field(
        ..., description="Type of transaction"
    )
    category: str = Field(..., description="Budget category name", min_length=1)
    details: str | None = Field(default=None, description="Optional merchant/description")


# Type alias for discriminated union
AppAction = LogBudgetEntryAction
