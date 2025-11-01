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


class CreateReminderAction(BaseAppAction):
    """Action to create a reminder in iOS Reminders app.

    Attributes:
        type: Always "create_reminder"
        title: Reminder title/description
        due_date: When the reminder is due (optional)
        list_id: Which reminders list to add to (optional)
        notes: Additional notes/context (optional)
    """

    type: Literal["create_reminder"] = "create_reminder"
    title: str = Field(..., description="Reminder title", min_length=1)
    due_date: datetime | None = Field(default=None, description="When reminder is due")
    list_id: str | None = Field(default=None, description="Target reminders list ID")
    notes: str | None = Field(default=None, description="Additional notes")


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


# Type alias for discriminated union
AppAction = CreateReminderAction | AddToShoppingListAction | CreateCalendarEventAction
