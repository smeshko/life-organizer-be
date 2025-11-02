"""Tests for BaseHandler abstract class."""

import pytest

from life_organizer.handlers.base import BaseHandler
from life_organizer.schemas.classification import ClassifiedInput
from life_organizer.schemas.enums import ActionType, Category
from life_organizer.schemas.responses import ActionResult


class TestBaseHandlerAbstraction:
    """Tests for BaseHandler abstract class enforcement."""

    def test_cannot_instantiate_base_handler_directly(self):
        """Test that BaseHandler cannot be instantiated without implementing abstract methods."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseHandler()  # type: ignore

    def test_concrete_handler_with_all_methods_works(self):
        """Test that a concrete handler implementing all methods can be instantiated."""

        class ConcreteHandler(BaseHandler):
            def can_handle(self, classified_input: ClassifiedInput) -> bool:
                return True

            def requires_app_action(self) -> bool:
                return False

            def execute(self, classified_input: ClassifiedInput) -> ActionResult:
                return ActionResult(
                    success=True,
                    action_type=ActionType.BACKEND_HANDLED,
                    message="Test handler",
                )

        # Should not raise
        handler = ConcreteHandler()
        assert isinstance(handler, BaseHandler)

    def test_missing_can_handle_raises_error(self):
        """Test that missing can_handle() method prevents instantiation."""

        class IncompleteHandler(BaseHandler):
            def requires_app_action(self) -> bool:
                return False

            def execute(self, classified_input: ClassifiedInput) -> ActionResult:
                return ActionResult(
                    success=True,
                    action_type=ActionType.BACKEND_HANDLED,
                    message="Test",
                )

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteHandler()  # type: ignore

    def test_missing_requires_app_action_raises_error(self):
        """Test that missing requires_app_action() method prevents instantiation."""

        class IncompleteHandler(BaseHandler):
            def can_handle(self, classified_input: ClassifiedInput) -> bool:
                return True

            def execute(self, classified_input: ClassifiedInput) -> ActionResult:
                return ActionResult(
                    success=True,
                    action_type=ActionType.BACKEND_HANDLED,
                    message="Test",
                )

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteHandler()  # type: ignore

    def test_missing_execute_raises_error(self):
        """Test that missing execute() method prevents instantiation."""

        class IncompleteHandler(BaseHandler):
            def can_handle(self, classified_input: ClassifiedInput) -> bool:
                return True

            def requires_app_action(self) -> bool:
                return False

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteHandler()  # type: ignore


class TestConcreteHandlerImplementation:
    """Tests for a working concrete handler implementation."""

    def test_concrete_handler_can_handle(self):
        """Test that concrete handler can implement can_handle logic."""

        class ExpenseHandler(BaseHandler):
            def can_handle(self, classified_input: ClassifiedInput) -> bool:
                return classified_input.category == Category.EXPENSE

            def requires_app_action(self) -> bool:
                return False

            def execute(self, classified_input: ClassifiedInput) -> ActionResult:
                return ActionResult(
                    success=True,
                    action_type=ActionType.BACKEND_HANDLED,
                    message="Expense logged",
                )

        handler = ExpenseHandler()

        # Should handle expense category
        expense_input = ClassifiedInput(
            category=Category.EXPENSE,
            confidence=0.9,
            raw_input="Spent $20 on lunch",
        )
        assert handler.can_handle(expense_input) is True

        # Should not handle other categories
        shopping_input = ClassifiedInput(
            category=Category.SHOPPING,
            confidence=0.9,
            raw_input="Buy milk",
        )
        assert handler.can_handle(shopping_input) is False

    def test_concrete_handler_execute(self):
        """Test that concrete handler can execute and return ActionResult."""

        class TestHandler(BaseHandler):
            def can_handle(self, classified_input: ClassifiedInput) -> bool:
                return True

            def requires_app_action(self) -> bool:
                return False

            def execute(self, classified_input: ClassifiedInput) -> ActionResult:
                return ActionResult(
                    success=True,
                    action_type=ActionType.BACKEND_HANDLED,
                    message=f"Processed: {classified_input.raw_input}",
                )

        handler = TestHandler()
        classified = ClassifiedInput(
            category=Category.EXPENSE,
            confidence=0.8,
            raw_input="Test input",
        )

        result = handler.execute(classified)

        assert isinstance(result, ActionResult)
        assert result.success is True
        assert result.action_type == ActionType.BACKEND_HANDLED
        assert "Test input" in result.message

    def test_concrete_handler_requires_app_action(self):
        """Test that handlers can specify if they need app actions."""

        class BackendHandler(BaseHandler):
            def can_handle(self, classified_input: ClassifiedInput) -> bool:
                return True

            def requires_app_action(self) -> bool:
                return False

            def execute(self, classified_input: ClassifiedInput) -> ActionResult:
                return ActionResult(
                    success=True,
                    action_type=ActionType.BACKEND_HANDLED,
                    message="Backend handled",
                )

        class AppActionHandler(BaseHandler):
            def can_handle(self, classified_input: ClassifiedInput) -> bool:
                return True

            def requires_app_action(self) -> bool:
                return True

            def execute(self, classified_input: ClassifiedInput) -> ActionResult:
                return ActionResult(
                    success=True,
                    action_type=ActionType.APP_ACTION_REQUIRED,
                    message="App action required",
                )

        backend_handler = BackendHandler()
        app_handler = AppActionHandler()

        assert backend_handler.requires_app_action() is False
        assert app_handler.requires_app_action() is True
