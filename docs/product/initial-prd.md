# Product Requirements Document: Life Organization Agent

## Project Overview

A personal voice-first intelligent agent that captures everyday life events and automatically routes them to the appropriate organizational system (shopping lists, reminders, expense tracking, etc.) with minimal friction and maximum reliability.

## Vision

Create a seamless, voice-activated personal assistant that eliminates the cognitive overhead of managing daily tasks by automatically categorizing and routing spoken inputs to the right destination with deterministic accuracy.

## Problem Statement

Daily life involves countless small tasks, expenses, and thoughts that get lost because manually organizing them across multiple apps requires too much effort. The friction between thinking something and actually logging it leads to forgotten tasks, incomplete expense tracking, and mental clutter.

## Primary Goals

- Enable hands-free capture of life events with high accuracy
- Reduce time from thought-to-action from ~30 seconds to <5 seconds
- Achieve deterministic routing with minimal failures
- Work seamlessly for you and your family members

## Core Features & Requirements

### 1. Voice Input Interface

#### Requirements
- **Mobile App**: Native iOS app with always-available voice capture
- **Siri Integration** (stretch goal): Siri shortcut that triggers the agent
- **Input Method**: Push-to-talk or wake word activated
- **Audio Quality**: Noise cancellation for various environments
- **Offline Capability**: Queue commands when offline, sync when connected

#### Technical Specifications
- Speech-to-text latency: <2 seconds
- Support for multiple accents and speech patterns
- Background recording capability (with user permission)

### 2. Intent Classification System

#### Command Categories & Use Cases

