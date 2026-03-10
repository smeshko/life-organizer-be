---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
skippedSteps: [5, 6]
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
date: '2026-03-09'
---

# Product Requirements Document - life-organizer-be

**Author:** Ivo
**Date:** 2026-03-09

## Executive Summary

### Vision

A personal backend API that serves two focused purposes: automated budget tracking through natural language input, and an on-demand meal planning assistant — both powered by LLM intelligence with full user control over AI behavior through system prompts.

### What Makes This Special

**Two distinct modes of LLM-powered personal assistance:**

1. **Budget Tracking (proven):** Rapid-fire natural language expense logging that beats manual spreadsheet entry. Say it, it's logged. Screenshot your Revolut transactions, they're all logged.
2. **Meal Planning (new):** On-demand dinner suggestions personalized through a user-controlled system prompt — no black-box algorithms, no app settings screens. Full ownership of the AI's knowledge: dietary restrictions, cuisine preferences, store inventory, and cooking history are all directly editable in the prompt. The success bar: at least one pick from the first set of suggestions, every time.

**The unifying principle:** LLM as a personal tool where the user has complete, transparent control over its behavior — not a product that hides its logic behind UI abstractions.

### Project Classification

| Attribute | Value |
|-----------|-------|
| **Technical Type** | API Backend |
| **Domain** | Personal Productivity |
| **Complexity** | Low-Medium |
| **Project Context** | Brownfield — pivoting from multi-category classifier to two focused features |
| **Distribution** | Personal use only |

### Current Scope

**Two focused features sharing infrastructure:**
- **Budget** — complete and proven, being simplified (remove classification routing, rename endpoint)
- **Meal Planner** — new feature, separate endpoint family, on-demand dinner suggestions

**Architectural pivot:**
- Removing: Classification orchestrator, category routing, Quote/Note placeholders
- Simplifying: `/api/v1/process` → `/api/v1/budget` (direct, no routing)
- Adding: `/api/v1/meals/*` endpoints (independent feature)

## Success Criteria

### User Success

**Budget (maintain):**
- Continues to work exactly as today — rapid-fire logging, no regressions
- Export endpoint remains functional until frontend replaces it

**Meal Planner (new):**

| Metric | Target |
|--------|--------|
| **First-try hit rate** | At least 1 of 3 suggestions is appealing on every request |
| **Suggestion relevance** | Matches dietary restrictions, cuisine preferences, and available ingredients |
| **Suggestion variety** | No repetitive suggestions across sessions |
| **Feasibility** | Only suggests meals the user can actually make (store inventory aware) |
| **Usage frequency** | Used a few times per week, sustained over months |

**The failure modes (all must be avoided):**
- None of the 3 suggestions appeal
- Suggestions become repetitive
- Suggestions include ingredients that can't be sourced

### Business Success

| Metric | Target |
|--------|--------|
| **Sustained use** | Still using the meal planner after 3 months |
| **Budget stability** | Budget feature unaffected by the pivot/refactor |
| **Low maintenance** | Preference tuning is just editing a system prompt, not code changes |

**Warning sign:** Trying suggestions a few times and nothing good comes out → tool gets abandoned.

### Technical Success

| Metric | Target |
|--------|--------|
| **Response time** | Budget: < 1 second. Meal planner: 2-3 seconds acceptable (LLM generation) |
| **Reliability** | No silent failures, no lost data (recipes, feedback, budget entries) |
| **Clean refactor** | Orchestrator/classifier removal doesn't break budget flow |
| **Endpoint clarity** | `/api/v1/budget` and `/api/v1/meals/*` — clean, focused naming |

### Measurable Outcomes

- Budget transactions logged per week: stable (no regression from refactor)
- Meal suggestions accepted on first try: target >80% of sessions
- Meal planner sessions per week: 2-3, sustained
- Unique meals suggested per month: high variety (low repetition)

## Product Scope

### MVP — Budget Simplification + Meal Planner V1

**Budget cleanup:**
- Remove classification orchestrator, category routing, Quote/Note code
- Rename `/api/v1/process` → `/api/v1/budget`
- Budget handler works directly, no routing layer
- Screenshot import: Claude Vision extracts transactions from Revolut screenshots (multi-image batch)

**Budget Frontend API:**
- `GET /api/v1/budget/transactions` — filtered, paginated transaction list (JSON)
- `GET /api/v1/budget/transactions/aggregate` — category totals for charts
- `GET /api/v1/budget/plan/{year}` — budget plan grid (categories × 12 months)
- `PUT /api/v1/budget/plan/{year}` — save/update budget plan amounts
- `GET /api/v1/budget/years` — available years for navigation
- New `budget_plans` database table for planned amounts per category/month/year

