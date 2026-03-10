---
stepsCompleted: ['step-01', 'step-02', 'step-03', 'step-04']
status: 'complete'
inputDocuments:
  - '_bmad-output/prd.md'
  - '_bmad-output/architecture.md'
project_name: 'life-organizer-be'
user_name: 'Ivo'
date: '2026-03-09'
---

# life-organizer-be - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for life-organizer-be, decomposing the requirements from the PRD and Architecture into implementable stories.

**Project Context:** Brownfield — pivoting from multi-category classifier to two focused features: budget tracking + meal planning. Core budget infrastructure exists; orchestrator/handler layers need removal, new meal planner feature needs building.

## Requirements Inventory

### Functional Requirements

**Budget Entry — Text Input:**
- FR1: User can submit natural language text to log one or more budget entries
- FR2: System can parse amount, currency, merchant, category, and date from natural language input
- FR3: System can infer expense category from merchant name or keywords
- FR4: System can handle multi-currency inputs (EUR, USD) with conversion to EUR. BGN supported for legacy data only.
- FR5: System can parse multiple transactions from a single text input
- FR6: System can infer dates from natural language ("yesterday", "monday")

**Budget Entry — Screenshot Import:**
- FR7: User can submit one or more images of Revolut transaction screens
- FR8: System can extract transaction data from Revolut screenshot images using Claude Vision
- FR9: System can process multiple screenshots in a single request
- FR10: System can route extracted screenshot data through the same categorization pipeline as text input

**Budget Management:**
- FR11: User can export budget transactions as TSV
- FR12: System can store budget entries with amount, currency, converted amounts, date, transaction type, category, and details

**Budget Frontend API:**
- FR30: User can fetch transactions as JSON with filters (date range, transaction type, category) and pagination
- FR31: User can fetch aggregated category totals for a given period (month or year) and transaction type
- FR32: User can fetch a budget plan for a specific year (categories × 12 months grid with planned amounts)
- FR33: User can create or update budget plan amounts for any category/month/year combination
- FR34: User can fetch a list of available years that contain transaction data
- FR35: System can store budget plan data (planned amount per category per month per year)

**Meal Suggestions:**
- FR13: User can request 3 dinner suggestions for tonight
- FR14: User can optionally provide requirements/constraints with a suggestion request (e.g., "I have chicken thighs")
- FR15: System can generate meal suggestions incorporating user preferences from system prompt
- FR16: System can generate meal suggestions aware of store inventory (defined in system prompt)
- FR17: System can avoid suggesting recently cooked meals by referencing meal history
- FR18: System can return recipe details including name, ingredients, instructions, prep time, cuisine, and tags
- FR19: User can request a new set of suggestions if the current ones don't appeal

**Meal Feedback & History:**
- FR20: User can submit feedback on a recipe (liked/disliked + optional notes)
- FR21: System can track meal history (what was cooked and when)
- FR22: System can store recipe feedback for future suggestion improvement

**Classification Feedback:**
- FR23: User can report a misclassification with the correct category
- FR24: System can store misclassification data for training improvement

**API Protection:**
- FR25: System can rate-limit LLM-hitting endpoints (budget, meals/suggest) to 5-10 requests per minute
- FR26: System can return appropriate rate limit exceeded responses with retry information

**Codebase Cleanup:**
- FR27: System removes classification orchestrator and category routing logic
- FR28: System removes Quote and Note category code (prompts, schemas, enum values, placeholders)
- FR29: Budget endpoint is renamed from `/api/v1/process` to `/api/v1/budget`

### NonFunctional Requirements

**Performance:**
- NFR1: Budget text entry response time < 1 second end-to-end
- NFR2: Budget screenshot processing time < 5 seconds per image
- NFR3: Meal suggestion response time < 3 seconds
- NFR4: Non-LLM endpoint response time < 200ms

**Reliability:**
- NFR5: Zero data loss — every submitted entry must persist
- NFR6: No silent failures — all errors return clear, descriptive responses
- NFR7: Database integrity — no partial or corrupted writes (atomic transactions)
- NFR8: LLM failure handling — graceful degradation with clear error

**Security:**
- NFR9: Rate limiting on LLM endpoints (5-10 req/min)
- NFR10: No secrets in codebase — API keys via environment variables only

### Additional Requirements

**From Architecture:**
- Brownfield project — no starter template needed
- Replace `ClassifierOrchestrator` + `ClaudeClassifier` with unified `ClaudeService` supporting three modes: text parse, vision extract, generative suggest (AD-1)
- Same `POST /api/v1/budget` endpoint handles both text (JSON) and images (multipart) via Content-Type header (AD-2)
- New database tables: `budget.plans`, `meals.recipes`, `meals.meal_history`, `meals.recipe_feedback` with full schema designs (AD-3)
- Remove orchestrator layer entirely — budget route calls `ClaudeService` directly (AD-4)
- Use `slowapi` for rate limiting on LLM endpoints, in-memory storage (AD-5)
- Stateless LLM generation with context injection per request for meal suggestions (AD-6)
- RESTful JSON endpoints for budget frontend API with pagination pattern (AD-7)
- Service layer pattern: `ClaudeService`, `BudgetService`, `MealService`
- New prompt files: `budget_vision_prompt_v1.txt`, `meals_suggest_prompt_v1.txt`
- New dependencies: `slowapi`, `python-multipart`
- Explicit file deletion list: `classifier_orchestrator.py`, `claude_classifier.py`, `classifier.py` route, `handlers/` directory, `classification.py`, `actions.py`, old prompt files, related test files
- Recommended implementation sequence: orchestrator removal → ClaudeService → budget routes → rate limiting → image upload → meals schema → meal suggest → meal feedback → budget frontend API

