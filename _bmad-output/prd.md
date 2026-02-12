---
stepsCompleted: [1, 2, 3, 4, 7, 8, 9, 10, 11]
inputDocuments:
  - '_bmad-output/index.md'
documentCounts:
  briefs: 0
  research: 0
  brainstorming: 0
  projectDocs: 1
workflowType: 'prd'
lastStep: 11
project_name: 'life-organizer-be'
user_name: 'Ivo'
date: '2026-01-31'
skippedSteps: [5, 6]
---

# Product Requirements Document - life-organizer-be

**Author:** Ivo
**Date:** 2026-01-31

## Executive Summary

### Vision

A personal intelligent agent that captures everyday life events via natural language and automatically routes them to the appropriate organizational system — with minimal friction and maximum reliability.

### What Makes This Special

**Instant, deterministic routing through two-stage classification:**

1. iOS local model performs category classification on-device
2. Backend receives pre-classified input and routes to targeted handler with category-specific prompt
3. No ambiguity, no confidence thresholds, no fallback UI in the happy path

**The killer UX:** Rapid-fire multi-transaction logging. Think it, type it, done. Repeat.

**Self-improving system:** Misclassifications are logged with correct categories and fed back into training data.

### Project Classification

| Attribute | Value |
|-----------|-------|
| **Technical Type** | API Backend + iOS Mobile App |
| **Domain** | Personal Productivity |
| **Complexity** | Low-Medium |
| **Project Context** | Brownfield — 1 of 3 classification flows complete |
| **Distribution** | Personal use only (no App Store) |

### Current Scope

**3 Active Classification Categories:**
- ✅ Budget (complete)
- 🔲 Quote (to build)
- 🔲 Note (to build)

**Removed from Codebase:**
- ~~Reminder~~ — Native app wins; removing completely
- ~~Calendar~~ — Native Calendar + shared with wife works
- ~~Shopping~~ — Shared Apple Note with wife works

## Success Criteria

### User Success

**Primary Metric:** Categories actively used in daily life (not just "technically working")

| Category | Status | Success Test |
|----------|--------|--------------|
| Budget | ✅ Active | Proven — rapid-fire logging beats laptop spreadsheet |
| Quote | 🔲 To build | Greenfield — no existing system to compete with |
| Note | 🔲 To build | Greenfield — no existing system to compete with |

**The real bar:** Total friction < Alternative friction

**Winning conditions identified:**
1. **Laptop → Phone:** Life Organizer wins (Budget)
2. **Phone → Phone:** Life Organizer loses (removed categories)
3. **Nothing → Phone:** Life Organizer wins (Quote, Note)

### Business Success

| Metric | Target |
|--------|--------|
| **Daily utility** | Used daily, not abandoned |
| **Net time saved** | Faster than manual alternatives |
| **Platform value** | Foundation for future automations |

### Technical Success

| Metric | Target |
|--------|--------|
| **Response time** | < 1 second end-to-end |
| **Classification accuracy** | Correct routing (with feedback loop for corrections) |
| **Reliability** | No silent failures, no lost data |

### Measurable Outcomes

- Budget transactions logged per week (baseline: current usage)
- Categories with active daily/weekly use: target 3 of 3
- Misclassification rate trending down over time

## Product Scope

### MVP — Already Achieved
- ✅ Budget flow (complete)
- ✅ Two-stage classification architecture
- ✅ iOS app (working WIP)
- ✅ Training data feedback loop

### Growth — Current Focus
- 🔲 Quote flow (greenfield opportunity)
- 🔲 Note flow (greenfield opportunity)
- 🗑️ Codebase cleanup (remove Reminder, Calendar, Shopping)
- Validate each category provides value before considering it "done"

### Removed from Scope & Codebase
- ~~Reminder~~ — Remove handler, model, prompts
- ~~Calendar~~ — Remove placeholders/comments
- ~~Shopping~~ — Remove placeholders/comments

### Vision — Future
- Additional automation categories (to be defined)
- "Never done" — living tool that evolves with needs

## User Journeys

### Journey 1: Batch Expense Reconciliation

Ivo realizes he hasn't logged expenses in a few days. He opens his banking apps, reviews the transactions, then fires them into Life Organizer one by one: "coffee 4.50", "lunch monday 12", "amazon 34.99". Each one takes 2-3 seconds. In under a minute, he's logged a week's worth of expenses that would have taken 10 minutes with the laptop spreadsheet. He closes the app and moves on with his day.

**Requirements revealed:** Batch input UX, transaction parsing, expense categorization, multi-currency support

---

### Journey 2: Capturing a Book Quote

Ivo is reading Atomic Habits and hits a powerful insight. He opens Life Organizer, takes a photo of the paragraph, and types: "quote from Atomic Habits page 47". The iOS app extracts the text from the photo (OCR) and sends the combined text to the backend. The system stores the quote with source metadata (book, page). Over time, Ivo builds a personal library of insights from everything he reads — something he always wanted but never had a system for.

**Requirements revealed:** Quote parsing (extract book title, page), quote storage with metadata, quote browsing/retrieval

**Note:** Photo handling and OCR are iOS-side responsibilities. Backend receives text only.

---

### Journey 3: Capturing a Random Thought

A thought strikes Ivo while walking — an idea, an observation, something worth remembering. He opens Life Organizer and types: "note: what if I automated my morning routine with shortcuts". It's captured instantly. He doesn't need to decide where it goes or what app to use. It just exists now, retrievable later.

**Requirements revealed:** Freeform note capture, minimal friction input, note storage, note retrieval/search

---

### Journey Requirements Summary

