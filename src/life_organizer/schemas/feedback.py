"""Pydantic schemas for misclassification feedback endpoint."""

from pydantic import BaseModel, Field, field_validator, model_validator

from life_organizer.schemas.enums import Category


class FeedbackRequest(BaseModel):
    """Request schema for submitting misclassification feedback.

    Attributes:
        original_input: The original user input that was misclassified
        wrong_category: The category incorrectly assigned by the classifier
        correct_category: The correct category as identified by the user
    """

    original_input: str = Field(min_length=1, max_length=1000)
    wrong_category: Category
    correct_category: Category

    @field_validator("wrong_category", "correct_category", mode="before")
    @classmethod
    def normalize_category(cls, v: object) -> object:
        """Normalize category input to lowercase for case-insensitive matching."""
        if isinstance(v, str):
            return v.lower()
        return v

    @field_validator("original_input")
    @classmethod
    def original_input_not_blank(cls, v: str) -> str:
        """Validate that original_input is not whitespace-only."""
        if not v.strip():
            msg = "original_input must not be empty or whitespace-only"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def categories_must_differ(self) -> "FeedbackRequest":
        """Validate that wrong_category and correct_category are different."""
        if self.wrong_category == self.correct_category:
            msg = "wrong_category and correct_category must differ"
            raise ValueError(msg)
        return self


class FeedbackResponse(BaseModel):
    """Response schema for feedback submission.

    Attributes:
        success: Whether the feedback was recorded successfully
        message: Human-readable message about the result
    """

    success: bool
    message: str
