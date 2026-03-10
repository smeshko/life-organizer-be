"""Tests for meals database models (Recipe, MealHistory, RecipeFeedback)."""

import datetime

from life_organizer.db.models.meals import MealHistory, Recipe, RecipeFeedback

# ──────────────────────────────────────────────
# Recipe model tests
# ──────────────────────────────────────────────


def test_recipe_can_be_instantiated():
    """Test Recipe can be instantiated with required fields."""
    recipe = Recipe(
        name="Spaghetti Bolognese",
        ingredients=["pasta", "tomato sauce", "ground beef"],
        instructions="Cook pasta. Make sauce. Combine.",
        prep_time=30,
        cuisine="Italian",
        tags=["dinner", "pasta"],
        source="seeded",
    )
    assert recipe.name == "Spaghetti Bolognese"
    assert recipe.ingredients == ["pasta", "tomato sauce", "ground beef"]
    assert recipe.instructions == "Cook pasta. Make sauce. Combine."
    assert recipe.prep_time == 30
    assert recipe.cuisine == "Italian"
    assert recipe.tags == ["dinner", "pasta"]
    assert recipe.source == "seeded"


def test_recipe_tablename():
    """Test __tablename__ equals 'recipes'."""
    assert Recipe.__tablename__ == "recipes"


def test_recipe_table_schema():
    """Test table schema is 'meals' via __table_args__."""
    table_args = Recipe.__table_args__
    assert isinstance(table_args, tuple)
    schema_dict = table_args[-1]
    assert isinstance(schema_dict, dict)
    assert schema_dict["schema"] == "meals"


def test_recipe_repr():
    """Test __repr__ returns a meaningful string."""
    recipe = Recipe(id=1, name="Spaghetti Bolognese", cuisine="Italian")
    result = repr(recipe)
    assert "Recipe" in result
    assert "1" in result
    assert "Spaghetti Bolognese" in result
    assert "Italian" in result


def test_recipe_times_made_has_default():
    """Test times_made column has a default value of 0."""
    col = Recipe.__table__.columns["times_made"]
    assert col.default is not None
    assert col.default.arg == 0


def test_recipe_last_made_nullable():
    """Test last_made column is nullable."""
    col = Recipe.__table__.columns["last_made"]
    assert col.nullable is True


def test_recipe_name_not_nullable():
    """Test name column is not nullable."""
    col = Recipe.__table__.columns["name"]
    assert col.nullable is False


def test_recipe_ingredients_not_nullable():
    """Test ingredients column is not nullable."""
    col = Recipe.__table__.columns["ingredients"]
    assert col.nullable is False


def test_recipe_instructions_not_nullable():
    """Test instructions column is not nullable."""
    col = Recipe.__table__.columns["instructions"]
    assert col.nullable is False


def test_recipe_prep_time_not_nullable():
    """Test prep_time column is not nullable."""
    col = Recipe.__table__.columns["prep_time"]
    assert col.nullable is False


def test_recipe_cuisine_not_nullable():
    """Test cuisine column is not nullable."""
    col = Recipe.__table__.columns["cuisine"]
    assert col.nullable is False


def test_recipe_tags_not_nullable():
    """Test tags column is not nullable."""
    col = Recipe.__table__.columns["tags"]
    assert col.nullable is False


def test_recipe_source_not_nullable():
    """Test source column is not nullable."""
    col = Recipe.__table__.columns["source"]
    assert col.nullable is False


def test_recipe_times_made_not_nullable():
    """Test times_made column is not nullable."""
    col = Recipe.__table__.columns["times_made"]
    assert col.nullable is False


def test_recipe_created_at_has_server_default():
    """Test created_at column has a server default."""
    col = Recipe.__table__.columns["created_at"]
    assert col.server_default is not None


def test_recipe_created_at_is_timezone_aware():
    """Test created_at column uses timezone-aware datetime."""
    col = Recipe.__table__.columns["created_at"]
    assert col.type.timezone is True


def test_recipe_updated_at_has_server_default():
    """Test updated_at column has a server default."""
    col = Recipe.__table__.columns["updated_at"]
    assert col.server_default is not None


