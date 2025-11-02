"""Tests for response schemas."""

from datetime import UTC, datetime

import pytest

from life_organizer.schemas.actions import (
    AddToShoppingListAction,
    CreateCalendarEventAction,
    CreateReminderAction,
)
from life_organizer.schemas.enums import ActionType
from life_organizer.schemas.responses import ActionResult, ConfirmationData


class TestConfirmationData:
    """Tests for ConfirmationData model."""

    def test_valid_confirmation_data(self):
        """Test creating valid confirmation data."""
        data = ConfirmationData(
            question="What type of expense is this?",
            options=["Food", "Transportation", "Entertainment"],
            original_classification="expense",
            confidence=0.65,
        )
        assert data.question == "What type of expense is this?"
        assert len(data.options) == 3
        assert data.confidence == 0.65

    def test_confidence_validation_range(self):
        """Test that confidence must be between 0.0 and 1.0."""
        # Valid confidence values
        ConfirmationData(
            question="Test?",
            options=["Yes", "No"],
            original_classification="test",
            confidence=0.0,
        )
        ConfirmationData(
            question="Test?",
            options=["Yes", "No"],
            original_classification="test",
            confidence=1.0,
        )

        # Invalid confidence values
        with pytest.raises(ValueError):
            ConfirmationData(
                question="Test?",
                options=["Yes", "No"],
                original_classification="test",
                confidence=1.5,
            )

        with pytest.raises(ValueError):
            ConfirmationData(
                question="Test?",
                options=["Yes", "No"],
                original_classification="test",
                confidence=-0.1,
            )

    def test_options_minimum_length(self):
        """Test that options must have at least 2 items."""
        # Valid: 2 options
        ConfirmationData(
            question="Test?",
            options=["Yes", "No"],
            original_classification="test",
            confidence=0.5,
        )

        # Invalid: 1 option
        with pytest.raises(ValueError):
            ConfirmationData(
                question="Test?",
                options=["Yes"],
                original_classification="test",
                confidence=0.5,
            )


class TestActionResult:
    """Tests for ActionResult model."""

    def test_backend_handled_response(self):
        """Test backend_handled response with no optional fields."""
        result = ActionResult(
            success=True,
            action_type=ActionType.BACKEND_HANDLED,
            message="Expense logged successfully",
        )
        assert result.success is True
        assert result.action_type == ActionType.BACKEND_HANDLED
        assert result.message == "Expense logged successfully"
        assert result.app_action is None
        assert result.confirmation is None

    def test_app_action_required_with_reminder(self):
        """Test app_action_required response with CreateReminderAction."""
        reminder_action = CreateReminderAction(
            title="Buy milk",
            due_date=datetime(2025, 11, 2, 10, 0, tzinfo=UTC),
            list_id="groceries",
            notes="Don't forget whole milk",
        )

        result = ActionResult(
            success=True,
            action_type=ActionType.APP_ACTION_REQUIRED,
            message="Reminder ready to create",
            app_action=reminder_action,
        )

        assert result.success is True
        assert result.action_type == ActionType.APP_ACTION_REQUIRED
        assert result.app_action is not None
        assert isinstance(result.app_action, CreateReminderAction)
        assert result.app_action.title == "Buy milk"
        assert result.app_action.type == "create_reminder"
        assert result.confirmation is None

    def test_app_action_required_with_shopping_list(self):
        """Test app_action_required response with AddToShoppingListAction."""
        shopping_action = AddToShoppingListAction(
            item="Eggs",
            quantity="1 dozen",
            list_id="shopping_list",
            notes="Organic if possible",
        )

        result = ActionResult(
            success=True,
            action_type=ActionType.APP_ACTION_REQUIRED,
            message="Shopping item ready to add",
            app_action=shopping_action,
        )

        assert result.success is True
        assert result.app_action is not None
        assert isinstance(result.app_action, AddToShoppingListAction)
        assert result.app_action.item == "Eggs"
        assert result.app_action.type == "add_to_shopping_list"

    def test_app_action_required_with_calendar_event(self):
        """Test app_action_required response with CreateCalendarEventAction."""
        calendar_action = CreateCalendarEventAction(
            title="Team Meeting",
            start_time=datetime(2025, 11, 2, 14, 0, tzinfo=UTC),
            end_time=datetime(2025, 11, 2, 15, 0, tzinfo=UTC),
            location="Conference Room A",
            notes="Quarterly planning",
        )

        result = ActionResult(
            success=True,
            action_type=ActionType.APP_ACTION_REQUIRED,
            message="Calendar event ready to create",
            app_action=calendar_action,
        )

        assert result.success is True
        assert result.app_action is not None
        assert isinstance(result.app_action, CreateCalendarEventAction)
        assert result.app_action.title == "Team Meeting"
        assert result.app_action.type == "create_calendar_event"

    def test_confirmation_needed_response(self):
        """Test confirmation_needed response with confirmation data."""
        confirmation = ConfirmationData(
            question="Is this an expense or a shopping list item?",
            options=["Expense", "Shopping List"],
            original_classification="expense",
            confidence=0.55,
        )

        result = ActionResult(
            success=True,
            action_type=ActionType.CONFIRMATION_NEEDED,
            message="Need clarification",
            confirmation=confirmation,
        )

        assert result.success is True
        assert result.action_type == ActionType.CONFIRMATION_NEEDED
        assert result.confirmation is not None
        assert result.confirmation.question.startswith("Is this")
        assert len(result.confirmation.options) == 2
        assert result.app_action is None

    def test_json_serialization_with_discriminated_union(self):
        """Test JSON serialization preserves discriminated union type field."""
        reminder_action = CreateReminderAction(
            title="Call dentist",
            due_date=datetime(2025, 11, 5, 9, 0, tzinfo=UTC),
        )

        result = ActionResult(
            success=True,
            action_type=ActionType.APP_ACTION_REQUIRED,
            message="Reminder created",
            app_action=reminder_action,
        )

        json_data = result.model_dump()
        assert json_data["app_action"]["type"] == "create_reminder"
        assert json_data["app_action"]["title"] == "Call dentist"

        # Test deserialization
        json_str = result.model_dump_json()
        reconstructed = ActionResult.model_validate_json(json_str)
        assert isinstance(reconstructed.app_action, CreateReminderAction)
        assert reconstructed.app_action.title == "Call dentist"

    def test_optional_fields_are_truly_optional(self):
        """Test that app_action and confirmation are optional."""
        # Can create ActionResult without optional fields
        result = ActionResult(
            success=True,
            action_type=ActionType.BACKEND_HANDLED,
            message="Done",
        )
        assert result.app_action is None
        assert result.confirmation is None

        # Verify it serializes correctly
        json_data = result.model_dump()
        assert "app_action" in json_data
        assert json_data["app_action"] is None

    def test_failed_action_result(self):
        """Test ActionResult with success=False."""
        result = ActionResult(
            success=False,
            action_type=ActionType.BACKEND_HANDLED,
            message="Failed to log expense: database error",
        )
        assert result.success is False
        assert result.message.startswith("Failed")
