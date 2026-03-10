# Transaction Query and Pagination Endpoints

**Date:** 2026-03-10
**Related Files:** `src/life_organizer/api/routes/budget.py`, `src/life_organizer/services/budget_service.py`, `src/life_organizer/schemas/budget.py`

## Overview

Adds two read-only GET endpoints for browsing transaction history: a paginated, filterable transaction list and a distinct-years lookup. These endpoints establish the pagination and query-filter patterns for all future non-LLM list endpoints in the budget domain.

## What Was Built

- `GET /api/v1/budget/transactions` — paginated transaction query with optional date range, type, and category filters
- `GET /api/v1/budget/years` — distinct years with transaction data, sorted ascending
- `PaginatedResult` TypedDict for typed service-layer return values
- Response schemas: `TransactionItem`, `PaginatedTransactionsResponse`, `AvailableYearsResponse`
- Database index on `category` column for query performance

## Technical Implementation

### Key Files

- `src/life_organizer/api/routes/budget.py`: Route handlers with FastAPI `Query()` validation and OpenAPI examples
- `src/life_organizer/services/budget_service.py`: `query_transactions()` and `get_available_years()` methods with SQLAlchemy async queries
- `src/life_organizer/schemas/budget.py`: Pydantic response models
- `src/life_organizer/db/models/budget.py`: Category index in `__table_args__`
- `alembic/versions/e1a4b6c83d29_add_category_index_to_budget_transactions.py`: Index migration

### Key Patterns

- **Pagination with deterministic ordering**: Always use a secondary sort key (e.g., `.order_by(date.desc(), id.desc())`) to prevent non-deterministic result ordering across pages when rows share the same primary sort value.

- **Optional filter building**: Build a list of SQLAlchemy conditions from optional parameters, then apply them in a loop. This avoids deeply nested if/else chains:
  ```python
  conditions = []
  if start_date is not None:
      conditions.append(Model.date >= start_date)
  if category is not None:
      conditions.append(Model.category == category)

  stmt = select(Model)
  for condition in conditions:
      stmt = stmt.where(condition)
  ```

- **Separate count query**: Run a `select(func.count())` query before the items query to get the total without loading all rows. Both queries share the same filter conditions.

- **PaginatedResult TypedDict**: Use a TypedDict instead of a plain dict for typed pagination results from service methods, avoiding mypy issues with `dict[str, object]`.

### Code Examples

```python
# Service method pattern for paginated queries
async def query_transactions(
    self,
    start_date: datetime.date | None,
    end_date: datetime.date | None,
    page: int,
    page_size: int,
) -> PaginatedResult:
    async with self.session_factory() as db:
        conditions = []
        if start_date is not None:
            conditions.append(BudgetTransaction.date >= start_date)

        count_stmt = select(func.count()).select_from(BudgetTransaction)
        for condition in conditions:
            count_stmt = count_stmt.where(condition)
        total = (await db.execute(count_stmt)).scalar() or 0

        items_stmt = (
            select(BudgetTransaction)
            .order_by(BudgetTransaction.date.desc(), BudgetTransaction.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        for condition in conditions:
            items_stmt = items_stmt.where(condition)
        transactions = (await db.execute(items_stmt)).scalars().all()

        return {"items": list(transactions), "total": total, "page": page, "page_size": page_size}
```

## How to Use

1. Call `GET /api/v1/budget/transactions` with optional query params: `start_date`, `end_date`, `transaction_type`, `category`, `page`, `page_size`
2. All filters are AND'd together when multiple are provided
3. Call `GET /api/v1/budget/years` to get the list of years with data (useful for year-picker UI)

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| page | int | 1 | Page number (1-based, min 1) |
| page_size | int | 50 | Items per page (min 1, max 200) |
| start_date | date | None | Filter on or after this date |
| end_date | date | None | Filter on or before this date |
| transaction_type | string | None | Filter by type (Expenses, Income, Savings) |
| category | string | None | Filter by category name |

## Notes

- The `category` column index (`ix_budget_transactions_category`) was added alongside existing `date` and `transaction_type` indexes to support filter queries
- `amount_eur` may be `None` for legacy records imported before EUR conversion was added
- No rate limiting on these endpoints (non-LLM, read-only)
- Mock setup in tests requires `MagicMock` (not `AsyncMock`) for `.scalars().all()` chain since those are sync calls on the result of `await db.execute()`
