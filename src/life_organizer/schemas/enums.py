"""Enum types for schemas."""

from enum import StrEnum


class ActionType(StrEnum):
    """Types of actions that can be returned from handlers.

    Attributes:
        BACKEND_HANDLED: Action was completed by backend (e.g., logged to database)
        APP_ACTION_REQUIRED: iOS app needs to perform an action (e.g., create reminder)
        CONFIRMATION_NEEDED: Ambiguous input, user needs to clarify
    """

    BACKEND_HANDLED = "backend_handled"
    APP_ACTION_REQUIRED = "app_action_required"
    CONFIRMATION_NEEDED = "confirmation_needed"


class Category(StrEnum):
    """Categories of user input that the classification engine can identify.

    Attributes:
        BUDGET: Financial budget tracking (expenses, income, savings)
        SHOPPING: Shopping list items
        REMINDER: Time-based reminders
        CALENDAR: Calendar events
        UNKNOWN: Could not classify input
    """

    BUDGET = "budget"
    SHOPPING = "shopping"
    REMINDER = "reminder"
    CALENDAR = "calendar"
    UNKNOWN = "unknown"
