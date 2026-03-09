"""Tests for enum types."""

from life_organizer.schemas.enums import ActionType, Category


def test_action_type_values():
    """Test ActionType enum has correct string values."""
    assert ActionType.BACKEND_HANDLED == "backend_handled"


def test_action_type_string_type():
    """Test ActionType values are strings (StrEnum)."""
    assert isinstance(ActionType.BACKEND_HANDLED, str)


def test_category_values():
    """Test Category enum has correct string values."""
    assert Category.BUDGET == "budget"
    assert Category.UNKNOWN == "unknown"


def test_category_string_type():
    """Test Category values are strings (StrEnum)."""
    assert isinstance(Category.BUDGET, str)
    assert isinstance(Category.UNKNOWN, str)


def test_action_type_comparison():
    """Test ActionType enum comparison works correctly."""
    action1 = ActionType.BACKEND_HANDLED
    action2 = ActionType.BACKEND_HANDLED

    assert action1 == action2
    assert action1 == "backend_handled"  # StrEnum compares with strings


def test_category_comparison():
    """Test Category enum comparison works correctly."""
    cat1 = Category.BUDGET
    cat2 = Category.BUDGET
    cat3 = Category.UNKNOWN

    assert cat1 == cat2
    assert cat1 != cat3
    assert cat1 == "budget"  # StrEnum compares with strings


def test_category_has_exactly_two_members():
    """Test Category enum contains exactly BUDGET and UNKNOWN."""
    expected_members = {"BUDGET", "UNKNOWN"}
    actual_members = {member.name for member in Category}
    assert actual_members == expected_members
    assert len(Category) == 2


def test_enum_in_list():
    """Test enums work correctly in collections."""
    valid_categories = [Category.BUDGET]
    assert Category.BUDGET in valid_categories
    assert Category.UNKNOWN not in valid_categories
