## TASK-002: Create Enum Types

---
**Status:** COMPLETE
**Branch:** feature/project-scaffold-models
**Type:** IMPLEMENTATION
**Phase:** 1
**Depends On:** TASK-001

---

### Overview

Define enum types for ActionType and Category to provide type-safe constants throughout the application. Enums prevent string typos and provide better IDE autocomplete while integrating seamlessly with Pydantic validation.

ActionType enums represent the three possible response types from handlers. Category enums represent the types of user inputs the classification engine can identify.

### Files Modified

- `src/life_organizer/schemas/enums.py`
- `tests/schemas/test_enums.py`

### Implementation Steps

- [x] Create `src/life_organizer/schemas/enums.py`
- [x] Import Python's `enum.Enum` and `enum.StrEnum`
- [x] Define `ActionType` enum with values: BACKEND_HANDLED, APP_ACTION_REQUIRED, CONFIRMATION_NEEDED
- [x] Define `Category` enum with initial values: EXPENSE, SHOPPING, REMINDER, CALENDAR, UNKNOWN
- [x] Add docstrings explaining each enum and its values
- [x] Create `tests/schemas/test_enums.py`
- [x] Write tests verifying enum values are strings
- [x] Write tests verifying enum comparison and serialization

### Code Example

**File: `src/life_organizer/schemas/enums.py`**

```python
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
        EXPENSE: Financial expense logging
        SHOPPING: Shopping list items
        REMINDER: Time-based reminders
        CALENDAR: Calendar events
        UNKNOWN: Could not classify input
    """

    EXPENSE = "expense"
    SHOPPING = "shopping"
    REMINDER = "reminder"
    CALENDAR = "calendar"
    UNKNOWN = "unknown"
```

**Reference: Existing enum pattern**

No enums exist in the current codebase, but this follows Python standard library patterns and integrates with Pydantic automatically.

### Success Criteria

- [x] Build succeeds: `make lint`
- [x] All tests pass: `pytest tests/schemas/test_enums.py`
- [x] mypy type checking passes with no errors
- [x] Enums can be imported: `from life_organizer.schemas.enums import ActionType, Category`
- [x] Enum values are strings (StrEnum for JSON serialization)

### Verification Commands

```bash
# Run tests
pytest tests/schemas/test_enums.py -v

# Type checking
mypy src/life_organizer/schemas/enums.py

# Verify imports
python -c "from life_organizer.schemas.enums import ActionType, Category; print(ActionType.BACKEND_HANDLED)"
```

### Notes

Using `StrEnum` (Python 3.11+) instead of regular `Enum` ensures values are strings, which works better with JSON serialization and Pydantic. The enum values match the architecture document's response contract exactly.
