"""Tests for BudgetEntryHandler."""

from datetime import datetime, timedelta

import pytest

from life_organizer.handlers.budget_entry import (
    BudgetEntryHandler,
    _classify_transaction_type,
    _convert_to_bgn,
    _extract_amount_currency,
    _extract_details,
    _parse_date,
)
from life_organizer.schemas.classification import ClassifiedInput
from life_organizer.schemas.enums import ActionType, Category


class TestBudgetEntryHandlerCommonPatterns:
    """Test common personal spending patterns."""

    @pytest.mark.asyncio
    async def test_next_clothing_purchase(self):
        """Test: spent 120eur at next"""
        classified = ClassifiedInput(
            category=Category.BUDGET,
            confidence=0.9,
            extracted_data={"amount": 120.0, "currency": "EUR"},
            raw_input="spent 120eur at next",
            classifier_source="keyword",
        )

        handler = BudgetEntryHandler()
        result = await handler.execute(classified)

        assert result.success is True
        assert result.action_type == ActionType.APP_ACTION_REQUIRED
        assert result.app_action is not None
        assert result.app_action.amount == 234.6  # 120 * 1.955
        assert result.app_action.transaction_type == "Expenses"
        assert result.app_action.category == "Clothes"
        assert result.app_action.details == "next"

    @pytest.mark.asyncio
    async def test_dm_body_care_bgn(self):
        """Test: spent 95bgn at dm"""
        classified = ClassifiedInput(
            category=Category.BUDGET,
            confidence=0.9,
            extracted_data={"amount": 95.0, "currency": "BGN"},
            raw_input="spent 95bgn at dm",
            classifier_source="keyword",
        )

        handler = BudgetEntryHandler()
        result = await handler.execute(classified)

        assert result.success is True
        assert result.app_action is not None
        assert result.app_action.amount == 95.0
        assert result.app_action.category == "Body care"
        assert result.app_action.details == "dm"

    @pytest.mark.asyncio
    async def test_billa_groceries(self):
        """Test: 120 billa"""
        classified = ClassifiedInput(
            category=Category.BUDGET,
            confidence=0.85,
            extracted_data={},
            raw_input="120 billa",
            classifier_source="keyword",
        )

        handler = BudgetEntryHandler()
        result = await handler.execute(classified)

        assert result.success is True
        assert result.app_action is not None
        assert result.app_action.amount == 120.0
        assert result.app_action.category == "Groceries"

    @pytest.mark.asyncio
    async def test_coffee_eat_out(self):
        """Test: coffee 7"""
        classified = ClassifiedInput(
            category=Category.BUDGET,
            confidence=0.8,
            extracted_data={},
            raw_input="coffee 7",
            classifier_source="keyword",
        )

        handler = BudgetEntryHandler()
        result = await handler.execute(classified)

        assert result.success is True
        assert result.app_action is not None
        assert result.app_action.amount == 7.0
        assert result.app_action.category == "Eat out"

    @pytest.mark.asyncio
    async def test_banitsa_eat_out(self):
        """Test: 7 for banitsa"""
        classified = ClassifiedInput(
            category=Category.BUDGET,
            confidence=0.8,
            extracted_data={},
            raw_input="7 for banitsa",
            classifier_source="keyword",
        )

        handler = BudgetEntryHandler()
        result = await handler.execute(classified)

        assert result.success is True
        assert result.app_action is not None
        assert result.app_action.amount == 7.0
        assert result.app_action.category == "Eat out"
        # Date should be today (not year 7!)
        today = datetime.now().strftime("%Y-%m-%d")
        assert result.app_action.date == today

    @pytest.mark.asyncio
    async def test_income_rent(self):
        """Test: received 250bgn rent"""
        classified = ClassifiedInput(
            category=Category.BUDGET,
            confidence=0.9,
            extracted_data={},
            raw_input="received 250bgn rent",
            classifier_source="keyword",
        )

        handler = BudgetEntryHandler()
        result = await handler.execute(classified)

        assert result.success is True
        assert result.app_action is not None
        assert result.app_action.amount == 250.0
        assert result.app_action.transaction_type == "Income"

    @pytest.mark.asyncio
    async def test_savings_ibkr(self):
        """Test: saved 1220 in ibkr"""
        classified = ClassifiedInput(
            category=Category.BUDGET,
            confidence=0.9,
            extracted_data={},
            raw_input="saved 1220 in ibkr",
            classifier_source="keyword",
        )

        handler = BudgetEntryHandler()
        result = await handler.execute(classified)

        assert result.success is True
        assert result.app_action is not None
        assert result.app_action.amount == 1220.0
        assert result.app_action.transaction_type == "Savings"
        assert result.app_action.category == "Savings"
        # Date should be today (not year 1220!)
        today = datetime.now().strftime("%Y-%m-%d")
        assert result.app_action.date == today


