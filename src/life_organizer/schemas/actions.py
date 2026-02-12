"""App action schemas for iOS client actions."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class BaseAppAction(BaseModel):
    """Base model for iOS app actions that the backend requests.

    When the backend cannot handle an action directly (e.g., creating a reminder
    requires iOS Reminders app access), it returns an app action that tells the
    iOS client what to do.

    Subclasses define specific action types with their required fields.
    The iOS app uses the 'type' field to determine which action to perform.

    Attributes:
        type: Action type discriminator
    """

    type: str = Field(..., description="Action type discriminator")


class AddToShoppingListAction(BaseAppAction):
    """Action to add an item to a shopping list.

    Attributes:
        type: Always "add_to_shopping_list"
        item: Item name to add
        quantity: How much to buy (optional, e.g., "2 gallons", "1 lb")
        list_id: Which shopping list (defaults to "shopping_list")
        notes: Additional notes/context (optional)
    """

    type: Literal["add_to_shopping_list"] = "add_to_shopping_list"
    item: str = Field(..., description="Item to add to list", min_length=1)
    quantity: str | None = Field(default=None, description="Quantity to buy")
    list_id: str = Field(default="shopping_list", description="Target list ID")
    notes: str | None = Field(default=None, description="Additional notes")


class CreateCalendarEventAction(BaseAppAction):
    """Action to create a calendar event in iOS Calendar.

    Attributes:
        type: Always "create_calendar_event"
        title: Event title
        start_time: Event start time
        end_time: Event end time
        location: Event location (optional)
        notes: Additional notes/context (optional)
    """

    type: Literal["create_calendar_event"] = "create_calendar_event"
    title: str = Field(..., description="Event title", min_length=1)
    start_time: datetime = Field(..., description="Event start time")
    end_time: datetime = Field(..., description="Event end time")
    location: str | None = Field(default=None, description="Event location")
    notes: str | None = Field(default=None, description="Additional notes")


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
AppAction = AddToShoppingListAction | CreateCalendarEventAction | LogBudgetEntryAction