### FR Coverage Map

| FR | Epic | Description |
|----|------|-------------|
| FR1 | Epic 1 | Submit natural language text for budget entries |
| FR2 | Epic 1 | Parse amount, currency, merchant, category, date |
| FR3 | Epic 1 | Infer expense category from merchant/keywords |
| FR4 | Epic 1 | Multi-currency support (EUR, USD, BGN legacy) |
| FR5 | Epic 1 | Parse multiple transactions from single input |
| FR6 | Epic 1 | Infer dates from natural language |
| FR7 | Epic 2 | Submit Revolut transaction screenshots |
| FR8 | Epic 2 | Extract transactions via Claude Vision |
| FR9 | Epic 2 | Process multiple screenshots per request |
| FR10 | Epic 2 | Route screenshot data through same pipeline |
| FR11 | Epic 1 | Export budget transactions as TSV |
| FR12 | Epic 1 | Store budget entries with full metadata |
| FR13 | Epic 3 | Request 3 dinner suggestions |
| FR14 | Epic 3 | Optional requirements/constraints |
| FR15 | Epic 3 | Suggestions incorporate user preferences |
| FR16 | Epic 3 | Store inventory awareness |
| FR17 | Epic 3 | Avoid recently cooked meals |
| FR18 | Epic 3 | Return recipe details |
| FR19 | Epic 3 | Regenerate suggestions |
| FR20 | Epic 3 | Submit recipe feedback |
| FR21 | Epic 3 | Track meal history |
| FR22 | Epic 3 | Store feedback for improvement |
| FR23 | — | Already implemented (LIFE-8) |
| FR24 | — | Already implemented (LIFE-9) |
| FR25 | Epic 1 | Rate-limit LLM endpoints |
| FR26 | Epic 1 | Rate limit exceeded responses |
| FR27 | Epic 1 | Remove orchestrator and routing |
| FR28 | Epic 1 | Remove Quote/Note code |
| FR29 | Epic 1 | Rename endpoint to /api/v1/budget |
| FR30 | Epic 4 | Fetch transactions with filters + pagination |
| FR31 | Epic 4 | Aggregated category totals |
| FR32 | Epic 4 | Fetch budget plan grid |
| FR33 | Epic 4 | Create/update budget plan amounts |
| FR34 | Epic 4 | List available years |
| FR35 | Epic 4 | Store budget plan data |

## Epic List

### Epic 1: Budget Simplification & Direct Logging

Remove the orchestrator/handler architecture, create unified `ClaudeService` + `BudgetService`, rename endpoint to `/api/v1/budget`, and add rate limiting. Budget text logging works directly — faster, simpler, same user experience.

**User Outcome:** Budget logging continues to work exactly as before but through a cleaner, direct endpoint (`/budget` instead of `/process`), with cost protection via rate limiting.
**FRs covered:** FR1-FR6, FR11-FR12, FR25-FR26, FR27-FR29
**Dependencies:** None (foundational epic)

---

### Epic 2: Budget Screenshot Import

Add Claude Vision support so users can snap Revolut transaction screenshots and have all transactions extracted and logged automatically.

**User Outcome:** Take screenshots of Revolut transactions, send them, and 25+ transactions are logged in seconds — no manual typing.
**FRs covered:** FR7-FR10
**Dependencies:** Builds on Epic 1 (`ClaudeService` + budget persistence)

---

### Epic 3: Meal Planning & Feedback

Full meal planner feature: on-demand dinner suggestions with optional constraints, feedback capture, and meal history tracking to avoid repetition.

**User Outcome:** "What's for dinner?" — get 3 personalized suggestions, pick one, give feedback. System learns preferences and avoids repetition.
**FRs covered:** FR13-FR22
**Dependencies:** Builds on Epic 1 (`ClaudeService` for LLM generation, rate limiting)

---

### Epic 4: Budget Frontend API

Transaction queries with filtering/pagination, category aggregations for charts, and budget plan CRUD for the planning grid.

**User Outcome:** Frontend can display transaction history, spending charts, and a budget planning spreadsheet — all powered by new API endpoints.
**FRs covered:** FR30-FR35
**Dependencies:** Builds on Epic 1 (budget infrastructure)

---

## Epic 1: Budget Simplification & Direct Logging

Remove the orchestrator/handler architecture, create unified `ClaudeService` + `BudgetService`, rename endpoint to `/api/v1/budget`, and add rate limiting.

### Story 1.1: Replace Orchestrator with Direct Budget Flow

As a user,
I want budget logging to work through a direct, simplified endpoint,
So that my expense entries are processed faster and the system is easier to maintain.

**FRs Covered:** FR1-FR6, FR11-FR12, FR27, FR29

