"""Tests for MisclassificationFeedback database model."""

from life_organizer.db.models.feedback import MisclassificationFeedback


def test_model_can_be_instantiated():
    """Test MisclassificationFeedback can be instantiated with required fields."""
    feedback = MisclassificationFeedback(
        original_input="Buy groceries",
        wrong_category="note",
        correct_category="budget",
    )
    assert feedback.original_input == "Buy groceries"
    assert feedback.wrong_category == "note"
    assert feedback.correct_category == "budget"


def test_tablename():
    """Test __tablename__ equals 'misclassifications'."""
    assert MisclassificationFeedback.__tablename__ == "misclassifications"


def test_table_schema():
    """Test table schema is 'feedback' via __table_args__."""
    table_args = MisclassificationFeedback.__table_args__
    # __table_args__ is a tuple ending with a dict for schema
    assert isinstance(table_args, tuple)
    schema_dict = table_args[-1]
    assert isinstance(schema_dict, dict)
    assert schema_dict["schema"] == "feedback"


def test_repr():
    """Test __repr__ returns a meaningful string."""
    feedback = MisclassificationFeedback(
        id=1,
        original_input="Buy groceries",
        wrong_category="note",
        correct_category="budget",
    )
    result = repr(feedback)
    assert "MisclassificationFeedback" in result
    assert "1" in result
    assert "note" in result
    assert "budget" in result


def test_column_original_input_not_nullable():
    """Test original_input column is not nullable."""
    col = MisclassificationFeedback.__table__.columns["original_input"]
    assert col.nullable is False


def test_column_wrong_category_not_nullable():
    """Test wrong_category column is not nullable."""
    col = MisclassificationFeedback.__table__.columns["wrong_category"]
    assert col.nullable is False


def test_column_correct_category_not_nullable():
    """Test correct_category column is not nullable."""
    col = MisclassificationFeedback.__table__.columns["correct_category"]
    assert col.nullable is False


def test_column_created_at_has_server_default():
    """Test created_at column has a server default."""
    col = MisclassificationFeedback.__table__.columns["created_at"]
    assert col.server_default is not None


def test_column_created_at_is_timezone_aware():
    """Test created_at column uses timezone-aware datetime."""
    col = MisclassificationFeedback.__table__.columns["created_at"]
    assert col.type.timezone is True


def test_importable_from_db_models():
    """Test model is importable from life_organizer.db.models."""
    from life_organizer.db.models import MisclassificationFeedback as MF

    assert MF is MisclassificationFeedback
