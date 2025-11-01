## TASK-006: Implement AppAction Models with Inheritance

---
**Status:** OPEN
**Branch:** feature/project-scaffold-models
**Type:** IMPLEMENTATION
**Phase:** 1
**Depends On:** TASK-001

---

### Overview

Create structured AppAction models using inheritance and Pydantic's discriminated union pattern. BaseAppAction serves as the abstract base with a `type` discriminator field, and concrete subclasses (CreateReminderAction, AddToShoppingListAction, CreateCalendarEventAction) define specific fields for each action type.

This provides type safety while allowing the iOS app to determine which action type was returned based on the `type` field.

### Files Modified

- `src/life_organizer/schemas/actions.py`
- `tests/schemas/test_actions.py`

### Implementation Steps

- [ ] Create `src/life_organizer/schemas/actions.py`
- [ ] Import BaseModel, Field, Literal from pydantic
- [ ] Import datetime from Python standard library
- [ ] Define BaseAppAction base class with type field
- [ ] Define CreateReminderAction subclass (title, due_date, list_id, notes)
- [ ] Define AddToShoppingListAction subclass (item, quantity, list_id, notes)
- [ ] Define CreateCalendarEventAction subclass (title, start_time, end_time, location, notes)
- [ ] Add comprehensive docstrings for all models
- [ ] Create `tests/schemas/test_actions.py`
- [ ] Write test for CreateReminderAction validation
- [ ] Write test for AddToShoppingListAction validation
- [ ] Write test for CreateCalendarEventAction validation
- [ ] Write test for Pydantic discriminated union (parsing JSON with type field)

### Code Example

**File: `src/life_organizer/schemas/actions.py`**

```python
"""App action schemas for iOS client actions."""

from datetime import datetime

from pydantic import BaseModel, Field
from typing import Literal


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
```

**Reference: Pydantic discriminated union pattern**

Pydantic automatically handles discrimination based on the `type` field using Literal types. When parsing JSON, it looks at the `type` value and instantiates the correct subclass.
```

### Success Criteria

- [ ] Build succeeds: `make lint`
- [ ] All tests pass: `pytest tests/schemas/test_actions.py`
- [ ] mypy type checking passes
- [ ] Each action subclass validates its specific fields correctly
- [ ] Pydantic discriminated union works (parses JSON to correct subclass)
- [ ] All three action types (reminder, shopping, calendar) work correctly
- [ ] Type alias AppAction exports correctly for use in ActionResult

### Verification Commands

```bash
# Run tests
pytest tests/schemas/test_actions.py -v

# Type checking
mypy src/life_organizer/schemas/actions.py

# Test discriminated union manually
python -c "
from life_organizer.schemas.actions import CreateReminderAction, AppAction
from datetime import datetime
import json

# Create specific action
action = CreateReminderAction(
    title='Buy milk',
    due_date=datetime(2025, 10, 31, 10, 0)
)
print('Created:', action.model_dump_json())

# Parse from JSON (Pydantic determines correct subclass)
json_str = '{\"type\": \"create_reminder\", \"title\": \"Test\"}'
parsed = CreateReminderAction.model_validate_json(json_str)
print('Parsed:', type(parsed).__name__)
"
```

### Notes

The discriminated union pattern provides excellent type safety. The iOS app can check the `type` field to determine which fields are present. Future action types (e.g., `CreateNoteAction`, `SendMessageAction`) can be added by creating new subclasses and updating the AppAction type alias.
