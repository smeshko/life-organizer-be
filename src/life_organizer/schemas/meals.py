"""Pydantic schemas for meal suggestion endpoint."""

from pydantic import BaseModel, Field


class MealSuggestRequest(BaseModel):
    """Request schema for meal suggestion endpoint.

    Attributes:
        requirements: Optional user constraints (e.g., "I have chicken thighs")
    """

    requirements: str | None = Field(default=None)


class MealSuggestion(BaseModel):
    """Schema for a single meal suggestion returned by the LLM.

    Attributes:
        name: Name of the meal
        ingredients: List of ingredient strings
        instructions: Cooking instructions
        prep_time: Preparation time in minutes
        cuisine: Cuisine type (e.g., "Italian")
        tags: List of tags (e.g., ["dinner", "pasta"])
    """

    name: str
    ingredients: list[str]
    instructions: str
    prep_time: int
    cuisine: str
    tags: list[str]


class MealSuggestResponse(BaseModel):
    """Response schema for meal suggestion endpoint.

    Attributes:
        suggestions: List of meal suggestions
    """

    suggestions: list[MealSuggestion]


class MealFeedbackRequest(BaseModel):
    """Request schema for meal feedback endpoint.

    Attributes:
        recipe_id: Optional ID of an existing recipe
        recipe_name: Name of the recipe (always required)
        liked: Whether the user liked the recipe
        notes: Optional feedback notes
    """

    recipe_id: int | None = Field(default=None, gt=0)
    recipe_name: str = Field(min_length=1, max_length=255)
    liked: bool
    notes: str | None = Field(default=None)


class MealFeedbackResponse(BaseModel):
    """Response schema for meal feedback endpoint.

    Attributes:
        success: Whether the feedback was recorded
        message: Status message
    """

    success: bool
    message: str