**Architecture Notes:**
- **AD-1:** Create `ClaudeService` in `services/claude_service.py` with `parse_budget_text(text: str) -> list[ClassifiedInput]` method. This replaces both `ClaudeClassifier` and `ClassifierOrchestrator`. Reuse existing `budget_system_prompt_v2.txt` unchanged. Retain tenacity retry logic (max 3 retries, exponential backoff) from the existing classifier.
- **AD-4:** Create `BudgetService` in `services/budget_service.py`. Extract persistence logic from `BudgetEntryHandler.execute()` — validation, currency conversion (EUR base), and DB write. The service accepts `async_session_factory` via constructor (same pattern as current classifier instantiation).
- **AD-4:** New route file `api/routes/budget.py` with `POST /api/v1/budget` accepting `{"input": "..."}` JSON body. Route calls `ClaudeService.parse_budget_text()` → `BudgetService.create_entries()`. Move existing TSV export to `GET /api/v1/budget/export`.
- **AD-4:** Delete `api/routes/classifier.py` and remove its router from `main.py`. The old `/api/v1/process` endpoint ceases to exist.
- `ClassifiedInput` schema is retained as an internal type used between `ClaudeService` and `BudgetService` — it moves from `schemas/classification.py` into `schemas/budget.py` or inline in the service.
- `BudgetTransaction` DB model remains unchanged.
- The existing budget prompt v2 is unchanged — same input format, same JSON output structure.

**Acceptance Criteria:**

**Given** the system has the new `ClaudeService` with `parse_budget_text()` method
**When** it receives natural language text like "coffee 4.50"
**Then** it returns a list of `ClassifiedInput` objects with parsed amount, currency, category, and date
**And** it uses the existing `budget_system_prompt_v2.txt` prompt unchanged
**And** it retries up to 3 times with exponential backoff on Claude API failures

**Given** the system has the new `BudgetService` with `create_entries()` method
**When** it receives parsed `ClassifiedInput` objects
**Then** it validates the data, converts currency to EUR, and persists `BudgetTransaction` records atomically
**And** no partial writes occur if any entry in a batch fails

**Given** a user sends `POST /api/v1/budget` with `{"input": "lunch 12 eur, coffee 4.50"}`
**When** the request is processed
**Then** multiple budget entries are created in the database (FR5)
**And** the response confirms all entries were saved with a 200 status

**Given** a user sends `POST /api/v1/budget` with `{"input": "groceries yesterday 45 usd"}`
**When** the request is processed
**Then** the date is inferred as yesterday's date (FR6)
**And** the amount is converted from USD to EUR (FR4)
**And** the category is inferred as groceries (FR3)

**Given** the old `/api/v1/process` endpoint
**When** a request is sent to it after this story is complete
**Then** a 404 is returned (endpoint no longer exists)

**Given** a user sends `GET /api/v1/budget/export`
**When** the request is processed
**Then** budget transactions are returned as TSV (FR11, moved from old export path)

**Given** the Claude API is down or returns an error
**When** a budget entry request is made
**Then** the system returns a 500 with a clear error message (not raw API error) (NFR6, NFR8)
**And** the full error is logged internally

**Given** the API routes have been restructured
**When** the FastAPI app is running
**Then** Swagger UI is accessible at `/api/v1/docs` (NFR11)
**And** all new budget endpoints appear in the interactive documentation with correct request/response schemas

**Given** all changes are complete
**When** `make lint && make type-check && make test` are run
**Then** all quality gates pass with no errors

---

### Story 1.2: Remove Legacy Code and Quote/Note Cleanup

As a developer,
I want all dead code from the old architecture removed,
So that the codebase only contains active, maintained code.

**FRs Covered:** FR28

**Architecture Notes:**
- **Files to delete** (from Architecture "Files Deleted" section):
  - `services/classifier_orchestrator.py`
  - `services/claude_classifier.py` (replaced by `claude_service.py` in Story 1.1)
  - `handlers/` directory entirely (`__init__.py`, `base.py`, `budget_entry.py`)
  - `schemas/classification.py` (if `ClassifiedInput` was moved in Story 1.1)
  - `schemas/actions.py` (entire file — `AppAction` pattern removed)
  - `prompts/note_system_prompt_v1.txt`
  - `prompts/quote_system_prompt_v1.txt`
  - `prompts/budget_system_prompt_v1.txt` (v1 already unused, v2 is active)
- **Test files to delete:**
  - `tests/handlers/` directory entirely
  - `tests/services/test_claude_classifier.py`
  - `tests/services/test_claude_classifier_response_parsing.py`
  - `tests/services/test_classifier_orchestrator.py`
- **Schema cleanup:** Remove `QUOTE` and `NOTE` from any remaining enum if they exist. Remove `ActionType` enum if no longer used (was part of handler pattern). Keep only budget-related enums (`ExpenseCategory`, `IncomeCategory`, `SavingsCategory`).
- **Imports cleanup:** Search entire codebase for any remaining imports of deleted modules and remove them.

**Acceptance Criteria:**

**Given** the orchestrator files exist (`classifier_orchestrator.py`, `claude_classifier.py`)
**When** the cleanup is complete
**Then** both files are deleted from `services/`
**And** no other file imports from them

**Given** the `handlers/` directory exists with `__init__.py`, `base.py`, `budget_entry.py`
**When** the cleanup is complete
**Then** the entire `handlers/` directory is deleted
**And** no other file references handler classes

**Given** `schemas/actions.py` exists with `AppAction` and action classes
**When** the cleanup is complete
**Then** the file is deleted
**And** no other file imports `AppAction` or action types

**Given** Quote and Note prompt files exist in `prompts/`
**When** the cleanup is complete
**Then** `note_system_prompt_v1.txt`, `quote_system_prompt_v1.txt`, and `budget_system_prompt_v1.txt` are deleted
**And** only `budget_system_prompt_v2.txt` remains in `prompts/`

