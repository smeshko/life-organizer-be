"""SQLAlchemy ORM models for database tables.

This module contains all database models organized by domain:
- budget: Budget transaction tracking (expenses, income, savings)
- feedback: Misclassification feedback for training improvements
- meals: Recipes, meal history, and recipe feedback
"""

from life_organizer.db.base import Base
from life_organizer.db.models.budget import BudgetPlan, BudgetTransaction
from life_organizer.db.models.feedback import MisclassificationFeedback
from life_organizer.db.models.meals import MealHistory, Recipe, RecipeFeedback

__all__ = [
    "Base",
    "BudgetPlan",
    "BudgetTransaction",
    "MealHistory",
    "MisclassificationFeedback",
    "Recipe",
    "RecipeFeedback",
]
