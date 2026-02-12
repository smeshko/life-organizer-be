"""Enum types for schemas."""

from enum import StrEnum


class ActionType(StrEnum):
    """Types of actions that can be returned from handlers.

    Attributes:
        BACKEND_HANDLED: Action was completed by backend (e.g., logged to database)
        APP_ACTION_REQUIRED: iOS app needs to perform an action (e.g., add to shopping list)
    """

    BACKEND_HANDLED = "backend_handled"
    APP_ACTION_REQUIRED = "app_action_required"


class Category(StrEnum):
    """Categories of user input that the classification engine can identify.

    Attributes:
        BUDGET: Financial budget tracking (expenses, income, savings)
        NOTE: Quick notes and memos
        QUOTE: Inspirational quotes
        UNKNOWN: Could not classify input
    """

    BUDGET = "budget"
    NOTE = "note"
    QUOTE = "quote"
    UNKNOWN = "unknown"
