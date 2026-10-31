"""Tests for response schemas."""

import datetime

import pytest
from pydantic import ValidationError

from life_organizer.schemas.budget import TransactionItem
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

    def test_new_fields_default_empty(self):
        """transactions and image_index default to [] and None."""
        result = ProcessingResponse(
            success=True,
            action_type=ActionType.BACKEND_HANDLED,
            message="Done",
        )

        assert result.transactions == []
        assert result.image_index is None
        dumped = result.model_dump(mode="json")
        assert dumped["success"] is True
        assert dumped["action_type"] == "backend_handled"
        assert dumped["message"] == "Done"
        assert dumped["transactions"] == []
        assert dumped["image_index"] is None

    def test_transactions_roundtrip(self):
        """A TransactionItem survives a JSON round trip."""
        item = TransactionItem(
            id=7,
            amount=12.5,
            currency="USD",
            amount_eur=11.0,
            date=datetime.date(2026, 3, 1),
            transaction_type="Expenses",
            category="Food",
            details="Cafe",
        )
        result = ProcessingResponse(
            success=True,
            action_type=ActionType.BACKEND_HANDLED,
            message="Done",
            transactions=[item],
            image_index=2,
        )

        reconstructed = ProcessingResponse.model_validate_json(result.model_dump_json())
        assert reconstructed.transactions == [item]
        assert reconstructed.image_index == 2

    def test_invalid_transaction_rejected(self):
        """A transactions entry without an id is invalid."""
        with pytest.raises(ValidationError):
            ProcessingResponse.model_validate(
                {
                    "success": True,
                    "action_type": "backend_handled",
                    "message": "Done",
                    "transactions": [
                        {
                            "amount": 1.0,
                            "currency": "EUR",
                            "amount_eur": 1.0,
                            "date": "2026-03-01",
                            "transaction_type": "Expenses",
                            "category": "Food",
                            "details": None,
                        }
                    ],
                }
            )