| Capability | Budget | Quote | Note |
|------------|--------|-------|------|
| Text parsing | ✅ | ✅ | ✅ |
| Photo input | — | iOS only | — |
| Metadata extraction | Category, amount, date | Book, page | — |
| Storage | SQLite | SQLite | SQLite |
| Retrieval/Browse | iOS | iOS | iOS |

## API Backend Requirements

### Architecture Overview

| Aspect | Implementation |
|--------|----------------|
| **Endpoint** | Single unified endpoint |
| **Authentication** | None (personal use, trusted client) |
| **Input** | Text only (iOS handles OCR/photo processing) |
| **Storage** | SQLite |
| **Retrieval API** | None (iOS handles browsing locally) |

### Endpoint Architecture

**Single Unified Endpoint:**
- Receives pre-classified text from iOS
- Routes to category-specific handler based on classification
- Returns success/failure response

**Request Pattern:**
```
POST /classify
{
  "category": "quote",
  "text": "quote from Atomic Habits page 47: The goal is not to read a book..."
}
```

### Data Storage

**SQLite Tables:**

| Category | Table | Key Fields |
|----------|-------|------------|
| Budget | expenses | amount, currency, category, merchant, date |
| Quote | quotes (new) | text, source (book), page, date |
| Note | notes (new) | text, date |

### Handler Requirements

**Quote Handler:**
- Parse source metadata (book title, page number) from text using targeted prompt
- Store quote text and extracted metadata
- No image handling (iOS extracts text before sending)

**Note Handler:**
- Store freeform text with timestamp
- Minimal parsing needed
- Simplest handler of all

### Technical Constraints

| Constraint | Value |
|------------|-------|
| Authentication | None required |
| Rate limiting | None (personal use) |
| API versioning | None needed |
| Retrieval endpoints | None (iOS handles) |
| Image handling | None (iOS responsibility) |

## Project Scoping & Phased Development

### MVP Strategy

**Approach:** Problem-Solving MVP — validate each category solves a real friction problem before building it.

**Philosophy:** "Prove it works for me before adding more."

### Development Phases

**Phase 1: MVP — Complete ✅**
- Budget flow (proven daily utility)
- Two-stage classification architecture
- iOS app + Backend foundation

**Phase 2: Growth — Current Focus**
- Quote flow (greenfield — no competition)
- Note flow (greenfield — no competition)
- Codebase cleanup (remove dead code)
- Success criteria: Actually used, not just built

**Phase 3: Future — TBD**
- Additional categories based on emerging needs
- "Never done" — evolves with life

### Risk Assessment

| Risk | Mitigation |
|------|------------|
| **Building unused features** | Validate friction comparison before building |
| **Scope creep** | Stick to 3 active categories until proven |
| **Technical debt** | Personal project — pragmatic over perfect |

### Out of Scope (Confirmed)

- Reminder (removing from codebase)
- Calendar (removing placeholders)
- Shopping (removing placeholders)
- Multi-user support (personal tool)
- App Store distribution (personal use)

## Functional Requirements

### Input Processing

- **FR1:** System can receive pre-classified text input with category designation
- **FR2:** System can validate that the category is one of the supported types (budget, quote, note)
- **FR3:** System can route input to the appropriate category handler based on classification

### Budget Management

- **FR4:** System can parse expense text to extract amount, currency, and merchant
- **FR5:** System can infer expense category from merchant name or keywords
- **FR6:** System can handle multi-currency inputs (EUR, USD, BGN, etc.)
- **FR7:** System can store expense records with all extracted metadata
- **FR8:** System can handle date parsing from natural language ("yesterday", "monday", etc.)

### Quote Management

- **FR9:** System can parse quote text to extract source (book title) and page number
- **FR10:** System can store quote records with text, source, page, and date
- **FR11:** System can handle quotes without explicit page numbers (optional field)

### Note Management

- **FR12:** System can store freeform note text with timestamp
- **FR13:** System can handle notes with minimal parsing (no metadata extraction required)

### Classification Feedback

- **FR14:** System can log misclassification events (wrong category, correct category, input text)
- **FR15:** System can store feedback data for training data updates

### System Response

- **FR16:** System can return success/failure response to iOS client
- **FR17:** System can return structured error messages for failed operations

## Codebase Cleanup Required

| Item | Action |
|------|--------|
| Reminder handler | Delete |
| Reminder model/schema | Delete |
| Reminder prompts | Delete |
| Reminder tests | Delete |
| Calendar placeholders | Delete |
| Shopping placeholders | Delete |
| iOS training data | Update to remove reminder/calendar/shopping categories |

## Non-Functional Requirements

### Performance

| Requirement | Target | Rationale |
|-------------|--------|-----------|
| **NFR1:** End-to-end response time | < 1 second | Must feel instant to enable rapid-fire logging |
| **NFR2:** Handler processing time | < 500ms | LLM parsing should not bottleneck UX |
| **NFR3:** Database write time | < 100ms | SQLite local writes should be near-instant |

### Reliability

| Requirement | Target | Rationale |
|-------------|--------|-----------|
| **NFR4:** No data loss | Zero tolerance | Every logged entry must persist |
| **NFR5:** Graceful error handling | 100% | Failures return clear errors, never silent |
| **NFR6:** Database integrity | Always consistent | No corrupted or partial writes |

### Maintainability

| Requirement | Target | Rationale |
|-------------|--------|-----------|
| **NFR7:** Handler pattern consistency | All handlers follow same pattern | Easy to add new categories |
| **NFR8:** Clear logging | All operations logged | Debug issues when they occur |