class TestEURConversion:
    """Test EUR to BGN conversion."""

    def test_eur_to_bgn_conversion(self):
        """Test: 120 EUR -> 234.6 BGN"""
        assert _convert_to_bgn(120.0, "EUR") == 234.6

    def test_bgn_passthrough(self):
        """Test: 95 BGN -> 95 BGN"""
        assert _convert_to_bgn(95.0, "BGN") == 95.0

    def test_decimal_conversion(self):
        """Test: 45.50 EUR -> 88.95 BGN"""
        assert _convert_to_bgn(45.5, "EUR") == 88.95


class TestTransactionTypeClassification:
    """Test transaction type classification."""

    def test_income_keywords(self):
        """Test income keyword detection."""
        classified = ClassifiedInput(
            category=Category.BUDGET,
            confidence=0.9,
            extracted_data={},
            raw_input="received 250bgn rent",
            classifier_source="keyword",
        )
        assert _classify_transaction_type(classified) == "Income"

    def test_savings_keywords(self):
        """Test savings keyword detection."""
        classified = ClassifiedInput(
            category=Category.BUDGET,
            confidence=0.9,
            extracted_data={},
            raw_input="saved 1220 in ibkr",
            classifier_source="keyword",
        )
        assert _classify_transaction_type(classified) == "Savings"

    def test_expense_default(self):
        """Test expense is the default."""
        classified = ClassifiedInput(
            category=Category.BUDGET,
            confidence=0.9,
            extracted_data={},
            raw_input="spent 120 at next",
            classifier_source="keyword",
        )
        assert _classify_transaction_type(classified) == "Expenses"


class TestDateParsing:
    """Test date parsing edge cases."""

    def test_yesterday(self):
        """Test: yesterday"""
        classified = ClassifiedInput(
            category=Category.BUDGET,
            confidence=0.9,
            extracted_data={},
            raw_input="spent 95 at dm yesterday",
            classifier_source="keyword",
        )
        expected = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        assert _parse_date(classified) == expected

    def test_today_default(self):
        """Test: no date mentioned defaults to today"""
        classified = ClassifiedInput(
            category=Category.BUDGET,
            confidence=0.9,
            extracted_data={},
            raw_input="spent 120eur at next",
            classifier_source="keyword",
        )
        expected = datetime.now().strftime("%Y-%m-%d")
        assert _parse_date(classified) == expected

    def test_avoids_year_7_bug(self):
        """Test: '7 for banitsa' doesn't parse as year 7"""
        classified = ClassifiedInput(
            category=Category.BUDGET,
            confidence=0.9,
            extracted_data={},
            raw_input="7 for banitsa",
            classifier_source="keyword",
        )
        result = _parse_date(classified)
        # Should be this year, not year 7
        current_year = datetime.now().year
        assert str(current_year) in result

    def test_avoids_year_1220_bug(self):
        """Test: 'saved 1220 in ibkr' doesn't parse as year 1220"""
        classified = ClassifiedInput(
            category=Category.BUDGET,
            confidence=0.9,
            extracted_data={},
            raw_input="saved 1220 in ibkr",
            classifier_source="keyword",
        )
        result = _parse_date(classified)
        # Should be this year, not year 1220
        current_year = datetime.now().year
        assert str(current_year) in result


