---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7]
inputDocuments:
  - '_bmad-output/prd.md'
  - '_bmad-output/epics.md'
  - '_bmad-output/index.md'
  - 'docs/architecture/backend-architecture-high-level-design.md'
workflowType: 'architecture'
lastStep: 7
project_name: 'life-organizer-be'
user_name: 'Ivo'
date: '2026-02-02'
projectType: 'brownfield'
---

# Architecture Decision Document - life-organizer-be

> Voice-first intelligent agent API for personal life organization
> Generated via BMAD Architecture Workflow

---

## Project Context Analysis

### Vision & Purpose

A personal intelligent agent that captures everyday life events via natural language and automatically routes them to the appropriate organizational system — with minimal friction and maximum reliability.

**The Killer Feature:** Rapid-fire multi-transaction logging. Think it, type it, done. Repeat.

### Requirements Overview

**Functional Requirements (Current Scope):**

| Category | Status | Backend Responsibility |
|----------|--------|------------------------|
| Budget | ✅ Complete | Parse, categorize, persist to PostgreSQL |
| Quote | 🔲 To Build | Parse source/page metadata, return app action |
| Note | 🔲 To Build | Store freeform text, return app action |

**Removed from Scope (Cleanup Required):**
- ~~Reminder~~ — Delete handler, model, prompts, tests
- ~~Calendar~~ — Delete placeholders/comments
- ~~Shopping~~ — Delete placeholders/comments

**Non-Functional Requirements:**

| NFR | Target | Rationale |
|-----|--------|-----------|
| End-to-end response | < 1 second | Must feel instant for rapid-fire logging |
| Handler processing | < 500ms | LLM parsing should not bottleneck UX |
| Database writes | < 100ms | PostgreSQL writes should be near-instant |
| Data loss | Zero tolerance | Every logged entry must persist |
| Error handling | 100% graceful | Failures return clear errors, never silent |

### Scale & Complexity

- **Primary Domain:** API Backend with LLM Integration
- **Complexity Level:** Low-Medium
- **Project Context:** Brownfield — 1 of 3 classification flows complete
- **Distribution:** Personal use only (no multi-tenancy, no auth)

### Technical Constraints

| Constraint | Value |
|------------|-------|
| Authentication | None required (personal use) |
| Rate limiting | None (single user) |
| API versioning | Versioned at `/api/v1/` |
| Retrieval endpoints | None (iOS handles local browsing) |
| Image handling | None (iOS handles OCR) |

---

## Core Architectural Decisions

### Architecture Pattern

**Decision:** Async REST API Backend with LLM Integration

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌────────────────────┐    ┌─────────────┐ │
│  │  API Routes  │───▶│  Classifier        │───▶│  Claude AI  │ │
│  │              │    │  Orchestrator      │    │  (Anthropic)│ │
│  └──────────────┘    └────────────────────┘    └─────────────┘ │
│         │                     │                                  │
│         ▼                     ▼                                  │
│  ┌──────────────┐    ┌────────────────────┐                     │
│  │  Handlers    │───▶│  Database Layer    │                     │
│  │  (Budget,    │    │  (SQLAlchemy +     │                     │
│  │   Quote,     │    │   asyncpg)         │                     │
│  │   Note)      │    │                    │                     │
│  └──────────────┘    └────────────────────┘                     │
│                               │                                  │
└───────────────────────────────┼──────────────────────────────────┘
                                │
                                ▼
                       ┌────────────────┐
                       │  PostgreSQL    │
                       │  (budget.*)    │
                       └────────────────┘
