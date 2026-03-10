---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7]
inputDocuments:
  - '_bmad-output/prd.md'
  - '_bmad-output/index.md'
workflowType: 'architecture'
lastStep: 7
project_name: 'life-organizer-be'
user_name: 'Ivo'
date: '2026-03-09'
status: 'complete'
projectType: 'brownfield'
---

# Architecture Decision Document - life-organizer-be

> Personal backend API: budget tracking + meal planning, powered by Claude LLM
> Generated via BMAD Architecture Workflow

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
- 35 FRs across 8 capability areas
- Budget domain: 18 FRs (text input, screenshot import, management, frontend API)
- Meal domain: 7 FRs (suggestions, feedback, history)
- System: 10 FRs (feedback, rate limiting, cleanup)

**Non-Functional Requirements:**
- Performance: tiered response times (< 1s text, < 5s vision, < 3s generation, < 200ms non-LLM)
- Reliability: zero data loss, atomic transactions, graceful LLM failure
- Security: rate limiting on LLM endpoints (5-10 req/min), env-based secrets

**Scale & Complexity:**
- Primary domain: API backend with LLM integration
- Complexity level: Low-Medium
- Single user, personal tool
- Estimated architectural components: ~8

### Technical Constraints & Dependencies

- **Existing stack:** Python 3.13, FastAPI, PostgreSQL 16, async SQLAlchemy 2.0, Claude API
- **Brownfield:** Must preserve working budget flow while removing orchestrator
- **Claude API dependency:** Text completions (Haiku 4.5) + Vision API for screenshots + generative for meals
- **No authentication:** Personal tool, rate limiting is sole abuse protection
- **iOS client dependency:** Budget text input format must remain compatible

### Cross-Cutting Concerns

1. **LLM Service Abstraction** — three modes (text parse, vision extract, generative suggest)
2. **Rate Limiting** — selective middleware for LLM endpoints only
3. **Error Handling** — consistent error response format across all endpoints
4. **Image Handling** — multipart form-data support (new)
5. **Database Schema Evolution** — new tables alongside existing ones
6. **API Documentation** — FastAPI's auto-generated Swagger UI at `/api/v1/docs` must remain enabled for all endpoints (NFR11)

## Starter Template Evaluation

### Primary Technology Domain

**API Backend** — existing brownfield project, no starter template needed.

### Existing Stack (Retained)

| Decision | Choice | Version |
|----------|--------|---------|
| **Language & Runtime** | Python | 3.13 |
| **Framework** | FastAPI | latest |
| **Database** | PostgreSQL | 16 |
| **ORM** | SQLAlchemy (async) | 2.0 |
| **DB Driver** | asyncpg | latest |
| **Migrations** | Alembic | latest |
| **LLM SDK** | anthropic | latest |
| **Testing** | pytest + pytest-asyncio | latest |
| **Linting** | Ruff | latest |
| **Type Checking** | MyPy (strict) | latest |
| **Retry Logic** | tenacity | latest |

### New Dependencies

| Dependency | Purpose | Version |
|------------|---------|---------|
| **slowapi** | Rate limiting for FastAPI | latest |
| **python-multipart** | Multipart form-data (image upload) | latest |

No new infrastructure dependencies. Same PostgreSQL instance, same deployment target.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (block implementation):**
1. How to restructure the LLM service for three interaction modes
2. How to handle image upload and Vision API calls
3. New database schema for meals and budget plans
4. How to remove orchestrator without breaking budget

**Important Decisions (shape architecture):**
5. Rate limiting approach
6. Meal suggestion prompt design strategy
7. Budget frontend API query patterns

**Deferred Decisions (post-MVP):**
- Preference learning algorithm
- Recipe deduplication strategy

### AD-1: LLM Service Restructure

**Decision:** Replace `ClaudeClassifier` + `ClassifierOrchestrator` with a single `ClaudeService` that supports three interaction modes.

**Current state:**
- `ClassifierOrchestrator` — pass-through wrapper, serves no purpose
- `ClaudeClassifier` — tightly coupled to classification (text in → structured JSON out)

**New `ClaudeService` design:**

