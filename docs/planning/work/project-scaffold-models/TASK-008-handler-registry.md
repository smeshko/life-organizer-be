## TASK-008: Implement Handler Registry System

---
**Status:** OPEN
**Branch:** feature/project-scaffold-models
**Type:** IMPLEMENTATION
**Phase:** 2
**Depends On:** TASK-007 (needs BaseHandler)

---

### Overview

Create the handler registry system that stores available handlers and finds the appropriate handler for classified input. This implements a simple list-based registry with a get_handler() function that iterates to find the first matching handler.

Also includes a DummyHandler for testing the registry system end-to-end.

### Files Modified

- `src/life_organizer/handlers/__init__.py`
- `tests/handlers/test_registry.py`
- `tests/handlers/dummy_handler.py` (test fixture)

### Implementation Steps

- [ ] Update `src/life_organizer/handlers/__init__.py`
- [ ] Import BaseHandler from handlers.base
- [ ] Import ClassifiedInput from schemas
- [ ] Create HANDLERS list (empty initially)
- [ ] Implement get_handler(classified_input) function with O(n) iteration
- [ ] Add docstring explaining registry pattern
- [ ] Create `tests/handlers/dummy_handler.py` with example implementation
- [ ] Create `tests/handlers/test_registry.py`
- [ ] Write test for get_handler() finding correct handler
- [ ] Write test for get_handler() returning None when no match
- [ ] Write test for handler precedence (first match wins)

### Code Example

**File: `src/life_organizer/handlers/__init__.py`**

```python
"""Handler registry for the plugin architecture.

The handler registry maintains a list of available handlers and provides
a lookup function to find the appropriate handler for classified input.

Handlers are checked in order, and the first handler where can_handle()
returns True is selected. This allows for handler precedence and fallback logic.

Example:
    ```python
    from life_organizer.handlers import get_handler

    classified = ClassifiedInput(category=Category.EXPENSE, ...)
    handler = get_handler(classified)
    if handler:
        result = handler.execute(classified)
    ```
"""

from life_organizer.handlers.base import BaseHandler
from life_organizer.schemas.classification import ClassifiedInput

# Handler registry - add concrete handlers here as they're implemented
# Order matters: first matching handler is selected
HANDLERS: list[BaseHandler] = [
    # Future: ExpenseHandler(),
    # Future: ShoppingHandler(),
    # Future: ReminderHandler(),
]


def get_handler(classified_input: ClassifiedInput) -> BaseHandler | None:
    """Find the first handler that can process the classified input.

    Iterates through the handler registry in order and returns the first
    handler where can_handle() returns True. If no handler can process
    the input, returns None.

    Args:
        classified_input: The classified user input

    Returns:
        The first matching handler, or None if no handler can process this input

    Note:
        Handler order in the HANDLERS list determines precedence. More specific
        handlers should come before more general handlers.
    """
    for handler in HANDLERS:
        if handler.can_handle(classified_input):
            return handler
    return None


__all__ = ["BaseHandler", "get_handler", "HANDLERS"]
```

**File: `tests/handlers/dummy_handler.py`** (test fixture)

```python
"""Dummy handler for testing the registry system."""

from life_organizer.handlers.base import BaseHandler
from life_organizer.schemas.classification import ClassifiedInput
from life_organizer.schemas.enums import ActionType, Category
from life_organizer.schemas.responses import ActionResult


class DummyHandler(BaseHandler):
    """Test handler that handles UNKNOWN category."""

    def can_handle(self, classified_input: ClassifiedInput) -> bool:
        return classified_input.category == Category.UNKNOWN

    def requires_app_action(self) -> bool:
        return False

    def execute(self, classified_input: ClassifiedInput) -> ActionResult:
        return ActionResult(
            success=True,
            action_type=ActionType.BACKEND_HANDLED,
            message="Handled by dummy handler",
        )
```

### Success Criteria

- [ ] Build succeeds: `make lint`
- [ ] All tests pass: `pytest tests/handlers/test_registry.py`
- [ ] mypy type checking passes
- [ ] get_handler() returns correct handler when match exists
- [ ] get_handler() returns None when no handler matches
- [ ] Handler precedence works (first match in list wins)
- [ ] DummyHandler successfully implements BaseHandler contract

### Verification Commands

```bash
# Run tests
pytest tests/handlers/test_registry.py -v

# Type checking
mypy src/life_organizer/handlers/

# Test manually with dummy handler
python -c "
from tests.handlers.dummy_handler import DummyHandler
from life_organizer.handlers import HANDLERS, get_handler
from life_organizer.schemas.classification import ClassifiedInput
from life_organizer.schemas.enums import Category

# Add dummy to registry
HANDLERS.append(DummyHandler())

# Test lookup
classified = ClassifiedInput(
    category=Category.UNKNOWN,
    confidence=0.5,
    raw_input='test'
)
handler = get_handler(classified)
print(f'Found handler: {type(handler).__name__}')
"
```

### Notes

The simple list-based registry is O(n) but sufficient for 5-10 handlers. If handler count grows significantly, this can be optimized to a dict-based lookup by category. The test fixture (DummyHandler) demonstrates how to properly implement the BaseHandler contract.
