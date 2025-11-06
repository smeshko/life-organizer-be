# Life Organizer Backend - API Documentation

This directory contains comprehensive API documentation for integrating with the Life Organizer backend from the iOS application.

## 📁 Documentation Files

### 1. `openapi.yaml`
**Complete OpenAPI 3.0.3 Specification**

This is the industry-standard OpenAPI specification that describes all endpoints, request/response models, and examples. You can use this file with various tools:

- **Swagger UI**: View interactive API documentation
- **Code Generation**: Generate Swift client code automatically
- **API Testing**: Use with Postman, Insomnia, or similar tools
- **Validation**: Verify API compliance

**View the docs:**
```bash
# Start the backend server
make run

# Then visit:
http://localhost:8000/api/v1/docs
```

### 2. `models.yaml`
**iOS Integration Blueprint**

A focused, iOS-friendly reference containing:
- All public data models with detailed property descriptions
- Swift implementation examples and best practices
- Codable struct patterns for discriminated unions
- Complete example API requests and responses
- Integration guide for handling different action types

**This is your go-to reference for implementing the API client in Swift.**

### 3. `API_DOCUMENTATION.md` (this file)
**Integration Guide**

Overview and quick start guide for iOS developers.

---

## 🚀 Quick Start

### Base URL
- **Development**: `http://localhost:8000`
- **Production**: TBD

### API Version
Current API version: **v1**

All versioned endpoints are prefixed with `/api/v1`

### Primary Endpoint
```
POST /api/v1/process
```

This is the main endpoint your iOS app will interact with. It:
1. Accepts user voice/text input
2. Classifies and processes it
3. Returns an action for your app to execute

---

## 📱 iOS Integration Flow

### 1. User Input
User speaks or types input in your app:
```
"spent 120 euros at Next"
"remind me to buy milk tomorrow at 9am"
"add bananas to shopping list"
```

### 2. API Request
Send input to backend:
```swift
POST /api/v1/process
Content-Type: application/json

{
  "input": "spent 120 euros at Next"
}
```

### 3. Process Response
Backend returns an `ActionResult`:
```json
{
  "success": true,
  "action_type": "app_action_required",
  "message": "Logged expenses: 234.6 BGN in Clothes",
  "app_action": {
    "type": "log_budget_entry",
    "amount": 234.6,
    "date": "2025-11-03",
    "transaction_type": "Expenses",
    "category": "Clothes",
    "details": "next"
  }
}
```

### 4. Execute Action
Your app checks `action_type` and executes the appropriate action:

```swift
switch result.actionType {
case .appActionRequired:
    if let action = result.appAction {
        switch action {
        case .logBudgetEntry(let entry):
            // Write to Excel sheet via iOS Files API
            await budgetTracker.logEntry(entry)
        case .createReminder(let reminder):
            // Create iOS Reminder
            await reminderManager.create(reminder)
        case .addToShoppingList(let item):
            // Add to shopping list
            await shoppingList.add(item)
        case .createCalendarEvent(let event):
            // Create iOS Calendar event
            await calendar.createEvent(event)
        }
    }
    // Show success message
    showAlert(result.message)
}
```

---

## 🎯 Action Types

The `action_type` field determines what your app should do:

### 1. `app_action_required`
**iOS app must perform an action**

The `app_action` field will contain a discriminated union with one of:
- `CreateReminderAction` - Create iOS Reminder
- `AddToShoppingListAction` - Add to shopping list
- `CreateCalendarEventAction` - Create iOS Calendar event
- `LogBudgetEntryAction` - Log to Excel budget sheet

**What to do:**
1. Parse the `type` field in `app_action`
2. Decode the specific action
3. Execute it using iOS APIs
4. Show the `message` to the user

### 2. `backend_handled`
**Backend completed the action**

The backend handled everything (e.g., logged to database, calculated something).

**What to do:**
1. Show the `message` to the user
2. No further action needed

### 3. `confirmation_needed`
**User needs to clarify**

The backend couldn't understand the input with high confidence.

**What to do:**
1. Show the `confirmation.question` to the user
2. Present `confirmation.options` as choices
3. Get user selection
4. Send a new request with the clarified input

---

## 📊 Budget Entry Details

Budget entries are the most complex action. Here's what you need to know:

### Transaction Types
- **Expenses**: User spending (most common)
- **Income**: Money received
- **Savings**: Money saved/invested

### Categories by Type