**Given** test files exist for deleted modules
**When** the cleanup is complete
**Then** `tests/handlers/` directory is deleted
**And** `test_claude_classifier.py`, `test_claude_classifier_response_parsing.py`, `test_classifier_orchestrator.py` are deleted from `tests/services/`

**Given** `QUOTE` or `NOTE` values exist in any enum
**When** the cleanup is complete
**Then** they are removed from all enums
**And** only valid budget-related values remain

**Given** all legacy code is removed
**When** `grep -r "orchestrator\|ClassifierOrchestrator\|ClaudeClassifier\|BudgetEntryHandler\|BaseHandler\|AppAction\|QUOTE\|NOTE" src/` is run
**Then** no matches are found (except in comments explaining the removal, if any)

**Given** all cleanup is complete
**When** `make lint && make type-check && make test` are run
**Then** all quality gates pass with zero errors

---

### Story 1.3: Add Rate Limiting to LLM Endpoints

As a user,
I want LLM-hitting endpoints to be rate-limited,
So that accidental or abusive usage doesn't cause unexpected API costs.

**FRs Covered:** FR25, FR26

**Architecture Notes:**
- **AD-5:** Install `slowapi` (built on `limits` library). Use `get_remote_address` as key function. In-memory storage is fine for single-user deployment — no Redis needed.
- Configure the `Limiter` instance in `main.py` and add it to the FastAPI app state.
- Apply `@limiter.limit("10/minute")` decorator to `POST /api/v1/budget` route.
- The `POST /api/v1/meals/suggest` endpoint (Epic 3) will also get rate limiting when it's created — this story just sets up the infrastructure and applies it to budget.
- `slowapi` auto-returns 429 with `Retry-After` header on limit exceeded — no custom handler needed.
- Add `slowapi` to project dependencies (pyproject.toml or requirements).

**Acceptance Criteria:**

**Given** the `slowapi` package is installed and configured
**When** the FastAPI app starts
**Then** the rate limiter is initialized with in-memory storage
**And** the limiter is attached to the app via `app.state.limiter`

**Given** a user sends requests to `POST /api/v1/budget`
**When** they send 10 requests within 1 minute
**Then** all 10 requests are processed normally

**Given** a user has sent 10 requests to `POST /api/v1/budget` within 1 minute
**When** they send an 11th request
**Then** a 429 status code is returned
**And** the response includes a `Retry-After` header indicating when the limit resets
**And** the response body contains a clear error message (FR26)

**Given** a user has been rate-limited
**When** the rate limit window expires (1 minute)
**Then** subsequent requests are processed normally again

**Given** a user sends requests to non-LLM endpoints (`GET /api/v1/budget/export`, `GET /api/v1/health`, `POST /api/v1/feedback`)
**When** they send unlimited requests
**Then** no rate limiting is applied to these endpoints

**Given** rate limiting is configured
**When** `make lint && make type-check && make test` are run
**Then** all quality gates pass

---

## Epic 2: Budget Screenshot Import

Add Claude Vision support so users can snap Revolut transaction screenshots and have all transactions extracted and logged automatically.

### Story 2.1: Budget Entry via Revolut Screenshot Import

As a user,
I want to take screenshots of my Revolut transaction history and have all transactions automatically extracted and logged,
So that I can reconcile weeks of expenses in seconds instead of typing each one manually.

**FRs Covered:** FR7, FR8, FR9, FR10

**Architecture Notes:**
- **AD-2:** Install `python-multipart` for FastAPI multipart form-data support. Same endpoint path `POST /api/v1/budget` but with `Content-Type: multipart/form-data` — FastAPI routes to a separate handler function based on content type. Use two separate route functions on the same path with different signatures.
- **AD-1:** Add `parse_budget_images(images: list[bytes]) -> list[ClassifiedInput]` method to `ClaudeService`. This uses Claude Vision API — send images as base64-encoded content blocks alongside a budget extraction prompt.
- **AD-2:** Create `budget_vision_prompt_v1.txt` in `prompts/`. The prompt instructs Claude to extract transactions from Revolut-specific screenshot format. It returns the same `ClassifiedInput` JSON structure as text parsing so both flows converge on `BudgetService.create_entries()`.
- **AD-2:** Route function accepts `files: list[UploadFile]`. Read bytes from each file, validate they are images (check content type), pass to `ClaudeService.parse_budget_images()`.
- The same rate limiting from Story 1.3 applies to this endpoint automatically (same route path).
- NFR2: Target < 5 seconds per image processing time.

**Acceptance Criteria:**

**Given** a user has one Revolut transaction screenshot
**When** they send `POST /api/v1/budget` with `Content-Type: multipart/form-data` containing the image
**Then** Claude Vision extracts all transactions from the screenshot
**And** each transaction is parsed into `ClassifiedInput` format (amount, currency, date, category, merchant)
**And** all extracted entries are persisted via `BudgetService.create_entries()`
**And** the response confirms the number of transactions logged

**Given** a user has 3 Revolut transaction screenshots
**When** they send all 3 images in a single multipart request (FR9)
**Then** all images are processed
**And** transactions from all screenshots are extracted and combined
**And** all entries are persisted atomically
**And** the response shows the total count of transactions logged across all images

