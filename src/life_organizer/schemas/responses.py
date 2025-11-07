"""Response schemas for the Life Organizer API."""

from pydantic import BaseModel, Field

from life_organizer.schemas.actions import AppAction
from life_organizer.schemas.enums import ActionType


class ActionResult(BaseModel):
    """Result returned from handlers and serialized to API response.

    Different action_type values use different optional fields:
    - backend_handled: Only success, action_type, message
    - app_action_required: Includes app_action (discriminated union of action types)

    Attributes:
        success: Whether the action was successful
        action_type: Type of action (backend_handled, app_action_required)
        message: Human-readable message about what happened
        app_action: Optional AppAction (CreateReminderAction | AddToShoppingListAction | CreateCalendarEventAction)
    """

    success: bool = Field(..., description="Whether the action was successful")
    action_type: ActionType = Field(..., description="Type of action performed/required")
    message: str = Field(..., description="Human-readable message about the result")
    app_action: AppAction | None = Field(
        default=None,
        description="iOS app action (when action_type is app_action_required). "
        "Discriminated union of CreateReminderAction | AddToShoppingListAction | CreateCalendarEventAction",
    )
