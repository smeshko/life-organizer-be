---
stepsCompleted: [1, 2, 3, 4]
status: complete
inputDocuments:
  - '_bmad-output/prd.md'
  - '_bmad-output/architecture.md'
project_name: 'life-organizer-be'
user_name: 'Ivo'
date: '2026-02-10'
---

# life-organizer-be - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for life-organizer-be, decomposing the requirements from the PRD and Architecture into implementable stories.

**Project Context:** Brownfield — Budget flow complete, core infrastructure exists. This epic breakdown covers only remaining work.

## Requirements Inventory

### Functional Requirements

**Input Processing (Implemented):**
- FR1: System can receive pre-classified text input with category designation ✅
- FR2: System can validate that the category is one of the supported types ✅
- FR3: System can route input to the appropriate category handler based on classification ✅

**Budget Management (Implemented):**
- FR4: System can parse expense text to extract amount, currency, and merchant ✅
- FR5: System can infer expense category from merchant name or keywords ✅
- FR6: System can handle multi-currency inputs (EUR, USD, BGN, etc.) ✅
- FR7: System can store expense records with all extracted metadata ✅
- FR8: System can handle date parsing from natural language ✅

**Quote Management (To Build):**
- FR9: System can parse quote text to extract source (book title) and page number
- FR10: System can store quote records with text, source, page, and date
- FR11: System can handle quotes without explicit page numbers (optional field)

**Note Management (To Build):**
- FR12: System can store freeform note text with timestamp
- FR13: System can handle notes with minimal parsing (no metadata extraction required)

**Classification Feedback (To Build):**
- FR14: System can log misclassification events (wrong category, correct category, input text)
- FR15: System can store feedback data for training data updates

**System Response (Implemented):**
- FR16: System can return success/failure response to iOS client ✅
- FR17: System can return structured error messages for failed operations ✅

### NonFunctional Requirements

All NFRs are satisfied by existing infrastructure:

- NFR1: End-to-end response time < 1 second ✅
- NFR2: Handler processing time < 500ms ✅
- NFR3: Database write time < 100ms ✅
- NFR4: No data loss - zero tolerance ✅
- NFR5: Graceful error handling - 100% ✅
- NFR6: Database integrity - always consistent ✅
- NFR7: Handler pattern consistency - all handlers follow same pattern ✅
- NFR8: Clear logging - all operations logged ✅

### Additional Requirements

**Codebase Cleanup (Required before new features):**
- Delete Reminder handler (`handlers/reminder_handler.py`)
- Delete Reminder prompt (`prompts/reminder_system_prompt_v1.txt`)
- Delete `CreateReminderAction` from `schemas/actions.py`
- Remove Reminder from handler registry (`handlers/__init__.py`)
- Remove REMINDER from Category enum (`schemas/enums.py`)
- Delete Shopping prompt (`prompts/shopping_system_prompt_v1.txt`)
- Delete `AddToShoppingListAction` from `schemas/actions.py`
- Remove SHOPPING from Category enum
- Delete Calendar prompt (`prompts/calendar_system_prompt_v1.txt`)
- Delete `CreateCalendarEventAction` from `schemas/actions.py`
- Remove CALENDAR from Category enum
- Remove all classifier references for Reminder/Shopping/Calendar (`services/claude_classifier.py`)

**Technical Implementation Patterns (From Architecture):**
- Handler plugin architecture with BaseHandler interface
- SQLAlchemy async session for all database access
- Tenacity retry for Claude API calls (max 3 retries, exponential backoff)
- Pre-commit hooks and quality gates (make lint, make type-check, make test)
- Conventional commit format required

**Project Context:**
- Brownfield project — Budget flow complete, infrastructure exists
- Quote and Note handlers follow existing BudgetEntryHandler pattern
- All new handlers must be registered in handler registry

### FR Coverage Map

| FR | Epic | Description |
|----|------|-------------|
| — | Epic 1 | Codebase cleanup (Reminder, Shopping, Calendar removal) |
| FR14 | Epic 2 | Log misclassification events |
| FR15 | Epic 2 | Store feedback for training updates |
| FR9 | Epic 3 | Parse quote text for source/page metadata |
| FR10 | Epic 3 | Store quote records with metadata |
| FR11 | Epic 3 | Handle quotes without page numbers |
| FR12 | Epic 4 | Store freeform note text with timestamp |
| FR13 | Epic 4 | Handle notes with minimal parsing |