| Category | Example Inputs | Target Action | Notes |
|----------|---------------|---------------|-------|
| **Shopping & Groceries** | "We're out of milk", "Need to buy bread", "Add eggs to the list", "Running low on coffee" | Add to shared iOS Notes grocery list | Auto-detect duplicates, consolidate similar items |
| **Household Tasks** | "Take out the trash", "Change air filter", "Water the plants", "Clean the gutters" | Create iOS Reminder with smart timing | Context-aware: trash â†’ 10 mins, seasonal tasks â†’ appropriate time |
| **Personal Reminders** | "Call dentist tomorrow", "Pick up dry cleaning", "Send birthday card to mom", "Refill prescription" | Create iOS Reminder with smart timing | Parse relative times and set appropriate defaults |
| **Expenses & Purchases** | "Paid 50 EUR at restaurant", "Spent $30 on gas", "Groceries cost 120", "Amazon order 45.99" | Log to Excel expense tracker | Auto-categorize by merchant/keywords |
| **Income & Reimbursements** | "Got paid 2000 EUR", "Received 50 back from John", "Venmo from Sarah 25" | Log to Excel income sheet | Separate tab or marked as income |
| **Bills & Subscriptions** | "Netflix charged 15.99", "Electricity bill 85", "Water bill is due next week" | Log expense + set reminder if needed | Track recurring bills, predict due dates |
| **Health & Fitness** | "Went for a 5k run", "Ate 2000 calories today", "Weight is 75kg", "Doctor appointment next Monday at 3" | Log to health tracking sheet / Create calendar event | Track workouts, nutrition, measurements |
| **Medication & Supplements** | "Took vitamin D", "Need to refill blood pressure meds", "Took ibuprofen for headache" | Log to medication tracker + Create reminder | Track adherence, set refill reminders |
| **Car Maintenance** | "Need to change oil soon", "Car inspection due next month", "Filled up gas, 65 liters, 80 EUR" | Create reminder + Log expense | Track maintenance schedule and fuel costs |
| **Home Maintenance** | "Furnace filter needs changing", "Scheduled plumber for Tuesday", "Roof leak in guest room" | Create reminder / Log in home maintenance notes | Track issues and scheduled repairs |
| **Communication Log** | "Mom just called", "John texted about dinner", "Email from boss about project", "Missed call from dentist" | Log to communication history | Quick reference for who contacted when |
| **Social Plans** | "Dinner with Sarah next Friday", "Coffee with Mike tomorrow at 10", "Party at John's on Saturday" | Create calendar event | Parse time and create event with details |
| **Work & Meetings** | "Team meeting at 2pm tomorrow", "Client call Thursday 3pm", "Project deadline next Friday" | Create calendar event / reminder | Work-specific calendar or reminders |
| **Kids & Family** | "Emma's soccer practice Tuesday 4pm", "Pick up kids at 3:30", "Parent-teacher conference next week", "Tommy needs gym clothes" | Create calendar event / reminder / shopping list | Family member-specific tracking |
| **Pet Care** | "Gave dog flea medication", "Cat vet appointment next month", "Need to buy dog food", "Walked the dog" | Log care activity + reminders + shopping | Track pet health and care schedule |
| **Ideas & Thoughts** | "Remember that movie recommendation", "Idea for project: voice agent", "Look into solar panels" | Add to ideas/notes capture list | Separate note for brainstorming |
| **Books & Media** | "Want to read Dune", "Movie to watch: Inception", "Podcast recommendation: Huberman" | Add to media tracking list | Books to read, movies/shows to watch |
| **Recipes & Cooking** | "Try that pasta recipe Sarah mentioned", "Need to meal prep Sunday", "Dinner idea: thai curry" | Add to recipe ideas / Create reminder | Meal planning and recipe collection |
| **Travel & Trips** | "Flight to Barcelona July 15", "Hotel confirmation number 12345", "Need to book rental car", "Pack sunscreen" | Create calendar event / notes / reminders | Trip planning and packing lists |
| **Financial Goals** | "Saving for vacation", "Spent too much on eating out this month", "Check investment account" | Log to financial notes / Create reminder | Track savings goals and spending patterns |
| **Subscriptions** | "Cancel gym membership", "Spotify renews next week", "Free trial ends on 15th" | Create reminder with details | Track and manage all subscriptions |
| **Gifts & Occasions** | "Mom's birthday is March 10", "Need gift for Sarah's baby shower", "Anniversary in 2 weeks" | Create reminder + Add to gift ideas list | Never forget important dates |
| **Warranty & Returns** | "Laptop warranty until 2026", "Need to return Amazon package", "Blender receipt in email" | Log warranty info / Create reminder | Track warranties and return windows |
| **Learning & Skills** | "Practice Spanish 30 minutes", "Finished chapter 3 of book", "Want to learn photography" | Log progress / Create recurring reminder | Track learning activities and goals |
| **Habit Tracking** | "Did morning meditation", "Drank 8 glasses of water", "Went to bed at 11pm" | Log to habit tracker | Build positive habits with tracking |
| **Password & Account Notes** | "Changed Netflix password", "Bank account number is in email", "Set up 2FA on Gmail" | Log to secure notes (with warning) | Quick reference for account changes |
| **Weather-Dependent Tasks** | "Mow lawn when sunny", "Wash car next weekend if not raining" | Smart reminder with weather check | Context-aware scheduling |
| **Seasonal Reminders** | "Change smoke detector batteries in spring", "Schedule AC maintenance", "Plant tomatoes in April" | Create annual recurring reminder | Never forget seasonal tasks |
| **Package Tracking** | "Amazon package arriving tomorrow", "Expecting delivery from UPS", "Order from Etsy shipped" | Create reminder to check | Track expected deliveries |
| **Energy & Utilities** | "Meter reading is 5432", "Submit electricity reading", "Solar panels produced 45 kWh today" | Log to utilities tracker | Monitor usage and costs |
| **Insurance** | "Car insurance renews in June", "Need to update health insurance beneficiary", "Home insurance quote 800/year" | Create reminder + Log cost | Track policies and renewals |
| **Documents & Papers** | "Need to file 2025 taxes", "Scan mortgage documents", "Print concert tickets" | Create reminder with details | Don't lose important documents |
| **Random Capture** | "That thing I saw on the street corner", "Interesting thought about time", "Random: check that website later" | Add to general capture inbox | Catch everything else |

#### Classification Strategy
- **Rule-based system** for deterministic matching
- **Keyword detection** with priority weighting
- **Context awareness** (time, location, recent history)
- **Fallback handling** with user confirmation for ambiguous inputs

#### Technical Requirements
- Classification decision time: <500ms
- Confidence threshold: >85% for automatic execution
- Below threshold: Present options to user for quick selection
- Learning capability: Remember user corrections to improve accuracy

### 3. Action Execution Layer

#### iOS Notes Integration (Shopping Lists)
- **Requirements**:
  - Access shared Notes via iCloud API
  - Identify correct shopping list note (by title or tag)
  - Append items in consistent format
  - Handle duplicates (smart consolidation)

- **Format**:
  ```
  - Milk (added via agent - 2025-10-29)
  ```

#### iOS Reminders Integration
- **Requirements**:
  - Create reminders with contextual timing
  - Smart time parsing ("in 10 minutes", "tomorrow morning", "next week")
  - Support for location-based reminders
  - Priority inference from language

