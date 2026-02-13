"""Tests for request schemas."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from life_organizer.schemas.requests import ProcessInputRequest


def test_valid_request():
    """Test ProcessInputRequest with valid data."""
    request = ProcessInputRequest(
        user_id="family_member_123",
        input="Spent 45 euros at restaurant",
        timestamp=datetime(2025, 11, 1, 12, 30, 0),
    )

    assert request.user_id == "family_member_123"
    assert request.input == "Spent 45 euros at restaurant"
    assert request.timestamp == datetime(2025, 11, 1, 12, 30, 0)


def test_request_serialization():
    """Test ProcessInputRequest JSON serialization."""
    request = ProcessInputRequest(
        user_id="test_user",
        input="Buy milk",
        timestamp=datetime(2025, 11, 1, 12, 30, 0),
    )

    json_data = request.model_dump_json()
    assert "test_user" in json_data
    assert "Buy milk" in json_data
    # Pydantic serializes datetime to ISO 8601 format
    assert "2025-11-01T12:30:00" in json_data


def test_request_deserialization():
    """Test ProcessInputRequest from JSON data."""
    data = {
        "user_id": "test_user",
        "input": "Buy milk",
        "timestamp": "2025-11-01T12:30:00",
    }

    request = ProcessInputRequest(**data)
    assert request.user_id == "test_user"
    assert request.input == "Buy milk"
    assert request.timestamp == datetime(2025, 11, 1, 12, 30, 0)


def test_missing_user_id():
    """Test validation error when user_id is missing."""
    with pytest.raises(ValidationError) as exc_info:
        ProcessInputRequest(input="Buy milk", timestamp=datetime(2025, 11, 1, 12, 30, 0))

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("user_id",)
    assert errors[0]["type"] == "missing"


def test_missing_input():
    """Test validation error when input is missing."""
    with pytest.raises(ValidationError) as exc_info:
        ProcessInputRequest(user_id="test_user", timestamp=datetime(2025, 11, 1, 12, 30, 0))

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("input",)
    assert errors[0]["type"] == "missing"


def test_missing_timestamp():
    """Test validation error when timestamp is missing."""
    with pytest.raises(ValidationError) as exc_info:
        ProcessInputRequest(user_id="test_user", input="Buy milk")

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("timestamp",)
    assert errors[0]["type"] == "missing"


def test_empty_user_id():
    """Test validation error for empty user_id (min_length=1)."""
    with pytest.raises(ValidationError) as exc_info:
        ProcessInputRequest(
            user_id="", input="Buy milk", timestamp=datetime(2025, 11, 1, 12, 30, 0)
        )

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("user_id",)
    assert "at least 1 character" in str(errors[0]["msg"]).lower()


def test_empty_input():
    """Test validation error for empty input (min_length=1)."""
    with pytest.raises(ValidationError) as exc_info:
        ProcessInputRequest(
            user_id="test_user", input="", timestamp=datetime(2025, 11, 1, 12, 30, 0)
        )

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("input",)
    assert "at least 1 character" in str(errors[0]["msg"]).lower()


def test_invalid_timestamp_format():
    """Test validation error for invalid timestamp format."""
    with pytest.raises(ValidationError) as exc_info:
        ProcessInputRequest(user_id="test_user", input="Buy milk", timestamp="not-a-valid-date")

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("timestamp",)
    # Pydantic v2 uses different error types for datetime parsing
    assert errors[0]["type"] in ["datetime_from_date_parsing", "datetime_parsing"]


def test_classify_request_rejects_reminder_category():
    """Test ClassifyRequest rejects deprecated 'reminder' category."""
    from life_organizer.schemas.requests import ClassifyRequest

    with pytest.raises(ValidationError) as exc_info:
        ClassifyRequest(
            input="Call the dentist",
            category="reminder",
        )

    errors = exc_info.value.errors()
    assert len(errors) >= 1
    assert any(error["loc"] == ("category",) for error in errors)


def test_whitespace_only_input():
    """Test validation error for whitespace-only input."""
    # Note: min_length=1 allows whitespace, but we'll test it anyway
    # to document the current behavior
    request = ProcessInputRequest(
        user_id="test_user", input=" ", timestamp=datetime(2025, 11, 1, 12, 30, 0)
    )
    assert request.input == " "


def test_whitespace_only_user_id():
    """Test validation error for whitespace-only user_id."""
    # Note: min_length=1 allows whitespace, but we'll test it anyway
    # to document the current behavior
    request = ProcessInputRequest(
        user_id=" ", input="Buy milk", timestamp=datetime(2025, 11, 1, 12, 30, 0)
    )
    assert request.user_id == " "
