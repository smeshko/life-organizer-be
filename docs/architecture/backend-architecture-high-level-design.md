# Backend Architecture - High Level Design

## Core Principles

Let me propose a simple, extensible backend architecture that keeps your options open while staying maintainable:

---

## The Big Picture

```
Voice Input → Backend → Classification → Action Handler → Response
                                              ↓
                                    [Google Sheets API]
                                    [Other Integrations]
```

---

## 1. Request/Response Contract

Keep it dead simple - one endpoint to rule them all:

**Request (from iOS app):**

```python
{
    "user_id": "family_member_123",
    "input": "Spent 45 euros at the restaurant",
    "timestamp": "2025-10-30T14:23:00Z",
    "context": {
        "location": "Barcelona, Spain",
        "previous_action": null
    }
}
```

**Response (to iOS app):**

```python
{
    "success": true,
    "action_type": "backend_handled" | "app_action_required" | "confirmation_needed",
    "message": "Logged 45 EUR dining expense",

    "app_action": {
        "type": "create_reminder" | "add_to_shopping_list" | "create_calendar_event",
        "data": {
            "title": "Buy milk",
            "due_date": "2025-10-31T10:00:00Z",
            "list_id": "shopping_list"
        }
    },

    "confirmation": {
        "question": "Did you mean to log this as 'Dining' or 'Groceries'?",
        "options": ["Dining", "Groceries", "Other"],
        "original_classification": "Dining",
        "confidence": 0.65
    }
}
```

---

## 2. Backend Components (Layered Architecture)

### Layer 1: API Gateway

```
/api/process-input (POST)
    ↓
[Request validation]
[Authentication check]
[Rate limiting]
    ↓
Pass to Classification Layer
```

**Responsibility:** Accept requests, validate, pass along. That's it.

---

### Layer 2: Classification Engine

```
Input text →
    ↓
[Intent Classifier] → Determines category (expense, shopping, reminder, etc.)
    ↓
[Confidence Scorer] → High confidence? Auto-execute. Low? Ask user.
    ↓
Route to appropriate handler
```

**Responsibility:** "What kind of thing is this?" Nothing else.

**Simple Implementation (Stage 1):**

* Start with keyword matching dictionary
* Add scoring based on keyword confidence
* Threshold: >85% confidence = auto-execute, <85% = ask user

**Future Enhancement (Stage 3+):**

* Add LLM (Claude API) for complex cases that keyword matching misses
* Keep keyword matching as first pass (faster, cheaper)

---

### Layer 3: Action Handlers (Plugin Architecture)

This is the key to extensibility. Each handler is self-contained:

```
handlers/
├── expense_handler.py
├── shopping_handler.py
├── reminder_handler.py
├── calendar_handler.py
├── base_handler.py (abstract class)
└── __init__.py (handler registry)
```

**Base Handler Pattern:**

```python
class BaseHandler:
    def can_handle(self, classified_input) -> bool:
        pass

    def requires_app_action(self) -> bool:
        pass

    def execute(self, classified_input) -> ProcessingResponse:
        pass
```

**Example - Expense Handler:**

```python
class ExpenseHandler(BaseHandler):
    def can_handle(self, classified_input):
        return classified_input.category == "expense"

    def requires_app_action(self):
        return False

    def execute(self, classified_input):
        # Extract amount, currency, category
        # Call Google Sheets API
        return ProcessingResponse(
            success=True,
            action_type="backend_handled",
            message="Logged expense"
        )
```

**Example - Shopping Handler:**

```python
class ShoppingHandler(BaseHandler):
    def can_handle(self, classified_input):
        return classified_input.category == "shopping"

    def requires_app_action(self):
        return True

    def execute(self, classified_input):
        return ProcessingResponse(
            success=True,
            action_type="app_action_required",
            app_action={
                "type": "create_reminder",
                "data": {
                    "title": classified_input.item,
                    "list_id": "shopping_list"
                }
            }
        )
```

**Why This Works**

* ✅ Adding new event types: Just add a new handler file.
* ✅ Backend vs App distinction: Handler decides via `requires_app_action()`
* ✅ Testing: Each handler is independent, easy to test
* ✅ Maintainability: Each handler is 20-50 lines, self-contained

---

## 3. Handler Registry (The Glue)

```python
# handlers/__init__.py
from .expense_handler import ExpenseHandler
from .shopping_handler import ShoppingHandler
from .reminder_handler import ReminderHandler

HANDLERS = [
    ExpenseHandler(),
    ShoppingHandler(),
    ReminderHandler()
]

def get_handler(classified_input):
    for handler in HANDLERS:
        if handler.can_handle(classified_input):
            return handler
    return DefaultHandler()
```

---

## 4. Data Flow Example

### Example 1: "Spent 45 EUR at restaurant"

1. API Gateway receives POST request
2. Classification Engine:

   * Detects keywords: "spent", "EUR", "restaurant"
   * Category: "expense"
   * Confidence: 95%
   * Extracts: `{amount: 45, currency: "EUR", category: "Dining"}`
3. Handler Registry finds ExpenseHandler
4. ExpenseHandler executes:

   * Calls Google Sheets API
   * Appends row: `[2025-10-30, 45, EUR, Dining, restaurant, ...]`
5. Returns:

```python
{
    "success": true,
    "action_type": "backend_handled",
    "message": "Logged 45 EUR dining expense"
}
```

### Example 2: "We're out of milk"

