"""Tests for the keyword-based classifier service."""

import pytest

from life_organizer.config import KEYWORD_CONFIG
from life_organizer.schemas.enums import Category
from life_organizer.services.classifier import KeywordClassifier


@pytest.fixture
def classifier() -> KeywordClassifier:
    """Create a classifier instance with default config."""
    return KeywordClassifier(keyword_config=KEYWORD_CONFIG)


class TestKeywordMatching:
    """Tests for keyword matching functionality."""

    def test_single_expense_keyword_match(self, classifier: KeywordClassifier) -> None:
        """Test that a single expense keyword is matched correctly."""
        result = classifier.classify("I spent money today")
        assert result.category == Category.BUDGET
        assert result.confidence > 0.0

    def test_multiple_keywords_increase_confidence(self, classifier: KeywordClassifier) -> None:
        """Test that multiple keyword matches increase confidence score."""
        single_keyword = classifier.classify("spent money")
        multiple_keywords = classifier.classify("spent 45 EUR at restaurant")

        assert multiple_keywords.confidence > single_keyword.confidence

    def test_keyword_weights_affect_score(self, classifier: KeywordClassifier) -> None:
        """Test that higher-weighted keywords produce higher scores."""
        # "spent" has weight 1.0, "coffee" has weight 0.5
        high_weight = classifier.classify("spent money")
        low_weight = classifier.classify("coffee shop")

        # High weight keyword should give better confidence
        assert high_weight.confidence >= low_weight.confidence

    def test_case_insensitive_matching(self, classifier: KeywordClassifier) -> None:
        """Test that keyword matching is case-insensitive."""
        lowercase = classifier.classify("spent money")
        uppercase = classifier.classify("SPENT MONEY")
        mixed = classifier.classify("SpEnT MoNeY")

        assert lowercase.category == uppercase.category == mixed.category
        assert abs(lowercase.confidence - uppercase.confidence) < 0.01
        assert abs(lowercase.confidence - mixed.confidence) < 0.01

    def test_phrase_matching(self, classifier: KeywordClassifier) -> None:
        """Test that multi-word phrases are matched correctly."""
        result = classifier.classify("we're out of milk")

        assert result.category == Category.SHOPPING
        # "out of" is a high-weight phrase (1.0)
        assert result.confidence > 0.5


class TestConfidenceScoring:
    """Tests for confidence scoring logic."""

    def test_high_confidence_clear_expense(self, classifier: KeywordClassifier) -> None:
        """Test high confidence for clear expense input."""
        result = classifier.classify("Spent 45 EUR at restaurant")

        assert result.category == Category.BUDGET
        assert result.confidence > 0.75

    def test_high_confidence_clear_shopping(self, classifier: KeywordClassifier) -> None:
        """Test high confidence for clear shopping input."""
        result = classifier.classify("We're out of milk, add to shopping list")

        assert result.category == Category.SHOPPING
        assert result.confidence > 0.85

    def test_low_confidence_ambiguous_input(self, classifier: KeywordClassifier) -> None:
        """Test low confidence for ambiguous input."""
        # "need to call" could be reminder or other
        result = classifier.classify("I need to call")

        # Should still classify, but with lower confidence
        assert result.confidence < 0.85

    def test_unknown_category_no_matches(self, classifier: KeywordClassifier) -> None:
        """Test that inputs with no keyword matches return UNKNOWN category."""
        result = classifier.classify("The quick brown fox jumps over the lazy dog")

        assert result.category == Category.UNKNOWN
        assert result.confidence == 0.0

    def test_confidence_normalized_to_one(self, classifier: KeywordClassifier) -> None:
        """Test that confidence scores are normalized to max 1.0."""
        # Even with many keywords, confidence shouldn't exceed 1.0
        result = classifier.classify(
            "spent paid purchased charged cost bought expense restaurant cafe grocery supermarket"
        )

        assert result.category == Category.BUDGET
        assert result.confidence <= 1.0


class TestCategoryDetection:
    """Tests for detecting correct categories."""

    def test_expense_detection(self, classifier: KeywordClassifier) -> None:
        """Test expense category detection."""
        inputs = [
            "Spent 45 EUR at restaurant",
            "Paid 20 dollars for gas",
            "Cost me 100 euros",
            "Purchased groceries for 50",
        ]

        for input_text in inputs:
            result = classifier.classify(input_text)
            assert result.category == Category.BUDGET, f"Failed for: {input_text}"

    def test_shopping_detection(self, classifier: KeywordClassifier) -> None:
        """Test shopping category detection."""
        inputs = [
            "We're out of milk",
            "Need to buy bread",
            "Add eggs to the list",
            "Running low on coffee",
        ]

        for input_text in inputs:
            result = classifier.classify(input_text)
            assert result.category == Category.SHOPPING, f"Failed for: {input_text}"

    def test_reminder_detection(self, classifier: KeywordClassifier) -> None:
        """Test reminder category detection."""
        inputs = [
            "Remind me to call the dentist",
            "Don't forget to pick up dry cleaning",
            "Need to take out the trash",
            "Remember to refill prescription",
        ]

        for input_text in inputs:
            result = classifier.classify(input_text)
            assert result.category == Category.REMINDER, f"Failed for: {input_text}"

    def test_calendar_detection(self, classifier: KeywordClassifier) -> None:
        """Test calendar category detection."""
        inputs = [
            "Meeting with John tomorrow",
            "Doctor appointment next week",
            "Schedule a call for tonight",
            "Team event on Friday",
        ]

        for input_text in inputs:
            result = classifier.classify(input_text)
            assert result.category == Category.CALENDAR, f"Failed for: {input_text}"


