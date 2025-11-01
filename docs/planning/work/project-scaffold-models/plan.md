# Implementation Plan: Project Structure Scaffolding and Data Models

---
**Date:** 2025-10-31
**Requirements:** `docs/planning/work/project-scaffold-models/requirements.md`
**Research:** `docs/planning/work/project-scaffold-models/research.md`
**Linear Issue:** Not available (will be added manually)
**Feature Branch:** `feature/project-scaffold-models`
**Status:** draft

---

## Summary

**What:** Scaffold the complete project directory structure and create foundational Pydantic data models that enable the plugin-based handler architecture.

**Why:** All future development depends on this structure. Without it, developers don't have clear patterns to follow and the iOS app can't communicate with the backend.

**Who:** Backend developers implementing handlers, iOS app developers integrating with the backend, future maintainers of the codebase.

## Technical Context

### Platform & Technology
- **Stack:** Python 3.13 / FastAPI 0.115+
- **Version Requirements:** Python >=3.13
- **Build System:** uv + hatchling

### Key Dependencies
**Required:**
- fastapi >=0.115.0: Web framework and routing
- pydantic >=2.9.0: Data validation and schemas
- pydantic-settings >=2.6.0: Configuration management
- uvicorn >=0.32.0: ASGI server

**Optional:**
- None for this phase (database dependencies deferred)

### Architectural Patterns
**Primary Pattern:** Layered Architecture with Plugin-Based Handlers

**Rationale:** The architecture document defines clear separation between API Gateway, Classification Engine, Action Handlers, and Persistence layers. This supports extensibility through handler plugins.

**Key Principles:**
- Separation of concerns (API, business logic, handlers, persistence)
- Dependency injection via FastAPI (settings, services)
- Type safety enforced via Pydantic V2 and mypy strict mode
- Plugin architecture for handlers (easy to add new event types)

### Files to Modify/Create
| File | Action | Purpose |
|------|--------|---------|
| `src/life_organizer/schemas/__init__.py` | create | Package init |
| `src/life_organizer/schemas/requests.py` | create | API request models (ProcessInputRequest) |
| `src/life_organizer/schemas/responses.py` | create | API response models (ActionResult) |
| `src/life_organizer/schemas/classification.py` | create | Classification models (ClassifiedInput) |
| `src/life_organizer/schemas/actions.py` | create | BaseAppAction model (specific actions deferred) |
| `src/life_organizer/schemas/enums.py` | create | Enum types (ActionType, Category) |
| `src/life_organizer/handlers/__init__.py` | create | Handler registry |
| `src/life_organizer/handlers/base.py` | create | Base handler abstract class |
| `src/life_organizer/services/__init__.py` | create | Services package (placeholder) |
| `src/life_organizer/db/__init__.py` | create | Database package (placeholder) |
| `src/life_organizer/api/routes/__init__.py` | create | Routes package |
| `tests/schemas/test_requests.py` | create | Test request schema validation |
| `tests/schemas/test_responses.py` | create | Test response schema serialization |
| `tests/handlers/test_base.py` | create | Test handler base class contract |

## Technical Decisions

### Decision Summary
Key architectural and technical choices made during research:

1. **Separate schemas/ and models/ directories:** Keep separate
   - Rationale: Industry best practice - schemas for API contracts, models for domain objects
   - Impact: Clear distinction between API layer and domain layer, easier to maintain

2. **Use Pydantic V2 for all data models:** Chosen over dataclasses or TypedDict
   - Rationale: Native FastAPI integration, runtime validation, automatic OpenAPI docs
   - Impact: All endpoints get free validation and documentation

3. **Abstract Base Class for handlers:** Use abc.ABC with abstractmethod
   - Rationale: Enforces contract at runtime, type-safe with mypy, standard Python pattern
   - Impact: Impossible to create invalid handlers, clear documentation of requirements

4. **Enum for action types:** Use enum.Enum for action_type field
   - Rationale: Type-safe constants, prevents typos, better IDE support
   - Impact: Invalid action types caught at validation time, not runtime

5. **Defer database models:** Create placeholder db/ directory only
   - Rationale: Handler implementations (which need DB) are out of scope for this task
   - Impact: Faster delivery, database work can be done separately with clear requirements

## Phase Breakdown

> High-level implementation phases. Detailed tasks will be generated separately.

### Phase 0: Setup & Infrastructure
**Goal:** Create directory structure and package initialization files

**Deliverables:**
- [ ] Directory structure created (schemas/, handlers/, services/, db/, api/routes/)
- [ ] All `__init__.py` files created for proper Python package structure
- [ ] Test directory structure mirrors src structure