- **Default Behaviors**:
  - "Take out trash" â†’ 10 minutes from now
  - "Call dentist" â†’ Tomorrow at 10am
  - User-configurable default times per category

#### Excel Expense Tracker Integration
- **Requirements**:
  - Connect to local/cloud Excel file
  - Support multiple storage options (iCloud, Dropbox, OneDrive)
  - Parse amount, currency, category, merchant
  - Auto-categorization based on merchant name

- **Schema**:
  ```
  Date | Amount | Currency | Category | Merchant | Notes
  ```

- **Auto-categorization Rules**:
  - Restaurant names â†’ Food & Dining
  - Gas stations â†’ Transportation
  - Grocery stores â†’ Groceries
  - Fallback â†’ Uncategorized (user can correct)

#### Communication Log
- **Requirements**:
  - Log to dedicated Notes/database
  - Capture: Who, When, Type (call/text), Brief note
  - Enable search and history review

### 4. Backend Service Architecture

#### Components

**API Gateway**
- Receives audio/text from mobile app
- Handles authentication and rate limiting
- Routes to processing pipeline

**Speech-to-Text Service**
- Provider options: Apple Speech Framework, Whisper API, Google Speech-to-Text
- Requirement: Supports real-time streaming

**Intent Classifier**
- Rules engine with keyword matching
- NLU model for complex cases (Claude API or local model)
- Confidence scoring
- Context manager

**Action Router**
- Executes actions via API integrations
- Implements retry logic and error handling
- Maintains action queue for reliability
- Logs all actions for audit trail

**Integration Manager**
- iOS APIs: Notes, Reminders, Calendar
- Excel: via Microsoft Graph API or file manipulation
- Handles OAuth, API keys, permissions

#### Technical Stack Recommendations

**Backend**
- Language: Python (FastAPI) or Node.js (Express)
- Hosting: Cloudflare Workers, Railway, or Fly.io for low-latency
- Database: PostgreSQL for action logs and user settings
- Queue: Redis for job processing

**Mobile App**
- Platform: iOS (Swift/SwiftUI)
- Speech: AVFoundation for recording
- Background: Background tasks API for queued processing

**Determinism & Reliability**
- Transaction-based action execution
- Idempotency keys to prevent duplicates
- Rollback capability for failed actions
- Comprehensive logging for debugging

### 5. User Experience Flow

#### Happy Path
1. User activates voice input (app button or Siri shortcut)
2. User speaks: "We're out of milk"
3. Visual feedback: "Listening..." â†’ "Processing..."
4. Classification: Shopping list (95% confidence)
5. Action: Add "Milk" to shared grocery list
6. Confirmation: "Added milk to grocery list" (haptic + brief visual)
7. Total time: 3-4 seconds

#### Ambiguous Path
1. User speaks: "Need to remember about Sarah"
2. Classification: Low confidence (60%)
3. Quick selection UI: "Is this a: Reminder | Note | Contact Log?"
4. User taps selection
5. Action executed
6. System learns: Next time similar input â†’ higher confidence

#### Error Path
1. User speaks: "Add to list"
2. System: "Which list? Shopping | To-do | General notes?"
3. User clarifies or cancels
4. Action completed or aborted safely

### 6. Configuration & Personalization

#### User Settings
- **List Mappings**: Which Notes are for shopping/other purposes
- **Default Times**: Custom default reminder times per category
- **Expense Categories**: User-defined categories and rules
- **Shared Access**: Who has access to shared lists
- **Voice Preferences**: Confirmation style (silent, haptic, verbal)

#### Learning Preferences
- Track user corrections over time
- Adjust keyword weights based on usage
- Suggest new categories based on patterns

## Technical Requirements

### Security & Privacy
- Local audio processing preferred (privacy)
- Encrypted transmission of all data
- OAuth 2.0 for all integrations
- No persistent audio storage
- All data stored in your personal accounts (iCloud, Excel files)
- Option to run backend locally or on personal cloud

### Reliability
- Automatic retry on failure (up to 3 attempts)
- Offline queueing with sync on reconnection
- Graceful degradation if services unavailable
- Local backup of all actions taken

## Integration Specifications

### iOS Notes
- **API**: CloudKit JS / iOS native APIs
- **Authentication**: iCloud account
- **Rate Limits**: Apple's CloudKit limits
- **Fallback**: Local app notes if iCloud unavailable

