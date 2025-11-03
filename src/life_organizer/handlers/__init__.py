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
from life_organizer.handlers.budget_entry import BudgetEntryHandler
from life_organizer.schemas.classification import ClassifiedInput

# Handler registry - add concrete handlers here as they're implemented
# Order matters: first matching handler is selected
HANDLERS: list[BaseHandler] = [
    BudgetEntryHandler(),  # Budget entries (expenses/income/savings)
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


__all__ = ["HANDLERS", "BaseHandler", "BudgetEntryHandler", "get_handler"]