def test_recipe_updated_at_is_timezone_aware():
    """Test updated_at column uses timezone-aware datetime."""
    col = Recipe.__table__.columns["updated_at"]
    assert col.type.timezone is True


def test_recipe_ingredients_is_json_type():
    """Test ingredients column uses JSON type."""
    from sqlalchemy import JSON

    col = Recipe.__table__.columns["ingredients"]
    assert isinstance(col.type, JSON)


def test_recipe_tags_is_json_type():
    """Test tags column uses JSON type."""
    from sqlalchemy import JSON

    col = Recipe.__table__.columns["tags"]
    assert isinstance(col.type, JSON)


def test_recipe_has_check_constraints():
    """Test Recipe has check constraints for source and prep_time."""
    constraints = [c for c in Recipe.__table__.constraints if hasattr(c, "sqltext")]
    constraint_names = {c.name for c in constraints}
    assert "check_source_valid" in constraint_names
    assert "check_prep_time_positive" in constraint_names


def test_recipe_has_name_index():
    """Test Recipe has an index on name column."""
    index_names = {idx.name for idx in Recipe.__table__.indexes}
    assert "ix_meals_recipes_name" in index_names


def test_recipe_has_cuisine_index():
    """Test Recipe has an index on cuisine column."""
    index_names = {idx.name for idx in Recipe.__table__.indexes}
    assert "ix_meals_recipes_cuisine" in index_names


# ──────────────────────────────────────────────
# MealHistory model tests
# ──────────────────────────────────────────────


def test_meal_history_can_be_instantiated():
    """Test MealHistory can be instantiated with required fields."""
    history = MealHistory(
        recipe_name="Spaghetti Bolognese",
        cooked_date=datetime.date(2026, 3, 10),
    )
    assert history.recipe_name == "Spaghetti Bolognese"
    assert history.cooked_date == datetime.date(2026, 3, 10)
    assert history.recipe_id is None


def test_meal_history_tablename():
    """Test __tablename__ equals 'meal_history'."""
    assert MealHistory.__tablename__ == "meal_history"


def test_meal_history_table_schema():
    """Test table schema is 'meals' via __table_args__."""
    table_args = MealHistory.__table_args__
    assert isinstance(table_args, tuple)
    schema_dict = table_args[-1]
    assert isinstance(schema_dict, dict)
    assert schema_dict["schema"] == "meals"


def test_meal_history_repr():
    """Test __repr__ returns a meaningful string."""
    history = MealHistory(
        id=1,
        recipe_name="Spaghetti Bolognese",
        cooked_date=datetime.date(2026, 3, 10),
    )
    result = repr(history)
    assert "MealHistory" in result
    assert "1" in result
    assert "Spaghetti Bolognese" in result


def test_meal_history_recipe_id_nullable():
    """Test recipe_id column is nullable (FK is optional)."""
    col = MealHistory.__table__.columns["recipe_id"]
    assert col.nullable is True


def test_meal_history_recipe_name_not_nullable():
    """Test recipe_name column is not nullable."""
    col = MealHistory.__table__.columns["recipe_name"]
    assert col.nullable is False


def test_meal_history_cooked_date_not_nullable():
    """Test cooked_date column is not nullable."""
    col = MealHistory.__table__.columns["cooked_date"]
    assert col.nullable is False


def test_meal_history_cooked_date_is_date_type():
    """Test cooked_date column is Date type (not DateTime)."""
    from sqlalchemy import Date

    col = MealHistory.__table__.columns["cooked_date"]
    assert isinstance(col.type, Date)


def test_meal_history_recipe_id_has_foreign_key():
    """Test recipe_id has a foreign key to meals.recipes.id."""
    col = MealHistory.__table__.columns["recipe_id"]
    fk_targets = {fk.target_fullname for fk in col.foreign_keys}
    assert "meals.recipes.id" in fk_targets


def test_meal_history_created_at_has_server_default():
    """Test created_at column has a server default."""
    col = MealHistory.__table__.columns["created_at"]
    assert col.server_default is not None