**Expense Categories (16):**
- Baby, Body care, Clothes, Eat out, Fun, Groceries, Hobbies, Home improvements, Maya, Medical, Mortgage, Other, Subscriptions, Transport, Utilities, Vacation

**Income Categories (4):**
- Salary Ivo, Salary Kalina, Rent, Other

**Savings Categories (3):**
- Avi Savings, Metlife, Savings

### Currency Conversion
- Backend automatically converts EUR → BGN
- You receive amounts in BGN
- Current rate: ~1.95 BGN per EUR

### Excel Integration
The iOS app should write entries to the Excel budget tracking sheet using:
- iOS Files API to access the shared Excel file
- OpenPyXL-equivalent Swift library (or Excel formulas)
- Proper date formatting (YYYY-MM-DD)

---

## 🔧 Implementation Checklist

### Phase 1: Basic Integration
- [ ] Create Swift Codable models from `models.yaml`
- [ ] Implement API client with `POST /api/v1/process`
- [ ] Handle `ActionResult` response
- [ ] Test with simple inputs

### Phase 2: Action Handlers
- [ ] Implement `LogBudgetEntryAction` handler
  - [ ] Excel file access via Files API
  - [ ] Write entry to correct sheet
  - [ ] Validate categories
- [ ] Implement `CreateReminderAction` handler
  - [ ] Request EventKit permissions
  - [ ] Create reminder in default or specified list
- [ ] Implement `AddToShoppingListAction` handler
  - [ ] Manage shopping lists
  - [ ] Handle quantities
- [ ] Implement `CreateCalendarEventAction` handler
  - [ ] Request Calendar permissions
  - [ ] Create event with time/location

### Phase 3: Polish
- [ ] Add error handling (422, 500 responses)
- [ ] Implement confirmation flow
- [ ] Add loading states
- [ ] Test edge cases
- [ ] Add offline queueing

---

## 🧪 Testing

### Health Check
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "service": "life-organizer-backend",
  "version": "0.1.0"
}
```

### Process Input
```bash
curl -X POST http://localhost:8000/api/v1/process \
  -H "Content-Type: application/json" \
  -d '{"input": "spent 50 euros at dm"}'
```

---

## 🛠️ Code Generation

You can auto-generate Swift client code from `openapi.yaml`:

### Using OpenAPI Generator
```bash
# Install
brew install openapi-generator

# Generate Swift client
openapi-generator generate \
  -i openapi.yaml \
  -g swift5 \
  -o ./ios-client \
  --additional-properties=projectName=LifeOrganizerAPI
```

### Using Swagger Codegen
```bash
swagger-codegen generate \
  -i openapi.yaml \
  -l swift5 \
  -o ./ios-client
```

**Note:** Auto-generated code may need adjustments for discriminated unions. Use `models.yaml` examples as a reference.

---

## 📖 Additional Resources

### OpenAPI Spec
- [OpenAPI 3.0 Specification](https://swagger.io/specification/)
- [Swagger Editor](https://editor.swagger.io/) - Paste `openapi.yaml` to view/edit

### Swift Integration
- [Codable Documentation](https://developer.apple.com/documentation/swift/codable)
- [URLSession Guide](https://developer.apple.com/documentation/foundation/urlsession)
- [EventKit (Reminders)](https://developer.apple.com/documentation/eventkit)
- [EventKit (Calendar)](https://developer.apple.com/documentation/eventkit/accessing_the_event_store)

### Excel Integration
- [iOS Files API](https://developer.apple.com/documentation/uikit/view_controllers/providing_access_to_directories)
- Consider using CSV format if direct Excel manipulation is complex

---

## 🤝 Support

For questions or issues:
1. Check `models.yaml` for detailed model descriptions
2. Review example responses in `models.yaml`
3. Test with Swagger UI at `/api/v1/docs`
4. Check backend logs for processing errors

---

## 🔄 API Versioning

Current version: **v1**

Breaking changes will increment the version (v2, v3, etc.). Endpoints will support multiple versions during migration periods.

**Deprecation Policy:**
- 3 months notice for deprecated endpoints
- 6 months support for old versions
- Migration guide provided

---

## 📝 Changelog

### v0.1.0 (Current)
- Initial API release
- POST /api/v1/process endpoint
- Support for budget, shopping, reminder, calendar categories
- EUR to BGN conversion
- LLM-based classification with Claude

### Future Features
- Authentication (JWT tokens)
- User management
- Budget analytics endpoints
- Recurring entries
- Multi-currency support
- Family member management
