# Meal Suggestion Endpoint

**Date:** 2026-03-10
**Related Files:** `src/life_organizer/api/routes/meals.py`, `src/life_organizer/services/meal_service.py`, `src/life_organizer/services/claude_service.py`, `src/life_organizer/schemas/meals.py`, `src/life_organizer/prompts/meals_suggest_prompt_v1.txt`

## Overview

The meal suggestion endpoint (`POST /api/v1/meals/suggest`) generates 3 personalized dinner suggestions using Claude LLM. It gathers context from the database (recent meal history and liked recipes), combines it with a system prompt containing user preferences and store inventory, and returns structured suggestions validated through Pydantic models.

## What Was Built

- **MealService** orchestrator: queries DB for context, delegates to ClaudeService for generation
- **ClaudeService.suggest_meals()**: LLM integration with retry logic and JSON response parsing
- **Pydantic schemas**: `MealSuggestRequest`, `MealSuggestion`, `MealSuggestResponse`
- **System prompt** (`meals_suggest_prompt_v1.txt`): family preferences, store inventory, output format
- **API route** with rate limiting (`10/minute`) and OpenAPI documentation

## Technical Implementation

### Key Files

- `src/life_organizer/api/routes/meals.py`: POST /suggest endpoint with rate limiting and error handling
- `src/life_organizer/services/meal_service.py`: Orchestrates DB queries + ClaudeService call
- `src/life_organizer/services/claude_service.py`: `suggest_meals()` method with retry and JSON parsing
- `src/life_organizer/schemas/meals.py`: Request/response Pydantic models
- `src/life_organizer/prompts/meals_suggest_prompt_v1.txt`: System prompt with inventory and rules

### Key Patterns

- **Service Orchestration**: `MealService` takes `session_factory` in constructor and `ClaudeService` as a method parameter. This avoids circular imports (ClaudeService imports from db module chain) by using `TYPE_CHECKING` guards. Follow this pattern for new LLM-powered services.
- **LLM Response Parsing**: Claude returns raw JSON text. The `suggest_meals()` method strips markdown code fences, parses JSON, then the caller validates with Pydantic `model_validate()`. Parse errors raise `HTTPException(500)` with raw response logged.
- **Retry with Exponential Backoff**: Uses `@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5), reraise=True)` for Claude API calls. Only `anthropic.APIError` is retried; parse errors are not.
- **Context Building**: User message is built from parts (history, liked recipes, requirements) joined by newlines. System prompt uses `cache_control: {"type": "ephemeral"}` for prompt caching.

### Code Examples

```python
# Creating a new service that follows MealService pattern
class NewService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def do_work(self, claude_service: ClaudeService) -> list[Schema]:
        async with self.session_factory() as db:
            # Query context from DB
            result = await db.execute(select(Model).where(...))
            context = result.scalars().all()

        # Call Claude with context
        raw = await claude_service.some_method(context=context)

        # Validate with Pydantic
        return [Schema.model_validate(item) for item in raw]
```

## How to Use

1. Send `POST /api/v1/meals/suggest` with optional body `{"requirements": "I have chicken thighs"}`
2. The endpoint queries the last 14 days of `meal_history` and top 10 liked recipes from `recipe_feedback`
3. Claude generates 3 suggestions respecting the store inventory and avoiding recent meals
4. Response returns `{"suggestions": [...]}`  with each suggestion containing name, ingredients, instructions, prep_time, cuisine, and tags
5. To regenerate, simply call the endpoint again (no server-side state)

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| Rate limit | string | `10/minute` | Max requests per minute per client |
| History window | int | 14 days | How far back to check meal history |
| Liked recipes limit | int | 10 | Max liked recipes included in context |
| Max tokens | int | 2000 | Claude response token limit |
| Retry attempts | int | 3 | Max retries on Claude API failure |

## Notes

- Regeneration (FR19) is handled by simply calling the endpoint again — no server-side state needed
- The store inventory in the system prompt is currently hardcoded; future stories may make it configurable
- `TYPE_CHECKING` import guard is required for `ClaudeService` in `meal_service.py` to avoid circular imports through the db session config chain