```

**Rationale:** Two-stage classification where iOS performs on-device category classification, then backend receives pre-classified input and routes to targeted handler with category-specific prompt.

### Technology Stack

| Category | Technology | Version | Rationale |
|----------|------------|---------|-----------|
| **Language** | Python | 3.13 | Modern async support, LLM ecosystem |
| **Framework** | FastAPI | >=0.115.0 | Async-native, automatic OpenAPI |
| **ASGI Server** | Uvicorn | >=0.32.0 | High-performance async server |
| **Validation** | Pydantic | >=2.9.0 | Type-safe request/response handling |
| **Database** | PostgreSQL | 16-alpine | Production-grade, JSONB support |
| **ORM** | SQLAlchemy | >=2.0.0 | Async support, migration tooling |
| **DB Driver** | asyncpg | >=0.30.0 | Native async PostgreSQL driver |
| **Migrations** | Alembic | >=1.13.0 | Database schema versioning |
| **AI/LLM** | Anthropic Claude | >=0.40.0 | Best-in-class classification |
| **Retry Logic** | Tenacity | >=8.0.0 | Robust retry patterns |
| **Testing** | Pytest | >=8.3.0 | Async test support |
| **Linting** | Ruff | >=0.7.0 | Fast Python linter |
| **Type Checking** | MyPy | >=1.13.0 | Strict type enforcement |
| **Package Mgmt** | uv | latest | Fast Python package manager |

### Data Architecture

**Database Schema Namespace:** `budget`

**Decision:** Single schema namespace for all domain tables, prefixed operations.

#### BudgetTransaction Table (Existing)

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `amount` | NUMERIC(10,2) | Original amount |
| `currency` | VARCHAR(3) | Currency code (EUR) |
| `amount_eur` | NUMERIC(10,2) | Normalized EUR amount |
| `date` | DATE | Transaction date |
| `transaction_type` | VARCHAR(20) | Expenses/Income/Savings |
| `category` | VARCHAR(50) | Category name |
| `details` | TEXT | Merchant/description |
| `created_at` | TIMESTAMP | Created timestamp |
| `updated_at` | TIMESTAMP | Updated timestamp |

#### Quote Table (To Build)

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `text` | TEXT | Quote content |
| `source` | VARCHAR(255) | Book title (nullable) |
| `author` | VARCHAR(255) | Author name (nullable) |
| `page` | INTEGER | Page number (nullable) |
| `created_at` | TIMESTAMP | Created timestamp |

#### Note Table (To Build)

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `content` | TEXT | Note content |
| `title` | VARCHAR(255) | Optional title (nullable) |
| `created_at` | TIMESTAMP | Created timestamp |

### API Design

**Decision:** Single unified endpoint receives pre-classified input, routes to handler.

**Endpoint Pattern:**

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/process` | Process classified input (multi-tx) |
| GET | `/api/v1/budget/export` | Export budget transactions TSV |
| GET | `/health` | Health check |
| GET | `/api/v1/health` | Versioned health |

**Request Contract:**

```json
{
  "input": "quote from Atomic Habits page 47: The goal is not to read a book...",
  "category": "QUOTE"
}
```

**Response Contract:**

```json
{
  "success": true,
  "action_type": "backend_handled" | "app_action_required",
  "message": "Saved quote from Atomic Habits",
  "app_action": {
    "type": "save_quote",
    "data": { "quote": "...", "source": "Atomic Habits", "page": 47 }
  }
}
```

### Handler Architecture

**Decision:** Plugin-based handler registry with BaseHandler interface.

```python
class BaseHandler:
    def can_handle(self, classified_input) -> bool: ...
    def requires_app_action(self) -> bool: ...
    async def execute(self, classified_input) -> ProcessingResponse: ...
```

**Handler Routing:**

| Category | Handler | Action Type | Persistence |
|----------|---------|-------------|-------------|
| BUDGET | BudgetHandler | backend_handled | PostgreSQL |
| QUOTE | QuoteHandler | app_action_required | PostgreSQL |
| NOTE | NoteHandler | app_action_required | PostgreSQL |

### Error Handling Strategy

**Decision:** All errors return structured JSON, never silent failures.

```json
{
  "success": false,
  "action_type": "error",
  "message": "Classification failed: invalid category",
  "error_code": "CLASSIFICATION_ERROR"
}
```

**Retry Policy:** Tenacity-based retry for Claude API calls with exponential backoff.

---

## Implementation Patterns & Consistency Rules

### Naming Patterns

**Database Naming:**
- Tables: `snake_case`, plural (`quotes`, `notes`, `budget_transactions`)
- Columns: `snake_case` (`created_at`, `transaction_type`)
- Foreign keys: `{table}_id` format (`user_id`)
- Indexes: `idx_{table}_{column}` format

**API Naming:**
- Endpoints: `/api/v1/{resource}` (lowercase, plural where appropriate)
- Query params: `snake_case` (`start_date`, `end_date`)
- JSON fields: `snake_case` (matches Python conventions)

**Code Naming:**
- Files: `snake_case.py` (`budget_handler.py`, `quote_handler.py`)
- Classes: `PascalCase` (`BudgetHandler`, `QuoteHandler`)
- Functions: `snake_case` (`process_input`, `get_handler`)
- Constants: `SCREAMING_SNAKE_CASE` (`DEFAULT_CURRENCY`)
- Type aliases: `PascalCase` (`ClassifiedInput`, `ProcessingResponse`)

### Structure Patterns

**Handler Organization:**
- One handler per category in `handlers/` directory
- All handlers inherit from `BaseHandler`
- Handler registration via `__init__.py` imports

**Schema Organization:**
- Request/Response models in `schemas/requests.py` and `schemas/responses.py`
- Domain-specific schemas in dedicated files (`schemas/budget.py`, `schemas/quote.py`)
- Shared enums in `schemas/enums.py`
- App actions in `schemas/actions.py`

