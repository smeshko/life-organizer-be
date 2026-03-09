"""Tests for classification schemas."""

import pytest
from pydantic import ValidationError

from life_organizer.schemas.classification import ClassifiedInput
from life_organizer.schemas.enums import Category


def test_valid_classification_with_extracted_data():
    """Test ClassifiedInput with valid data including extracted_data."""
    classified = ClassifiedInput(
        category=Category.BUDGET,
        confidence=0.95,
        extracted_data={"amount": 45, "currency": "EUR", "category": "restaurant"},
        raw_input="Spent 45 euros at restaurant",
        classifier_source="keyword",
    )

    assert classified.category == Category.BUDGET
    assert classified.confidence == 0.95
    assert classified.extracted_data == {
        "amount": 45,
        "currency": "EUR",
        "category": "restaurant",
    }
    assert classified.raw_input == "Spent 45 euros at restaurant"


def test_classification_without_extracted_data():
    """Test ClassifiedInput with empty extracted_data (defaults to empty dict)."""
    classified = ClassifiedInput(
        category=Category.UNKNOWN,
        confidence=0.2,
        raw_input="Something unclear",
        classifier_source="keyword",
    )

    assert classified.category == Category.UNKNOWN
    assert classified.confidence == 0.2
    assert classified.extracted_data == {}
    assert classified.raw_input == "Something unclear"


def test_classification_serialization():
    """Test JSON serialization of ClassifiedInput."""
    classified = ClassifiedInput(
        category=Category.BUDGET,
        confidence=0.85,
        extracted_data={"amount": 45, "currency": "EUR"},
        raw_input="Spent 45 euros",
        classifier_source="keyword",
    )

    json_data = classified.model_dump_json()
    assert "budget" in json_data  # Category serializes to string
    assert "0.85" in json_data
    assert "45" in json_data
    assert "Spent 45 euros" in json_data


def test_classification_deserialization():
    """Test ClassifiedInput from JSON data."""
    data = {
        "category": "budget",
        "confidence": 0.9,
        "extracted_data": {"amount": 45, "currency": "EUR", "category": "restaurant"},
        "raw_input": "Spent 45 at restaurant",
        "classifier_source": "keyword",
    }

    classified = ClassifiedInput(**data)
    assert classified.category == Category.BUDGET
    assert classified.confidence == 0.9
    assert classified.extracted_data == {
        "amount": 45,
        "currency": "EUR",
        "category": "restaurant",
    }


def test_confidence_minimum_valid():
    """Test confidence at minimum valid value (0.0)."""
    classified = ClassifiedInput(
        category=Category.UNKNOWN,
        confidence=0.0,
        raw_input="No idea",
        classifier_source="keyword",
    )

    assert classified.confidence == 0.0


def test_confidence_maximum_valid():
    """Test confidence at maximum valid value (1.0)."""
    classified = ClassifiedInput(
        category=Category.BUDGET,
        confidence=1.0,
        raw_input="Clear expense",
        classifier_source="keyword",
    )

    assert classified.confidence == 1.0


def test_confidence_below_minimum():
    """Test validation error for confidence below 0.0."""
    with pytest.raises(ValidationError) as exc_info:
        ClassifiedInput(
            category=Category.BUDGET,
            confidence=-0.1,
            raw_input="Test",
            classifier_source="keyword",
        )

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("confidence",)
    assert "greater than or equal to 0" in str(errors[0]["msg"]).lower()


def test_confidence_above_maximum():
    """Test validation error for confidence above 1.0."""
    with pytest.raises(ValidationError) as exc_info:
        ClassifiedInput(
            category=Category.BUDGET, confidence=1.5, raw_input="Test", classifier_source="keyword"
        )

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("confidence",)
    assert "less than or equal to 1" in str(errors[0]["msg"]).lower()


def test_missing_category():
    """Test validation error when category is missing."""
    with pytest.raises(ValidationError) as exc_info:
        ClassifiedInput(confidence=0.9, raw_input="Test input", classifier_source="keyword")

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("category",)
    assert errors[0]["type"] == "missing"


def test_missing_confidence():
    """Test validation error when confidence is missing."""
    with pytest.raises(ValidationError) as exc_info:
        ClassifiedInput(
            category=Category.BUDGET, raw_input="Test input", classifier_source="keyword"
        )

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("confidence",)
    assert errors[0]["type"] == "missing"


def test_missing_raw_input():
    """Test validation error when raw_input is missing."""
    with pytest.raises(ValidationError) as exc_info:
        ClassifiedInput(category=Category.BUDGET, confidence=0.9, classifier_source="keyword")

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("raw_input",)
    assert errors[0]["type"] == "missing"


def test_invalid_category():
    """Test validation error for invalid category string."""
    with pytest.raises(ValidationError) as exc_info:
        ClassifiedInput(
            category="invalid_category",
            confidence=0.9,
            raw_input="Test",
            classifier_source="keyword",
        )

    errors = exc_info.value.errors()
    assert len(errors) >= 1
    assert any(error["loc"] == ("category",) for error in errors)


def test_rejected_deprecated_category_reminder():
    """Test ClassifiedInput rejects deprecated 'reminder' category."""
    with pytest.raises(ValidationError) as exc_info:
        ClassifiedInput(
            category="reminder",
            confidence=0.9,
            raw_input="Call the dentist",
            classifier_source="keyword",
        )

    errors = exc_info.value.errors()
    assert len(errors) >= 1
    assert any(error["loc"] == ("category",) for error in errors)


def test_extracted_data_complex_types():
    """Test extracted_data with complex nested data."""
    classified = ClassifiedInput(
        category=Category.BUDGET,
        confidence=0.88,
        extracted_data={
            "amount": 150.0,
            "currency": "EUR",
            "transaction_type": "Expenses",
            "metadata": {"source": "voice", "language": "en"},
        },
        raw_input="Spent 150 euros on groceries",
        classifier_source="keyword",
    )

    assert classified.extracted_data["amount"] == 150.0
    assert classified.extracted_data["currency"] == "EUR"
    assert isinstance(classified.extracted_data["metadata"], dict)
