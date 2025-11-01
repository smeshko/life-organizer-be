# Research: Project Structure Scaffolding and Data Models

---
**Date:** 2025-10-31
**Requirements:** `docs/planning/work/project-scaffold-models/requirements.md`
**Linear Issue:** Not available (will be added manually)
**Status:** complete

---

## Platform Detection

**Primary Technology Stack:**
- Language/Framework: Python 3.13 / FastAPI 0.115+
- Version: Python 3.13
- Runtime/Platform: Python 3.13+ (as specified in pyproject.toml:6)

**Build System:**
- uv (modern Python package manager)
- hatchling (build backend)
- Pre-commit hooks for code quality

## Dependencies Analysis

### Required Dependencies
| Dependency | Version | Purpose | Source |
|------------|---------|---------|--------|
| fastapi | >=0.115.0 | Web framework and API layer | existing (pyproject.toml:18) |
| pydantic | >=2.9.0 | Data validation and settings | existing (pyproject.toml:20) |
| pydantic-settings | >=2.6.0 | Configuration management | existing (pyproject.toml:21) |
| uvicorn | >=0.32.0 | ASGI server | existing (pyproject.toml:19) |

### Optional Dependencies
| Dependency | Version | Purpose | Trade-off |
|------------|---------|---------|-----------|
| sqlalchemy | >=2.0.0 | Database ORM (future) | Deferred to separate task - adds complexity but needed for persistence |
| sqlmodel | latest | Combines SQLAlchemy + Pydantic | Alternative to pure SQLAlchemy, simpler but less flexible |

## Codebase Patterns

### Architectural Patterns Found
- **Pattern:** Pydantic Settings for Configuration
  - **Location:** `src/life_organizer/config.py:9-56`
  - **Usage:** BaseSettings with Field descriptors, lru_cache for singleton pattern
  - **Relevance:** We should follow this pattern for all configuration models

- **Pattern:** FastAPI Application Factory
  - **Location:** `src/life_organizer/main.py:42-50`
  - **Usage:** Single app instance with lifespan context manager for startup/shutdown
  - **Relevance:** Main.py will need to register new routes when we add them

- **Pattern:** Type Hints with Modern Python
  - **Location:** Throughout codebase (e.g., `config.py:29` using `list[str]`, `config.py:35` using `str | None`)
  - **Usage:** Python 3.13 native syntax for unions and generics
  - **Relevance:** All models must use modern type hints (no typing.Optional, typing.List)

### Code Conventions
- **State Management:** Dependency injection via FastAPI (settings via get_settings())
  - Example: `src/life_organizer/main.py:14`
- **Error Handling:** Pydantic ValidationError for request validation (built-in to FastAPI)
  - Will be automatic for all Pydantic models used in routes
- **Async Patterns:** Async/await for all route handlers
  - Example: `src/life_organizer/main.py:64-77`

### Naming Conventions
- Files: snake_case.py (e.g., `logging_config.py`)
- Types/Classes: PascalCase (e.g., `Settings`, `BaseSettings`)
- Functions: snake_case (e.g., `get_settings`, `health_check`)
- Constants: UPPER_SNAKE_CASE (not yet used but standard Python convention)

## Integration Points

### Components to Modify
| Component | Location | Change Type | Impact |
|-----------|----------|-------------|--------|
| FastAPI app | `src/life_organizer/main.py:42` | Extend | Will need to register new routes from api/routes/ |
| Project structure | `src/life_organizer/` | Create | Add new directories: schemas/, handlers/, services/, db/ |
| API directory | `src/life_organizer/api/` | Extend | Add routes/ subdirectory for endpoint modules |

### Dependencies Between Components
```
main.py (FastAPI app)
    ↓
api/routes/ (endpoint modules - future)
    ↓
schemas/ (request/response models) ← NEW
    ↓
handlers/ (business logic) ← NEW
    ↓
services/ (external integrations - future)
```

**Description:** The FastAPI app will import route modules from api/routes/, which will use schemas for request/response validation. Handlers will process requests and return structured ActionResult objects defined in schemas.

### External Integrations
- **API/Service:** Google Sheets API (future - not in scope)
  - Endpoint: Google Sheets REST API
  - Authentication: OAuth2 or service account
  - Data Format: JSON

## Clarifications Resolved

### Clarification 1: Separate models/ and schemas/ directories?
**Question:** Should we use separate `models/` and `schemas/` directories or combine into one?
**Finding:** Industry best practice in FastAPI applications is to separate:
- `schemas/` for API contracts (request/response Pydantic models)
- `models/` for domain/business logic objects or database models
**Decision:** Keep separate directories. Use `schemas/` for all Pydantic models that represent API contracts. Reserve `models/` for future database models (SQLAlchemy/SQLModel).
**Source:** FastAPI documentation best practices and common patterns in FastAPI projects

**Recommendation from requirements:** Keep separate - models are domain objects, schemas are API contracts ✓

