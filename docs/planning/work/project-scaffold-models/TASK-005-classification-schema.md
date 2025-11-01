## TASK-005: Implement ClassifiedInput Schema

---
**Status:** COMPLETE
**Branch:** feature/project-scaffold-models
**Type:** IMPLEMENTATION
**Phase:** 1
**Depends On:** TASK-002 (needs Category enum)

---

### Overview

Create the ClassifiedInput Pydantic model that the classification engine will return. This model contains the category, confidence score, and extracted data from user input. Handlers receive this model to determine how to process the request.

### Files Modified

- `src/life_organizer/schemas/classification.py`
- `tests/schemas/test_classification.py`

### Implementation Steps

- [x] Create `src/life_organizer/schemas/classification.py`
- [x] Import BaseModel, Field from pydantic
- [x] Import Category enum from schemas.enums
- [x] Define ClassifiedInput model with fields: category, confidence, extracted_data, raw_input
- [x] Add Field() descriptions and validation (confidence 0.0-1.0)
- [x] Add comprehensive docstring explaining model purpose
- [x] Create `tests/schemas/test_classification.py`
- [x] Write test for valid classification with extracted data
- [x] Write test for confidence score validation (must be 0.0-1.0)
- [x] Write test for unknown category with low confidence
- [x] Write test for JSON serialization

### Code Example

**File: `src/life_organizer/schemas/classification.py`**

```python
"""Classification schemas for processed user input."""

from pydantic import BaseModel, Field

from life_organizer.schemas.enums import Category


class ClassifiedInput(BaseModel):
    """Result of classifying user input through the classification engine.

    The classification engine analyzes raw user input and determines:
    - What category it belongs to (expense, shopping, reminder, etc.)
    - How confident it is in that classification (0.0-1.0)
    - What specific data was extracted (amounts, items, dates, etc.)

    Handlers use this classification to determine if they can handle the input
    and what actions to take.

    Attributes:
        category: The classified category type
        confidence: Confidence score from 0.0 (no confidence) to 1.0 (certain)
        extracted_data: Dictionary of extracted structured data
        raw_input: Original unprocessed input text
    """

    category: Category = Field(..., description="Classified category of the input")
    confidence: float = Field(
        ..., description="Confidence score (0.0-1.0)", ge=0.0, le=1.0
    )
    extracted_data: dict[str, object] = Field(
        default_factory=dict,
        description="Extracted structured data (amounts, items, categories, etc.)",
    )
    raw_input: str = Field(..., description="Original raw input text")
```

**Reference: Field validation pattern**

Similar to the ConfirmationData.confidence field, we use `ge=0.0, le=1.0` to enforce range validation. Pydantic will reject any confidence values outside this range automatically.

### Success Criteria

- [x] Build succeeds: `make lint`
- [x] All tests pass: `pytest tests/schemas/test_classification.py`
- [x] mypy type checking passes
- [x] Confidence field rejects values <0.0 or >1.0
- [x] extracted_data defaults to empty dict if not provided
- [x] Schema serializes to/from JSON correctly

### Verification Commands

```bash
# Run tests
pytest tests/schemas/test_classification.py -v

# Type checking
mypy src/life_organizer/schemas/classification.py

# Test validation
python -c "
from life_organizer.schemas.classification import ClassifiedInput
from life_organizer.schemas.enums import Category
classified = ClassifiedInput(
    category=Category.EXPENSE,
    confidence=0.95,
    extracted_data={'amount': 45, 'currency': 'EUR'},
    raw_input='Spent 45 euros at restaurant'
)
print(classified.model_dump_json())
"
```

### Notes

The extracted_data dict is intentionally flexible - different categories will extract different fields. For example, EXPENSE might extract {amount, currency, category}, while SHOPPING might extract {item, quantity}. This flexibility avoids needing separate classification models for each category.
