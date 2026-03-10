"""Meal service for orchestrating meal suggestion generation."""

from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING

from sqlalchemy import select

from life_organizer.db.models.meals import MealHistory, RecipeFeedback
from life_organizer.schemas.meals import MealSuggestion

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from life_organizer.services.claude_service import ClaudeService

logger = logging.getLogger(__name__)


class MealService:
    """Service for orchestrating meal suggestions.

    Queries meal history and recipe feedback from the database,
    then calls ClaudeService to generate personalized suggestions.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        """Initialize MealService.

        Args:
            session_factory: Async session factory for database access
        """
        self.session_factory = session_factory

    async def get_suggestions(
        self,
        requirements: str | None,
        claude_service: ClaudeService,
    ) -> list[MealSuggestion]:
        """Generate meal suggestions using DB context and Claude LLM.

        Queries recent meal history (last 14 days) and liked recipes,
        then passes this context to ClaudeService for suggestion generation.

        Args:
            requirements: Optional user constraints (e.g., "I have chicken thighs")
            claude_service: ClaudeService instance for LLM calls

        Returns:
            List of MealSuggestion Pydantic models

        Raises:
            HTTPException: If Claude fails to generate or parse suggestions
        """
        async with self.session_factory() as db:
            # Query recent meal history (last 14 days)
            cutoff_date = datetime.date.today() - datetime.timedelta(days=14)
            history_stmt = (
                select(MealHistory)
                .where(MealHistory.cooked_date >= cutoff_date)
                .order_by(MealHistory.cooked_date.desc())
            )
            history_result = await db.execute(history_stmt)
            history_rows = history_result.scalars().all()
            history = [row.recipe_name for row in history_rows]

            # Query liked recipes (top 10, most recent first)
            feedback_stmt = (
                select(RecipeFeedback)
                .where(RecipeFeedback.liked.is_(True))
                .order_by(RecipeFeedback.created_at.desc())
                .limit(10)
            )
            feedback_result = await db.execute(feedback_stmt)
            feedback_rows = feedback_result.scalars().all()
            liked_recipes = [row.recipe_name for row in feedback_rows]

        logger.info(
            f"Meal context: {len(history)} recent meals, {len(liked_recipes)} liked recipes"
        )

        # Call Claude for suggestions
        suggestion_dicts = await claude_service.suggest_meals(
            requirements=requirements,
            history=history,
            liked_recipes=liked_recipes,
        )

        # Parse dicts into Pydantic models
        return [MealSuggestion.model_validate(s) for s in suggestion_dicts]
