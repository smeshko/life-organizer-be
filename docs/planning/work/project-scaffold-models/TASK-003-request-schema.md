## TASK-003: Implement ProcessInputRequest Schema

---
**Status:** COMPLETE
**Branch:** feature/project-scaffold-models
**Type:** IMPLEMENTATION
**Phase:** 1
**Depends On:** TASK-001

---

### Overview

Create the ProcessInputRequest Pydantic model that defines the contract for iOS app requests. This schema validates incoming requests at the API layer and provides automatic OpenAPI documentation.

The model follows the simplified contract: user_id, input text, and timestamp only (UserContext removed per clarification).

### Files Modified

- `src/life_organizer/schemas/requests.py`
- `tests/schemas/test_requests.py`

### Implementation Steps

- [x] Create `src/life_organizer/schemas/requests.py`
- [x] Import Pydantic BaseModel and Field
- [x] Import datetime from Python standard library
- [x] Define ProcessInputRequest class with fields: user_id, input, timestamp
- [x] Add Field() descriptions for OpenAPI documentation
- [x] Add docstring explaining the model's purpose
- [x] Create `tests/schemas/test_requests.py`
- [x] Write test for valid request data
- [x] Write test for missing required fields (validation errors)
- [x] Write test for invalid timestamp format
- [x] Write test for empty/whitespace input string

### Code Example

**File: `src/life_organizer/schemas/requests.py`**

```python
"""Request schemas for the Life Organizer API."""

from datetime import datetime

from pydantic import BaseModel, Field


class ProcessInputRequest(BaseModel):
    """Request model for processing user voice/text input.

    This is the primary API contract between the iOS app and backend.
    The backend validates, classifies, and routes the input to appropriate handlers.

    Attributes:
        user_id: Identifier for the family member making the request
        input: Raw voice or text input from the user
        timestamp: When the input was captured (ISO 8601 format)
    """

    user_id: str = Field(
        ...,
        description="Family member identifier (e.g., 'family_member_123')",
        min_length=1,
    )
    input: str = Field(
        ...,
        description="Voice or text input from user (e.g., 'Spent 45 euros at restaurant')",
        min_length=1,
    )
    timestamp: datetime = Field(
        ..., description="When the input was captured (ISO 8601 format)"
    )
```

**Reference: Existing Pydantic pattern from config.py:9-56**

```python
# From src/life_organizer/config.py - shows Field() usage pattern
class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    api_version: str = Field(default="v1", description="API version")
```

### Success Criteria

- [x] Build succeeds: `make lint`
- [x] All tests pass: `pytest tests/schemas/test_requests.py`
- [x] mypy type checking passes with no errors
- [x] Pydantic validates correct data and rejects invalid data
- [x] Schema appears in FastAPI automatic OpenAPI docs
- [x] Modern Python type hints used (str not Optional[str], datetime not typing.Optional)

### Verification Commands

```bash
# Run tests
pytest tests/schemas/test_requests.py -v

# Type checking
mypy src/life_organizer/schemas/requests.py

# Test validation interactively
python -c "
from life_organizer.schemas.requests import ProcessInputRequest
from datetime import datetime
req = ProcessInputRequest(user_id='test', input='hello', timestamp=datetime.now())
print(req.model_dump_json())
"
```

### Notes

Following the research.md decision to remove UserContext. The timestamp field uses Python's datetime which Pydantic automatically serializes/deserializes to ISO 8601 format. Field() descriptions will appear in the auto-generated FastAPI OpenAPI documentation.
