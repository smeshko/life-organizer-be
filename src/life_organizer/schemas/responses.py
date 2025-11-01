"""Response schemas for the Life Organizer API."""

from pydantic import BaseModel, Field

from life_organizer.schemas.actions import AppAction
from life_organizer.schemas.enums import ActionType


class ConfirmationData(BaseModel):
    """Data for confirmation requests when classification is uncertain.

    Attributes:
        question: Question to ask the user for clarification
        options: List of possible answers the user can choose from
        original_classification: What the system initially classified this as
        confidence: Confidence score (0.0-1.0) of original classification
    """

    question: str = Field(..., description="Question to ask user for clarification")
    options: list[str] = Field(..., description="List of possible answers", min_length=2)
    original_classification: str = Field(..., description="System's initial classification guess")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)", ge=0.0, le=1.0)


class ActionResult(BaseModel):
    """Result returned from handlers and serialized to API response.

    Different action_type values use different optional fields:
    - backend_handled: Only success, action_type, message
    - app_action_required: Includes app_action (discriminated union of action types)
    - confirmation_needed: Includes confirmation data

    Attributes:
        success: Whether the action was successful
        action_type: Type of action (backend_handled, app_action_required, confirmation_needed)
        message: Human-readable message about what happened
        app_action: Optional AppAction (CreateReminderAction | AddToShoppingListAction | CreateCalendarEventAction)
        confirmation: Optional confirmation data when user input is ambiguous
    """

    success: bool = Field(..., description="Whether the action was successful")
    action_type: ActionType = Field(..., description="Type of action performed/required")
    message: str = Field(..., description="Human-readable message about the result")
    app_action: AppAction | None = Field(
        default=None,
        description="iOS app action (when action_type is app_action_required). "
        "Discriminated union of CreateReminderAction | AddToShoppingListAction | CreateCalendarEventAction",
    )
    confirmation: ConfirmationData | None = Field(
        default=None,
        description="Confirmation request data (when action_type is confirmation_needed)",
    )
