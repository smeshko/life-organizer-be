"""Meals API endpoints for meal suggestion generation."""

import logging

from fastapi import APIRouter, HTTPException, Request

from life_organizer.config import get_settings
from life_organizer.db.session import async_session_factory
from life_organizer.rate_limit import limiter
from life_organizer.schemas.meals import (
    MealSuggestRequest,
    MealSuggestResponse,
)
from life_organizer.services.claude_service import ClaudeService
from life_organizer.services.meal_service import MealService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
settings = get_settings()
claude_service = ClaudeService(api_key=settings.claude_api_key)
meal_service = MealService(session_factory=async_session_factory)


@router.post(
    "/suggest",
    response_model=MealSuggestResponse,
    response_description="List of 3 dinner suggestions",
    responses={
        200: {
            "description": "Successfully generated meal suggestions",
            "content": {
                "application/json": {
                    "examples": {
                        "suggestions": {
                            "summary": "3 Dinner Suggestions",
                            "value": {
                                "suggestions": [
                                    {
                                        "name": "Chicken Stir Fry",
                                        "ingredients": [
                                            "chicken breast",
                                            "bell peppers",
                                            "soy sauce",
                                            "rice",
                                        ],
                                        "instructions": "Cut chicken into strips. Stir fry with sliced peppers. Add soy sauce. Serve over steamed rice.",
                                        "prep_time": 25,
                                        "cuisine": "Asian",
                                        "tags": ["quick", "healthy"],
                                    },
                                    {
                                        "name": "Spaghetti Bolognese",
                                        "ingredients": [
                                            "spaghetti",
                                            "ground beef",
                                            "tomato paste",
                                            "onions",
                                        ],
                                        "instructions": "Cook spaghetti. Brown beef with onions. Add tomato paste. Simmer. Combine.",
                                        "prep_time": 35,
                                        "cuisine": "Italian",
                                        "tags": ["comfort", "pasta"],
                                    },
                                    {
                                        "name": "Greek Salad with Feta",
                                        "ingredients": [
                                            "lettuce",
                                            "cucumber",
                                            "tomatoes",
                                            "feta cheese",
                                            "olives",
                                        ],
                                        "instructions": "Chop vegetables. Add crumbled feta and olives. Drizzle with olive oil.",
                                        "prep_time": 15,
                                        "cuisine": "Mediterranean",
                                        "tags": ["quick", "healthy", "salad"],
                                    },
                                ]
                            },
                        }
                    }
                }
            },
        },
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Server error during suggestion generation"},
    },
)
@limiter.limit("10/minute")
async def suggest_meals(
    request: Request,  # noqa: ARG001 - required by slowapi rate limiter
    body: MealSuggestRequest = MealSuggestRequest(),
) -> MealSuggestResponse:
    """Generate 3 personalized dinner suggestions.

    Queries recent meal history and liked recipes from the database,
    then uses Claude LLM to generate varied dinner suggestions that
    respect user preferences and available ingredients.

    Optionally accepts user constraints (e.g., "I have chicken thighs")
    to further personalize suggestions.

    Args:
        request: Starlette Request object (required by slowapi rate limiter)
        body: Optional MealSuggestRequest with requirements

    Returns:
        MealSuggestResponse with 3 meal suggestions

    Raises:
        HTTPException 429: Rate limit exceeded
        HTTPException 500: Server error during suggestion generation
    """
    try:
        suggestions = await meal_service.get_suggestions(
            requirements=body.requirements,
            claude_service=claude_service,
        )
        return MealSuggestResponse(suggestions=suggestions)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Meal suggestion error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing error: {e!s}") from e