### Clarification 2: UserContext field usage?
**Question:** What is the `context` field in the request supposed to be used for? The architecture document shows it in the request example but never explains or uses it.
**Finding:** The context field (with location and previous_action) appears only in the example request but is never referenced in classification logic, handler implementations, or data flow examples.
**Decision:** Remove the context field entirely. Keep ProcessInputRequest simple with just user_id, input, and timestamp. Can add contextual fields later when there's a clear use case.
**Source:** Architecture document review + user clarification

### Clarification 3: Database models now or later?
**Question:** Do we need database models (SQLAlchemy/SQLModel) now or later?
**Finding:**
- Current requirements focus on structure and API contracts only
- Architecture document mentions SQLite for Stage 1 but doesn't require immediate implementation
- Handler implementations (which would use database) are explicitly out of scope
**Decision:** Defer database models to separate task. Create placeholder `db/` directory with basic structure only.
**Source:** requirements.md:112-113, architecture document

**Recommendation from requirements:** Defer to separate task ✓

## Technical Decisions

### Decision 1: Directory Structure Organization
**Choice:** Create separate directories for schemas, handlers, services, db, and api/routes
**Rationale:**
- Mirrors layered architecture from design document
- Clear separation of concerns
- Makes codebase self-documenting (REQ-001)
- Follows FastAPI community conventions

**Alternatives Considered:**
- Flat structure in life_organizer/: Rejected because becomes unwieldy as project grows
- Feature-based structure (group by feature, not layer): Rejected because this is infrastructure/foundation work, not feature work

**Impact:** All future code has clear location. Testing and maintenance are easier.

### Decision 2: Use Pydantic for All Data Models
**Choice:** Use Pydantic V2 models for all schemas and data structures
**Rationale:**
- Already in dependencies (pyproject.toml:20)
- Native FastAPI integration (automatic validation, OpenAPI docs)
- Type safety and validation at runtime
- Modern Python 3.13 type hints support

**Alternatives Considered:**
- dataclasses: Rejected because no runtime validation
- TypedDict: Rejected because no validation, less ergonomic
- attrs: Rejected because Pydantic is FastAPI standard

**Impact:** All API endpoints will have automatic request/response validation and OpenAPI documentation generation.

### Decision 3: Abstract Base Class for Handlers
**Choice:** Use Python's abc.ABC with abstractmethod decorators for base handler
**Rationale:**
- Forces concrete handlers to implement required methods (can_handle, requires_app_action, execute)
- Type-safe with mypy (strict mode enabled in pyproject.toml:80-100)
- Standard Python pattern for defining contracts
- Provides clear documentation of handler contract

**Alternatives Considered:**
- Protocol (typing.Protocol): Rejected because ABC provides better runtime enforcement
- No base class: Rejected because doesn't enforce contract

**Impact:** All handlers must implement the required interface, preventing bugs from missing methods.

### Decision 4: Enum for Action Types
**Choice:** Use Python's enum.Enum for action_type field values
**Rationale:**
- Type-safe string constants
- Prevents typos in string literals
- Better IDE autocomplete
- Works seamlessly with Pydantic (automatic validation)

**Alternatives Considered:**
- Literal types: Could work but Enum is more explicit and reusable
- Plain strings: Rejected because no type safety

**Impact:** Action types are validated at API layer, impossible to have invalid action_type values.

## Performance Considerations

**Constraints Identified:**
- N/A: This is foundational scaffolding work with no performance-critical paths

**Optimization Opportunities:**
- Use Pydantic model_config for performance tuning if needed in future
- Lazy imports for handler registry if handler count becomes large

## Risks & Unknowns

### Known Risks
1. **Risk:** Handler registry pattern may need refactoring if handler count exceeds 20-30
   - **Mitigation:** Use simple list-based registry now, can optimize to dict-based lookup later if needed
   - **Impact if unaddressed:** O(n) lookup time, but n will be small (5-10 handlers)

2. **Risk:** Pydantic model validation could be strict and reject valid edge cases
   - **Mitigation:** Use sensible defaults and optional fields where appropriate
   - **Impact if unaddressed:** iOS app may have trouble sending valid requests

### Remaining Unknowns
- None - all technical questions resolved

## Research Summary

**Key Findings:**
1. FastAPI + Pydantic V2 already configured with strict mypy type checking - excellent foundation
2. Project follows modern Python 3.13 conventions (native unions, generics) - maintain consistency
3. Existing patterns (Settings with lru_cache, async route handlers) should guide implementation
4. Separate schemas/ and models/ directories aligns with FastAPI best practices
5. Database layer can be safely deferred to separate task

**Confidence Level:** High
- All clarifications resolved with clear decisions
- Existing codebase provides strong patterns to follow
- No technical blockers identified
- Requirements are clear and well-defined

**Recommended Next Steps:**
1. Create directory structure (schemas/, handlers/, services/, db/, api/routes/)
2. Implement base Pydantic schemas for request/response contract
3. Implement base handler abstract class
4. Create handler registry with minimal implementation
5. Add route registration mechanism to main.py

---

**Ready for Planning:** Yes - all research complete, clear path forward
