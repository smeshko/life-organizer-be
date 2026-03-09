"""Response schemas for the Life Organizer API."""

from pydantic import BaseModel, Field

from life_organizer.schemas.enums import ActionType


class ProcessingResponse(BaseModel):
    """Result returned from budget processing, serialized to API response.

    Attributes:
        success: Whether the action was successful
        action_type: Type of action (backend_handled)
        message: Human-readable message about what happened
    """

    success: bool = Field(..., description="Whether the action was successful")
    action_type: ActionType = Field(..., description="Type of action performed/required")
    message: str = Field(..., description="Human-readable message about the result")