**Prompt Organization:**
- One prompt file per category in `prompts/` directory
- Naming: `{category}_system_prompt_v{version}.txt`
- Version suffix enables A/B testing of prompts

### Format Patterns

**API Response Format:**

```python
class ProcessingResponse(BaseModel):
    success: bool
    action_type: str  # "backend_handled" | "app_action_required" | "error"
    message: str
    app_action: Optional[AppAction] = None
    error_code: Optional[str] = None
```

**Date/Time Format:**
- API responses: ISO 8601 strings (`2026-02-02T14:30:00Z`)
- Database: Native PostgreSQL timestamps with timezone
- User input parsing: Natural language via LLM ("yesterday", "last Monday")

**Error Response Format:**

```python
{
    "success": False,
    "action_type": "error",
    "message": "Human-readable error message",
    "error_code": "CATEGORY_SPECIFIC_ERROR_CODE"
}
```

### Process Patterns

**Handler Execution Flow:**
1. Receive `ClassifyRequest` with pre-classified category
2. Route to appropriate handler via registry
3. Handler calls Claude with category-specific prompt
4. Parse LLM response into structured data
5. Persist to database (if backend_handled)
6. Return `ProcessingResponse` with app_action (if needed)

**Multi-Transaction Handling:**
- Single input can contain multiple transactions ("50 at DM and 30 at grocery")
- Handler returns list of `ProcessingResponse`
- Each transaction persisted independently

**Retry Pattern:**
- Tenacity retry on Claude API calls
- Max 3 retries with exponential backoff
- Log all retry attempts

---

## Project Structure & Boundaries

### Complete Project Directory Structure

```
life-organizer-be/
├── README.md
├── DOCKER.md
├── Makefile
├── pyproject.toml
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── docker-compose.yml
├── Dockerfile
├── openapi.yaml                    # API specification
├── models.yaml                     # iOS integration models
│
├── alembic/                        # Database migrations
│   ├── env.py
│   ├── alembic.ini
│   └── versions/
│       └── *.py                    # Migration files
│
├── src/life_organizer/
│   ├── __init__.py
│   ├── main.py                     # [ENTRY] FastAPI application
│   ├── config.py                   # Pydantic Settings
│   ├── logging_config.py           # Logging setup
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── classifier.py       # POST /api/v1/process
│   │       └── budget.py           # GET /api/v1/budget/export
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py                 # SQLAlchemy base
│   │   ├── session.py              # Async session factory
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── budget.py           # BudgetTransaction model
│   │       ├── quote.py            # Quote model (TO BUILD)
│   │       └── note.py             # Note model (TO BUILD)
│   │
│   ├── handlers/
│   │   ├── __init__.py             # Handler registry
│   │   ├── base.py                 # BaseHandler interface
│   │   ├── budget_entry.py         # Budget handler ✅
│   │   ├── quote_handler.py        # Quote handler (TO BUILD)
│   │   └── note_handler.py         # Note handler (TO BUILD)
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── enums.py                # Shared enums (Category, etc.)
│   │   ├── budget.py               # Budget categories
│   │   ├── requests.py             # ClassifyRequest
│   │   ├── responses.py            # ProcessingResponse
│   │   ├── classification.py       # ClassifiedInput
│   │   └── actions.py              # App action types
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── classifier_orchestrator.py
│   │   └── claude_classifier.py    # Claude API integration
│   │
│   └── prompts/
│       ├── budget_system_prompt_v2.txt
│       ├── quote_system_prompt_v1.txt   # (TO BUILD)
│       └── note_system_prompt_v1.txt    # (TO BUILD)
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures
│   ├── handlers/
│   │   ├── test_budget_handler.py
│   │   ├── test_quote_handler.py   # (TO BUILD)
│   │   └── test_note_handler.py    # (TO BUILD)
│   ├── services/
│   │   └── test_classifier.py
│   ├── schemas/
│   │   └── test_schemas.py
│   ├── integration/
│   │   └── test_api.py
│   └── fixtures/
│       └── *.json                  # Test data
│
├── docs/
│   ├── product/
│   │   └── initial-prd.md
│   ├── architecture/
│   │   └── backend-architecture-high-level-design.md
│   ├── development/
│   │   └── setup.md
│   └── planning/
│       ├── work/
│       └── archive/
│
└── _bmad-output/                   # BMAD workflow outputs
    ├── index.md
    ├── prd.md
    ├── epics.md
    └── architecture.md             # This document
```

### Architectural Boundaries