**Given** a user sends a non-image file (e.g., .txt or .pdf)
**When** the multipart request is processed
**Then** the server returns 400 with a descriptive error: "Invalid file type. Only image files are accepted."

**Given** a user sends an image that is not a Revolut screenshot (random photo)
**When** Claude Vision processes it
**Then** the system returns a meaningful error indicating no transactions could be extracted
**And** no entries are persisted to the database

**Given** a user sends a multipart request with no files
**When** the request is processed
**Then** a 400 error is returned with a descriptive message

**Given** the budget text endpoint still works
**When** a user sends `POST /api/v1/budget` with `Content-Type: application/json` and `{"input": "coffee 4.50"}`
**Then** text parsing works exactly as before (FR10 — same pipeline)

**Given** screenshot processing encounters a Claude Vision API error
**When** the error occurs
**Then** the system retries up to 3 times with exponential backoff
**And** if all retries fail, returns 500 with a clear error message (NFR8)
**And** no partial entries are persisted (NFR7)

**Given** rate limiting is active on `POST /api/v1/budget`
**When** screenshot requests are sent
**Then** they count toward the same rate limit as text requests (10/min combined)

**Given** the prompt file `budget_vision_prompt_v1.txt` exists
**When** it is used for Vision API calls
**Then** it specifically instructs extraction of Revolut transaction format (amount, date, merchant, currency)
**And** it returns the same JSON structure as `budget_system_prompt_v2.txt`

**Given** all changes are complete
**When** `make lint && make type-check && make test` are run
**Then** all quality gates pass

---

## Epic 3: Meal Planning & Feedback

Full meal planner feature: on-demand dinner suggestions with optional constraints, feedback capture, and meal history tracking to avoid repetition.

### Story 3.1: Create Meals Database Schema and Models

As a developer,
I want the meals database schema and ORM models created,
So that meal data (recipes, history, feedback) can be persisted and queried.

**FRs Covered:** Foundation for FR13-FR22

**Architecture Notes:**
- **AD-3:** Create `meals` PostgreSQL schema with three tables. All table designs are specified in Architecture AD-3.
- **`meals.recipes`** table: `id` (PK), `name` (str), `ingredients` (JSON list), `instructions` (str), `prep_time` (int minutes), `cuisine` (str), `tags` (JSON list), `source` (str: "seeded" | "llm_generated" | "liked"), `times_made` (int default 0), `last_made` (date nullable), `created_at`, `updated_at`.
- **`meals.meal_history`** table: `id` (PK), `recipe_id` (FK nullable → recipes), `recipe_name` (str denormalized), `cooked_date` (date), `created_at`. Recipe name is denormalized because LLM-generated meals may not be saved as recipes.
- **`meals.recipe_feedback`** table: `id` (PK), `recipe_id` (FK nullable → recipes), `recipe_name` (str denormalized), `liked` (bool), `notes` (str nullable), `created_at`.
- Create Alembic migration `xxx_create_meals_schema_and_tables.py`.
- ORM models go in `db/models/meals.py`. Follow existing patterns from `db/models/budget.py`.
- Add models to `db/models/__init__.py` exports.

**Acceptance Criteria:**

**Given** the database is running
**When** the Alembic migration is applied
**Then** the `meals` schema is created
**And** `meals.recipes` table exists with all specified columns and types
**And** `meals.meal_history` table exists with FK to recipes (nullable) and all columns
**And** `meals.recipe_feedback` table exists with FK to recipes (nullable) and all columns

**Given** the `Recipe` ORM model is defined in `db/models/meals.py`
**When** a recipe is created with all fields populated
**Then** it is persisted correctly with JSON fields (ingredients, tags) stored as JSON
**And** `source` field accepts only "seeded", "llm_generated", or "liked"
**And** `times_made` defaults to 0
**And** `last_made` is nullable

**Given** the `MealHistory` ORM model is defined
**When** a meal history record is created
**Then** `recipe_id` is optional (nullable FK)
**And** `recipe_name` is always populated (denormalized)
**And** `cooked_date` stores a date (not datetime)

**Given** the `RecipeFeedback` ORM model is defined
**When** a feedback record is created
**Then** `recipe_id` is optional (nullable FK)
**And** `recipe_name` is always populated
**And** `liked` is a required boolean
**And** `notes` is optional

**Given** the migration is applied and then rolled back
**When** `alembic downgrade -1` is run
**Then** all meals tables and schema are removed cleanly

**Given** all models are created
**When** `make lint && make type-check && make test` are run
**Then** all quality gates pass

---

### Story 3.2: Create Meal Suggestion Endpoint

As a user,
I want to request dinner suggestions and optionally specify constraints,
So that I get personalized meal ideas that match my preferences and available ingredients.

**FRs Covered:** FR13, FR14, FR15, FR16, FR17, FR18, FR19