**Dependencies:** None (can start immediately)

**Estimated Effort:** 30 minutes

**Success Criteria:**
- Project still builds without errors
- All new packages are importable
- Test discovery still works

---

### Phase 1: Core Schema Models
**Goal:** Implement request/response schemas and classification models

**Deliverables:**
- [ ] ProcessInputRequest schema with validation (user_id, input, timestamp only)
- [ ] ActionResult schema with discriminated union for action_type
- [ ] ClassifiedInput schema with category, confidence, extracted data
- [ ] ActionType and Category enums defined
- [ ] Comprehensive tests for all schemas (validation, serialization)

**Note:** UserContext removed - the `context` field from the architecture document is not used anywhere and can be added later if needed.

**Dependencies:**
- Requires: Phase 0 (directory structure)
- Blocks: Phase 2 (handlers need schemas)

**Estimated Effort:** 3-4 hours

**Success Criteria:**
- All schemas validate correct data and reject invalid data
- FastAPI automatic OpenAPI docs include all schemas
- Test coverage >90% for schema modules
- mypy passes with no errors

**Technical Approach:**
Define Pydantic BaseModel subclasses following the contract from the architecture document. Use Field() for descriptions and validation rules. Create discriminated unions for ActionResult to handle different response types (backend_handled, app_action_required, confirmation_needed). Write comprehensive tests covering happy path, validation errors, and edge cases.

---

### Phase 2: App Action Models with Inheritance
**Goal:** Implement structured app action models using inheritance

**Deliverables:**
- [ ] BaseAppAction base class with type discriminator
- [ ] CreateReminderAction concrete model
- [ ] AddToShoppingListAction concrete model
- [ ] CreateCalendarEventAction concrete model
- [ ] Tests for all action models and discriminated union

**Dependencies:**
- Requires: Phase 1 (core schemas must exist first)
- Blocks: Phase 3 (responses use these models)

**Estimated Effort:** 2-3 hours

**Success Criteria:**
- BaseAppAction serves as base class with type field
- Each concrete action has specific fields (title, due_date, etc.)
- Pydantic discriminated union works correctly
- ActionResult.app_action field accepts AppAction union type
- Tests validate each action type independently
- iOS app can determine action type from JSON response

**Technical Approach:**
Create BaseAppAction base class with `type` discriminator field. Each action type (reminder, shopping, calendar) gets a concrete subclass with Literal type for the type field and specific fields for that action. Use Pydantic's discriminated union pattern so the type field determines which subclass to instantiate. ActionResult.app_action uses the AppAction type alias (union of all concrete types).

---

### Phase 3: Handler Base Architecture
**Goal:** Implement base handler class and registry system

**Deliverables:**
- [ ] BaseHandler abstract class with required methods (can_handle, requires_app_action, execute)
- [ ] ActionResult return type enforced in execute method signature
- [ ] Handler registry list in handlers/__init__.py
- [ ] get_handler() function to find appropriate handler
- [ ] Tests verifying abstract methods are enforced
- [ ] Example/dummy handler for testing registry

**Dependencies:**
- Requires: Phase 1 and 2 (handlers use schemas)
- Blocks: Future handler implementations

**Estimated Effort:** 2-3 hours

**Success Criteria:**
- Cannot instantiate BaseHandler directly (abstract class enforcement)
- Concrete handlers must implement all abstract methods
- Handler registry successfully finds correct handler
- Tests verify the handler contract is enforceable
- mypy enforces return types correctly

**Technical Approach:**
Use Python's abc.ABC to define BaseHandler with abstractmethod decorators on can_handle(), requires_app_action(), and execute(). The execute method must accept ClassifiedInput and return ActionResult. Create a simple list-based registry in handlers/__init__.py that iterates through handlers to find one that can_handle() a given input. Write a dummy/example handler in tests to verify the system works end-to-end.

---

### Phase 4: Integration & Documentation
**Goal:** Finalize package structure and add documentation

**Deliverables:**
- [ ] All __init__.py files properly export public APIs
- [ ] Docstrings for all public classes and methods
- [ ] Type hints verified by mypy with no errors
- [ ] Code formatted with ruff
- [ ] README updates if needed (probably not)
- [ ] Architecture documentation updated to reference actual code

**Dependencies:**
- Requires: All previous phases complete

**Estimated Effort:** 1-2 hours

**Success Criteria:**
- `make lint` passes (ruff, mypy)
- `make test` passes with >85% coverage
- All public APIs have docstrings
- Can import and use schemas/handlers from outside packages

