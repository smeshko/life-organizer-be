"""Enum types for schemas."""

from enum import StrEnum


class ActionType(StrEnum):
    """Types of actions that can be returned from processing.

    Attributes:
        BACKEND_HANDLED: Action was completed by backend (e.g., logged to database)
    """

    BACKEND_HANDLED = "backend_handled"


class Category(StrEnum):
    """Categories of user input.

    Attributes:
        BUDGET: Financial budget tracking (expenses, income, savings)
        UNKNOWN: Could not classify input
    """

    BUDGET = "budget"
    UNKNOWN = "unknown"
