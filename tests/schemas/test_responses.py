"""Tests for response schemas."""

from life_organizer.schemas.enums import ActionType
from life_organizer.schemas.responses import ProcessingResponse


class TestProcessingResponse:
    """Tests for ProcessingResponse model."""

    def test_backend_handled_response(self):
        """Test backend_handled response."""
        result = ProcessingResponse(
            success=True,
            action_type=ActionType.BACKEND_HANDLED,
            message="Expense logged successfully",
        )
        assert result.success is True
        assert result.action_type == ActionType.BACKEND_HANDLED
        assert result.message == "Expense logged successfully"

    def test_optional_fields_are_truly_optional(self):
        """Test ProcessingResponse only requires success, action_type, message."""
        result = ProcessingResponse(
            success=True,
            action_type=ActionType.BACKEND_HANDLED,
            message="Done",
        )

        json_data = result.model_dump()
        assert json_data["success"] is True
        assert json_data["action_type"] == "backend_handled"
        assert json_data["message"] == "Done"

    def test_failed_action_result(self):
        """Test ProcessingResponse with success=False."""
        result = ProcessingResponse(
            success=False,
            action_type=ActionType.BACKEND_HANDLED,
            message="Failed to log expense: database error",
        )
        assert result.success is False
        assert result.message.startswith("Failed")

    def test_json_serialization_roundtrip(self):
        """Test JSON serialization and deserialization."""
        result = ProcessingResponse(
            success=True,
            action_type=ActionType.BACKEND_HANDLED,
            message="Budget entry logged",
        )

        json_str = result.model_dump_json()
        reconstructed = ProcessingResponse.model_validate_json(json_str)
        assert reconstructed.success is True
        assert reconstructed.action_type == ActionType.BACKEND_HANDLED
        assert reconstructed.message == "Budget entry logged"
