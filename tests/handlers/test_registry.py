"""Tests for handler registry system."""

from life_organizer.handlers import HANDLERS, get_handler
from life_organizer.schemas.classification import ClassifiedInput
from life_organizer.schemas.enums import Category
from tests.handlers.dummy_handler import DummyHandler, ExpenseDummyHandler


class TestHandlerRegistry:
    """Tests for handler registry and lookup."""

    def test_get_handler_returns_none_when_no_handlers_registered(self):
        """Test that get_handler returns None when registry is empty."""
        # Save original handlers
        original_handlers = HANDLERS.copy()
        HANDLERS.clear()

        try:
            classified = ClassifiedInput(
                category=Category.EXPENSE,
                confidence=0.9,
                raw_input="Spent $20 on lunch",
            )

            result = get_handler(classified)
            assert result is None
        finally:
            # Restore original handlers
            HANDLERS.clear()
            HANDLERS.extend(original_handlers)

    def test_get_handler_finds_matching_handler(self):
        """Test that get_handler returns the correct handler for matching input."""
        # Save original handlers
        original_handlers = HANDLERS.copy()
        HANDLERS.clear()

        try:
            # Register dummy handler
            dummy = DummyHandler()
            HANDLERS.append(dummy)

            # Create input that matches DummyHandler (UNKNOWN category)
            classified = ClassifiedInput(
                category=Category.UNKNOWN,
                confidence=0.5,
                raw_input="Some random text",
            )

            result = get_handler(classified)
            assert result is not None
            assert result is dummy
            assert isinstance(result, DummyHandler)
        finally:
            # Restore original handlers
            HANDLERS.clear()
            HANDLERS.extend(original_handlers)

    def test_get_handler_returns_none_when_no_match(self):
        """Test that get_handler returns None when no handler matches."""
        # Save original handlers
        original_handlers = HANDLERS.copy()
        HANDLERS.clear()

        try:
            # Register handler that only handles UNKNOWN
            HANDLERS.append(DummyHandler())

            # Create input that doesn't match (EXPENSE category)
            classified = ClassifiedInput(
                category=Category.EXPENSE,
                confidence=0.9,
                raw_input="Spent $20",
            )

            result = get_handler(classified)
            assert result is None
        finally:
            # Restore original handlers
            HANDLERS.clear()
            HANDLERS.extend(original_handlers)

    def test_handler_precedence_first_match_wins(self):
        """Test that the first matching handler in the list is selected."""
        # Save original handlers
        original_handlers = HANDLERS.copy()
        HANDLERS.clear()

        try:
            # Register two handlers that both match EXPENSE
            first_handler = ExpenseDummyHandler()
            second_handler = ExpenseDummyHandler()
            HANDLERS.append(first_handler)
            HANDLERS.append(second_handler)

            # Create EXPENSE input
            classified = ClassifiedInput(
                category=Category.EXPENSE,
                confidence=0.9,
                raw_input="Spent $20",
            )

            result = get_handler(classified)
            assert result is not None
            # Should be the FIRST handler, not the second
            assert result is first_handler
            assert result is not second_handler
        finally:
            # Restore original handlers
            HANDLERS.clear()
            HANDLERS.extend(original_handlers)

    def test_multiple_handlers_with_different_categories(self):
        """Test registry with multiple handlers for different categories."""
        # Save original handlers
        original_handlers = HANDLERS.copy()
        HANDLERS.clear()

        try:
            # Register handlers for different categories
            unknown_handler = DummyHandler()
            expense_handler = ExpenseDummyHandler()
            HANDLERS.append(unknown_handler)
            HANDLERS.append(expense_handler)

            # Test UNKNOWN category
            unknown_input = ClassifiedInput(
                category=Category.UNKNOWN,
                confidence=0.5,
                raw_input="Random text",
            )
            result = get_handler(unknown_input)
            assert result is unknown_handler

            # Test EXPENSE category
            expense_input = ClassifiedInput(
                category=Category.EXPENSE,
                confidence=0.9,
                raw_input="Spent $20",
            )
            result = get_handler(expense_input)
            assert result is expense_handler

            # Test category with no handler (SHOPPING)
            shopping_input = ClassifiedInput(
                category=Category.SHOPPING,
                confidence=0.8,
                raw_input="Buy milk",
            )
            result = get_handler(shopping_input)
            assert result is None
        finally:
            # Restore original handlers
            HANDLERS.clear()
            HANDLERS.extend(original_handlers)
