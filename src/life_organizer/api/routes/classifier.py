"""Process endpoint for user input."""

from fastapi import APIRouter, HTTPException

from life_organizer.config import KEYWORD_CONFIG, get_settings
from life_organizer.handlers import get_handler
from life_organizer.schemas.requests import ClassifyRequest
from life_organizer.schemas.responses import ActionResult
from life_organizer.services.classifier import KeywordClassifier
from life_organizer.services.classifier_orchestrator import ClassifierOrchestrator
from life_organizer.services.claude_classifier import ClaudeClassifier

router = APIRouter()

# Initialize classifiers
settings = get_settings()
keyword_classifier = KeywordClassifier(keyword_config=KEYWORD_CONFIG)
claude_classifier = ClaudeClassifier(api_key=settings.claude_api_key)

# Initialize orchestrator
orchestrator = ClassifierOrchestrator(
    keyword_classifier=keyword_classifier,
    llm_classifier=claude_classifier,
)


@router.post("/process", response_model=ActionResult)
async def process_input(request: ClassifyRequest) -> ActionResult:
    """Classify user input and execute the appropriate handler.

    This endpoint combines classification and handler execution. It classifies
    the input, finds the appropriate handler, and executes it to return an
    ActionResult with app actions or backend-handled responses.

    Args:
        request: ClassifyRequest with input text

    Returns:
        ActionResult with action type, message, and optional app_action

    Raises:
        HTTPException: If input validation fails or processing error occurs

    Example:
        Request:
            POST /process
            {"input": "spent 120eur at next"}

        Response:
            {
                "success": true,
                "action_type": "app_action_required",
                "message": "Logged expenses: 234.6 BGN in Clothes",
                "app_action": {
                    "type": "log_budget_entry",
                    "amount": 234.6,
                    "date": "2025-11-03",
                    "transaction_type": "Expenses",
                    "category": "Clothes",
                    "details": "next"
                }
            }
    """
    try:
        # Validate input is not empty after stripping
        if not request.input.strip():
            raise HTTPException(status_code=422, detail="Input cannot be empty or whitespace only")

        # Classify the input using orchestrator
        classified = await orchestrator.classify(request.input)

        # Find appropriate handler
        handler = get_handler(classified)

        if not handler:
            # No handler found, return confirmation needed
            from life_organizer.schemas.enums import ActionType

            return ActionResult(
                success=False,
                action_type=ActionType.CONFIRMATION_NEEDED,
                message=f"No handler available for category: {classified.category}",
            )

        # Execute handler
        result = await handler.execute(classified)

        return result

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log and return 500 for unexpected errors
        raise HTTPException(status_code=500, detail=f"Processing error: {e!s}") from e
