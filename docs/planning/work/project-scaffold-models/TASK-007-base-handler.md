## TASK-007: Implement BaseHandler Abstract Class

---
**Status:** OPEN
**Branch:** feature/project-scaffold-models
**Type:** IMPLEMENTATION
**Phase:** 2
**Depends On:** TASK-004, TASK-005 (needs ActionResult and ClassifiedInput schemas)

---

### Overview

Create the BaseHandler abstract base class that defines the contract all handlers must implement. This uses Python's abc module to enforce that concrete handlers implement can_handle(), requires_app_action(), and execute() methods.

The abstract class provides compile-time (mypy) and runtime (instantiation) enforcement of the handler contract.

### Files Modified

- `src/life_organizer/handlers/base.py`
- `tests/handlers/test_base.py`

### Implementation Steps

- [ ] Create `src/life_organizer/handlers/base.py`
- [ ] Import ABC, abstractmethod from abc module
- [ ] Import ClassifiedInput and ActionResult schemas
- [ ] Define BaseHandler class inheriting from ABC
- [ ] Add abstract method can_handle(classified_input) -> bool
- [ ] Add abstract method requires_app_action() -> bool
- [ ] Add abstract method execute(classified_input) -> ActionResult
- [ ] Add comprehensive docstrings explaining the handler contract
- [ ] Create `tests/handlers/test_base.py`
- [ ] Write test verifying BaseHandler cannot be instantiated directly
- [ ] Write test creating a concrete handler implementation
- [ ] Write test verifying missing methods cause TypeError

### Code Example

**File: `src/life_organizer/handlers/base.py`**

```python
"""Base handler class defining the handler contract."""

from abc import ABC, abstractmethod

from life_organizer.schemas.classification import ClassifiedInput
from life_organizer.schemas.responses import ActionResult


class BaseHandler(ABC):
    """Abstract base class for all handlers in the plugin architecture.

    Handlers are responsible for processing classified user input and returning
    appropriate actions. Each handler decides if it can handle a particular input
    category and whether it processes the action itself or delegates to the iOS app.

    Concrete handlers must implement three methods:
    - can_handle(): Determine if this handler can process the input
    - requires_app_action(): Whether this handler needs iOS app involvement
    - execute(): Process the input and return a result

    Example:
        ```python
        class ExpenseHandler(BaseHandler):
            def can_handle(self, classified_input: ClassifiedInput) -> bool:
                return classified_input.category == Category.EXPENSE

            def requires_app_action(self) -> bool:
                return False  # Backend handles entirely via Google Sheets

            def execute(self, classified_input: ClassifiedInput) -> ActionResult:
                # Log to Google Sheets
                return ActionResult(
                    success=True,
                    action_type=ActionType.BACKEND_HANDLED,
                    message="Logged expense"
                )
        ```
    """

    @abstractmethod
    def can_handle(self, classified_input: ClassifiedInput) -> bool:
        """Determine if this handler can process the classified input.

        Args:
            classified_input: The classified user input

        Returns:
            True if this handler should process this input, False otherwise
        """
        pass

    @abstractmethod
    def requires_app_action(self) -> bool:
        """Determine if this handler requires iOS app involvement.

        Returns:
            True if handler returns app_action_required, False if backend_handled
        """
        pass

    @abstractmethod
    def execute(self, classified_input: ClassifiedInput) -> ActionResult:
        """Process the classified input and return the result.

        Args:
            classified_input: The classified user input with extracted data

        Returns:
            ActionResult indicating what happened and any required follow-up actions
        """
        pass
```

**Reference: Abstract base class pattern from Python stdlib**

Python's abc module provides the @abstractmethod decorator that prevents instantiation of classes that don't implement all abstract methods. This is enforced at both runtime and by mypy.

### Success Criteria

- [ ] Build succeeds: `make lint`
- [ ] All tests pass: `pytest tests/handlers/test_base.py`
- [ ] mypy type checking passes
- [ ] Cannot instantiate BaseHandler directly (raises TypeError)
- [ ] Concrete handlers with missing methods raise TypeError
- [ ] Method signatures enforce correct types (ClassifiedInput -> ActionResult)

### Verification Commands

```bash
# Run tests
pytest tests/handlers/test_base.py -v

# Type checking
mypy src/life_organizer/handlers/base.py

# Verify abstract enforcement
python -c "
from life_organizer.handlers.base import BaseHandler
try:
    handler = BaseHandler()
    print('ERROR: Should not be able to instantiate')
except TypeError as e:
    print('SUCCESS: Abstract class enforcement works')
"
```

### Notes

The abstract class contract ensures that future handler implementations cannot forget to implement required methods. This prevents runtime errors and provides clear documentation of what handlers must do.
