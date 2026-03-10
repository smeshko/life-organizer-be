"""create meals schema and tables

Revision ID: c5d2f7a41e89
Revises: b4f1c8e23a67
Create Date: 2026-03-10

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c5d2f7a41e89"
down_revision: Union[str, Sequence[str], None] = "b4f1c8e23a67"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create meals schema and recipes, meal_history, recipe_feedback tables."""
    # Create meals schema first
    op.execute("CREATE SCHEMA IF NOT EXISTS meals")

    # Create recipes table in meals schema
    op.create_table(
        "recipes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("ingredients", sa.JSON(), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column("prep_time", sa.Integer(), nullable=False),
        sa.Column("cuisine", sa.String(length=100), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("times_made", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_made", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("prep_time > 0", name="check_prep_time_positive"),
        sa.CheckConstraint(
            "source IN ('seeded', 'llm_generated', 'liked')",
            name="check_source_valid",
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="meals",
    )

    # Create indexes on recipes
    op.create_index("ix_meals_recipes_name", "recipes", ["name"], unique=False, schema="meals")
    op.create_index(
        "ix_meals_recipes_cuisine",
        "recipes",
        ["cuisine"],
        unique=False,
        schema="meals",
    )

    # Create meal_history table in meals schema
    op.create_table(
        "meal_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "recipe_id",
            sa.Integer(),
            sa.ForeignKey("meals.recipes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("recipe_name", sa.String(length=255), nullable=False),
        sa.Column("cooked_date", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="meals",
    )

    # Create index on meal_history
    op.create_index(
        "ix_meals_meal_history_cooked_date",
        "meal_history",
        ["cooked_date"],
        unique=False,
        schema="meals",
    )

    # Create recipe_feedback table in meals schema
    op.create_table(
        "recipe_feedback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "recipe_id",
            sa.Integer(),
            sa.ForeignKey("meals.recipes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("recipe_name", sa.String(length=255), nullable=False),
        sa.Column("liked", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="meals",
    )


def downgrade() -> None:
    """Drop meals tables and schema."""
    # Drop tables in reverse order (respect FK dependencies)
    op.drop_table("recipe_feedback", schema="meals")

    # Drop index before table
    op.drop_index(
        "ix_meals_meal_history_cooked_date",
        table_name="meal_history",
        schema="meals",
    )
    op.drop_table("meal_history", schema="meals")

    # Drop indexes before table
    op.drop_index("ix_meals_recipes_cuisine", table_name="recipes", schema="meals")
    op.drop_index("ix_meals_recipes_name", table_name="recipes", schema="meals")
    op.drop_table("recipes", schema="meals")

    # Drop schema
    op.execute("DROP SCHEMA IF EXISTS meals CASCADE")
