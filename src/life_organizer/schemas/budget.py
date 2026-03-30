"""Budget categories, transaction types, and response schemas for budget endpoints."""

import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ExpenseCategory(StrEnum):
    """Expense categories for budget tracking (16 total).

    These categories map directly to the expense categories in the
    Ultimate Personal Budget Extended.xlsx spreadsheet.
    """

    BABY = "Baby"
    BODY_CARE = "Body care"
    CLOTHES = "Clothes"
    EAT_OUT = "Eat out"
    FUN = "Fun"
    GROCERIES = "Groceries"
    HOBBIES = "Hobbies"
    HOME_IMPROVEMENTS = "Home improvements"
    MAYA = "Maya"
    MEDICAL = "Medical"
    MORTGAGE = "Mortgage"
    OTHER = "Other"
    SUBSCRIPTIONS = "Subscriptions"
    TRANSPORT = "Transport"
    UTILITIES = "Utilities"
    VACATION = "Vacation"


class IncomeCategory(StrEnum):
    """Income categories for budget tracking (5 total).

    These categories map directly to the income categories in the
    Ultimate Personal Budget Extended.xlsx spreadsheet.
    """

    SALARY_IVO = "Salary Ivo"
    SALARY_KALINA = "Salary Kalina"
    RENT = "Rent"
    REFUNDS = "Refunds"
    OTHER = "Other"


class SavingsCategory(StrEnum):
    """Savings categories for budget tracking (3 total).

    These categories map directly to the savings categories in the
    Ultimate Personal Budget Extended.xlsx spreadsheet.
    """

    AVI_SAVINGS = "Avi Savings"
    METLIFE = "Metlife"
    SAVINGS = "Savings"


class TransactionItem(BaseModel):
    """Single transaction in a paginated response."""

    id: int = Field(description="Transaction primary key")
    amount: float = Field(description="Original transaction amount")
    currency: str = Field(description="Currency code (e.g. EUR, USD)")
    amount_eur: float | None = Field(
        description="Amount converted to EUR (null for legacy records)"
    )
    date: datetime.date = Field(description="Transaction date")
    transaction_type: str = Field(description="Transaction type (Expenses, Income, or Savings)")
    category: str = Field(description="Transaction category")
    details: str | None = Field(description="Merchant name or description")


class PaginatedTransactionsResponse(BaseModel):
    """Paginated list of budget transactions."""

    items: list[TransactionItem] = Field(description="List of transactions for the current page")
    total: int = Field(description="Total number of matching transactions")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Number of items per page")


class AvailableYearsResponse(BaseModel):
    """List of years that have transaction data."""

    years: list[int] = Field(description="Sorted list of years with transactions")


class CategoryAggregation(BaseModel):
    """Spending total for a single category."""

    category: str = Field(description="Transaction category name")
    total_eur: float = Field(description="Total amount in EUR for this category")
    count: int = Field(description="Number of transactions in this category")


class AggregationPeriod(BaseModel):
    """Time period for the aggregation."""

    year: int = Field(description="Year of the aggregation period")
    month: int | None = Field(default=None, description="Month (1-12) or null for full year")


class AggregationResponse(BaseModel):
    """Aggregated spending totals by category."""

    period: AggregationPeriod = Field(description="Time period covered by the aggregation")
    aggregations: list[CategoryAggregation] = Field(
        description="Category-level totals sorted by total_eur descending"
    )


# Budget Plan schemas


class BudgetPlanEntry(BaseModel):
    """Single entry in a budget plan upsert request."""

    transaction_type: str = Field(description="Transaction type (Expenses, Income, or Savings)")
    category: str = Field(description="Category name within the transaction type")
    month: int = Field(ge=1, le=12, description="Month number (1-12)")
    planned_amount: float = Field(ge=0, description="Planned amount for this category/month")


class BudgetPlanRequest(BaseModel):
    """Request body for PUT /plan/{year} endpoint."""

    entries: list[BudgetPlanEntry] = Field(
        min_length=1, description="List of budget plan entries to upsert"
    )


class BudgetPlanUpsertResponse(BaseModel):
    """Response for PUT /plan/{year} endpoint."""

    success: bool = Field(description="Whether the upsert operation succeeded")
    updated: int = Field(description="Number of entries upserted")


class BudgetPlanAmounts(BaseModel):
    """Single category's planned amounts across months in a GET response."""

    transaction_type: str = Field(description="Transaction type (Expenses, Income, or Savings)")
    category: str = Field(description="Category name within the transaction type")
    amounts: dict[str, float] = Field(
        description="Planned amounts by month number (keys '1'-'12', months without plans omitted)"
    )


class BudgetPlanResponse(BaseModel):
    """Response for GET /plan/{year} endpoint."""

    year: int = Field(description="Budget plan year")
    entries: list[BudgetPlanAmounts] = Field(
        description="Plan entries grouped by transaction type and category"
    )


# Transaction update/delete schemas


class TransactionUpdateRequest(BaseModel):
    """Request body for PATCH /transactions/{id} endpoint. All fields optional."""

    amount: float | None = Field(default=None, gt=0, description="New transaction amount")
    currency: str | None = Field(default=None, max_length=3, description="New currency code")
    date: datetime.date | None = Field(default=None, description="New transaction date")
    transaction_type: str | None = Field(default=None, description="New transaction type")
    category: str | None = Field(default=None, description="New category")
    details: str | None = Field(default=None, description="New merchant/description")