**Architecture Notes:**
- **AD-6:** Create `MealService` in `services/meal_service.py` with `get_suggestions(requirements: str | None, session) -> list[MealSuggestion]`. The service orchestrates: (1) query recent `meal_history` (last 14 days), (2) query top-rated recipes from `recipe_feedback`, (3) build context, (4) call `ClaudeService.suggest_meals()`.
- **AD-1:** Add `suggest_meals(requirements: str | None, history: list, recipes: list) -> list[MealSuggestion]` method to `ClaudeService`. This uses generative mode — different from budget parsing. Model can be Sonnet for faster response (vs Haiku for budget).
- **AD-6:** Create `meals_suggest_prompt_v1.txt` in `prompts/`. System prompt contains: user preferences (dietary restrictions, allergies, cuisine preferences), store inventory (available/unavailable items), output format instructions. User message constructed per-request includes: recent meal history, liked recipes, optional user requirements, "Suggest 3 dinner options for tonight."
- **AD-6:** Response schema `MealSuggestion`: `name` (str), `ingredients` (list[str]), `instructions` (str), `prep_time` (int), `cuisine` (str), `tags` (list[str]).
- Create route `POST /api/v1/meals/suggest` in `api/routes/meals.py`. Request body: `{"requirements": "optional text"}`. Response: list of 3 `MealSuggestion` objects.
- Apply `@limiter.limit("10/minute")` rate limiting (from Story 1.3 infrastructure).
- Register meals router in `main.py`.
- NFR3: Target < 3 seconds response time.
- FR19 (regeneration): Handled naturally — user just calls the endpoint again. No server-side state needed.

**Acceptance Criteria:**

**Given** a user sends `POST /api/v1/meals/suggest` with no body or `{}`
**When** the request is processed
**Then** 3 dinner suggestions are returned (FR13)
**And** each suggestion includes: name, ingredients list, instructions, prep_time, cuisine, and tags (FR18)
**And** the response is valid JSON matching the `MealSuggestion` schema

**Given** a user sends `POST /api/v1/meals/suggest` with `{"requirements": "I have chicken thighs"}`
**When** the request is processed
**Then** all 3 suggestions incorporate chicken thighs as an ingredient (FR14)
**And** the suggestions respect user preferences from the system prompt (FR15)

**Given** the system prompt contains store inventory information
**When** meal suggestions are generated
**Then** suggestions only use ingredients available in the defined store inventory (FR16)
**And** no suggestion requires ingredients marked as unavailable

**Given** the user cooked pasta carbonara 3 days ago (recorded in meal_history)
**When** meal suggestions are generated
**Then** pasta carbonara is NOT among the 3 suggestions (FR17)
**And** the recent 14-day meal history is included in the LLM context

**Given** a user doesn't like the current suggestions
**When** they call `POST /api/v1/meals/suggest` again
**Then** a new set of 3 different suggestions is generated (FR19)
**And** the suggestions differ from the previous set (due to LLM non-determinism + history context)

**Given** there are liked recipes in `recipe_feedback`
**When** suggestions are generated
**Then** the LLM context includes top-rated recipes as candidates for re-suggestion

**Given** the Claude API fails or times out
**When** a suggestion request is made
**Then** the system retries up to 3 times with exponential backoff
**And** if all retries fail, returns 500 with a clear error message (NFR8)

**Given** the Claude API returns malformed JSON
**When** the response is parsed
**Then** the system returns 500 with "Failed to parse meal suggestions" error (NFR6)
**And** the raw response is logged for debugging

**Given** rate limiting is active
**When** more than 10 suggestion requests are made within 1 minute
**Then** a 429 response is returned with `Retry-After` header (FR25, FR26)

**Given** the meals router is registered in `main.py`
**When** `GET /api/v1/meals/suggest` is attempted (wrong method)
**Then** a 405 Method Not Allowed is returned

**Given** the meals router is registered in `main.py`
**When** the FastAPI app is running
**Then** all meal endpoints appear in Swagger UI at `/api/v1/docs` (NFR11)
**And** request/response schemas are correctly documented via Pydantic models

**Given** all changes are complete
**When** `make lint && make type-check && make test` are run
**Then** all quality gates pass

---

### Story 3.3: Create Meal Feedback and History Tracking

As a user,
I want to rate recipes and have my cooking history tracked,
So that future suggestions improve over time and avoid repetition.

**FRs Covered:** FR20, FR21, FR22

**Architecture Notes:**
- **AD-6:** Add to `MealService`: `save_feedback(recipe_id: int | None, recipe_name: str, liked: bool, notes: str | None, session)` and `record_meal(recipe_id: int | None, recipe_name: str, cooked_date: date, session)`.
- When feedback is positive (`liked=True`) and the recipe was LLM-generated (no `recipe_id`), save it to `meals.recipes` with `source="liked"`. This builds the curated collection over time.
- When feedback is submitted, also record a `meal_history` entry (the user cooked this meal).
- Create route `POST /api/v1/meals/feedback` in `api/routes/meals.py`. Request body: `{"recipe_id": null, "recipe_name": "Greek Lemon Chicken", "liked": true, "notes": "great, would add more garlic"}`.
- `recipe_id` is nullable — LLM-generated suggestions that haven't been saved don't have an ID yet. `recipe_name` is always required for denormalization.
- No rate limiting on this endpoint (non-LLM, per AD-5).

**Acceptance Criteria:**

**Given** a user sends `POST /api/v1/meals/feedback` with:
```json
{
  "recipe_name": "Greek Lemon Chicken",
  "liked": true,
  "notes": "great, would add more garlic"
}
```
**When** the request is processed
**Then** a `recipe_feedback` record is created with `liked=true` and the notes (FR20)
**And** a `meal_history` record is created with today's date and the recipe name (FR21)
**And** a 201 response is returned with `{"success": true, "message": "Feedback recorded"}`

