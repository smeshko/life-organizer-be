## TASK-004: Implement ActionResult Response Schema

---
**Status:** OPEN
**Branch:** feature/project-scaffold-models
**Type:** IMPLEMENTATION
**Phase:** 1
**Depends On:** TASK-002 (needs ActionType enum), TASK-006 (needs AppAction types)

---

### Overview

Create the ActionResult Pydantic model that handlers return and the API serializes to JSON responses. This schema uses Optional fields based on action_type to support three response patterns: backend_handled, app_action_required, and confirmation_needed.

The model includes all fields from the architecture document's response contract.

### Files Modified

- `src/life_organizer/schemas/responses.py`
- `tests/schemas/test_responses.py`

### Implementation Steps

- [ ] Create `src/life_organizer/schemas/responses.py`
- [ ] Import BaseModel, Field from pydantic
- [ ] Import ActionType enum from schemas.enums
- [ ] Import AppAction type from schemas.actions
- [ ] Define ConfirmationData model (question, options, original_classification, confidence)
- [ ] Define ActionResult model with fields: success, action_type, message
- [ ] Add optional fields: app_action (AppAction union type), confirmation (ConfirmationData)
- [ ] Add Field() descriptions for all fields
- [ ] Add comprehensive docstrings
- [ ] Create `tests/schemas/test_responses.py`
- [ ] Write test for backend_handled response (no optional fields)
- [ ] Write test for app_action_required response (with CreateReminderAction)
- [ ] Write test for app_action_required response (with AddToShoppingListAction)
- [ ] Write test for confirmation_needed response (confirmation present)
- [ ] Write test for JSON serialization format with discriminated union

### Code Example

**File: `src/life_organizer/schemas/responses.py`**

```python
"""Response schemas for the Life Organizer API."""

from pydantic import BaseModel, Field

from life_organizer.schemas.actions import AppAction
from life_organizer.schemas.enums import ActionType


class ConfirmationData(BaseModel):
    """Data for confirmation requests when classification is uncertain.

    Attributes:
        question: Question to ask the user for clarification
        options: List of possible answers the user can choose from
        original_classification: What the system initially classified this as
        confidence: Confidence score (0.0-1.0) of original classification
    """

    question: str = Field(..., description="Question to ask user for clarification")
    options: list[str] = Field(
        ..., description="List of possible answers", min_length=2
    )
    original_classification: str = Field(
        ..., description="System's initial classification guess"
    )
    confidence: float = Field(..., description="Confidence score (0.0-1.0)", ge=0.0, le=1.0)


class ActionResult(BaseModel):
    """Result returned from handlers and serialized to API response.

    Different action_type values use different optional fields:
    - backend_handled: Only success, action_type, message
    - app_action_required: Includes app_action (discriminated union of action types)
    - confirmation_needed: Includes confirmation data

    Attributes:
        success: Whether the action was successful
        action_type: Type of action (backend_handled, app_action_required, confirmation_needed)
        message: Human-readable message about what happened
        app_action: Optional AppAction (CreateReminderAction | AddToShoppingListAction | CreateCalendarEventAction)
        confirmation: Optional confirmation data when user input is ambiguous
    """

    success: bool = Field(..., description="Whether the action was successful")
    action_type: ActionType = Field(..., description="Type of action performed/required")
    message: str = Field(..., description="Human-readable message about the result")
    app_action: AppAction | None = Field(
        default=None,
        description="iOS app action (when action_type is app_action_required). "
        "Discriminated union of CreateReminderAction | AddToShoppingListAction | CreateCalendarEventAction"
    )
    confirmation: ConfirmationData | None = Field(
        default=None, description="Confirmation request data (when action_type is confirmation_needed)"
    )
```

**Reference: Modern Python type hints from config.py**

```python
# From src/life_organizer/config.py:29 - shows list[str] pattern
cors_origins: list[str] = Field(
    default=["http://localhost:3000"],
    description="Allowed CORS origins",
)

# From src/life_organizer/config.py:35 - shows str | None pattern
openai_api_key: str | None = Field(default=None, description="OpenAI API key")
```

### Success Criteria

- [ ] Build succeeds: `make lint`
- [ ] All tests pass: `pytest tests/schemas/test_responses.py`
- [ ] mypy type checking passes
- [ ] All three response types (backend_handled, app_action_required, confirmation_needed) validate correctly
- [ ] Optional fields are truly optional (can create ActionResult without them)
- [ ] Schema matches architecture document response contract

### Verification Commands

```bash
# Run tests
pytest tests/schemas/test_responses.py -v

# Type checking
mypy src/life_organizer/schemas/responses.py

# Test manually
python -c "
from life_organizer.schemas.responses import ActionResult
from life_organizer.schemas.enums import ActionType
result = ActionResult(success=True, action_type=ActionType.BACKEND_HANDLED, message='Done')
print(result.model_dump_json())
"
```

### Notes

The AppAction type alias is a discriminated union of all concrete action types. Pydantic automatically serializes/deserializes to the correct subclass based on the `type` field. This provides strong typing while maintaining JSON compatibility with the iOS app. The iOS app receives the `type` field and knows exactly which fields will be present.
