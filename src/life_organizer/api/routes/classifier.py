"""Classification endpoint for user input."""

from fastapi import APIRouter, HTTPException

from life_organizer.config import KEYWORD_CONFIG, get_settings
from life_organizer.schemas.classification import ClassifiedInput
from life_organizer.schemas.requests import ClassifyRequest
from life_organizer.services.classifier import KeywordClassifier
from life_organizer.services.classifier_orchestrator import ClassifierOrchestrator
from life_organizer.services.claude_classifier import ClaudeClassifier

router = APIRouter()

# Initialize classifiers
settings = get_settings()
keyword_classifier = KeywordClassifier(keyword_config=KEYWORD_CONFIG)
claude_classifier = ClaudeClassifier(api_key=settings.claude_api_key)

# Initialize orchestrator
classifier = ClassifierOrchestrator(
    keyword_classifier=keyword_classifier,
    llm_classifier=claude_classifier,
)


@router.post("/classify", response_model=ClassifiedInput)
async def classify_input(request: ClassifyRequest) -> ClassifiedInput:
    """Classify user input and return category with confidence score.

    This endpoint analyzes text input using keyword matching to determine
    the intent category (expense, shopping, reminder, calendar) and extracts
    relevant structured data.

    Args:
        request: ClassifyRequest with input text

    Returns:
        ClassifiedInput with category, confidence, extracted data, and raw input

    Raises:
        HTTPException: If input validation fails or processing error occurs

    Example:
        Request:
            POST /classify
            {"input": "Spent 45 EUR at restaurant"}

        Response:
            {
                "category": "expense",
                "confidence": 0.92,
                "extracted_data": {
                    "amount": 45.0,
                    "currency": "EUR",
                    "merchant_hint": "restaurant"
                },
                "raw_input": "Spent 45 EUR at restaurant"
            }
    """
    try:
        # Validate input is not empty after stripping
        if not request.input.strip():
            raise HTTPException(status_code=422, detail="Input cannot be empty or whitespace only")

        # Classify the input using orchestrator
        result = await classifier.classify(request.input)

        return result

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log and return 500 for unexpected errors
        raise HTTPException(status_code=500, detail=f"Classification error: {e!s}") from e