**Given** a user submits positive feedback for an LLM-generated recipe (no `recipe_id`)
**When** `liked` is `true`
**Then** the recipe is saved to `meals.recipes` with `source="liked"` (FR22)
**And** the new recipe includes name, ingredients, instructions, prep_time, cuisine, and tags from the suggestion
**And** the `recipe_feedback` and `meal_history` records are updated to reference the new recipe ID

**Given** a user submits negative feedback
**When** `liked` is `false`
**Then** a `recipe_feedback` record is created with `liked=false` and optional notes
**And** a `meal_history` record is still created (the user tried it)
**And** the recipe is NOT saved to `meals.recipes`

**Given** a user submits feedback for a known recipe (with `recipe_id`)
**When** the feedback is processed
**Then** `recipe.times_made` is incremented by 1
**And** `recipe.last_made` is updated to today's date
**And** the feedback record references the existing `recipe_id`

**Given** a user submits feedback with a `recipe_id` that doesn't exist
**When** the request is processed
**Then** a 404 error is returned with "Recipe not found"

**Given** a user submits feedback with missing required fields (no `recipe_name` or no `liked`)
**When** the request is processed
**Then** a 422 validation error is returned with field-level detail

**Given** feedback is submitted and the database write fails
**When** the error occurs
**Then** no partial writes occur (atomic transaction) (NFR7)
**And** a 500 error is returned with a clear message (NFR6)

**Given** all changes are complete
**When** `make lint && make type-check && make test` are run
**Then** all quality gates pass

---

## Epic 4: Budget Frontend API

Transaction queries with filtering/pagination, category aggregations for charts, and budget plan CRUD for the planning grid.

### Story 4.1: Transaction Query and Available Years Endpoints

As a user,
I want to browse my transaction history with filters and pagination,
So that the frontend can display a searchable, navigable transaction list.

**FRs Covered:** FR30, FR34

**Architecture Notes:**
- **AD-7:** Add to `BudgetService`: `query_transactions(start_date, end_date, transaction_type, category, page, page_size, session) -> PaginatedResult` and `get_available_years(session) -> list[int]`.
- **AD-7:** `GET /api/v1/budget/transactions` — query params: `start_date` (date), `end_date` (date), `transaction_type` (str optional), `category` (str optional), `page` (int, default 1), `page_size` (int, default 50). Response: `{"items": [...], "total": int, "page": int, "page_size": int}`.
- **AD-7:** `GET /api/v1/budget/years` — no params. Response: `{"years": [2024, 2025, 2026]}`. Queries distinct years from `budget.transactions` table.
- Both endpoints added to existing `api/routes/budget.py`.
- No rate limiting (non-LLM endpoints, per AD-5).
- NFR4: Target < 200ms response time. Consider adding database indexes on `date`, `transaction_type`, `category` columns if not already present.

**Acceptance Criteria:**

**Given** transactions exist in the database
**When** `GET /api/v1/budget/transactions` is called with no filters
**Then** the first page of transactions is returned (default page=1, page_size=50)
**And** the response includes `items` (array), `total` (count), `page`, and `page_size`
**And** items are ordered by date descending (most recent first)

**Given** transactions exist across multiple months
**When** `GET /api/v1/budget/transactions?start_date=2026-01-01&end_date=2026-01-31` is called
**Then** only transactions within January 2026 are returned
**And** the `total` reflects the filtered count

**Given** transactions exist with different types (Expenses, Income, Savings)
**When** `GET /api/v1/budget/transactions?transaction_type=Expenses` is called
**Then** only expense transactions are returned

**Given** transactions exist with different categories
**When** `GET /api/v1/budget/transactions?category=Groceries` is called
**Then** only transactions categorized as Groceries are returned

