"""Tests for enum types."""

from life_organizer.schemas.enums import ActionType, Category


def test_action_type_values():
    """Test ActionType enum has correct string values."""
    assert ActionType.BACKEND_HANDLED == "backend_handled"
    assert ActionType.APP_ACTION_REQUIRED == "app_action_required"


def test_action_type_string_type():
    """Test ActionType values are strings (StrEnum)."""
    assert isinstance(ActionType.BACKEND_HANDLED, str)
    assert isinstance(ActionType.APP_ACTION_REQUIRED, str)


def test_category_values():
    """Test Category enum has correct string values."""
    assert Category.BUDGET == "budget"
    assert Category.SHOPPING == "shopping"
    assert Category.CALENDAR == "calendar"
    assert Category.UNKNOWN == "unknown"


def test_category_string_type():
    """Test Category values are strings (StrEnum)."""
    assert isinstance(Category.BUDGET, str)
    assert isinstance(Category.SHOPPING, str)
    assert isinstance(Category.CALENDAR, str)
    assert isinstance(Category.UNKNOWN, str)


def test_action_type_comparison():
    """Test ActionType enum comparison works correctly."""
    action1 = ActionType.BACKEND_HANDLED
    action2 = ActionType.BACKEND_HANDLED
    action3 = ActionType.APP_ACTION_REQUIRED

    assert action1 == action2
    assert action1 != action3
    assert action1 == "backend_handled"  # StrEnum compares with strings


def test_category_comparison():
    """Test Category enum comparison works correctly."""
    cat1 = Category.BUDGET
    cat2 = Category.BUDGET
    cat3 = Category.SHOPPING

    assert cat1 == cat2
    assert cat1 != cat3
    assert cat1 == "budget"  # StrEnum compares with strings


def test_enum_in_list():
    """Test enums work correctly in collections."""
    valid_categories = [Category.BUDGET, Category.SHOPPING]
    assert Category.BUDGET in valid_categories
    assert Category.CALENDAR not in valid_categories