def test_meal_history_created_at_is_timezone_aware():
    """Test created_at column uses timezone-aware datetime."""
    col = MealHistory.__table__.columns["created_at"]
    assert col.type.timezone is True


def test_meal_history_has_cooked_date_index():
    """Test MealHistory has an index on cooked_date column."""
    index_names = {idx.name for idx in MealHistory.__table__.indexes}
    assert "ix_meals_meal_history_cooked_date" in index_names


# ──────────────────────────────────────────────
# RecipeFeedback model tests
# ──────────────────────────────────────────────


def test_recipe_feedback_can_be_instantiated():
    """Test RecipeFeedback can be instantiated with required fields."""
    feedback = RecipeFeedback(
        recipe_name="Spaghetti Bolognese",
        liked=True,
    )
    assert feedback.recipe_name == "Spaghetti Bolognese"
    assert feedback.liked is True
    assert feedback.recipe_id is None
    assert feedback.notes is None


def test_recipe_feedback_tablename():
    """Test __tablename__ equals 'recipe_feedback'."""
    assert RecipeFeedback.__tablename__ == "recipe_feedback"


def test_recipe_feedback_table_schema():
    """Test table schema is 'meals' via __table_args__."""
    table_args = RecipeFeedback.__table_args__
    assert isinstance(table_args, tuple)
    schema_dict = table_args[-1]
    assert isinstance(schema_dict, dict)
    assert schema_dict["schema"] == "meals"


def test_recipe_feedback_repr():
    """Test __repr__ returns a meaningful string."""
    feedback = RecipeFeedback(
        id=1,
        recipe_name="Spaghetti Bolognese",
        liked=True,
    )
    result = repr(feedback)
    assert "RecipeFeedback" in result
    assert "1" in result
    assert "Spaghetti Bolognese" in result


def test_recipe_feedback_recipe_id_nullable():
    """Test recipe_id column is nullable (FK is optional)."""
    col = RecipeFeedback.__table__.columns["recipe_id"]
    assert col.nullable is True


def test_recipe_feedback_recipe_name_not_nullable():
    """Test recipe_name column is not nullable."""
    col = RecipeFeedback.__table__.columns["recipe_name"]
    assert col.nullable is False


def test_recipe_feedback_liked_not_nullable():
    """Test liked column is not nullable."""
    col = RecipeFeedback.__table__.columns["liked"]
    assert col.nullable is False


def test_recipe_feedback_notes_nullable():
    """Test notes column is nullable."""
    col = RecipeFeedback.__table__.columns["notes"]
    assert col.nullable is True


def test_recipe_feedback_recipe_id_has_foreign_key():
    """Test recipe_id has a foreign key to meals.recipes.id."""
    col = RecipeFeedback.__table__.columns["recipe_id"]
    fk_targets = {fk.target_fullname for fk in col.foreign_keys}
    assert "meals.recipes.id" in fk_targets


def test_recipe_feedback_created_at_has_server_default():
    """Test created_at column has a server default."""
    col = RecipeFeedback.__table__.columns["created_at"]
    assert col.server_default is not None


def test_recipe_feedback_created_at_is_timezone_aware():
    """Test created_at column uses timezone-aware datetime."""
    col = RecipeFeedback.__table__.columns["created_at"]
    assert col.type.timezone is True


# ──────────────────────────────────────────────
# Importability tests
# ──────────────────────────────────────────────


def test_recipe_importable_from_db_models():
    """Test Recipe is importable from life_organizer.db.models."""
    from life_organizer.db.models import Recipe as R

    assert R is Recipe


def test_meal_history_importable_from_db_models():
    """Test MealHistory is importable from life_organizer.db.models."""
    from life_organizer.db.models import MealHistory as MH

    assert MH is MealHistory


def test_recipe_feedback_importable_from_db_models():
    """Test RecipeFeedback is importable from life_organizer.db.models."""
    from life_organizer.db.models import RecipeFeedback as RF

    assert RF is RecipeFeedback
