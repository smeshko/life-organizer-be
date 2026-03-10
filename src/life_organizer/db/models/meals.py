"""Meals database models for recipes, meal history, and recipe feedback.

This module defines the SQLAlchemy ORM models for the meals domain,
which are stored in the 'meals' schema namespace.
"""

import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from life_organizer.db.base import Base


class Recipe(Base):
    """Recipe model for storing meal recipes.

    Stores recipe details including ingredients, instructions, preparation time,
    cuisine type, and tracking data for how often recipes are made.

    All recipes are stored in the 'meals' schema namespace.

    Attributes:
        id: Primary key auto-incremented integer
        name: Recipe name
        ingredients: JSON list of ingredient strings
        instructions: Full recipe instructions text
        prep_time: Preparation time in minutes (must be positive)
        cuisine: Cuisine type (e.g. 'Italian', 'Mexican')
        tags: JSON list of tag strings
        source: Recipe origin ('seeded', 'llm_generated', or 'liked')
        times_made: Number of times this recipe has been cooked (default 0)
        last_made: Date recipe was last cooked (nullable)
        created_at: Timestamp when record was created (auto-generated)
        updated_at: Timestamp when record was last modified (auto-updated)

    Example:
        recipe = Recipe(
            name="Spaghetti Bolognese",
            ingredients=["pasta", "tomato sauce", "ground beef"],
            instructions="Cook pasta. Make sauce. Combine.",
            prep_time=30,
            cuisine="Italian",
            tags=["dinner", "pasta"],
            source="seeded",
        )
    """

    __tablename__ = "recipes"
    __table_args__ = (
        Index("ix_meals_recipes_name", "name"),
        Index("ix_meals_recipes_cuisine", "cuisine"),
        CheckConstraint("prep_time > 0", name="check_prep_time_positive"),
        CheckConstraint(
            "source IN ('seeded', 'llm_generated', 'liked')",
            name="check_source_valid",
        ),
        {"schema": "meals"},
    )

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    # Recipe details
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    ingredients: Mapped[Any] = mapped_column(JSON, nullable=False)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)
    prep_time: Mapped[int] = mapped_column(Integer, nullable=False)
    cuisine: Mapped[str] = mapped_column(String(100), nullable=False)
    tags: Mapped[Any] = mapped_column(JSON, nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)

    # Tracking
    times_made: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    last_made: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)

    # Timestamps
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<Recipe(id={self.id}, name={self.name}, cuisine={self.cuisine})>"


class MealHistory(Base):
    """Meal history model for tracking cooked meals.

    Stores records of meals that have been cooked, with an optional link
    to a saved recipe. The recipe_name is denormalized because LLM-generated
    meals may not be saved as recipes.

    All meal history records are stored in the 'meals' schema namespace.

    Attributes:
        id: Primary key auto-incremented integer
        recipe_id: Optional foreign key to recipes table
        recipe_name: Denormalized recipe name (always populated)
        cooked_date: Date the meal was cooked
        created_at: Timestamp when record was created (auto-generated)

    Example:
        history = MealHistory(
            recipe_name="Spaghetti Bolognese",
            cooked_date=datetime.date(2026, 3, 10),
            recipe_id=1,
        )
    """

    __tablename__ = "meal_history"
    __table_args__ = (
        Index("ix_meals_meal_history_cooked_date", "cooked_date"),
        {"schema": "meals"},
    )

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    # Recipe reference (optional)
    recipe_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("meals.recipes.id", ondelete="SET NULL"), nullable=True
    )
    recipe_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Meal data
    cooked_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)

    # Timestamps
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<MealHistory(id={self.id}, "
            f"recipe_name={self.recipe_name}, "
            f"cooked_date={self.cooked_date})>"
        )


class RecipeFeedback(Base):
    """Recipe feedback model for tracking user opinions on meals.

    Stores user feedback (liked/disliked) for recipes, with optional notes.
    The recipe_id is nullable because feedback can be given on LLM-generated
    meals that aren't saved as recipes.

    All feedback records are stored in the 'meals' schema namespace.

    Attributes:
        id: Primary key auto-incremented integer
        recipe_id: Optional foreign key to recipes table
        recipe_name: Denormalized recipe name (always populated)
        liked: Whether the user liked the recipe
        notes: Optional text notes about the recipe
        created_at: Timestamp when record was created (auto-generated)

    Example:
        feedback = RecipeFeedback(
            recipe_name="Spaghetti Bolognese",
            liked=True,
            notes="Great flavour, will make again",
        )
    """

    __tablename__ = "recipe_feedback"
    __table_args__ = ({"schema": "meals"},)

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    # Recipe reference (optional)
    recipe_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("meals.recipes.id", ondelete="SET NULL"), nullable=True
    )
    recipe_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Feedback data
    liked: Mapped[bool] = mapped_column(Boolean, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<RecipeFeedback(id={self.id}, recipe_name={self.recipe_name}, liked={self.liked})>"
