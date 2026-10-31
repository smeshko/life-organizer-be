"""Response schemas for the Life Organizer API."""

from pydantic import BaseModel, Field

from life_organizer.schemas.budget import TransactionItem
from life_organizer.schemas.enums import ActionType


class ProcessingResponse(BaseModel):
    """Result returned from budget processing, serialized to API response.

    Attributes:
        success: Whether the action was successful
        action_type: Type of action (backend_handled)
        message: Human-readable message about what happened
        transactions: Transactions this result created (empty when it created none)
        image_index: Zero-based upload index of the source image (image captures only)
    """

    success: bool = Field(..., description="Whether the action was successful")
    action_type: ActionType = Field(..., description="Type of action performed/required")
    message: str = Field(..., description="Human-readable message about the result")
    transactions: list[TransactionItem] = Field(
        default_factory=list,
        description="Transactions this result created; empty when it created none",
    )
    image_index: int | None = Field(
        default=None,
        description=(
            "Zero-based index, in upload order, of the image this result came from "
            "(image captures only)"
        ),
    )