**API Boundary:**
- Single entry point: `POST /api/v1/process`
- Request validation at API layer via Pydantic
- All responses follow `ProcessingResponse` contract

**Handler Boundary:**
- Handlers are isolated, no cross-handler dependencies
- Each handler owns its category-specific logic
- Handlers communicate only via defined interfaces

**Service Boundary:**
- `ClassifierOrchestrator` coordinates classification flow
- `ClaudeClassifier` encapsulates all LLM interactions
- Services are injected via dependency injection

**Data Boundary:**
- All database access via SQLAlchemy async session
- Models define schema, handlers use repositories
- No direct SQL outside of migration files

### Requirements to Structure Mapping

| Requirement | Components |
|-------------|------------|
| Budget Flow | `handlers/budget_entry.py`, `db/models/budget.py`, `prompts/budget_*.txt` |
| Quote Flow | `handlers/quote_handler.py`, `db/models/quote.py`, `prompts/quote_*.txt` |
| Note Flow | `handlers/note_handler.py`, `db/models/note.py`, `prompts/note_*.txt` |
| Classification | `services/classifier_orchestrator.py`, `services/claude_classifier.py` |
| API Contract | `api/routes/classifier.py`, `schemas/requests.py`, `schemas/responses.py` |

---

## Implementation Guidance for AI Agents

### Adding a New Handler (Quote/Note)

1. **Create model** in `db/models/{category}.py`
   - Follow existing `BudgetTransaction` pattern
   - Add to `db/models/__init__.py` exports
   - Create Alembic migration

2. **Create handler** in `handlers/{category}_handler.py`
   - Inherit from `BaseHandler`
   - Implement `can_handle()`, `requires_app_action()`, `execute()`
   - Register in `handlers/__init__.py`

3. **Create prompt** in `prompts/{category}_system_prompt_v1.txt`
   - Follow existing prompt structure
   - Include extraction instructions for metadata

4. **Create app action** in `schemas/actions.py`
   - Add to discriminated union `AppAction`
   - Follow existing `LogBudgetEntryAction` pattern

5. **Add tests** in `tests/handlers/test_{category}_handler.py`
   - Unit tests for handler logic
   - Integration tests for full flow

### Cleanup Tasks (Reminder/Calendar/Shopping)

**Files to Delete:**
- `handlers/reminder_handler.py` (if exists)
- `prompts/reminder_system_prompt_v1.txt`
- `prompts/shopping_system_prompt_v1.txt`
- `prompts/calendar_system_prompt_v1.txt`
- Related test files
- References in handler registry

**Enum Updates:**
- Remove `REMINDER`, `CALENDAR`, `SHOPPING` from `Category` enum
- Update any switch/match statements

### Quality Gates

All changes MUST pass:
- `make lint` — Ruff linting
- `make type-check` — MyPy strict mode
- `make test` — All tests with coverage
- Pre-commit hooks (automatic on commit)

### Commit Standards

Use conventional commits:
- `feat(quote): add quote handler and model`
- `fix(budget): correct currency conversion`
- `refactor(handlers): remove reminder handler`
- `test(quote): add handler unit tests`

---

## Validation Checklist

### Architecture Coherence

- [x] Single unified API endpoint pattern
- [x] Handler plugin architecture for extensibility
- [x] Consistent schema patterns across all handlers
- [x] Clear separation: API → Service → Handler → Database
- [x] All technology versions documented

### Pattern Completeness

- [x] Naming conventions defined for all layers
- [x] Error handling patterns documented
- [x] Response format standardized
- [x] File organization patterns clear

### Implementation Readiness

- [x] PRD scope aligned (Budget ✅, Quote 🔲, Note 🔲)
- [x] Epics need alignment (remove Shopping/Calendar/Reminder stories)
- [x] New handler implementation path documented
- [x] Cleanup tasks identified
- [x] Quality gates defined

---

## Appendix: Quick Reference

### Key Commands

| Command | Description |
|---------|-------------|
| `make dev` | Install dependencies |
| `make run` | Start development server |
| `make test` | Run all tests with coverage |
| `make test-unit` | Run unit tests only |
| `make lint` | Run Ruff linter |
| `make type-check` | Run MyPy |

### Environment Variables

| Variable | Description |
|----------|-------------|
| `CLAUDE_API_KEY` | Anthropic API key |
| `DATABASE_URL` | PostgreSQL connection string |
| `LOG_LEVEL` | Logging level (INFO, DEBUG) |

### API Access Points

| URL | Description |
|-----|-------------|
| http://localhost:8000 | API base |
| http://localhost:8000/api/v1/docs | Swagger UI |
| http://localhost:8000/api/v1/redoc | ReDoc |
| http://localhost:8000/health | Health check |