## Epic List

### Epic 1: Remove Deprecated Categories

Clean slate — remove all dead code for unsupported categories so the codebase only contains what's actually used.

**User Outcome:** System only handles supported categories (Budget, Quote, Note)
**Covers:** Codebase cleanup requirements

---

### Epic 2: Classification Feedback Loop

Users can correct misclassifications, feeding improvements back into the system.

**User Outcome:** When iOS classifies wrong, user can correct it and the system learns
**FRs Covered:** FR14, FR15

---

### Epic 3: Quote Capture

Users can capture book quotes with source metadata, building a personal library of insights.

**User Outcome:** "quote from Atomic Habits page 47: ..." is parsed and stored
**FRs Covered:** FR9, FR10, FR11

---

### Epic 4: Note Capture

Users can capture freeform thoughts with zero friction.

**User Outcome:** "note: what if I automated my morning routine..." is stored instantly
**FRs Covered:** FR12, FR13

---

## Epic 1: Remove Deprecated Categories

Clean slate — remove all dead code for unsupported categories so the codebase only contains what's actually used.

### Story 1.1: Remove Reminder Category

**As a** developer,
**I want** the Reminder handler and all its references removed from the codebase,
**So that** the system only contains code for supported categories.

**Acceptance Criteria:**

**Given** the file `handlers/reminder_handler.py` exists
**When** the cleanup is complete
**Then** the file is deleted from the codebase

**Given** the file `prompts/reminder_system_prompt_v1.txt` exists
**When** the cleanup is complete
**Then** the file is deleted from the codebase

**Given** `CreateReminderAction` class exists in `schemas/actions.py`
**When** the cleanup is complete
**Then** the class and its imports are removed

**Given** `REMINDER` exists in the `Category` enum in `schemas/enums.py`
**When** the cleanup is complete
**Then** the enum value is removed

**Given** `ReminderHandler` is registered in `handlers/__init__.py`
**When** the cleanup is complete
**Then** the import and registration are removed

**Given** `claude_classifier.py` contains REMINDER references
**When** the cleanup is complete
**Then** all REMINDER handling code is removed from the classifier

**Given** all Reminder code is removed
**When** `make lint` and `make type-check` are run
**Then** no errors related to missing imports or references occur

---

### Story 1.2: Remove Shopping and Calendar Categories

**As a** developer,
**I want** Shopping and Calendar stub code removed from the codebase,
**So that** only active categories remain in the system.

**Acceptance Criteria:**

**Given** the file `prompts/shopping_system_prompt_v1.txt` exists
**When** the cleanup is complete
**Then** the file is deleted

**Given** the file `prompts/calendar_system_prompt_v1.txt` exists
**When** the cleanup is complete
**Then** the file is deleted

**Given** `AddToShoppingListAction` class exists in `schemas/actions.py`
**When** the cleanup is complete
**Then** the class and its imports are removed

**Given** `CreateCalendarEventAction` class exists in `schemas/actions.py`
**When** the cleanup is complete
**Then** the class and its imports are removed

**Given** `SHOPPING` and `CALENDAR` exist in the `Category` enum
**When** the cleanup is complete
**Then** both enum values are removed

**Given** `claude_classifier.py` contains SHOPPING/CALENDAR references
**When** the cleanup is complete
**Then** all handling code for these categories is removed

**Given** all Shopping and Calendar code is removed
**When** `make lint` and `make type-check` are run
**Then** no errors occur

---

### Story 1.3: Update Tests and Verify Cleanup

**As a** developer,
**I want** all tests updated to reflect the removed categories,
**So that** the test suite passes and validates the cleanup.

**Acceptance Criteria:**

**Given** tests exist that reference Reminder, Shopping, or Calendar
**When** the cleanup is complete
**Then** those test cases are removed or updated

**Given** the `Category` enum is used in test fixtures
**When** the cleanup is complete
**Then** fixtures only reference valid categories (BUDGET, QUOTE, NOTE, UNKNOWN)

**Given** all cleanup stories are complete
**When** `make test` is run
**Then** all tests pass

**Given** all cleanup stories are complete
**When** `make lint && make type-check && make test` is run
**Then** all quality gates pass

**Given** the API is running
**When** a request with `category: "REMINDER"` is sent
**Then** the system returns an appropriate error (invalid category)

---

## Epic 2: Classification Feedback Loop

