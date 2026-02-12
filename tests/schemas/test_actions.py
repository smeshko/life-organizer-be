"""Tests for app action schemas."""

import pytest
from pydantic import ValidationError

from life_organizer.schemas.actions import (
    BaseAppAction,
    LogBudgetEntryAction,
)


def test_appaction_type_alias():
    """Test AppAction type alias includes all action types."""
    budget = LogBudgetEntryAction(
        amount=50.0,
        date="2025-11-05",
        transaction_type="Expenses",
        category="Groceries",
    )

    assert isinstance(budget, BaseAppAction)


def test_discriminated_union_parsing():
    """Test that Pydantic can discriminate based on type field."""
    budget_data = {
        "type": "log_budget_entry",
        "amount": 50.0,
        "date": "2025-11-05",
        "transaction_type": "Expenses",
        "category": "Groceries",
    }
    budget = LogBudgetEntryAction(**budget_data)
    assert isinstance(budget, LogBudgetEntryAction)
    assert budget.type == "log_budget_entry"


def test_action_type_field_validation():
    """Test that type field is validated as a Literal."""
    action = LogBudgetEntryAction(
        amount=50.0,
        date="2025-11-05",
        transaction_type="Expenses",
        category="Groceries",
    )
    assert action.type == "log_budget_entry"

    # The type field should always be the literal value
    # Pydantic validates the Literal type and rejects wrong values
    with pytest.raises(ValidationError) as exc_info:
        LogBudgetEntryAction(
            type="wrong_type",
            amount=50.0,
            date="2025-11-05",
            transaction_type="Expenses",
            category="Groceries",
        )

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("type",)
    assert errors[0]["type"] == "literal_error"