class TestAmountExtraction:
    """Test amount and currency extraction."""

    def test_extract_from_extracted_data(self):
        """Test: amount from extracted_data"""
        classified = ClassifiedInput(
            category=Category.BUDGET,
            confidence=0.9,
            extracted_data={"amount": 120.0, "currency": "EUR"},
            raw_input="spent 120eur at next",
            classifier_source="llm",
        )
        amount, currency = _extract_amount_currency(classified)
        assert amount == 120.0
        assert currency == "EUR"

    def test_extract_from_raw_input_eur(self):
        """Test: extract from raw input with EUR"""
        classified = ClassifiedInput(
            category=Category.BUDGET,
            confidence=0.9,
            extracted_data={},
            raw_input="spent 120eur at next",
            classifier_source="keyword",
        )
        amount, currency = _extract_amount_currency(classified)
        assert amount == 120.0
        assert currency == "EUR"

    def test_extract_from_raw_input_bgn(self):
        """Test: extract from raw input with BGN"""
        classified = ClassifiedInput(
            category=Category.BUDGET,
            confidence=0.9,
            extracted_data={},
            raw_input="95bgn at dm",
            classifier_source="keyword",
        )
        amount, currency = _extract_amount_currency(classified)
        assert amount == 95.0
        assert currency == "BGN"

    def test_default_to_bgn(self):
        """Test: no currency specified defaults to BGN"""
        classified = ClassifiedInput(
            category=Category.BUDGET,
            confidence=0.9,
            extracted_data={},
            raw_input="120 billa",
            classifier_source="keyword",
        )
        amount, currency = _extract_amount_currency(classified)
        assert amount == 120.0
        assert currency == "BGN"


class TestDetailsExtraction:
    """Test merchant/details extraction."""

    def test_extract_merchant(self):
        """Test: extract merchant name"""
        classified = ClassifiedInput(
            category=Category.BUDGET,
            confidence=0.9,
            extracted_data={},
            raw_input="spent 120eur at next",
            classifier_source="keyword",
        )
        details = _extract_details(classified)
        assert details == "next"

    def test_extract_with_context(self):
        """Test: extract with context words"""
        classified = ClassifiedInput(
            category=Category.BUDGET,
            confidence=0.9,
            extracted_data={},
            raw_input="7 for banitsa",
            classifier_source="keyword",
        )
        details = _extract_details(classified)
        assert details == "banitsa"


class TestHandlerIntegration:
    """Test handler can_handle and requires_app_action."""

    def test_can_handle_expense_category(self):
        """Test: can handle EXPENSE category"""
        classified = ClassifiedInput(
            category=Category.BUDGET,
            confidence=0.9,
            extracted_data={},
            raw_input="spent 120eur at next",
            classifier_source="keyword",
        )
        handler = BudgetEntryHandler()
        assert handler.can_handle(classified) is True

    def test_cannot_handle_other_categories(self):
        """Test: cannot handle non-EXPENSE categories"""
        classified = ClassifiedInput(
            category=Category.SHOPPING,
            confidence=0.9,
            extracted_data={},
            raw_input="buy milk",
            classifier_source="keyword",
        )
        handler = BudgetEntryHandler()
        assert handler.can_handle(classified) is False

    def test_requires_app_action(self):
        """Test: always requires app action"""
        handler = BudgetEntryHandler()
        assert handler.requires_app_action() is True

    @pytest.mark.asyncio
    async def test_error_handling_invalid_amount(self):
        """Test: handles invalid amount gracefully"""
        classified = ClassifiedInput(
            category=Category.BUDGET,
            confidence=0.9,
            extracted_data={},
            raw_input="no amount here",
            classifier_source="keyword",
        )
        handler = BudgetEntryHandler()
        result = await handler.execute(classified)

        assert result.success is False
        assert result.action_type == ActionType.CONFIRMATION_NEEDED
        assert "Could not parse" in result.message