Users can correct misclassifications, feeding improvements back into the system.

### Story 2.1: Create Feedback Database Model and Migration

**As a** developer,
**I want** a database table to store misclassification feedback,
**So that** correction data can be persisted for training improvements.

**Acceptance Criteria:**

**Given** the database is running
**When** the migration is applied
**Then** a new `feedback.misclassifications` table exists with columns:
- `id` (INTEGER, PK, auto-increment)
- `original_input` (TEXT, NOT NULL) — the user's original input text
- `wrong_category` (VARCHAR(50), NOT NULL) — the category iOS classified it as
- `correct_category` (VARCHAR(50), NOT NULL) — the correct category per user
- `created_at` (TIMESTAMP WITH TZ, auto-generated)

**Given** the `MisclassificationFeedback` ORM model is defined in `db/models/feedback.py`
**When** I import it from `db.models`
**Then** I can create and query feedback records

**Given** the model is created
**When** `make lint && make type-check` are run
**Then** no errors occur

---

### Story 2.2: Create Feedback API Endpoint

**As a** user,
**I want** to submit a correction when iOS misclassifies my input,
**So that** the system can learn from mistakes.

**Acceptance Criteria:**

**Given** a valid feedback payload:
```json
{
  "original_input": "buy milk",
  "wrong_category": "NOTE",
  "correct_category": "SHOPPING"
}
```
**When** I POST to `/api/v1/feedback`
**Then** the feedback is stored in the database
**And** I receive a 201 response with `{"success": true, "message": "Feedback recorded"}`

**Given** an invalid payload with missing fields
**When** I POST to `/api/v1/feedback`
**Then** I receive a 422 validation error with clear field errors

**Given** a payload with invalid category values
**When** I POST to `/api/v1/feedback`
**Then** I receive a 422 error indicating invalid category

**Given** the feedback endpoint exists
**When** `make test` is run
**Then** endpoint tests pass for success and error cases

---

### Story 2.3: Feedback Export for Training Data

**As a** developer,
**I want** to export misclassification feedback as training data,
**So that** I can improve the iOS classification model.

**Acceptance Criteria:**

**Given** feedback records exist in the database
**When** I call `GET /api/v1/feedback/export`
**Then** I receive a JSON array of all feedback records

**Given** I want to filter by date range
**When** I call `GET /api/v1/feedback/export?start_date=2026-01-01&end_date=2026-02-01`
**Then** only records within that range are returned

**Given** I want CSV format for training pipelines
**When** I call `GET /api/v1/feedback/export?format=csv`
**Then** I receive CSV with headers: `original_input,wrong_category,correct_category,created_at`

**Given** no feedback exists
**When** I call the export endpoint
**Then** I receive an empty array (JSON) or header-only (CSV)

---

## Epic 3: Quote Capture

Users can capture book quotes with source metadata, building a personal library of insights.

### Story 3.1: Create Quote Database Model and Migration

**As a** developer,
**I want** a database table to store quotes with metadata,
**So that** quotes can be persisted and retrieved.

**Acceptance Criteria:**

**Given** the database is running
**When** the migration is applied
**Then** a new `quote.quotes` table exists with columns:
- `id` (INTEGER, PK, auto-increment)
- `text` (TEXT, NOT NULL) — the quote content
- `source` (VARCHAR(255), NULLABLE) — book/article title
- `author` (VARCHAR(255), NULLABLE) — author name
- `page` (INTEGER, NULLABLE) — page number
- `created_at` (TIMESTAMP WITH TZ, auto-generated)

**Given** the `Quote` ORM model is defined in `db/models/quote.py`
**When** I import it from `db.models`
**Then** I can create and query quote records

**Given** the model is created
**When** `make lint && make type-check` are run
**Then** no errors occur

---

### Story 3.2: Create Quote System Prompt

**As a** developer,
**I want** a Claude prompt that extracts quote metadata from user input,
**So that** quotes are parsed correctly with source information.

**Acceptance Criteria:**

**Given** user input: `"quote from Atomic Habits page 47: The goal is not to read a book"`
**When** the prompt processes this input
**Then** extracted data includes:
- `text`: "The goal is not to read a book"
- `source`: "Atomic Habits"
- `page`: 47

**Given** user input: `"quote: stay hungry stay foolish - Steve Jobs"`
**When** the prompt processes this input
**Then** extracted data includes:
- `text`: "stay hungry stay foolish"
- `author`: "Steve Jobs"
- `source`: null
- `page`: null

