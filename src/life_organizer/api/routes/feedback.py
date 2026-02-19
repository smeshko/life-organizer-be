"""Feedback endpoint for misclassification corrections."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from life_organizer.db.models.feedback import MisclassificationFeedback
from life_organizer.db.session import get_db
from life_organizer.schemas.feedback import FeedbackRequest, FeedbackResponse

router = APIRouter()


@router.post("/", status_code=201, response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
) -> FeedbackResponse:
    """Submit misclassification feedback.

    Records a user correction when the classifier assigns the wrong category.

    Args:
        request: Feedback payload with original_input and category corrections
        db: Database session (injected via dependency)

    Returns:
        FeedbackResponse confirming feedback was recorded
    """
    feedback = MisclassificationFeedback(
        original_input=request.original_input,
        wrong_category=request.wrong_category.value,
        correct_category=request.correct_category.value,
    )
    db.add(feedback)

    return FeedbackResponse(success=True, message="Feedback recorded")
