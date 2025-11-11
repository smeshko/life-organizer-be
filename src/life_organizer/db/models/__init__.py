"""SQLAlchemy ORM models for database tables.

This module contains all database models organized by domain:
- budget: Budget transaction tracking (expenses, income, savings)
- Future: notes, workout, system namespaces
"""

from life_organizer.db.base import Base
from life_organizer.db.models.budget import BudgetTransaction

__all__ = ["Base", "BudgetTransaction"]
