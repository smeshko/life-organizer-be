"""Process endpoint for user input."""

from fastapi import APIRouter, HTTPException

from life_organizer.config import get_settings
from life_organizer.handlers import get_handler
from life_organizer.schemas.requests import ClassifyRequest
from life_organizer.schemas.responses import ProcessingResponse
from life_organizer.services.classifier_orchestrator import ClassifierOrchestrator
from life_organizer.services.claude_classifier import ClaudeClassifier

router = APIRouter()

# Initialize classifiers
settings = get_settings()
claude_classifier = ClaudeClassifier(api_key=settings.claude_api_key)

# Initialize orchestrator with LLM classifier
orchestrator = ClassifierOrchestrator(
    llm_classifier=claude_classifier,
)


@router.post(
    "/process",
    response_model=list[ProcessingResponse],
    response_description="List of transaction processing results (always an array, even for single transaction)",
    responses={
        200: {
            "description": "Successfully processed transaction(s)",
            "content": {
                "application/json": {
                    "examples": {
                        "single_transaction": {
                            "summary": "Single Transaction",
                            "value": [
                                {
                                    "success": True,
                                    "action_type": "backend_handled",
                                    "message": "Logged expenses: 98 BGN in Groceries",
                                    "app_action": None,
                                }
                            ],
                        },
                        "multi_transaction": {
                            "summary": "Multiple Transactions",
                            "value": [
                                {
                                    "success": True,
                                    "action_type": "backend_handled",
                                    "message": "Logged expenses: 98 BGN in Body care",
                                    "app_action": None,
                                },
                                {
                                    "success": True,
                                    "action_type": "backend_handled",
                                    "message": "Logged expenses: 234.6 BGN in Clothes",
                                    "app_action": None,
                                },
                                {
                                    "success": True,
                                    "action_type": "backend_handled",
                                    "message": "Logged expenses: 5 BGN in Eat out",
                                    "app_action": None,
                                },
                            ],
                        },
                        "partial_failure": {
                            "summary": "Partial Success",
                            "value": [
                                {
                                    "success": True,
                                    "action_type": "backend_handled",
                                    "message": "Logged expenses: 50 BGN in Groceries",
                                    "app_action": None,
                                },
                                {
                                    "success": False,
                                    "action_type": "backend_handled",
                                    "message": "Could not process budget entry: Missing required fields: amount",
                                    "app_action": None,
                                },
                            ],
                        },
                    }
                }
            },
        },
        422: {
            "description": "Validation error (empty input, too many transactions)",
        },
        500: {"description": "Server error during processing"},
        501: {"description": "Category not yet supported"},
    },
)
async def process_input(request: ClassifyRequest) -> list[ProcessingResponse]:
    """Process user input through classification and execute appropriate handler.

    The endpoint now supports multi-transaction parsing from a single natural language input.
    For example: "I spent 50 at DM, 120 at Next, 5 at the bakery"

    **Important:** The response is ALWAYS an array, even for single transactions.

    **Multi-transaction support:**
    - Detects and processes up to 15 transactions per input
    - Each transaction is independently validated and persisted
    - Partial success is possible (some transactions succeed, others fail)
    - Shared context like dates applies to all transactions unless overridden

    Args:
        request: ClassifyRequest with text input

    Returns:
        List of ProcessingResponse objects (one per detected transaction)

    Raises:
        HTTPException 422: Input validation failed or transaction limit exceeded
        HTTPException 500: Server error during processing
        HTTPException 501: Detected category is not yet supported
    """
    try:
        # Input validation
        if not request.input.strip():
            raise HTTPException(status_code=422, detail="Input cannot be empty or whitespace only")

        # Extract category and convert enum to string
        category = request.category.value if request.category else None

        # Classify input with category-specific prompt (returns List[ClassifiedInput])
        classified_list = await orchestrator.classify(request.input, category=category)

        # Validate we have results
        if not classified_list:
            raise HTTPException(status_code=500, detail="Classification returned empty list")

        # Get handler for budget category (all should be budget for now)
        # Assuming all transactions are same category (budget)
        handler = get_handler(classified_list[0])

        if not handler:
            raise HTTPException(
                status_code=501,
                detail=f"Category '{classified_list[0].category}' is not yet supported",
            )

        # Execute handler with list of classified inputs
        result_list = await handler.execute(classified_list)

        return result_list

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Generic error handler: 500
        raise HTTPException(status_code=500, detail=f"Processing error: {e!s}") from e
