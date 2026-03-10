# Meals Database Schema and Models

**Date:** 2026-03-10
**Related Files:** `src/life_organizer/db/models/meals.py`, `alembic/versions/c5d2f7a41e89_create_meals_schema_and_tables.py`, `src/life_organizer/db/models/__init__.py`

## Overview

Introduces the `meals` PostgreSQL schema with three ORM models — `Recipe`, `MealHistory`, and `RecipeFeedback` — as the data foundation for the meal planning domain (Epic 3: FR13-FR22). The design uses denormalized `recipe_name` fields and nullable foreign keys to support LLM-generated meals that may never be saved as recipes.

## What Was Built

- **`meals.recipes`** table: Stores recipe details with JSON columns for ingredients and tags, check constraints on `source` and `prep_time`, and indexes on `name` and `cuisine`
- **`meals.meal_history`** table: Tracks cooked meals with optional recipe linkage and a denormalized recipe name
- **`meals.recipe_feedback`** table: Captures user liked/disliked feedback with optional notes and optional recipe linkage
- **Alembic migration** with full upgrade/downgrade support including schema creation and teardown

## Technical Implementation

### Key Files

- `src/life_organizer/db/models/meals.py`: Three ORM model classes (`Recipe`, `MealHistory`, `RecipeFeedback`)
- `alembic/versions/c5d2f7a41e89_create_meals_schema_and_tables.py`: Migration creating the `meals` schema and all three tables
- `src/life_organizer/db/models/__init__.py`: Re-exports all three models
- `tests/db/test_meals_model.py`: 49 unit tests covering column types, constraints, defaults, and importability

### Key Patterns

- **Schema namespace isolation**: All meals tables live in the `meals` schema, configured via `{"schema": "meals"}` in `__table_args__`. This matches the existing `budget` schema pattern.
- **Denormalized names on child tables**: `MealHistory.recipe_name` and `RecipeFeedback.recipe_name` are always populated even when `recipe_id` is null. This allows tracking meals suggested by the LLM that the user never saved as a recipe.
- **Nullable FK with `ondelete="SET NULL"`**: Both `meal_history.recipe_id` and `recipe_feedback.recipe_id` use `SET NULL` on delete so deleting a recipe preserves the history/feedback records.
- **Check constraints for enum-like values**: `Recipe.source` is restricted to `'seeded'`, `'llm_generated'`, `'liked'` via a `CheckConstraint` rather than a database enum, allowing easier future extension.
- **JSON columns typed as `Mapped[Any]`**: Required to satisfy MyPy strict mode since JSON columns can hold arbitrary structures.

### Code Examples

```python
from life_organizer.db.models.meals import Recipe, MealHistory, RecipeFeedback

# Create a recipe
recipe = Recipe(
    name="Spaghetti Bolognese",
    ingredients=["pasta", "tomato sauce", "ground beef"],
    instructions="Cook pasta. Make sauce. Combine.",
    prep_time=30,
    cuisine="Italian",
    tags=["dinner", "pasta"],
    source="seeded",
)

# Log a meal (with or without a saved recipe)
history = MealHistory(
    recipe_name="Quick Stir Fry",  # LLM-suggested, no saved recipe
    cooked_date=datetime.date(2026, 3, 10),
)

# Give feedback
feedback = RecipeFeedback(
    recipe_name="Spaghetti Bolognese",
    recipe_id=1,
    liked=True,
    notes="Great flavour, will make again",
)
```

## How to Use

1. Import models from `life_organizer.db.models` or `life_organizer.db.models.meals`
2. Apply the migration: `alembic upgrade head`
3. Use standard SQLAlchemy session operations to create/query/update records
4. When logging meals from LLM suggestions, always populate `recipe_name` — leave `recipe_id` as `None` if no recipe is saved

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `Recipe.source` | String | — | Must be `'seeded'`, `'llm_generated'`, or `'liked'` (enforced by DB check constraint) |
| `Recipe.times_made` | Integer | `0` | Auto-defaults at both Python and DB level |
| `Recipe.prep_time` | Integer | — | Must be positive (enforced by DB check constraint) |

## Notes

- Follows the exact same patterns as `db/models/budget.py`: `Mapped[]` type hints, `mapped_column()`, schema dict in `__table_args__`
- `times_made` has both `default=0` (Python) and `server_default="0"` (DB) for consistency across creation paths
- Migration downgrade drops tables in reverse FK order, then drops the `meals` schema with `CASCADE`
- 49 unit tests achieve full coverage of column types, nullability, constraints, indexes, defaults, and `__repr__` methods