**Meal Planner V1:**
- `POST /api/v1/meals/suggest` — 3 dinner suggestions for tonight
- `POST /api/v1/meals/feedback` — rate recipes (liked/disliked + notes)
- Hybrid recipe source: seeded in DB + LLM-generated
- Hardcoded preferences and store inventory in system prompt
- Recent meal history to avoid repetition
- Recipes and inventory managed directly in code/prompt, not via API

### Growth Features (Post-MVP)

- Meal planner preference learning from feedback patterns
- Recipe deduplication (LLM suggests something similar to existing)

### Vision (Future)

- Weekly meal planning
- Shopping list integration
- Macro/nutrition tracking

## User Journeys

### Journey 1: Batch Expense Reconciliation

Ivo realizes he hasn't logged expenses in a few days. He opens his banking app, reviews recent transactions, then switches to Life Organizer. He fires them in one by one: "coffee 4.50", "lunch monday 12", "amazon 34.99 usd". Each entry takes 2-3 seconds — the app sends it straight to `/api/v1/budget`, Claude parses it, and it's in the database. In under a minute, a week's worth of expenses are logged. No spreadsheet, no laptop needed.

**Requirements revealed:** Natural language parsing, multi-currency support, date inference, expense categorization, rapid sequential input

---

### Journey 2: What's For Dinner Tonight

It's 5pm and Ivo has no idea what to cook. He opens Life Organizer, taps the Meals tab, and hits "Suggest." Three dinner options appear — a Greek lemon chicken he's never tried, a pasta dish he liked last month, and a quick stir-fry. The Greek chicken catches his eye. He taps it, sees the ingredients and instructions, and heads to the kitchen. After dinner, he taps "liked" with a note: "great, would add more garlic next time."

**Requirements revealed:** On-demand suggestion generation, recipe display (ingredients + instructions), feedback capture, meal history tracking, mix of familiar and new suggestions

---

### Journey 3: Nothing Appeals

Ivo asks for suggestions but the three options don't land — one is too complex for a weeknight, one uses ingredients he doesn't have, and one he just made last week. He taps "Suggest" again. The second set is better — a simple shakshuka hits the spot. He picks it and moves on.

**Requirements revealed:** Regeneration capability, recent meal history awareness (avoid repetition), store inventory awareness, complexity consideration

---

### Journey 4: Cooking With Constraints

Ivo has chicken thighs defrosting and wants to use them tonight. He types "I have chicken thighs" as a requirement and hits suggest. All three suggestions incorporate chicken thighs — a teriyaki bowl, a Mediterranean bake, and a simple pan-sear with roasted vegetables. The suggestions respect his preferences while working within the constraint.

**Requirements revealed:** Optional requirements/constraints in suggestion request, constraint-aware LLM prompting, flexible input alongside the suggest action

---

### Journey 5: Screenshot Bulk Import

Ivo hasn't logged expenses in two weeks. Instead of typing them one by one, he opens Revolut, scrolls through recent transactions, and takes 3 screenshots covering the period. He switches to Life Organizer, selects the screenshots, and sends them. Claude Vision reads each screenshot, extracts every transaction — amounts, dates, merchants — and parses them just like typed input. 25 transactions logged in under 30 seconds. The Revolut-specific format means high accuracy with no manual cleanup.

**Requirements revealed:** Image input support (Claude Vision), multi-image batch processing, Revolut-specific transaction extraction, multi-transaction parsing from visual input, same categorization pipeline as text input

---

### Journey Requirements Summary

| Capability | Budget | Meal Planner |
|------------|--------|--------------|
| Natural language parsing | ✅ | — |
| Image input (Claude Vision) | ✅ | — |
| Multi-image batch processing | ✅ | — |
| LLM suggestion generation | — | ✅ |
| Optional text input | — | ✅ (requirements) |
| Recipe display | — | ✅ |
| Feedback capture | — | ✅ |
| Meal history tracking | — | ✅ |
| Store inventory awareness | — | ✅ (via prompt) |
| Multi-currency support | ✅ | — |
| Date inference | ✅ | — |
| Expense categorization | ✅ | — |

## API Backend Requirements

### Endpoint Specification

