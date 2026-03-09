"""Classification schemas for processed user input."""

from typing import Literal

from pydantic import BaseModel, Field

from life_organizer.schemas.enums import Category


class ClassifiedInput(BaseModel):
    """Result of parsing user input through the budget classification engine.

    The engine analyzes raw user input and determines:
    - What category it belongs to (budget or unknown)
    - How confident it is in that classification (0.0-1.0)
    - What specific data was extracted (amounts, items, dates, etc.)

    Attributes:
        category: The classified category type
        confidence: Confidence score from 0.0 (no confidence) to 1.0 (certain)
        extracted_data: Dictionary of extracted structured data
        raw_input: Original unprocessed input text
    """

    category: Category = Field(..., description="Classified category of the input")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)", ge=0.0, le=1.0)
    extracted_data: dict[str, object] = Field(
        default_factory=dict,
        description="Extracted structured data (amounts, items, categories, etc.)",
    )
    raw_input: str = Field(..., description="Original raw input text")
    classifier_source: Literal["keyword", "llm"] = Field(
        ..., description="Source classifier that produced this result"
    )