**Given** multiple filters are applied simultaneously
**When** `GET /api/v1/budget/transactions?start_date=2026-01-01&end_date=2026-03-31&transaction_type=Expenses&category=Groceries` is called
**Then** only matching transactions are returned (all filters AND'd)

**Given** 120 transactions match the filters
**When** `GET /api/v1/budget/transactions?page=2&page_size=50` is called
**Then** transactions 51-100 are returned
**And** `total` is 120, `page` is 2, `page_size` is 50

**Given** page exceeds available data
**When** `GET /api/v1/budget/transactions?page=999` is called
**Then** an empty `items` array is returned with the correct `total`

**Given** invalid filter values are provided (e.g., `page=-1`, `page_size=0`, malformed date)
**When** the request is processed
**Then** a 422 validation error is returned with descriptive field errors

**Given** transactions exist in years 2024, 2025, and 2026
**When** `GET /api/v1/budget/years` is called
**Then** the response is `{"years": [2024, 2025, 2026]}` (sorted ascending)

**Given** no transactions exist
**When** `GET /api/v1/budget/years` is called
**Then** the response is `{"years": []}`

**Given** all changes are complete
**When** `make lint && make type-check && make test` are run
**Then** all quality gates pass

---

### Story 4.2: Transaction Aggregation Endpoint

As a user,
I want to see spending totals by category for any period,
So that the frontend can display budget charts and spending breakdowns.

**FRs Covered:** FR31

**Architecture Notes:**
- **AD-7:** Add to `BudgetService`: `aggregate_transactions(year: int, month: int | None, transaction_type: str | None, session) -> list[CategoryAggregation]`.
- **AD-7:** `GET /api/v1/budget/transactions/aggregate` — query params: `year` (int required), `month` (int 1-12 optional), `transaction_type` (str optional). Response: `{"period": {"year": 2026, "month": 1}, "aggregations": [{"category": "Groceries", "total_eur": 450.00, "count": 23}]}`.
- SQL query: `SELECT category, SUM(amount_eur), COUNT(*) FROM budget.transactions WHERE year=? AND month=? GROUP BY category ORDER BY total DESC`.
- If `month` is omitted, aggregate for the full year.
- If `transaction_type` is omitted, aggregate across all types.
- Added to existing `api/routes/budget.py`.

**Acceptance Criteria:**

**Given** expense transactions exist for January 2026
**When** `GET /api/v1/budget/transactions/aggregate?year=2026&month=1&transaction_type=Expenses` is called
**Then** the response contains category-level totals: `{"period": {"year": 2026, "month": 1}, "aggregations": [{"category": "Groceries", "total_eur": 450.00, "count": 23}, ...]}`
**And** aggregations are sorted by `total_eur` descending

**Given** transactions exist for the full year 2025
**When** `GET /api/v1/budget/transactions/aggregate?year=2025` is called (no month filter)
**Then** aggregations cover the entire year
**And** the response period shows `{"year": 2025}` with no month field

**Given** transactions of mixed types exist
**When** `GET /api/v1/budget/transactions/aggregate?year=2026&transaction_type=Income` is called
**Then** only income transactions are aggregated

**Given** no transactions match the filters
**When** the aggregation endpoint is called
**Then** the response contains an empty `aggregations` array

**Given** `year` parameter is missing
**When** the request is processed
**Then** a 422 validation error is returned (year is required)

**Given** `month` is provided with an invalid value (e.g., 13 or 0)
**When** the request is processed
**Then** a 422 validation error is returned

**Given** all changes are complete
**When** `make lint && make type-check && make test` are run
**Then** all quality gates pass

---

### Story 4.3: Budget Plan CRUD Endpoints

As a user,
I want to create and view budget plans with planned amounts per category per month,
So that the frontend can display a budget planning spreadsheet and track planned vs actual spending.

**FRs Covered:** FR32, FR33, FR35

**Architecture Notes:**
- **AD-3:** Create `budget.plans` table via Alembic migration `xxx_create_budget_plans_table.py`. Schema: `id` (PK), `year` (int), `month` (int 1-12), `transaction_type` (str), `category` (str), `planned_amount` (Decimal 10,2), `created_at`, `updated_at`. Unique constraint on `(year, month, transaction_type, category)`.
- **AD-3:** Create `BudgetPlan` ORM model in `db/models/budget.py` (alongside existing `BudgetTransaction`).
- **AD-7:** Add to `BudgetService`: `get_plan(year: int, session)` and `upsert_plan(year: int, entries: list, session)`.
- **AD-7:** `GET /api/v1/budget/plan/{year}` — Response: `{"year": 2026, "entries": [{"transaction_type": "Expenses", "category": "Groceries", "amounts": {"1": 400, "2": 400, ...}}]}`. The amounts dict maps month numbers (1-12) to planned amounts. Frontend handles row/column totals.
- **AD-7:** `PUT /api/v1/budget/plan/{year}` — Request: `{"entries": [{"transaction_type": "Expenses", "category": "Groceries", "month": 1, "planned_amount": 400.00}]}`. Upserts — creates or updates based on unique constraint.
- Added to existing `api/routes/budget.py`.

**Acceptance Criteria:**

**Given** no budget plan exists for 2026
**When** `GET /api/v1/budget/plan/2026` is called
**Then** the response is `{"year": 2026, "entries": []}` (empty plan)

**Given** a user sends `PUT /api/v1/budget/plan/2026` with:
```json
{
  "entries": [
    {"transaction_type": "Expenses", "category": "Groceries", "month": 1, "planned_amount": 400.00},
    {"transaction_type": "Expenses", "category": "Groceries", "month": 2, "planned_amount": 450.00},
    {"transaction_type": "Income", "category": "Salary", "month": 1, "planned_amount": 5000.00}
  ]
}
```
**When** the request is processed
**Then** all entries are persisted to `budget.plans`
**And** the response is `{"success": true, "updated": 3}`

**Given** budget plan entries already exist for Groceries/January/2026
**When** `PUT /api/v1/budget/plan/2026` sends a new amount for that same combination
**Then** the existing entry is updated (upsert, not duplicate) via the unique constraint
**And** `updated_at` timestamp is refreshed

**Given** budget plan entries exist for 2026
**When** `GET /api/v1/budget/plan/2026` is called
**Then** entries are grouped by `transaction_type` and `category`
**And** each entry has an `amounts` object with month numbers as keys (1-12)
**And** months without planned amounts are omitted from the amounts object

**Given** invalid data is sent (e.g., `month: 13`, `planned_amount: -100`, missing required fields)
**When** `PUT /api/v1/budget/plan/2026` is called
**Then** a 422 validation error is returned with field-level detail
**And** no entries are persisted (atomic — all or nothing)

**Given** the `budget.plans` table migration is applied
**When** the table is inspected
**Then** a unique constraint exists on `(year, month, transaction_type, category)`
**And** `planned_amount` is `Decimal(10,2)`

**Given** the migration is rolled back
**When** `alembic downgrade -1` is run
**Then** the `budget.plans` table is removed cleanly

**Given** all changes are complete
**When** `make lint && make type-check && make test` are run
**Then** all quality gates pass