| Method | Endpoint | Purpose | Input |
|--------|----------|---------|-------|
| POST | `/api/v1/budget` | Log budget entries from text | JSON `{ "input": "..." }` |
| POST | `/api/v1/budget` | Log budget entries from screenshots | Multipart form-data (images) |
| GET | `/api/v1/budget/export` | Export transactions as TSV | Query params |
| GET | `/api/v1/budget/transactions` | Fetch transactions (filtered, paginated, JSON) | Query params (date range, type, category, page) |
| GET | `/api/v1/budget/transactions/aggregate` | Category totals for a period | Query params (year, month?, type) |
| GET | `/api/v1/budget/plan/{year}` | Fetch budget plan grid | Path param: year |
| PUT | `/api/v1/budget/plan/{year}` | Save/update budget plan | JSON (categories × months grid) |
| GET | `/api/v1/budget/years` | List available years | — |
| POST | `/api/v1/meals/suggest` | Get 3 dinner suggestions | JSON `{ "requirements?": "..." }` |
| POST | `/api/v1/meals/feedback` | Rate a recipe | JSON `{ "recipe_id", "liked", "notes?" }` |
| GET | `/api/v1/health` | Health check | — |
| GET | `/api/v1/status` | API status | — |
| POST | `/api/v1/feedback/` | Report misclassification | JSON |

### Authentication Model

- **None** — personal use only, trusted client
- API is exposed but not publicly advertised
- Rate limiting serves as the primary abuse protection

### Data Formats

- **Request/Response:** JSON (application/json)
- **Budget image input:** Multipart form-data (one or more images)
- **Budget export:** TSV (text/tab-separated-values)

### Rate Limiting

| Scope | Limit | Rationale |
|-------|-------|-----------|
| **LLM endpoints** (budget, meals/suggest) | 5-10 req/min | Cost protection — every request hits Claude |
| **Non-LLM endpoints** (export, health, status, feedback) | No limit | No cost concern, low risk |

### Error Handling

| Scenario | Response |
|----------|----------|
| Invalid input | 400 with descriptive error message |
| LLM parsing failure | 500 with error details, no silent failures |
| Rate limit exceeded | 429 with retry-after header |
| Image processing failure | 400 with details on which image(s) failed |

### Technical Constraints

| Constraint | Value |
|------------|-------|
| Authentication | None |
| API versioning | `/api/v1/` prefix (existing) |
| SDK | Not needed |
| Image size limits | TBD during implementation |

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP Approach:** Problem-Solving MVP — ship both features together as a cohesive personal tool update.

**Resource Requirements:** Solo developer, iterative delivery.

**Key Decision:** Budget cleanup, screenshot import, and meal planner all ship in one release. The budget refactor is a prerequisite (remove orchestrator before adding new features), but everything lands together.

### MVP Feature Set (Phase 1)

**Core User Journeys Supported:** All 5 journeys

**Must-Have Capabilities:**

| Feature | Capability | Journey |
|---------|-----------|---------|
| Budget refactor | Remove orchestrator, rename endpoint to `/api/v1/budget` | All budget |
| Budget text input | Natural language parsing (existing, simplified) | Journey 1 |
| Budget screenshot import | Claude Vision extraction from Revolut screenshots, multi-image | Journey 5 |
| Budget export | TSV export (existing) | — |
| Meal suggest | 3 dinner suggestions with optional requirements | Journeys 2, 3, 4 |
| Meal feedback | Like/dislike + notes on recipes | Journey 2 |
| Meal history | Track what was cooked to avoid repetition | Journeys 2, 3 |
| Rate limiting | 5-10 req/min on LLM endpoints | — |
| Codebase cleanup | Remove Quote/Note/orchestrator dead code | — |

### Meal Planner Soft Launch Strategy

The meal planner's biggest risk is suggestion quality. Approach:

1. **Build:** Get endpoint working with initial system prompt
2. **Test:** Use it personally for 1-2 weeks
3. **Iterate:** Tune system prompt based on real usage (preferences, inventory, prompt structure)
4. **Validate:** Hitting the "at least 1 of 3 appeals" bar consistently before considering it done

This is low-cost iteration — prompt changes, not code changes.

### Post-MVP Features (Phase 2)

- Budget frontend API support (filtering, pagination, aggregations)
- Meal planner preference learning from feedback patterns
- Recipe deduplication

### Vision (Phase 3)

- Weekly meal planning
- Shopping list integration
- Macro/nutrition tracking

### Risk Mitigation Strategy

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Meal suggestion quality** | Tool gets abandoned | Soft launch + prompt iteration cycle |
| **Budget refactor breaks existing flow** | Daily tool stops working | Comprehensive tests before/after refactor |
| **Screenshot extraction accuracy** | Wrong amounts logged | Revolut-specific prompt tuning, test with real screenshots |
| **LLM cost overrun** | Unexpected bills | Tight rate limiting (5-10 req/min) |
| **Scope creep** | Never ships | Two features only, everything else is post-MVP |

