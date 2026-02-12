"""Tests for response schemas."""

from life_organizer.schemas.actions import LogBudgetEntryAction
from life_organizer.schemas.enums import ActionType
from life_organizer.schemas.responses import ProcessingResponse


class TestProcessingResponse:
    """Tests for ProcessingResponse model."""

    def test_backend_handled_response(self):
        """Test backend_handled response with no optional fields."""
        result = ProcessingResponse(
            success=True,
            action_type=ActionType.BACKEND_HANDLED,
            message="Expense logged successfully",
        )
        assert result.success is True
        assert result.action_type == ActionType.BACKEND_HANDLED
        assert result.message == "Expense logged successfully"
        assert result.app_action is None

    def test_app_action_required_with_budget_entry(self):
        """Test app_action_required response with LogBudgetEntryAction."""
        budget_action = LogBudgetEntryAction(
            amount=50.0,
            date="2025-11-05",
            transaction_type="Expenses",
            category="Groceries",
            details="billa",
        )

        result = ProcessingResponse(
            success=True,
            action_type=ActionType.APP_ACTION_REQUIRED,
            message="Budget entry ready to log",
            app_action=budget_action,
        )

        assert result.success is True
        assert result.app_action is not None
        assert isinstance(result.app_action, LogBudgetEntryAction)
        assert result.app_action.amount == 50.0
        assert result.app_action.type == "log_budget_entry"

    def test_json_serialization_with_budget_action(self):
        """Test JSON serialization preserves action type field."""
        budget_action = LogBudgetEntryAction(
            amount=50.0,
            date="2025-11-05",
            transaction_type="Expenses",
            category="Groceries",
        )

        result = ProcessingResponse(
            success=True,
            action_type=ActionType.APP_ACTION_REQUIRED,
            message="Budget entry ready",
            app_action=budget_action,
        )

        json_data = result.model_dump()
        assert json_data["app_action"]["type"] == "log_budget_entry"
        assert json_data["app_action"]["amount"] == 50.0

        # Test deserialization
        json_str = result.model_dump_json()
        reconstructed = ProcessingResponse.model_validate_json(json_str)
        assert isinstance(reconstructed.app_action, LogBudgetEntryAction)
        assert reconstructed.app_action.amount == 50.0

    def test_optional_fields_are_truly_optional(self):
        """Test that app_action is optional."""
        # Can create ProcessingResponse without optional fields
        result = ProcessingResponse(
            success=True,
            action_type=ActionType.BACKEND_HANDLED,
            message="Done",
        )
        assert result.app_action is None

        # Verify it serializes correctly
        json_data = result.model_dump()
        assert "app_action" in json_data
        assert json_data["app_action"] is None

    def test_failed_action_result(self):
        """Test ProcessingResponse with success=False."""
        result = ProcessingResponse(
            success=False,
            action_type=ActionType.BACKEND_HANDLED,
            message="Failed to log expense: database error",
        )
        assert result.success is False
        assert result.message.startswith("Failed")
