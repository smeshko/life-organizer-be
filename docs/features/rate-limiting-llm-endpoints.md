# Rate Limiting for LLM Endpoints

**Date:** 2026-03-09
**Related Files:** `src/life_organizer/rate_limit.py`, `src/life_organizer/main.py`, `src/life_organizer/api/routes/budget.py`

## Overview

Rate limiting is applied to endpoints that call the Claude LLM API to prevent accidental or abusive usage from causing unexpected API costs. The implementation uses `slowapi` (built on the `limits` library) with in-memory storage, appropriate for the single-user deployment model.

## What Was Built

- Centralized `Limiter` instance in a dedicated module to avoid circular imports
- Custom 429 exception handler that guarantees a `Retry-After` header in responses
- Rate limit decorator applied to `POST /api/v1/budget` (10 requests/minute)
- Comprehensive test suite covering limit enforcement and non-LLM endpoint exclusion

## Technical Implementation

### Key Files

- `src/life_organizer/rate_limit.py`: Singleton `Limiter` instance using `get_remote_address` as key function
- `src/life_organizer/main.py`: Attaches limiter to `app.state`, registers custom exception handler
- `src/life_organizer/api/routes/budget.py`: Applies `@limiter.limit("10/minute")` to the POST endpoint
- `tests/api/test_rate_limiting.py`: Tests for limit enforcement, 429 responses, and non-LLM endpoint exclusion

### Key Patterns

- **Separate limiter module**: The `Limiter` instance lives in `rate_limit.py` (not `main.py`) to avoid circular imports when route modules need to import it. Both `main.py` and route files import from `life_organizer.rate_limit`.

- **Custom exception handler**: Instead of slowapi's default `_rate_limit_exceeded_handler`, a custom handler in `main.py` ensures the `Retry-After` header is always present and the error body follows the app's `{"error": "..."}` convention.

- **Decorator + Request parameter**: Every rate-limited endpoint must add `request: Request` as its first parameter (required by slowapi) and apply the `@limiter.limit()` decorator above the function definition.

### Adding Rate Limiting to a New Endpoint

```python
from fastapi import Request
from life_organizer.rate_limit import limiter

@router.post("/")
@limiter.limit("10/minute")
async def my_llm_endpoint(
    request: Request,  # noqa: ARG001 - required by slowapi
    body: MyRequestSchema,
) -> MyResponseSchema:
    ...
```

### Test Pattern for Rate Limiting

```python
from life_organizer.rate_limit import limiter

@pytest.fixture(autouse=True)
def _reset_limiter():
    """Reset rate limiter state between tests."""
    limiter.reset()
    yield
    limiter.reset()
```

## How to Use

1. Import `limiter` from `life_organizer.rate_limit`
2. Add `@limiter.limit("10/minute")` decorator to the endpoint function
3. Add `request: Request` as the first parameter (annotate with `# noqa: ARG001` if unused)
4. Non-LLM endpoints should NOT have the decorator — only endpoints that call the Claude API

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| Rate limit | String | `"10/minute"` | Per-endpoint limit string (slowapi format) |
| Key function | Callable | `get_remote_address` | Client identification strategy |
| Storage | In-memory | Default | No Redis needed for single-user deployment |

## Notes

- In-memory storage means rate limit counters reset on app restart
- If the app scales to multi-process or multi-user, switch to Redis-backed storage
- The `Retry-After` header is hardcoded to 60 seconds (matching the 1-minute window)
- `POST /api/v1/meals/suggest` (Epic 3) should also get this decorator when created
