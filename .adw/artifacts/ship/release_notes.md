## [Unreleased] - 2026-03-10

### Added
- Meal suggestion pydantic schemas (MealSuggestRequest, MealSuggestion, MealSuggestResponse)
- Meal suggestion system prompt with family preferences, store inventory, and JSON output format
- `suggest_meals` method to ClaudeService with retry logic and markdown code fence stripping
- MealService for meal suggestion orchestration (queries meal_history and recipe_feedback)
- Meals API route with POST /suggest endpoint and 10/minute rate limiting
- Meals router registered in main.py under /api/v1/meals

### Fixed
- Improve error handling for meal suggestion parsing

### Documentation
- Add meal suggestion endpoint feature documentation

### Other
- Add rate limiting tests for meals suggest endpoint
