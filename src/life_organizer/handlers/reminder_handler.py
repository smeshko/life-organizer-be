"""Reminder handler for creating iOS reminders from natural language."""

import logging
from datetime import datetime
from typing import Union

from life_organizer.handlers.base import BaseHandler
from life_organizer.schemas.actions import CreateReminderAction
from life_organizer.schemas.classification import ClassifiedInput
from life_organizer.schemas.enums import ActionType, Category
from life_organizer.schemas.responses import ProcessingResponse

logger = logging.getLogger(__name__)


class ReminderHandler(BaseHandler):
    """Handler for reminder creation requests.

    Processes LLM-classified reminder inputs with pre-extracted structured data
    and returns CreateReminderAction for the iOS app to execute.

    This handler does not persist data to the database - all reminder creation
    is delegated to the iOS Reminders app via the returned app action.

    Handles:
    - "remind me to call mom tomorrow at 5pm"
    - "don't forget to buy groceries"
    - "set a reminder for Friday to submit report"
    """

    def can_handle(self, classified_input: ClassifiedInput) -> bool:
        """Determine if this handler can process the input.

        Args:
            classified_input: Classified user input

        Returns:
            True if category is REMINDER
        """
        return classified_input.category == Category.REMINDER

    def requires_app_action(self) -> bool:
        """Determine if this handler requires iOS app involvement.

        Returns:
            True - reminders are created in iOS Reminders app
        """
        return True

    async def execute(
        self, classified_inputs: Union[list[ClassifiedInput], ClassifiedInput]
    ) -> list[ProcessingResponse]:
        """Process reminder requests and return CreateReminderAction for iOS.

        Args:
            classified_inputs: List (or single) of classifications with extracted_data containing:
                - title (str, required): The action/task to remember
                - due_date (str, optional): ISO 8601 datetime when reminder is due
                - notes (str, optional): Additional context

        Returns:
            List of ProcessingResponse objects with CreateReminderAction for each input.
        """
        # Normalize to list
        if isinstance(classified_inputs, ClassifiedInput):
            classified_inputs = [classified_inputs]

        results: list[ProcessingResponse] = []

        for classified_input in classified_inputs:
            try:
                # Validate required field: title
                title = classified_input.extracted_data.get("title")
                if not title:
                    raise ValueError("Could not extract reminder title from input")

                title_str = str(title)

                # Parse due_date if present (ISO 8601 format)
                due_date: datetime | None = None
                due_date_raw = classified_input.extracted_data.get("due_date")
                if due_date_raw:
                    try:
                        due_date = datetime.fromisoformat(str(due_date_raw))
                    except ValueError as e:
                        logger.warning(f"Invalid due_date format '{due_date_raw}': {e}")
                        # Continue without due_date rather than failing

                # Extract notes if present
                notes_raw = classified_input.extracted_data.get("notes")
                notes: str | None = str(notes_raw) if notes_raw else None

                # Create the app action
                app_action = CreateReminderAction(
                    title=title_str,
                    due_date=due_date,
                    list_id=None,  # Let iOS app use default list
                    notes=notes,
                )

                # Build success message
                if due_date:
                    message = f"Reminder ready to create: '{title_str}' due {due_date.strftime('%b %d at %I:%M %p')}"
                else:
                    message = f"Reminder ready to create: '{title_str}'"

                results.append(
                    ProcessingResponse(
                        success=True,
                        action_type=ActionType.APP_ACTION_REQUIRED,
                        message=message,
                        app_action=app_action,
                    )
                )

            except ValueError as e:
                logger.warning(f"Reminder validation error: {e}")
                results.append(
                    ProcessingResponse(
                        success=False,
                        action_type=ActionType.APP_ACTION_REQUIRED,
                        message=str(e),
                    )
                )

            except Exception as e:
                logger.error(f"Unexpected error processing reminder: {e}")
                results.append(
                    ProcessingResponse(
                        success=False,
                        action_type=ActionType.APP_ACTION_REQUIRED,
                        message=f"An error occurred processing your reminder: {e!s}",
                    )
                )

        return results
