---
type: feature
status: draft
priority: P1
created: 2025-10-31
slug: project-scaffold-models
feature_branch: feature/project-scaffold-models
---

# Project Structure Scaffolding and Data Models

## Overview

**Context**: The backend currently has a minimal FastAPI setup with basic configuration, logging, and health endpoints. The high-level architecture document defines a layered architecture with API Gateway, Classification Engine, Action Handlers, and Persistence layers, but none of these structural components exist in the codebase.

**Objective**: Scaffold the complete project directory structure and create foundational data models (schemas) that enable the plugin-based handler architecture described in the architecture document. This establishes the organizational foundation for implementing the classification system and individual handlers.

**Impact**: All future development depends on this structure. This affects:
- Backend developers implementing handlers and classification logic
- iOS app integration (request/response contract implementation)
- External integrations (Google Sheets, future services)
- Testing and maintainability of the codebase

## User Stories

### Primary Stories (P1)

**US-1**: As a backend developer, I want a clear directory structure that separates concerns (models, handlers, services, API routes) so that I can implement features without confusion about where code belongs.

**Acceptance Scenario**:
- **Given** a feature request for a new handler type
- **When** I need to create the handler implementation
- **Then** I have clear directories for schemas, handlers, and services with examples to follow

**US-2**: As an iOS app developer, I want well-defined request and response data models so that I can reliably communicate with the backend without ambiguity.

**Acceptance Scenario**:
- **Given** I need to send user input to the backend
- **When** I construct the API request
- **Then** I have a documented schema showing required fields, types, and validation rules

## Requirements

1. **REQ-001**: System must provide a directory structure that mirrors the layered architecture defined in the high-level design document
   - Rationale: Enforces separation of concerns and makes the codebase self-documenting

2. **REQ-002**: System must define Pydantic models for the core request/response contract
   - Rationale: Ensures type safety, validation, and API documentation via OpenAPI/Swagger

3. **REQ-003**: System must provide base classes/protocols for the handler architecture
   - Rationale: Establishes the contract that all handlers must follow for consistent behavior

4. **REQ-004**: System must define data models for different action result types (backend_handled, app_action_required, confirmation_needed)
   - Rationale: Handlers need structured ways to return results that the API layer can serialize

5. **REQ-005**: System must define models for classification results with confidence scoring
   - Rationale: Classification engine needs to communicate intent, extracted data, and confidence levels

6. **REQ-006**: System must define models for user context (location, user_id, previous actions)
   - Rationale: Classification and handlers may need contextual information to make decisions

7. **REQ-007**: System must define models for app actions (create_reminder, add_to_shopping_list, create_calendar_event)
   - Rationale: Backend needs to communicate iOS-side actions in a structured format

## Acceptance Criteria

### Functional Acceptance

- [ ] **Given** the codebase, **When** I navigate the directory structure, **Then** I see organized directories for: models/schemas, handlers, services, api/routes, db

- [ ] **Given** a request from the iOS app, **When** FastAPI receives it, **Then** Pydantic automatically validates it against the ProcessInputRequest schema

- [ ] **Given** a handler needs to return a result, **When** it uses the ActionResult model, **Then** the response includes all required fields (success, action_type, message) and optional fields based on action_type

- [ ] **Given** the classification engine produces a result, **When** it returns a ClassifiedInput object, **Then** it includes category, confidence score, and extracted data

- [ ] **Given** a developer needs to create a new handler, **When** they reference the base handler class, **Then** they see clear abstract methods they must implement (can_handle, requires_app_action, execute)

### Edge Cases

- [ ] Handles invalid request data by returning Pydantic validation errors in FastAPI standard format

- [ ] Handles missing optional fields in requests (context, previous_action) with sensible defaults

## Affected Areas

**Components**:
- API Layer - Requires request/response models
- Classification Engine - Requires classification models and protocols
- Handler System - Requires base handler classes and action result models
- Persistence Layer - May require database models (future)

**Files**:
- `src/life_organizer/models/` - New directory for all data models
- `src/life_organizer/schemas/` - New directory for API schemas (request/response)
- `src/life_organizer/handlers/` - New directory with base handler class
- `src/life_organizer/services/` - New directory for business logic services
- `src/life_organizer/db/` - New directory for database setup (placeholder)
- `src/life_organizer/api/routes/` - New directory for API route modules
- `src/life_organizer/main.py` - May need updates to register routes

**Related Systems**:
- FastAPI OpenAPI documentation - Will auto-generate from Pydantic models
- iOS app - Will implement matching request/response structures
- Google Sheets API - Handlers will interact with this (not in scope for this task)

## Assumptions

- Pydantic V2 is being used (already in dependencies)
- The request/response contract from the architecture document is the source of truth
- SQLite will be used for Stage 1 persistence (database setup is placeholder only)
- Handler implementations are out of scope - only base classes and structure needed
- Classification engine implementation is out of scope - only models needed

## Open Questions

- [ ] Should we use separate `models/` and `schemas/` directories or combine into one? (Recommendation: Keep separate - models are domain objects, schemas are API contracts)

- [ ] Do we need database models (SQLAlchemy/SQLModel) now or later? (Recommendation: Defer to separate task)

---

**Next Steps**: Review this document, clarify open questions, then proceed to implementation planning.
