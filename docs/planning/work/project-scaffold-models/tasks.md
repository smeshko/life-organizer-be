# Execution Tasks: Project Structure Scaffolding and Data Models

**Branch Strategy:** `feature/project-scaffold-models` → `staging` → `main`
**Complexity:** Medium
**Estimated Duration:** 7-11 hours (1-2 days)
**Created:** 2025-10-31

---

## Overview

Scaffold the complete project directory structure and create foundational Pydantic data models that enable the plugin-based handler architecture. This establishes the organizational foundation for implementing the classification system and individual handlers.

**Deliverables:**
- Directory structure (schemas/, handlers/, services/, db/, api/routes/)
- Request/response schemas (ProcessInputRequest, ActionResult)
- Classification schemas (ClassifiedInput, Category, ActionType enums)
- App action models (BaseAppAction, CreateReminderAction, AddToShoppingListAction, CreateCalendarEventAction)
- Handler base architecture (BaseHandler abstract class, registry system)

---

## Quick Reference

- **Total Phases:** 2
- **Total Tasks:** 8
- **Estimated Commits:** 8
- **Parallel Opportunities:** T002, T003, T005, T006 (first wave parallel)
- **Critical Path:** T001 → (T002/T003/T005/T006 parallel) → T004 → T007 → T008

---

## Phase 1: Complete Foundation

**Goal:** Create directory structure and implement all schema models including app actions
**PR Title:** `feat(foundation): scaffold project structure and core schemas`
**Deliverable:** Complete directory structure with all request/response/classification/action schemas implemented and tested

---

### Task T001: Create Directory Structure

**Source:** `TASK-001-directory-structure.md`
**Type:** IMPLEMENTATION
**Files:** All `__init__.py` files for new packages

**Implementation:**
- [x] Create directory structure (schemas/, handlers/, services/, db/, api/routes/)
- [x] Create all `__init__.py` files
- [x] Create test directories
- [x] Verify imports work

**Verification:**
✓ Build succeeds | ✓ All packages importable | ✓ No import errors

---

### Task T002: Create Enum Types

[P] **Parallelizable with T003-T006**
**Source:** `TASK-002-enums.md`
**Type:** IMPLEMENTATION
**Files:** `src/life_organizer/schemas/enums.py`, `tests/schemas/test_enums.py`

**Implementation:**
- [x] Define ActionType enum (BACKEND_HANDLED, APP_ACTION_REQUIRED, CONFIRMATION_NEEDED)
- [x] Define Category enum (EXPENSE, SHOPPING, REMINDER, CALENDAR, UNKNOWN)
- [x] Write tests for enum validation

**Verification:**
✓ Build succeeds | ✓ Tests pass | ✓ mypy passes

---

### Task T003: Implement ProcessInputRequest Schema

[P] **Parallelizable with T002, T004-T006**
**Source:** `TASK-003-request-schema.md`
**Type:** IMPLEMENTATION
**Files:** `src/life_organizer/schemas/requests.py`, `tests/schemas/test_requests.py`

**Implementation:**
- [x] Define ProcessInputRequest model (user_id, input, timestamp)
- [x] Add Field() descriptions for OpenAPI
- [x] Write comprehensive validation tests

**Verification:**
✓ Build succeeds | ✓ Tests pass | ✓ Pydantic validation works

---

### Task T004: Implement ActionResult Response Schema

**Depends On:** T006 (needs AppAction types)
**Source:** `TASK-004-response-schema.md`
**Type:** IMPLEMENTATION
**Files:** `src/life_organizer/schemas/responses.py`, `tests/schemas/test_responses.py`

**Implementation:**
- [x] Import AppAction type from schemas.actions
- [x] Define ConfirmationData model
- [x] Define ActionResult model with AppAction union type
- [x] Write tests for all three response types with concrete action models

**Verification:**
✓ Build succeeds | ✓ Tests pass | ✓ All response types validate | ✓ Discriminated union works

---

### Task T005: Implement ClassifiedInput Schema

[P] **Parallelizable with T002-T004, T006**
**Source:** `TASK-005-classification-schema.md`
**Type:** IMPLEMENTATION
**Files:** `src/life_organizer/schemas/classification.py`, `tests/schemas/test_classification.py`

**Implementation:**
- [x] Define ClassifiedInput model (category, confidence, extracted_data, raw_input)
- [x] Add confidence score validation (0.0-1.0)
- [x] Write tests for classification scenarios

**Verification:**
✓ Build succeeds | ✓ Tests pass | ✓ Confidence validation works

---

### Task T006: Implement AppAction Models with Inheritance

[P] **Parallelizable with T002-T003, T005**
**Source:** `TASK-006-app-action-schema.md`
**Type:** IMPLEMENTATION
**Files:** `src/life_organizer/schemas/actions.py`, `tests/schemas/test_actions.py`

**Implementation:**
- [x] Define BaseAppAction base class with type discriminator
- [x] Define CreateReminderAction (title, due_date, list_id, notes)
- [x] Define AddToShoppingListAction (item, quantity, list_id, notes)
- [x] Define CreateCalendarEventAction (title, start_time, end_time, location, notes)
- [x] Create AppAction type alias for discriminated union
- [x] Write tests for each action type and discrimination

