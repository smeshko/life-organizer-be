"""Dummy handler for testing the registry system."""

from life_organizer.handlers.base import BaseHandler
from life_organizer.schemas.classification import ClassifiedInput
from life_organizer.schemas.enums import ActionType, Category
from life_organizer.schemas.responses import ActionResult


class DummyHandler(BaseHandler):
    """Test handler that handles UNKNOWN category."""

    def can_handle(self, classified_input: ClassifiedInput) -> bool:
        """Handle UNKNOWN category inputs."""
        return classified_input.category == Category.UNKNOWN

    def requires_app_action(self) -> bool:
        """This handler is backend-only."""
        return False

    def execute(self, classified_input: ClassifiedInput) -> ActionResult:
        """Execute the dummy handler."""
        return ActionResult(
            success=True,
            action_type=ActionType.BACKEND_HANDLED,
            message="Handled by dummy handler",
        )


class ExpenseDummyHandler(BaseHandler):
    """Test handler that handles EXPENSE category."""

    def can_handle(self, classified_input: ClassifiedInput) -> bool:
        """Handle EXPENSE category inputs."""
        return classified_input.category == Category.EXPENSE

    def requires_app_action(self) -> bool:
        """This handler is backend-only."""
        return False

    def execute(self, classified_input: ClassifiedInput) -> ActionResult:
        """Execute the expense dummy handler."""
        return ActionResult(
            success=True,
            action_type=ActionType.BACKEND_HANDLED,
            message="Expense logged by dummy handler",
        )
