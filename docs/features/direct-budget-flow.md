# Direct Budget Flow

**Date:** 2026-03-09
**Related Files:** `src/life_organizer/services/claude_service.py`, `src/life_organizer/services/budget_service.py`, `src/life_organizer/api/routes/budget.py`

## Overview

Replaces the ClassifierOrchestrator + ClaudeClassifier pattern with a direct two-service pipeline: `ClaudeService` parses natural language into structured `ClassifiedInput` objects, and `BudgetService` validates and persists them as `BudgetTransaction` records. This simplifies the request path from 3+ layers to a single endpoint calling two focused services.

## What Was Built

- **ClaudeService** - Async LLM service that parses budget text into `ClassifiedInput` objects using Claude API with retry logic
- **BudgetService** - Persistence service that validates parsed inputs, converts currencies, and atomically commits `BudgetTransaction` records
- **POST /api/v1/budget** - Single endpoint that accepts `{"input": "..."}` and returns an array of `ProcessingResponse` objects
- **Removed** `/api/v1/process` endpoint and `classifier.py` route

## Technical Implementation

### Key Files

- `src/life_organizer/services/claude_service.py`: LLM parsing service with prompt caching, and transaction count validation
- `src/life_organizer/services/budget_service.py`: Persistence service with currency conversion, field validation, and atomic DB writes
- `src/life_organizer/api/routes/budget.py`: Route handler that wires ClaudeService -> BudgetService and includes OpenAPI examples

### Key Patterns

- **Module-level prompt loading**: The budget system prompt is loaded once at import time from `prompts/budget_system_prompt_v2.txt`. Date placeholders are injected per-request via `_get_system_prompt_with_current_date()`.

- **One attempt, no retries**: `parse_budget_text()` makes a single call. The client has `max_retries=0` and a 55 s timeout, so a slow Opus 5.5 response has nearly all of the iOS 60 s timeout, and a timed-out generation is never sent and billed twice.

- **Beta messages call**: `client.beta.messages.create` with `betas=["server-side-fallback-2026-07-01"]`, `fallbacks="default"`, `output_config={"effort": CLAUDE_EFFORT}` and `max_tokens=16000`. The first `text` block is parsed, so thinking blocks are skipped.

- **Refusals**: `stop_reason == "refusal"` is logged with its category and returned as an `UNKNOWN` input carrying an error, which `BudgetService` turns into a `success: false` row.

- **Prompt caching**: The system prompt is sent with `cache_control: {"type": "ephemeral"}` to reduce API costs on repeated calls.

- **Atomic batch persistence**: `BudgetService.create_entries()` processes all inputs in a single session. If the DB commit fails, all success responses are retroactively marked as failures — no partial writes.

- **Constructor-injected dependencies**: Both services accept their dependencies (API key, session factory) via constructor, making them testable with mocks.

### Code Examples

```python
# How the endpoint wires the two services together
classified_list = await claude_service.parse_budget_text(request.input)
return await budget_service.create_entries(classified_list)
```

```python
# Creating a testable BudgetService instance
from sqlalchemy.ext.asyncio import async_sessionmaker
budget_service = BudgetService(session_factory=async_session_factory)
results = await budget_service.create_entries(classified_inputs)
```

## How to Use

1. Send a POST request to `/api/v1/budget` with JSON body `{"input": "coffee 4.50, lunch 12 eur"}`
2. The endpoint parses the text via Claude, returning one `ProcessingResponse` per detected transaction
3. Each response indicates `success: true/false` with a descriptive message
   - `transactions` holds the transaction the result created, with its database `id` (the same id `PATCH`/`DELETE /api/v1/budget/transactions/{id}` take). It is filled only after the commit succeeds; a failed result, including every result of a failed commit, has `transactions: []`
   - `image_index` is always `null` for text input
4. For bulk exports, use `GET /api/v1/budget/export?start_date=YYYY-MM-DD` to get TSV output

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `CLAUDE_API_KEY` | env var | (required) | Anthropic API key for Claude |
| `CLAUDE_MODEL` | env var | `claude-opus-5-5` | Model used for parsing |
| `CLAUDE_EFFORT` | env var | `low` | Claude output effort (`low`, `medium`, `high`, `xhigh`, `max`) |
| Max transactions | hardcoded | 15 | Maximum transactions per request |
| USD_TO_EUR_RATE | constant | 0.92 | Static conversion rate |
| BGN_PER_EUR_RATE | constant | 1.95583 | Fixed euro peg (BGN per EUR) |

## Notes

- The `ClassifiedInput` schema is retained as the internal contract between ClaudeService and BudgetService
- Currency conversion uses a static USD rate (`USD_TO_EUR_RATE = 0.92`) and the fixed BGN peg (`BGN_PER_EUR_RATE = 1.95583`); EUR, USD and BGN are supported, other currencies default to EUR
- The `BudgetTransaction` DB model is unchanged from the previous implementation
- Transaction count is estimated via comma/and heuristics before calling the API to fail fast on oversized inputs