**Technical Approach:**
Review all created modules and ensure they follow project conventions (from research.md). Add comprehensive docstrings using NumPy or Google style. Update __init__.py files to export public APIs cleanly (using __all__ if needed). Run full test suite and linting. Update docs/architecture/ if any significant deviations from the original plan.

---

## Implementation Strategy

### State Management
No application state management needed for this task - we're creating data structures only. Future classification engine and handlers will manage state via FastAPI dependency injection (get_settings(), database sessions, etc.).

**State Structure:**
N/A for this phase

### Data Flow
```
[iOS Request] → [FastAPI validates via ProcessInputRequest] → [Classification Engine (future)]
                                                                        ↓
[ActionResult returned] ← [Handler executes] ← [Registry finds Handler]
```

**Description:** Request comes in as JSON, FastAPI automatically validates against ProcessInputRequest schema. Classification engine (future) produces ClassifiedInput. Handler registry finds appropriate handler based on can_handle(). Handler executes and returns ActionResult. FastAPI serializes ActionResult back to JSON response.

### Error Handling
**Strategy:** Pydantic ValidationError for schema validation (automatic), FastAPI exception handlers for other errors

**Error Types to Handle:**
- Invalid request data: Handled by Pydantic, FastAPI returns 422 with validation details
- Missing required fields: Handled by Pydantic validation
- Invalid enums: Handled by Pydantic enum validation
- No handler found: Future concern (not in scope for scaffolding)

### Performance Considerations
**Optimization Points:**
- Handler registry: Simple O(n) list iteration is fine for 5-10 handlers
- Pydantic validation: Already optimized in V2, no action needed
- JSON serialization: Pydantic handles efficiently

**Constraints:**
- None identified for this foundational work

## Dependencies & Risks

### Internal Dependencies
- Phase 1 must complete before Phase 2 (app actions reference core schemas)
- Phase 1 and 2 must complete before Phase 3 (handlers use schemas)
- Phase 4 is blocked by all previous phases

### External Dependencies
- None - all work is self-contained within the backend codebase

### Known Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Schema validation too strict, rejects valid iOS requests | Medium | High | Use optional fields liberally, add sensible defaults, write comprehensive tests |
| Handler contract unclear, future developers implement incorrectly | Low | Medium | Abstract base class enforces contract, docstrings clarify expectations |
| Handler registry performance issues with many handlers | Low | Low | Start simple, can optimize to dict-based lookup later if needed |

### Assumptions
> Critical assumptions that, if invalid, would require plan revision

- Pydantic V2 validation performance is acceptable (validated by existing FastAPI usage)
- Architecture document's request/response contract is correct and won't change
- Future handlers will all fit the base handler pattern (can_handle, execute)
- SQLite/database work can be deferred without blocking handler development

## Acceptance Criteria Mapping

> Maps requirements.md acceptance criteria to implementation phases

| Acceptance Criterion | Phase | Verification Method |
|---------------------|-------|---------------------|
| Organized directories visible in codebase | Phase 0 | Manual inspection, ls command |
| ProcessInputRequest validates requests | Phase 1 | Unit tests + FastAPI test client |
| ActionResult includes all required fields | Phase 1, 2 | Schema tests, serialization tests |
| ClassifiedInput includes category, confidence | Phase 1 | Unit tests for schema |
| Base handler shows required abstract methods | Phase 3 | Docstrings, cannot instantiate test |
| Invalid requests return Pydantic validation errors | Phase 1 | FastAPI integration test |
| Missing optional fields have sensible defaults | Phase 1 | Unit tests with partial data |

## Documentation Plan

**Code Documentation:**
- [x] Inline documentation for complex logic (minimal - schemas are self-documenting)
- [x] API documentation via Pydantic Field descriptions (appears in OpenAPI)
- [x] Type annotations on all functions and classes (enforced by mypy)

**User Documentation:**
- N/A - this is infrastructure work, no end-user impact

**Developer Documentation:**
- [ ] Update architecture docs to reference actual schema files
- [ ] Add inline comments explaining handler contract in base.py
- [ ] Docstrings explaining how to use schemas and handlers

## Next Steps

1. **Review this plan** with team or stakeholders
2. **Clarify any remaining questions** (none currently identified)
3. **Generate detailed tasks** for Phase 0 and Phase 1
4. **Begin implementation** in this worktree (feature/project-scaffold-models branch)

## Remaining Unknowns

> Issues that need resolution before or during implementation

None - all research complete, clear path forward.

**Impact:** N/A

---

**Plan Status:** draft (ready for review)
**Approval Required From:** N/A (foundation work, no architectural changes)
**Target Start Date:** 2025-10-31 (immediately)
