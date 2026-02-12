"""Tests for app action schemas."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from life_organizer.schemas.actions import (
    AddToShoppingListAction,
    BaseAppAction,
    CreateCalendarEventAction,
    LogBudgetEntryAction,
)

# AddToShoppingListAction Tests


def test_add_to_shopping_list_action_minimal():
    """Test AddToShoppingListAction with only required fields."""
    action = AddToShoppingListAction(item="Milk")

    assert action.type == "add_to_shopping_list"
    assert action.item == "Milk"
    assert action.quantity is None
    assert action.list_id == "shopping_list"  # Default value
    assert action.notes is None


def test_add_to_shopping_list_action_full():
    """Test AddToShoppingListAction with all fields."""
    action = AddToShoppingListAction(
        item="Eggs",
        quantity="1 dozen",
        list_id="grocery_list",
        notes="Organic if possible",
    )

    assert action.type == "add_to_shopping_list"
    assert action.item == "Eggs"
    assert action.quantity == "1 dozen"
    assert action.list_id == "grocery_list"
    assert action.notes == "Organic if possible"


def test_add_to_shopping_list_action_empty_item():
    """Test validation error for empty shopping item."""
    with pytest.raises(ValidationError) as exc_info:
        AddToShoppingListAction(item="")

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("item",)
    assert "at least 1 character" in str(errors[0]["msg"]).lower()


def test_add_to_shopping_list_action_serialization():
    """Test AddToShoppingListAction JSON serialization."""
    action = AddToShoppingListAction(item="Bread", quantity="2 loaves")

    json_data = action.model_dump_json()
    assert "add_to_shopping_list" in json_data
    assert "Bread" in json_data
    assert "2 loaves" in json_data


def test_add_to_shopping_list_action_deserialization():
    """Test AddToShoppingListAction from JSON."""
    data = {
        "type": "add_to_shopping_list",
        "item": "Cheese",
        "quantity": "200g",
        "list_id": "weekly_shopping",
    }

    action = AddToShoppingListAction(**data)
    assert action.type == "add_to_shopping_list"
    assert action.item == "Cheese"
    assert action.quantity == "200g"
    assert action.list_id == "weekly_shopping"


# CreateCalendarEventAction Tests


def test_create_calendar_event_action_minimal():
    """Test CreateCalendarEventAction with only required fields."""
    start = datetime(2025, 11, 5, 14, 0, 0)
    end = datetime(2025, 11, 5, 15, 0, 0)
    action = CreateCalendarEventAction(title="Team sync", start_time=start, end_time=end)

    assert action.type == "create_calendar_event"
    assert action.title == "Team sync"
    assert action.start_time == start
    assert action.end_time == end
    assert action.location is None
    assert action.notes is None


def test_create_calendar_event_action_full():
    """Test CreateCalendarEventAction with all fields."""
    start = datetime(2025, 11, 5, 14, 0, 0)
    end = datetime(2025, 11, 5, 15, 0, 0)
    action = CreateCalendarEventAction(
        title="Client presentation",
        start_time=start,
        end_time=end,
        location="Conference Room A",
        notes="Bring slides and demo",
    )

    assert action.type == "create_calendar_event"
    assert action.title == "Client presentation"
    assert action.start_time == start
    assert action.end_time == end
    assert action.location == "Conference Room A"
    assert action.notes == "Bring slides and demo"


def test_create_calendar_event_action_empty_title():
    """Test validation error for empty event title."""
    with pytest.raises(ValidationError) as exc_info:
        CreateCalendarEventAction(
            title="",
            start_time=datetime(2025, 11, 5, 14, 0, 0),
            end_time=datetime(2025, 11, 5, 15, 0, 0),
        )

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("title",)
    assert "at least 1 character" in str(errors[0]["msg"]).lower()


def test_create_calendar_event_action_missing_required_fields():
    """Test validation error for missing required fields."""
    with pytest.raises(ValidationError) as exc_info:
        CreateCalendarEventAction(title="Meeting")

    errors = exc_info.value.errors()
    assert len(errors) == 2
    error_locs = {error["loc"][0] for error in errors}
    assert "start_time" in error_locs
    assert "end_time" in error_locs


def test_create_calendar_event_action_serialization():
    """Test CreateCalendarEventAction JSON serialization."""
    action = CreateCalendarEventAction(
        title="Lunch meeting",
        start_time=datetime(2025, 11, 5, 12, 0, 0),
        end_time=datetime(2025, 11, 5, 13, 0, 0),
        location="Restaurant",
    )

    json_data = action.model_dump_json()
    assert "create_calendar_event" in json_data
    assert "Lunch meeting" in json_data
    assert "2025-11-05" in json_data
    assert "Restaurant" in json_data


def test_create_calendar_event_action_deserialization():
    """Test CreateCalendarEventAction from JSON."""
    data = {
        "type": "create_calendar_event",
        "title": "Workshop",
        "start_time": "2025-11-05T09:00:00",
        "end_time": "2025-11-05T17:00:00",
        "location": "Training Center",
    }

    action = CreateCalendarEventAction(**data)
    assert action.type == "create_calendar_event"
    assert action.title == "Workshop"
    assert action.start_time == datetime(2025, 11, 5, 9, 0, 0)
    assert action.end_time == datetime(2025, 11, 5, 17, 0, 0)
    assert action.location == "Training Center"


# Discriminated Union Tests


def test_appaction_type_alias():
    """Test AppAction type alias includes all action types."""
    # This is mainly for documentation and type checking
    # The union should work with isinstance checks
    shopping = AddToShoppingListAction(item="Test")
    calendar = CreateCalendarEventAction(
        title="Test",
        start_time=datetime(2025, 11, 5, 14, 0, 0),
        end_time=datetime(2025, 11, 5, 15, 0, 0),
    )
    budget = LogBudgetEntryAction(
        amount=50.0,
        date="2025-11-05",
        transaction_type="Expenses",
        category="Groceries",
    )

    # All should be instances of BaseAppAction
    assert isinstance(shopping, BaseAppAction)
    assert isinstance(calendar, BaseAppAction)
    assert isinstance(budget, BaseAppAction)


def test_discriminated_union_parsing():
    """Test that Pydantic can discriminate based on type field."""
    # Test parsing shopping list
    shopping_data = {"type": "add_to_shopping_list", "item": "Test item"}
    shopping = AddToShoppingListAction(**shopping_data)
    assert isinstance(shopping, AddToShoppingListAction)
    assert shopping.type == "add_to_shopping_list"

    # Test parsing calendar event
    calendar_data = {
        "type": "create_calendar_event",
        "title": "Test event",
        "start_time": "2025-11-05T14:00:00",
        "end_time": "2025-11-05T15:00:00",
    }
    calendar = CreateCalendarEventAction(**calendar_data)
    assert isinstance(calendar, CreateCalendarEventAction)
    assert calendar.type == "create_calendar_event"


def test_action_type_field_validation():
    """Test that type field is validated as a Literal."""
    action = AddToShoppingListAction(item="Test")
    assert action.type == "add_to_shopping_list"

    # The type field should always be the literal value
    # Pydantic validates the Literal type and rejects wrong values
    with pytest.raises(ValidationError) as exc_info:
        AddToShoppingListAction(type="wrong_type", item="Test")

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("type",)
    assert errors[0]["type"] == "literal_error"