class TestDataExtraction:
    """Tests for extracting structured data from input."""

    def test_amount_extraction_integer(self, classifier: KeywordClassifier) -> None:
        """Test extraction of integer amounts."""
        result = classifier.classify("Spent 45 EUR")

        assert "amount" in result.extracted_data
        assert result.extracted_data["amount"] == 45.0

    def test_amount_extraction_decimal(self, classifier: KeywordClassifier) -> None:
        """Test extraction of decimal amounts."""
        result = classifier.classify("Paid 45.99 dollars")

        assert "amount" in result.extracted_data
        assert result.extracted_data["amount"] == 45.99

    def test_amount_extraction_comma_decimal(self, classifier: KeywordClassifier) -> None:
        """Test extraction of amounts with comma as decimal separator."""
        result = classifier.classify("Cost 45,50 EUR")

        assert "amount" in result.extracted_data
        assert result.extracted_data["amount"] == 45.50

    def test_currency_detection_eur(self, classifier: KeywordClassifier) -> None:
        """Test EUR currency detection."""
        inputs = [
            ("Spent 45 EUR", "EUR"),
            ("Paid 20 euros", "EUR"),
            ("Cost 30 €", "EUR"),
        ]

        for input_text, expected_currency in inputs:
            result = classifier.classify(input_text)
            assert "currency" in result.extracted_data
            assert result.extracted_data["currency"] == expected_currency

    def test_currency_detection_usd(self, classifier: KeywordClassifier) -> None:
        """Test USD currency detection."""
        inputs = [
            ("Spent 45 USD", "USD"),
            ("Paid 20 dollars", "USD"),
            ("Cost 30 $", "USD"),
        ]

        for input_text, expected_currency in inputs:
            result = classifier.classify(input_text)
            assert "currency" in result.extracted_data
            assert result.extracted_data["currency"] == expected_currency

    def test_merchant_hint_extraction(self, classifier: KeywordClassifier) -> None:
        """Test extraction of merchant hints from keywords."""
        result = classifier.classify("Spent 45 EUR at restaurant")

        assert "merchant_hint" in result.extracted_data
        assert result.extracted_data["merchant_hint"] == "restaurant"

    def test_shopping_item_extraction(self, classifier: KeywordClassifier) -> None:
        """Test extraction of shopping items."""
        result = classifier.classify("We're out of milk")

        assert "items" in result.extracted_data
        assert "milk" in result.extracted_data["items"]

    def test_multiple_items_extraction(self, classifier: KeywordClassifier) -> None:
        """Test extraction of multiple shopping items."""
        result = classifier.classify("Need bread and we're out of milk")

        assert "items" in result.extracted_data
        items = result.extracted_data["items"]
        assert "milk" in items
        assert "bread" in items

    def test_reminder_action_extraction(self, classifier: KeywordClassifier) -> None:
        """Test extraction of action from reminder."""
        result = classifier.classify("Remind me to call the dentist")

        assert "action" in result.extracted_data
        assert result.extracted_data["action"] == "call"

    def test_calendar_time_reference_extraction(self, classifier: KeywordClassifier) -> None:
        """Test extraction of time reference from calendar input."""
        result = classifier.classify("Meeting tomorrow at 2pm")

        assert "time_reference" in result.extracted_data
        assert result.extracted_data["time_reference"] == "tomorrow"


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_string_input(self, classifier: KeywordClassifier) -> None:
        """Test classification of empty string."""
        result = classifier.classify("")

        assert result.category == Category.UNKNOWN
        assert result.confidence == 0.0
        assert result.raw_input == ""

    def test_whitespace_only_input(self, classifier: KeywordClassifier) -> None:
        """Test classification of whitespace-only input."""
        result = classifier.classify("   \n\t  ")

        assert result.category == Category.UNKNOWN
        assert result.confidence == 0.0

    def test_very_long_input(self, classifier: KeywordClassifier) -> None:
        """Test classification of very long input."""
        long_input = "spent " * 200 + "45 EUR at restaurant"
        result = classifier.classify(long_input)

        # Should still classify correctly
        assert result.category == Category.BUDGET
        assert result.confidence <= 1.0

    def test_special_characters(self, classifier: KeywordClassifier) -> None:
        """Test handling of special characters."""
        result = classifier.classify("Spent 45€ @restaurant!!! #food")

        assert result.category == Category.BUDGET
        assert "amount" in result.extracted_data

    def test_mixed_language_input(self, classifier: KeywordClassifier) -> None:
        """Test handling of mixed language input."""
        # English keywords should still work
        result = classifier.classify("Gasté 45 EUR restaurant")

        # Should detect "EUR" and "restaurant"
        assert result.category == Category.BUDGET

    def test_raw_input_preserved(self, classifier: KeywordClassifier) -> None:
        """Test that raw input is preserved exactly."""
        original = "Spent 45 EUR at Restaurant"
        result = classifier.classify(original)

        assert result.raw_input == original


class TestTieBreaking:
    """Tests for handling ties between categories."""

    def test_highest_score_wins(self, classifier: KeywordClassifier) -> None:
        """Test that category with highest score is selected."""
        # "coffee" appears in both EXPENSE and SHOPPING keywords
        # But "spent" is stronger for EXPENSE
        result = classifier.classify("spent money on coffee")

        assert result.category == Category.BUDGET

    def test_clear_winner_when_multiple_matches(self, classifier: KeywordClassifier) -> None:
        """Test that clear winner is selected when multiple categories match."""
        result = classifier.classify("spent 45 EUR need to buy milk")

        # Should have matches for both EXPENSE and SHOPPING
        # EXPENSE should win due to specific amount and currency
        assert result.category == Category.BUDGET or result.category == Category.SHOPPING
        # At least one should have high confidence
        assert result.confidence > 0.5
