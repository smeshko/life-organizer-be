"""Request schemas for the Life Organizer API."""

from datetime import datetime

from pydantic import BaseModel, Field

from life_organizer.schemas.enums import Category


class ProcessInputRequest(BaseModel):
    """Request model for processing user voice/text input.

    This is the primary API contract between the iOS app and backend.
    The backend validates, classifies, and routes the input to appropriate handlers.

    Attributes:
        user_id: Identifier for the family member making the request
        input: Raw voice or text input from the user
        timestamp: When the input was captured (ISO 8601 format)
    """

    user_id: str = Field(
        ...,
        description="Family member identifier (e.g., 'family_member_123')",
        min_length=1,
    )
    input: str = Field(
        ...,
        description="Voice or text input from user (e.g., 'Spent 45 euros at restaurant')",
        min_length=1,
    )
    timestamp: datetime = Field(..., description="When the input was captured (ISO 8601 format)")


class ClassifyRequest(BaseModel):
    """Request model for classifying user input.

    Simplified request for the classification endpoint that only requires
    the text input without user context or timestamp.

    Attributes:
        input: Text input to classify (e.g., 'Spent 45 euros at restaurant')
        category: Pre-classified category from front-end (optional, defaults to note)
    """

    input: str = Field(
        ...,
        description="Text input to classify",
        min_length=1,
        max_length=1000,
    )
    category: Category | None = Field(
        default=None,
        description="Pre-classified category from front-end (optional, defaults to note if not provided)",
    )