1. API Gateway receives request
2. Classification Engine:

   * Detects: "out of"
   * Category: "shopping"
   * Confidence: 90%
   * Extracts: `{item: "milk"}`
3. Handler Registry finds ShoppingHandler
4. ShoppingHandler executes:

   * Returns `ProcessingResponse(app_action_required)`
5. Response:

```python
{
    "success": true,
    "action_type": "app_action_required",
    "message": "Add milk to shopping list",
    "app_action": {
        "type": "create_reminder",
        "data": {
            "title": "Milk",
            "list_id": "shopping_list",
            "notes": "Added via: 'We're out of milk'"
        }
    }
}
```

---

## 5. Persistence Strategy

### What to Store on Backend

**1. Action Log:**

```python
{
    "id": "uuid",
    "timestamp": "2025-10-30T14:23:00Z",
    "user_id": "family_member_123",
    "raw_input": "Spent 45 EUR at restaurant",
    "classified_as": "expense",
    "confidence": 0.95,
    "handler": "ExpenseHandler",
    "action_type": "backend_handled",
    "success": true,
    "error": null
}
```

**2. User Preferences:**

```python
{
    "user_id": "family_member_123",
    "default_currency": "EUR",
    "default_reminder_list": "shopping_list",
    "category_mappings": {
        "carrefour": "Groceries",
        "mercadona": "Groceries"
    }
}
```

**3. Pending Actions Queue:**

```python
{
    "id": "uuid",
    "user_id": "family_member_123",
    "action": {...},
    "status": "pending" | "completed" | "failed",
    "retries": 0,
    "created_at": "...",
    "completed_at": null
}
```

**Stage 1:** SQLite (simple, no setup)
**Stage 2:** PostgreSQL (multi-instance, real-time)

---

## 6. Error Handling Strategy

**1. Classification Uncertainty:**

```python
{
    "action_type": "confirmation_needed",
    "confirmation": {
        "question": "Is this an expense or a reminder?",
        "options": ["Expense", "Reminder", "Something else"]
    }
}
```

**2. Backend Errors:**

```python
{
    "success": false,
    "action_type": "retry_later",
    "message": "Couldn't log expense right now, will retry",
    "queued": true
}
```

**3. App-Side Errors:** App handles this itself.

---

## 7. Configuration Management

```python
# config.py
EXPENSE_CONFIG = {
    "google_sheet_id": "your-sheet-id",
    "sheet_name": "Expenses",
    "category_keywords": {
        "Dining": ["restaurant", "cafe", "dinner", "lunch"],
        "Groceries": ["supermarket", "grocery", "carrefour"]
    }
}

SHOPPING_CONFIG = {
    "default_list": "Shopping List",
    "common_items": ["milk", "bread", "eggs"]
}

REMINDER_CONFIG = {
    "default_times": {
        "trash": "10 minutes from now",
        "call": "tomorrow at 10am",
        "generic": "1 hour from now"
    }
}
```

---

## 8. The Complete Picture

```
                    ┌─────────────────────┐
                    │   iOS Voice App     │
                    │  (App Intent / UI)  │
                    └──────────┬──────────┘
                               │ HTTPS POST
                               ↓
┌──────────────────────────────────────────────────────┐
│                  BACKEND SERVICE                      │
│                                                       │
│  ┌─────────────────────────────────────────────┐      │
│  │         API Gateway (FastAPI)                │      │
│  │  • /api/process-input                        │      │
│  │  • Authentication                            │      │
│  │  • Request validation                        │      │
│  └────────────────┬─────────────────────────────┘      │
│                   ↓                                   │
│  ┌─────────────────────────────────────────────┐      │
│  │      Classification Engine                   │      │
│  │  • Keyword matching (Stage 1)                │      │
│  │  • Confidence scoring                        │      │
│  │  • LLM fallback (Stage 3+)                   │      │
│  └────────────────┬─────────────────────────────┘      │
│                   ↓                                   │
│  ┌─────────────────────────────────────────────┐      │
│  │       Handler Registry                       │      │
│  │  Finds appropriate handler for category      │      │
│  └────────────────┬─────────────────────────────┘      │
│                   ↓                                   │
│  ┌─────────────────────────────────────────────┐      │
│  │         Action Handlers                      │      │
│  │  ┌─────────────────┐  ┌─────────────────┐     │      │
│  │  │ ExpenseHandler  │  │ ShoppingHandler │     │      │
│  │  │ Backend handled │  │ App action req. │     │      │
│  │  │ → Google Sheets │  │ → Return data   │     │      │
│  │  └─────────────────┘  └─────────────────┘     │      │
│  │  ┌─────────────────┐  ┌─────────────────┐     │      │
│  │  │ ReminderHandler │  │  [Future ones]  │     │      │
│  │  │ App action req. │  │   Easy to add!  │     │      │
│  │  │ → Return data   │  │                 │     │      │
│  │  └─────────────────┘  └─────────────────┘     │      │
│  └─────────────────────────────────────────────┘      │
│  ┌─────────────────────────────────────────────┐      │
│  │         Persistence Layer                    │      │
│  │  • Action logs (SQLite)                      │      │
│  │  • User preferences                          │      │
│  │  • Pending actions queue                     │      │
│  └─────────────────────────────────────────────┘      │
└───────────────────────┬───────────────────────────────┘
                        │ External APIs
                        ↓
              ┌──────────────────┐
              │ Google Sheets API │
              └──────────────────┘
```