**Given** user input: `"quote: simplicity is the ultimate sophistication"`
**When** the prompt processes this input (no source/author)
**Then** extracted data includes:
- `text`: "simplicity is the ultimate sophistication"
- `source`: null
- `author`: null
- `page`: null

**Given** the prompt file `prompts/quote_system_prompt_v1.txt` exists
**When** it replaces the current stub
**Then** the file contains complete extraction instructions (not just "return unknown")

---

### Story 3.3: Create Quote Handler

**As a** user,
**I want** my quote inputs to be parsed and stored in the database,
**So that** I can build a personal library of insights.

**Acceptance Criteria:**

**Given** a classified input with `category = QUOTE` and text `"quote from Atomic Habits page 47: The goal is..."`
**When** the QuoteHandler processes it
**Then** a new record is created in `quote.quotes` with extracted metadata
**And** the response has `action_type = backend_handled`
**And** the response message confirms: "Quote saved from Atomic Habits"

**Given** a quote without source metadata
**When** the QuoteHandler processes it
**Then** the quote is stored with null source/author/page fields
**And** the response confirms: "Quote saved"

**Given** the QuoteHandler is implemented
**When** it is registered in `handlers/__init__.py`
**Then** the handler registry routes QUOTE inputs to QuoteHandler

**Given** the QuoteHandler is complete
**When** `make test` is run
**Then** all quote handler tests pass

**Given** the full quote flow is complete
**When** I send `POST /api/v1/process` with `{"input": "quote from Deep Work: focus is a superpower", "category": "QUOTE"}`
**Then** the quote is stored and I receive a success response

---

## Epic 4: Note Capture

Users can capture freeform thoughts with zero friction.

### Story 4.1: Create Note Database Model and Migration

**As a** developer,
**I want** a database table to store freeform notes,
**So that** notes can be persisted and retrieved.

**Acceptance Criteria:**

**Given** the database is running
**When** the migration is applied
**Then** a new `note.notes` table exists with columns:
- `id` (INTEGER, PK, auto-increment)
- `content` (TEXT, NOT NULL) — the note content
- `created_at` (TIMESTAMP WITH TZ, auto-generated)

**Given** the `Note` ORM model is defined in `db/models/note.py`
**When** I import it from `db.models`
**Then** I can create and query note records

**Given** the model is created
**When** `make lint && make type-check` are run
**Then** no errors occur

---

### Story 4.2: Create Note System Prompt

**As a** developer,
**I want** a Claude prompt that extracts note content from user input,
**So that** notes are captured with minimal processing.

**Acceptance Criteria:**

**Given** user input: `"note: what if I automated my morning routine with shortcuts"`
**When** the prompt processes this input
**Then** extracted data includes:
- `content`: "what if I automated my morning routine with shortcuts"

**Given** user input: `"idea for the app: add dark mode support"`
**When** the prompt processes this input
**Then** extracted data includes:
- `content`: "idea for the app: add dark mode support"

**Given** user input: `"remember to check that restaurant review later"`
**When** the prompt processes this input
**Then** extracted data includes:
- `content`: "remember to check that restaurant review later"

**Given** the prompt file `prompts/note_system_prompt_v1.txt` exists
**When** it replaces the current stub
**Then** the file contains complete extraction instructions

---

### Story 4.3: Create Note Handler

**As a** user,
**I want** my note inputs to be stored instantly with zero friction,
**So that** I never lose a random thought.

**Acceptance Criteria:**

**Given** a classified input with `category = NOTE` and text `"note: automate morning routine"`
**When** the NoteHandler processes it
**Then** a new record is created in `note.notes`
**And** the response has `action_type = backend_handled`
**And** the response message confirms: "Note saved"

**Given** any freeform text classified as NOTE
**When** the NoteHandler processes it
**Then** the full content is stored without modification

**Given** the NoteHandler is implemented
**When** it is registered in `handlers/__init__.py`
**Then** the handler registry routes NOTE inputs to NoteHandler

**Given** the NoteHandler is complete
**When** `make test` is run
**Then** all note handler tests pass

**Given** the full note flow is complete
**When** I send `POST /api/v1/process` with `{"input": "note: brilliant idea for later", "category": "NOTE"}`
**Then** the note is stored and I receive a success response