```python
class ClaudeService:
    """Unified Claude API interface supporting text, vision, and generative modes."""

    async def parse_budget_text(self, text: str) -> list[ClassifiedInput]:
        """Parse natural language budget entries. Uses existing budget prompt v2."""

    async def parse_budget_images(self, images: list[bytes]) -> list[ClassifiedInput]:
        """Extract transactions from Revolut screenshots using Vision API."""

    async def suggest_meals(self, requirements: str | None, history: list, recipes: list) -> list[MealSuggestion]:
        """Generate 3 dinner suggestions using generative mode."""
```

**Rationale:**
- Single service, three methods — clear separation of concerns without over-abstraction
- Each method uses different Claude API parameters (text-only vs vision vs generative)
- Shared infrastructure: retry logic, error handling, API client
- Prompt management stays file-based (one prompt file per mode)

**What gets deleted:**
- `classifier_orchestrator.py` — entirely removed
- `ClaudeClassifier` class — replaced by `ClaudeService`
- Handler registry pattern (`get_handler`, `HANDLERS` list) — no longer needed

### AD-2: Image Upload & Vision API

**Decision:** Accept images via `UploadFile` (FastAPI's multipart support), send raw bytes to Claude Vision API.

**Flow:**
```
iOS sends multipart/form-data with 1+ images
  → FastAPI receives as list[UploadFile]
  → Read bytes from each file
  → Send to Claude Vision API with budget extraction prompt
  → Parse structured JSON response (same format as text parsing)
  → Route through same budget entry persistence logic
```

**API design:**
- Same endpoint `POST /api/v1/budget` handles both text and images
- Content-Type determines mode: `application/json` → text, `multipart/form-data` → images
- Two separate route functions, same path, different content types

**Vision prompt:** New prompt file `budget_vision_prompt_v1.txt` — instructs Claude to extract transactions from Revolut screenshot format specifically. Returns same JSON structure as text parsing.

### AD-3: Database Schema Design

**Decision:** Three PostgreSQL schemas: `budget` (existing), `meals` (new), `feedback` (existing).

**New tables:**

**`budget.plans`** (budget planning grid):
```
id: int (PK)
year: int
month: int (1-12)
transaction_type: str ("Expenses" | "Income" | "Savings")
category: str
planned_amount: Decimal(10,2)
created_at: datetime
updated_at: datetime

UNIQUE(year, month, transaction_type, category)
```

**`meals.recipes`** (curated recipe collection):
```
id: int (PK)
name: str
ingredients: JSON (list of strings)
instructions: str
prep_time: int (minutes)
cuisine: str
tags: JSON (list of strings)
source: str ("seeded" | "llm_generated" | "liked")
times_made: int (default 0)
last_made: date | null
created_at: datetime
updated_at: datetime
```

**`meals.meal_history`** (what was cooked and when):
```
id: int (PK)
recipe_id: int (FK → meals.recipes) | null
recipe_name: str (denormalized for LLM-generated meals not saved)
cooked_date: date
created_at: datetime
```

**`meals.recipe_feedback`** (user ratings):
```
id: int (PK)
recipe_id: int (FK → meals.recipes) | null
recipe_name: str (denormalized)
liked: bool
notes: str | null
created_at: datetime
```

**Rationale:**
- Schema separation (`budget.*`, `meals.*`, `feedback.*`) keeps domains isolated
- `recipe_name` denormalized on history/feedback because LLM-generated suggestions may not be saved as recipes
- `meals.recipes` stores both seeded recipes and liked LLM-generated ones
- Budget plans use a composite unique constraint — one planned amount per category/month/year

### AD-4: Orchestrator Removal & Budget Simplification

**Decision:** Remove the orchestrator layer entirely. Budget route calls `ClaudeService` directly.

**Current flow:**
```
POST /process → orchestrator.classify() → classifier.classify() → get_handler() → handler.execute()
```

**New flow:**
```
POST /budget (text) → claude_service.parse_budget_text() → persist_budget_entries()
POST /budget (images) → claude_service.parse_budget_images() → persist_budget_entries()
```

**What changes:**
- `api/routes/classifier.py` → **deleted** (replaced by budget route)
- `api/routes/budget.py` → **expanded** (handles text input, image input, export, transactions, plans, years)
- `handlers/` directory → **deleted entirely** (handler abstraction removed)
- Budget persistence logic moves from `BudgetEntryHandler.execute()` into a `budget_service.py`
- The `BudgetService` handles validation, currency conversion, and DB persistence

**What stays identical:**
- Budget prompt v2 — unchanged
- `ClassifiedInput` schema — still used as the LLM response format for budget parsing
- Database model `BudgetTransaction` — unchanged
- Currency conversion logic — moved to `BudgetService`

### AD-5: Rate Limiting

**Decision:** Use `slowapi` (built on `limits`) for rate limiting on LLM endpoints.

**Implementation:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/")
@limiter.limit("10/minute")
async def create_budget_entry(request: Request, ...):
    ...

@router.post("/suggest")
@limiter.limit("10/minute")
async def suggest_meals(request: Request, ...):
    ...
```

**Scope:**
- `POST /api/v1/budget` (text and image) — 10/min
- `POST /api/v1/meals/suggest` — 10/min
- All other endpoints — no limit

**Rationale:** `slowapi` is the de facto FastAPI rate limiting library. In-memory storage is fine for single-user. No need for Redis.

### AD-6: Meal Suggestion Architecture

**Decision:** Stateless LLM generation with context injection per request.

**Flow:**
```
POST /meals/suggest { requirements?: "chicken thighs" }
  → Load system prompt (hardcoded preferences, inventory)
  → Query recent meal_history (last 14 days)
  → Query top-rated recipes from recipe_feedback
  → Inject context into prompt
  → Claude generates 3 suggestions as structured JSON
  → Return suggestions to client
```

**Prompt structure:**
```
System prompt (meals_suggest_prompt_v1.txt):
  - User preferences (dietary restrictions, allergies, cuisine preferences)
  - Store inventory (available/unavailable items)
  - Instructions for output format

User message (constructed per request):
  - Recent meal history: [list of last 14 days meals]
  - Liked recipes: [top rated from feedback]
  - User requirements: "{optional requirements text}"
  - "Suggest 3 dinner options for tonight."
```

**Response schema:**
```python
class MealSuggestion(BaseModel):
    name: str
    ingredients: list[str]
    instructions: str
    prep_time: int  # minutes
    cuisine: str
    tags: list[str]
```

**Recipe saving:** When user gives positive feedback, the suggested recipe gets saved to `meals.recipes` with `source="liked"`. This builds the curated collection over time.

### AD-7: Budget Frontend API Design

**Decision:** RESTful JSON endpoints for transaction queries, aggregations, and budget plan CRUD.

**`GET /api/v1/budget/transactions`**
```
Query params: start_date, end_date, transaction_type, category, page, page_size (default 50)
Response: { items: [...], total: int, page: int, page_size: int }
```

**`GET /api/v1/budget/transactions/aggregate`**
```
Query params: year, month (optional), transaction_type (optional)
Response: { period: {year, month?}, aggregations: [{ category, total_eur, count }] }
```

**`GET /api/v1/budget/plan/{year}`**
```
Response: { year: int, entries: [{ transaction_type, category, amounts: {1: x, 2: y, ...12: z} }] }
```
Returns the full grid for a year. Frontend handles row/column totals and "to be allocated" calculations.

**`PUT /api/v1/budget/plan/{year}`**
```
Request: { entries: [{ transaction_type, category, month, planned_amount }] }
Response: { success: true, updated: int }
```
Upserts — creates or updates budget plan entries.

**`GET /api/v1/budget/years`**
```
Response: { years: [2024, 2025, 2026] }
```
Distinct years from `budget.transactions` table.

### Decision Impact Analysis

**Implementation Sequence (recommended order):**
1. Remove orchestrator + handler registry (AD-4) — unblocks everything
2. Create `ClaudeService` (AD-1) — replaces old classifier
3. Restructure budget routes (AD-4, AD-7) — new endpoint structure
4. Add rate limiting (AD-5) — middleware setup
5. Add image upload support (AD-2) — new budget capability
6. Create meals schema + models (AD-3) — database foundation
7. Build meal suggestion endpoint (AD-6) — new feature
8. Build meal feedback endpoint (AD-6) — completes meals
9. Build budget frontend API (AD-7) — transactions, aggregations, plans

## Implementation Patterns & Consistency Rules

### Naming Patterns

**Database:**
- Schemas: `snake_case` (e.g., `budget`, `meals`, `feedback`)
- Tables: `snake_case` plural (e.g., `transactions`, `recipes`, `recipe_feedback`)
- Columns: `snake_case` (e.g., `transaction_type`, `planned_amount`, `created_at`)
- Foreign keys: `{referenced_table_singular}_id` (e.g., `recipe_id`)
- Indexes: `ix_{schema}_{table}_{column}` (e.g., `ix_budget_transactions_date`)

**API:**
- Endpoints: `snake_case` with resource nouns (e.g., `/budget/transactions`, `/meals/suggest`)
- Query params: `snake_case` (e.g., `start_date`, `page_size`, `transaction_type`)
- Request/response fields: `snake_case` (consistent with Python conventions)
- URL prefix: `/api/v1/`

**Code:**
- Files: `snake_case.py` (e.g., `claude_service.py`, `budget_service.py`)
- Classes: `PascalCase` (e.g., `ClaudeService`, `BudgetService`, `MealSuggestion`)
- Functions/methods: `snake_case` (e.g., `parse_budget_text`, `suggest_meals`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `PROMPT_VERSIONS`, `MAX_TRANSACTIONS`)

### Structure Patterns

**Service layer:**
- One service class per domain: `ClaudeService`, `BudgetService`, `MealService`
- Services are instantiated at module level in route files (same pattern as current `ClaudeClassifier`)
- Services accept dependencies via constructor (DB session factory, other services)

**Route organization:**
- One route file per domain: `budget.py`, `meals.py`, `feedback.py`
- Route files import and instantiate services
- Routes handle HTTP concerns only (request parsing, response formatting)
- Business logic lives in services

**Prompt management:**
- One prompt file per LLM interaction mode in `src/life_organizer/prompts/`
- Prompt files are plain text with placeholder markers for dynamic content
- Prompts loaded at module import time (cached in memory)
- Date injection happens at call time (existing pattern)

### API Response Formats

**Success response (single resource):**
```json
{ "field1": "value", "field2": "value" }
```

**Success response (list):**
```json
{ "items": [...], "total": 42, "page": 1, "page_size": 50 }
```

**Success response (action):**
```json
{ "success": true, "message": "description" }
```

**Error response:**
```json
{ "detail": "Human-readable error message" }
```
Uses FastAPI's default `HTTPException` format. Status codes: 400 (bad input), 404 (not found), 422 (validation), 429 (rate limit), 500 (server error).

### Error Handling Patterns

**LLM errors:** Catch `anthropic.APIError`, log details, return 500 with generic message. Never expose raw LLM errors to client.

**Validation errors:** Use Pydantic validators. FastAPI auto-returns 422 with field-level detail.

**Database errors:** Catch `SQLAlchemyError`, rollback transaction, return 500. Log full traceback.

**Rate limit errors:** `slowapi` auto-returns 429 with `Retry-After` header.

**Pattern:** All error handlers log the full error internally. Client receives clean, descriptive messages without implementation details.

### API Documentation

FastAPI's auto-generated Swagger UI must remain enabled at `/api/v1/docs` (NFR11). This is the existing behavior — do not disable it during the refactor. All new endpoints (budget, meals) must appear in the interactive docs with proper request/response schemas. FastAPI generates this automatically from Pydantic models and route type hints — no additional configuration needed as long as routes use typed parameters and response models.

### Testing Patterns

**Unit tests:** Mock external dependencies (Claude API, database). Test service methods and route handlers independently.

**Integration tests:** Use real database (test PostgreSQL). Test full request → response cycle.

**Prompt validation tests:** Send real inputs to Claude API. Validate structured output format. Existing pattern in `tests/integration/`.

**Test file location:** Mirror source structure under `tests/` (e.g., `tests/services/test_claude_service.py`).

**Fixtures:** Shared fixtures in `conftest.py` files at appropriate directory levels.

## Project Structure & Boundaries

### Complete Directory Structure

```
src/life_organizer/
├── __init__.py
├── main.py                              # FastAPI app, routers, lifespan, rate limiter setup
├── config.py                            # Pydantic settings (unchanged)
├── logging_config.py                    # Logging setup (unchanged)
├── api/
│   ├── __init__.py
│   └── routes/
│       ├── __init__.py
│       ├── budget.py                    # POST / (text+image), GET /export, /transactions, /transactions/aggregate, /plan/{year}, /years
│       ├── meals.py                     # POST /suggest, POST /feedback
│       └── feedback.py                  # POST / (unchanged)
├── db/
│   ├── __init__.py
│   ├── base.py                          # DeclarativeBase (unchanged)
│   ├── session.py                       # Engine, session factory (unchanged)
│   └── models/
│       ├── __init__.py
│       ├── budget.py                    # BudgetTransaction (existing) + BudgetPlan (new)
│       ├── meals.py                     # Recipe, MealHistory, RecipeFeedback (new)
│       └── feedback.py                  # MisclassificationFeedback (unchanged)
├── schemas/
│   ├── __init__.py
│   ├── enums.py                         # ActionType only (Category enum removed)
│   ├── budget.py                        # ExpenseCategory, IncomeCategory, SavingsCategory (unchanged)
│   ├── requests.py                      # BudgetTextRequest, MealSuggestRequest, FeedbackRequest
│   ├── responses.py                     # BudgetEntryResponse, MealSuggestionResponse, TransactionListResponse, etc.
│   ├── meals.py                         # MealSuggestion, RecipeFeedbackRequest (new)
│   └── feedback.py                      # FeedbackRequest, FeedbackResponse (unchanged)
├── services/
│   ├── __init__.py
│   ├── claude_service.py                # ClaudeService (replaces classifier + orchestrator)
│   ├── budget_service.py                # BudgetService (validation, persistence, queries, plans)
│   └── meal_service.py                  # MealService (suggestions, feedback, history)
└── prompts/
    ├── budget_system_prompt_v2.txt      # Budget text parsing (existing, unchanged)
    ├── budget_vision_prompt_v1.txt      # Budget screenshot extraction (new)
    └── meals_suggest_prompt_v1.txt      # Meal suggestion generation (new)

tests/
├── conftest.py
├── api/
│   ├── test_budget_routes.py
│   ├── test_meals_routes.py
│   └── test_feedback_routes.py
├── services/
│   ├── test_claude_service.py
│   ├── test_budget_service.py
│   └── test_meal_service.py
├── db/
│   ├── test_budget_models.py
│   ├── test_meal_models.py
│   └── test_feedback_model.py
├── schemas/
│   └── test_*.py
├── integration/
│   ├── test_budget_prompt_validation.py
│   └── test_meal_prompt_validation.py
└── fixtures/
    └── budget_prompt_test_cases.json

alembic/
└── versions/
    ├── (existing migrations)
    ├── xxx_create_budget_plans_table.py
    ├── xxx_create_meals_schema_and_tables.py
    └── xxx_remove_note_quote_cleanup.py
```

### Files Deleted (Cleanup)

```
DELETED:
├── src/life_organizer/services/classifier_orchestrator.py
├── src/life_organizer/services/claude_classifier.py       (replaced by claude_service.py)
├── src/life_organizer/api/routes/classifier.py            (replaced by expanded budget.py)
├── src/life_organizer/handlers/                           (entire directory)
│   ├── __init__.py
│   ├── base.py
│   └── budget_entry.py
├── src/life_organizer/schemas/classification.py           (ClassifiedInput moves to budget internals)
├── src/life_organizer/schemas/actions.py                  (app_action pattern removed)
├── src/life_organizer/prompts/note_system_prompt_v1.txt
├── src/life_organizer/prompts/quote_system_prompt_v1.txt
├── src/life_organizer/prompts/budget_system_prompt_v1.txt (v1 already unused)
├── tests/handlers/                                        (entire directory)
├── tests/services/test_claude_classifier.py
├── tests/services/test_claude_classifier_response_parsing.py
├── tests/services/test_classifier_orchestrator.py
```

### Architectural Boundaries

**API Boundary:**
- Routes handle HTTP only: parse requests, call services, format responses
- No business logic in routes
- No direct database access in routes

**Service Boundary:**
- `ClaudeService` — owns all Claude API communication (text, vision, generative)
- `BudgetService` — owns budget business logic (validation, conversion, persistence, queries)
- `MealService` — owns meal business logic (suggestion context building, feedback, history)
- Services can depend on other services (e.g., `MealService` uses `ClaudeService`)

**Data Boundary:**
- SQLAlchemy models own schema definitions
- Services access DB via `async_session_factory` (existing pattern)
- No raw SQL — all queries through SQLAlchemy ORM
- Migrations via Alembic (existing pattern)

**Prompt Boundary:**
- Prompt files are plain text, loaded at module import
- Dynamic content (dates, history, preferences) injected at call time
- Prompt files are the primary tuning surface for LLM behavior

### Data Flow

```
Budget Text:   iOS → POST /budget (JSON) → ClaudeService.parse_budget_text() → BudgetService.create_entries() → DB
Budget Image:  iOS → POST /budget (multipart) → ClaudeService.parse_budget_images() → BudgetService.create_entries() → DB
Budget Query:  Frontend → GET /budget/transactions → BudgetService.query_transactions() → DB → Response
Budget Plan:   Frontend → PUT /budget/plan/{year} → BudgetService.upsert_plan() → DB → Response
Meal Suggest:  iOS → POST /meals/suggest → MealService.get_suggestions() → ClaudeService.suggest_meals() → Response
Meal Feedback: iOS → POST /meals/feedback → MealService.save_feedback() → DB → (optionally save recipe)
```

## Architecture Validation Results

### Coherence Validation

| Check | Status | Notes |
|-------|--------|-------|
| Decision compatibility | ✅ | All choices work together (same stack, consistent patterns) |
| Pattern consistency | ✅ | Naming, structure, and error handling consistent across domains |
| Structure alignment | ✅ | Directory structure supports service boundaries |
| Brownfield compatibility | ✅ | Existing budget data, migrations, and test patterns preserved |

### Requirements Coverage

| Requirement Set | Coverage | Notes |
|----------------|----------|-------|
| Budget FRs (FR1-FR12) | ✅ Full | Text, image, export, storage all architecturally supported |
| Budget Frontend API FRs (FR30-FR35) | ✅ Full | Transactions, aggregations, plans all designed |
| Meal FRs (FR13-FR22) | ✅ Full | Suggest, feedback, history all architecturally supported |
| Feedback FRs (FR23-FR24) | ✅ Full | Unchanged from current implementation |
| API Protection FRs (FR25-FR26) | ✅ Full | slowapi rate limiting designed |
| Cleanup FRs (FR27-FR29) | ✅ Full | Deletion list explicit, rename designed |
| NFR1-NFR4 (Performance) | ✅ Full | Tiered response times achievable with current stack |
| NFR5-NFR8 (Reliability) | ✅ Full | Atomic transactions, error handling patterns defined |
| NFR9-NFR10 (Security) | ✅ Full | Rate limiting + env-based secrets |
| NFR11 (Developer Experience) | ✅ Full | FastAPI auto-generated Swagger UI retained at `/api/v1/docs` |

### Implementation Readiness

| Check | Status |
|-------|--------|
| All architectural decisions documented with rationale | ✅ |
| Technology versions specified | ✅ |
| Database schema fully designed | ✅ |
| API contracts defined | ✅ |
| File structure complete with all new/deleted files | ✅ |
| Service boundaries clear | ✅ |
| Data flow documented | ✅ |
| Testing strategy defined | ✅ |

### Architecture Readiness Assessment

- **Overall Status:** READY FOR IMPLEMENTATION
- **Confidence Level:** High
- **Key Strengths:**
  - Minimal new dependencies (slowapi, python-multipart only)
  - Consistent patterns across both domains
  - Clear deletion list for cleanup
  - Service layer simplifies the over-engineered handler registry
- **Areas for Future Enhancement:**
  - Preference learning algorithm (post-MVP)
  - Recipe deduplication strategy (post-MVP)
  - Budget frontend caching strategy (if query performance becomes an issue)