## Functional Requirements

### Budget Entry — Text Input

- **FR1:** User can submit natural language text to log one or more budget entries
- **FR2:** System can parse amount, currency, merchant, category, and date from natural language input
- **FR3:** System can infer expense category from merchant name or keywords
- **FR4:** System can handle multi-currency inputs (EUR, USD) with conversion to EUR. BGN supported for legacy data only.
- **FR5:** System can parse multiple transactions from a single text input
- **FR6:** System can infer dates from natural language ("yesterday", "monday")

### Budget Entry — Screenshot Import

- **FR7:** User can submit one or more images of Revolut transaction screens
- **FR8:** System can extract transaction data from Revolut screenshot images using Claude Vision
- **FR9:** System can process multiple screenshots in a single request
- **FR10:** System can route extracted screenshot data through the same categorization pipeline as text input

### Budget Management

- **FR11:** User can export budget transactions as TSV
- **FR12:** System can store budget entries with amount, currency, converted amounts, date, transaction type, category, and details

### Budget Frontend API

- **FR30:** User can fetch transactions as JSON with filters (date range, transaction type, category) and pagination
- **FR31:** User can fetch aggregated category totals for a given period (month or year) and transaction type
- **FR32:** User can fetch a budget plan for a specific year (categories × 12 months grid with planned amounts)
- **FR33:** User can create or update budget plan amounts for any category/month/year combination
- **FR34:** User can fetch a list of available years that contain transaction data
- **FR35:** System can store budget plan data (planned amount per category per month per year)

### Meal Suggestions

- **FR13:** User can request 3 dinner suggestions for tonight
- **FR14:** User can optionally provide requirements/constraints with a suggestion request (e.g., "I have chicken thighs")
- **FR15:** System can generate meal suggestions incorporating user preferences from system prompt
- **FR16:** System can generate meal suggestions aware of store inventory (defined in system prompt)
- **FR17:** System can avoid suggesting recently cooked meals by referencing meal history
- **FR18:** System can return recipe details including name, ingredients, instructions, prep time, cuisine, and tags
- **FR19:** User can request a new set of suggestions if the current ones don't appeal

### Meal Feedback & History

- **FR20:** User can submit feedback on a recipe (liked/disliked + optional notes)
- **FR21:** System can track meal history (what was cooked and when)
- **FR22:** System can store recipe feedback for future suggestion improvement

### Classification Feedback

- **FR23:** User can report a misclassification with the correct category
- **FR24:** System can store misclassification data for training improvement

### API Protection

- **FR25:** System can rate-limit LLM-hitting endpoints (budget, meals/suggest) to 5-10 requests per minute
- **FR26:** System can return appropriate rate limit exceeded responses with retry information

### Codebase Cleanup

- **FR27:** System removes classification orchestrator and category routing logic
- **FR28:** System removes Quote and Note category code (prompts, schemas, enum values, placeholders)
- **FR29:** Budget endpoint is renamed from `/api/v1/process` to `/api/v1/budget`

## Non-Functional Requirements

### Performance

| Requirement | Target | Context |
|-------------|--------|---------|
| **NFR1:** Budget text entry response time | < 1 second end-to-end | Must feel instant for rapid-fire logging |
| **NFR2:** Budget screenshot processing time | < 5 seconds per image | Vision API is slower; user expects batch processing delay |
| **NFR3:** Meal suggestion response time | < 3 seconds | LLM generation; user taps and waits |
| **NFR4:** Non-LLM endpoint response time | < 200ms | Export, health, feedback — should be near-instant |

### Reliability

| Requirement | Target | Context |
|-------------|--------|---------|
| **NFR5:** Zero data loss | Every submitted entry must persist | Budget entries and meal feedback are irreplaceable |
| **NFR6:** No silent failures | All errors return clear, descriptive responses | User must always know if something failed |
| **NFR7:** Database integrity | No partial or corrupted writes | Atomic transactions for all DB operations |
| **NFR8:** LLM failure handling | Graceful degradation with clear error | If Claude is down, user gets an informative error, not a crash |

### Security

| Requirement | Target | Context |
|-------------|--------|---------|
| **NFR9:** Rate limiting on LLM endpoints | 5-10 req/min | Cost protection since API is exposed |
| **NFR10:** No secrets in codebase | API keys via environment variables only | Standard practice |

### Developer Experience

| Requirement | Target | Context |
|-------------|--------|---------|
| **NFR11:** Swagger UI available | Interactive API docs served at `/api/v1/docs` | FastAPI's auto-generated Swagger UI must remain enabled for all endpoints. Essential for API exploration and testing during development. |
