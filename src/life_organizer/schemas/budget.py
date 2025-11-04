"""Budget categories and transaction types for budget entry handler."""

from enum import StrEnum


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
    """Income categories for budget tracking (4 total).

    These categories map directly to the income categories in the
    Ultimate Personal Budget Extended.xlsx spreadsheet.
    """

    SALARY_IVO = "Salary Ivo"
    SALARY_KALINA = "Salary Kalina"
    RENT = "Rent"
    OTHER = "Other"


class SavingsCategory(StrEnum):
    """Savings categories for budget tracking (3 total).

    These categories map directly to the savings categories in the
    Ultimate Personal Budget Extended.xlsx spreadsheet.
    """

    AVI_SAVINGS = "Avi Savings"
    METLIFE = "Metlife"
    SAVINGS = "Savings"
