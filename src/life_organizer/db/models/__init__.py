"""SQLAlchemy ORM models for database tables.

This module contains all database models organized by domain:
- budget: Budget transaction tracking (expenses, income, savings)
- feedback: Misclassification feedback for training improvements
"""

from life_organizer.db.base import Base
from life_organizer.db.models.budget import BudgetTransaction
from life_organizer.db.models.feedback import MisclassificationFeedback

__all__ = ["Base", "BudgetTransaction", "MisclassificationFeedback"]