**Verification:**
✓ Build succeeds | ✓ Tests pass | ✓ Discriminated union works | ✓ All three action types validate

---

**Phase 1 Completion Checklist:**
- [x] All 6 tasks completed (T001-T006)
- [x] Build succeeds: `make lint`
- [x] All tests passing: `make test`
- [x] No mypy errors
- [x] Test coverage >85% (94% achieved)
- [x] All schemas export from `life_organizer.schemas`
- [ ] Create PR: `feature/project-scaffold-models` → `staging`

---

## Phase 2: Handler Architecture

**Goal:** Implement handler base class and registry system
**PR Title:** `feat(handlers): implement base handler architecture and registry`
**Deliverable:** BaseHandler abstract class with registry system, ready for concrete handler implementations

---

### Task T007: Implement BaseHandler Abstract Class

**Source:** `TASK-007-base-handler.md`
**Type:** IMPLEMENTATION
**Files:** `src/life_organizer/handlers/base.py`, `tests/handlers/test_base.py`

**Implementation:**
- [x] Define BaseHandler with ABC
- [x] Add abstract methods (can_handle, requires_app_action, execute)
- [x] Write tests verifying abstract enforcement

**Verification:**
✓ Build succeeds | ✓ Tests pass | ✓ Cannot instantiate BaseHandler directly

---

### Task T008: Implement Handler Registry System

**Source:** `TASK-008-handler-registry.md`
**Type:** IMPLEMENTATION
**Files:** `src/life_organizer/handlers/__init__.py`, `tests/handlers/test_registry.py`, `tests/handlers/dummy_handler.py`

**Implementation:**
- [x] Implement HANDLERS list
- [x] Implement get_handler() function
- [x] Create DummyHandler for testing
- [x] Write registry tests (find handler, no match, precedence)

**Verification:**
✓ Build succeeds | ✓ Tests pass | ✓ Registry lookup works correctly

---

**Phase 2 Completion Checklist:**
- [ ] All 2 tasks completed (T007-T008)
- [ ] Build succeeds: `make lint`
- [ ] All tests passing: `make test`
- [ ] No mypy errors
- [ ] DummyHandler demonstrates complete handler contract
- [ ] Handler registry works end-to-end
- [ ] Create PR: `feature/project-scaffold-models` → `staging`

---

## Task Reference

| ID | Task | Type | Phase | Dependencies | Files |
|----|------|------|-------|--------------|-------|
| T001 | Directory Structure | IMPL | 1 | None | All __init__.py |
| T002 | Enum Types | IMPL | 1 | T001 | enums.py |
| T003 | ProcessInputRequest | IMPL | 1 | T001 | requests.py |
| T004 | ActionResult | IMPL | 1 | T002, T006 | responses.py |
| T005 | ClassifiedInput | IMPL | 1 | T001, T002 | classification.py |
| T006 | AppAction Models | IMPL | 1 | T001 | actions.py |
| T007 | BaseHandler | IMPL | 2 | T004, T005 | base.py |
| T008 | Handler Registry | IMPL | 2 | T007 | __init__.py |

---

## Timeline Estimate

**Phase 1:** 5-8 hours
- T001: 30 minutes (directory structure)
- T002-T003, T005-T006: 3-6 hours (schemas in parallel)
- T004: 1-1.5 hours (depends on T006, integration of action types)

**Phase 2:** 3-4 hours
- T007: 1.5-2 hours (base handler)
- T008: 1.5-2 hours (registry)

**Total:** 8-12 hours across 2 phases, 2 PRs

---

## Execution Notes

### Commit Message Format

```
feat(schemas): implement ProcessInputRequest schema

- Add ProcessInputRequest Pydantic model
- Add Field() descriptions for OpenAPI
- Add comprehensive validation tests

Task: T003 | Phase: 1
```

### Build Verification

```bash
# Lint and type check
make lint

# Should output no errors from ruff or mypy
```

### Test Verification

```bash
# Run all tests
make test

# Run specific test file
pytest tests/schemas/test_requests.py -v

# Check coverage
pytest --cov=life_organizer --cov-report=term-missing
```

### Parallel Execution Strategy

**Phase 1 Parallelization:**
After completing T001 (directory structure):
1. **First wave (parallel):** T002, T003, T005, T006 can run in parallel
   - T002 (enums.py)
   - T003 (requests.py)
   - T005 (classification.py)
   - T006 (actions.py - now includes concrete action models)

2. **Second wave:** T004 (responses.py) must wait for T002 and T006 to complete
   - T004 imports ActionType from T002
   - T004 imports AppAction from T006

Suggested approach: Complete T001, parallelize T002/T003/T005/T006, then finish with T004.

**Phase 2 Sequential:**
T007 and T008 must be sequential (registry needs base handler).

---

## Next Steps

1. Review this task breakdown
2. Begin Phase 1 with TASK-001 (directory structure)
3. After T001, parallelize T002, T003, T005, T006 (first wave)
4. Complete T004 after T002 and T006 finish (second wave)
5. Complete Phase 1, create PR to staging
6. Begin Phase 2 with T007-T008
7. Complete Phase 2, create final PR to staging

**Ready to begin execution?**
