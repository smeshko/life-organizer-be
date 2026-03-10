# Budget Plan CRUD Endpoints

**Date:** 2026-03-10
**Related Files:** `src/life_organizer/api/routes/budget.py`, `src/life_organizer/services/budget_service.py`, `src/life_organizer/schemas/budget.py`, `src/life_organizer/db/models/budget.py`, `alembic/versions/d7a3f1b52e94_create_budget_plans_table.py`

## Overview

Adds budget planning CRUD endpoints that allow users to create and view planned spending amounts per category per month. This enables the frontend to display a budget planning spreadsheet and compare planned vs actual spending. The implementation uses PostgreSQL upsert (ON CONFLICT DO UPDATE) for efficient bulk updates.

## What Was Built

- `GET /api/v1/budget/plan/{year}` — Retrieves plan entries grouped by transaction type and category, with amounts keyed by month number
- `PUT /api/v1/budget/plan/{year}` — Upserts plan entries with validation, deduplication, and rate limiting
- `BudgetPlan` ORM model in the `budget.plans` table with unique constraint on `(year, month, transaction_type, category)`
- Alembic migration for the `budget.plans` table with check constraints on month range and non-negative amounts

## Technical Implementation

### Key Files

- `alembic/versions/d7a3f1b52e94_create_budget_plans_table.py`: Migration creating `budget.plans` with unique constraint, check constraints, and year index
- `src/life_organizer/db/models/budget.py`: `BudgetPlan` SQLAlchemy 2.0 ORM model with `Mapped` type hints
- `src/life_organizer/schemas/budget.py`: Pydantic schemas for request/response (`BudgetPlanEntry`, `BudgetPlanRequest`, `BudgetPlanResponse`, `BudgetPlanAmounts`, `BudgetPlanUpsertResponse`)
- `src/life_organizer/services/budget_service.py`: `get_plan()` and `upsert_plan()` service methods
- `src/life_organizer/api/routes/budget.py`: GET and PUT route handlers with validation and grouping logic

### Key Patterns

- **PostgreSQL Upsert via `pg_insert`**: Uses `sqlalchemy.dialects.postgresql.insert` with `.on_conflict_do_update()` targeting the named unique constraint. This allows atomic bulk insert-or-update in a single statement:
  ```python
  stmt = pg_insert(BudgetPlan).values(rows)
  stmt = stmt.on_conflict_do_update(
      constraint="uq_budget_plans_year_month_type_category",
      set_={
          "planned_amount": stmt.excluded.planned_amount,
          "updated_at": func.now(),
      },
  )
  ```

- **Flat-to-Grouped Response Transformation**: The GET endpoint reads flat `(type, category, month, amount)` rows and groups them into `{type, category, amounts: {month: amount}}` objects in the router layer using a dict keyed by `(transaction_type, category)` tuples.

- **Request Deduplication**: The PUT endpoint deduplicates entries before upserting using a last-write-wins strategy keyed by `(month, transaction_type, category)`, preventing duplicate key errors from PostgreSQL.

- **Category Validation at API Layer**: The PUT endpoint validates `transaction_type` against known types and `category` against the corresponding enum (`ExpenseCategory`, `IncomeCategory`, `SavingsCategory`) before reaching the service layer.

## How to Use

1. **Create/update a budget plan**: Send `PUT /api/v1/budget/plan/2026` with a JSON body containing entries:
   ```json
   {
     "entries": [
       {"transaction_type": "Expenses", "category": "Groceries", "month": 1, "planned_amount": 400.00},
       {"transaction_type": "Expenses", "category": "Groceries", "month": 2, "planned_amount": 450.00}
     ]
   }
   ```

2. **Retrieve a budget plan**: Send `GET /api/v1/budget/plan/2026` to get entries grouped by type/category:
   ```json
   {
     "year": 2026,
     "entries": [
       {"transaction_type": "Expenses", "category": "Groceries", "amounts": {"1": 400.0, "2": 450.0}}
     ]
   }
   ```

3. Sending the same `(year, month, transaction_type, category)` combination again updates the existing entry rather than creating a duplicate.

## Configuration

No additional configuration is required. The endpoints use the existing database connection and rate limiter (10 requests/minute on the PUT endpoint).

## Notes

- The `budget.plans` table lives in the `budget` schema alongside `budget.transactions`
- Month numbers are stored as integers (1-12) with a check constraint; months without plans are simply omitted from the GET response
- The `planned_amount` column is `Numeric(10,2)` with a non-negative check constraint
- The migration downgrades cleanly by dropping the table without affecting the shared `budget` schema
