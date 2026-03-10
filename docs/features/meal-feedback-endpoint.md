# Meal Feedback and History Tracking

**Date:** 2026-03-10
**Related Files:** `src/life_organizer/api/routes/meals.py`, `src/life_organizer/services/meal_service.py`, `src/life_organizer/schemas/meals.py`

## Overview

Implements `POST /api/v1/meals/feedback` — a feedback endpoint that records user recipe ratings, tracks cooking history, and auto-saves liked LLM-generated recipes. This closes the meal suggestion feedback loop (FR20, FR21, FR22) so future suggestions improve over time and avoid repetition.

## What Was Built

- `MealFeedbackRequest` / `MealFeedbackResponse` Pydantic schemas with validation (`recipe_id > 0`, `recipe_name` max 255 chars)
- `MealService.save_feedback()` — atomic service method handling recipe lookup, liked-recipe auto-save, feedback recording, and history creation
- `POST /api/v1/meals/feedback` route with OpenAPI response documentation (201, 404, 422, 500)

## Technical Implementation

### Key Files

- `src/life_organizer/schemas/meals.py`: `MealFeedbackRequest` and `MealFeedbackResponse` schemas
- `src/life_organizer/services/meal_service.py`: `save_feedback()` method with all business logic
- `src/life_organizer/api/routes/meals.py`: `/feedback` endpoint using `Depends(get_db)` injection

### Key Patterns

- **Resolved Name Pattern**: When a `recipe_id` is provided, `save_feedback()` uses the recipe's canonical name (`recipe.name`) instead of the user-supplied `recipe_name` for feedback and history records. This prevents data inconsistency if the client sends a different name than what's stored.

- **Liked Recipe Auto-Save**: When `liked=True` and no `recipe_id` exists (LLM-generated recipe), a new `Recipe` is created with `source="liked"`, then `session.flush()` obtains the auto-generated ID so feedback/history records can reference it. The recipe is initialized with `times_made=1` and `last_made=today`.

- **Session Injection (`Depends(get_db)`)**: Unlike the `/suggest` endpoint which uses `session_factory` internally (because it manages its own session lifetime around LLM calls), the `/feedback` endpoint receives the session via FastAPI dependency injection. This is the preferred pattern for non-LLM endpoints — the `get_db` dependency handles commit on success and rollback on failure automatically.

### Code Examples

```python
# Request: Liked LLM-generated recipe (no recipe_id)
POST /api/v1/meals/feedback
{
    "recipe_name": "Greek Lemon Chicken",
    "liked": true,
    "notes": "great, would add more garlic"
}
# Result: Recipe saved with source="liked", feedback + history created

# Request: Feedback for known recipe
POST /api/v1/meals/feedback
{
    "recipe_id": 42,
    "recipe_name": "Greek Lemon Chicken",
    "liked": false
}
# Result: recipe.times_made incremented, last_made updated, feedback + history created
```

## How to Use

1. After a user tries a suggested meal, call `POST /api/v1/meals/feedback` with `recipe_name`, `liked`, and optionally `recipe_id` and `notes`
2. If the recipe came from `/suggest` (LLM-generated), omit `recipe_id` — it will be auto-saved if liked
3. If the recipe is already in the database, include `recipe_id` to update tracking fields
4. The endpoint returns `201` with `{"success": true, "message": "Feedback recorded"}`

## Notes

- `prep_time=1` is used for auto-saved liked recipes because the `check_prep_time_positive` DB constraint requires `prep_time > 0`
- No rate limiting on this endpoint (non-LLM, per architecture decision AD-6)
- Atomicity is ensured by the `get_db` dependency — all DB operations within a single session that commits or rolls back together
- `recipe_id` validation uses `gt=0` in the Pydantic schema to reject zero/negative IDs at the validation layer
