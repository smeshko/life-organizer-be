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
                return classified_input.category == Category.BUDGET

            def requires_app_action(self) -> bool:
                return False  # Backend handles entirely via Google Sheets

            async def execute(self, classified_input: ClassifiedInput) -> ActionResult:
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
    async def execute(self, classified_input: ClassifiedInput) -> ActionResult:
        """Process the classified input and return the result.

        Args:
            classified_input: The classified user input with extracted data

        Returns:
            ActionResult indicating what happened and any required follow-up actions
        """
        pass