### iOS Reminders
- **API**: EventKit framework
- **Permissions**: Calendar/Reminders access
- **Sync**: Native iCloud sync

### Excel Expense Tracker
- **Options**:
  1. Microsoft Graph API (for OneDrive/SharePoint)
  2. Local file manipulation (if file in iCloud/Dropbox)
  3. Google Sheets API (alternative)
- **Format**: .xlsx or .csv
- **Lock Handling**: Detect when file is open, queue updates

## Implementation Plan

### Stage 1: Core Foundation (Build First)
**Focus: Get basic system working**
- Mobile app with voice input (or Siri Shortcut)
- Rule-based classification for 5-10 most common categories
- iOS Notes integration (shopping lists)
- iOS Reminders integration (tasks)
- Basic Excel logging (expenses)

### Stage 2: Essential Daily Use Cases
**Focus: Cover 80% of daily needs**
- Add categories: Bills, Health tracking, Car/Home maintenance
- Improve classification with better keyword matching
- Add Calendar integration
- Excel with multiple sheets (expenses, income, tracking)
- Auto-categorization for expenses

### Stage 3: Family & Advanced Features
**Focus: Multi-user and smart features**
- Family member recognition (voice or profile selection)
- Kids' activities and scheduling
- Pet care tracking
- Shared vs personal lists/reminders
- Learning from corrections

### Stage 4: Nice-to-Haves
**Focus: Polish and convenience**
- Weather-aware reminders
- Seasonal recurring tasks
- Package tracking integration
- Habit tracking and streaks
- Weekly/monthly summary reports
- Voice confirmations (TTS)

### Future Ideas
- Apple Watch support
- Location-based triggers (remind me when I get home)
- Integration with other apps (Notion, Things, YNAB)
- Smart suggestions based on patterns
- Photo capture with voice notes ("Take a picture of this receipt and log it")

## Technical Challenges to Consider

| Challenge | Solution Approach |
|-----------|------------------|
| Speech recognition in noisy environments | Use Apple's native STT with noise cancellation; test in car, kitchen, outdoor |
| Ambiguous commands | Confidence thresholds + quick confirmation UI |
| Family member differentiation | Voice recognition or simple profile selection before command |
| Excel file conflicts (multiple users) | Lock detection, queue updates with timestamps, consider Google Sheets |
| iOS API limitations | Abstract integration layer; have fallbacks ready |
| Offline functionality | Queue all commands locally; sync when reconnected |
| Privacy concerns | Process audio locally when possible; no cloud storage of recordings |
| Maintenance overhead | Keep architecture simple; document everything; automated testing |

## Questions to Answer

1. **Interface**: Native iOS app or just Siri Shortcuts to start?
2. **Backend Hosting**: Local (Raspberry Pi/Mac Mini) vs cloud (Railway/Fly.io)?
3. **Excel vs Alternatives**: Stick with Excel or use Google Sheets for easier multi-user?
4. **Voice Recognition**: Built-in iPhone STT vs Whisper API for better accuracy?
5. **Classification**: Pure rules-based or add LLM (Claude/GPT) for edge cases?
6. **Family Setup**: Individual profiles with different lists or fully shared?
7. **Data Storage**: Keep everything in existing tools or create central database?

## Getting Started

### Immediate Next Steps
1. **Quick Prototype** (Weekend project)
   - Simple iOS app with voice recording
   - Send audio to basic Python backend
   - Test Notes API integration with one list
   - Validate the core idea works

2. **Core Integrations** (Week 1-2)
   - iOS Reminders integration
   - Excel expense logging
   - Basic rule-based classification

3. **Daily Testing** (Week 2-3)
   - Use it yourself for a week
   - Note what works and what doesn't
   - Refine classification rules based on real usage

4. **Family Rollout** (Week 3-4)
   - Add family members
   - Test shared lists
   - Gather feedback and iterate

### Technology Choices

**Option A: Simplest Start**
- Siri Shortcut that sends text to webhook
- Python Flask backend on local machine
- CSV files for expense tracking
- ~1 day to get working

**Option B: Better Long-term**
- SwiftUI iOS app
- Python FastAPI backend (Railway or local)
- Excel with openpyxl
- ~1-2 weeks for MVP

**Option C: Most Powerful**
- Native iOS app with background recording
- Claude API for classification
- Google Sheets for collaboration
- Full offline support
- ~3-4 weeks for polished version

---

**Document Version**: 2.0 - Personal Use Focus
**Last Updated**: October 29, 2025
**Status**: Personal Project Specification
