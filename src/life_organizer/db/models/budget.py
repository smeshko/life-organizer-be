"""Budget database models.

This module defines the SQLAlchemy ORM models for budget transactions and
budget plans, which are stored in the 'budget' schema namespace.
"""

import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from life_organizer.db.base import Base


class BudgetTransaction(Base):
    """Budget transaction model for tracking expenses, income, and savings.

    Stores financial transactions with original amounts, currency conversion to EUR,
    transaction type (Expenses/Income/Savings), category, and optional details.

    All transactions are stored in the 'budget' schema namespace.

    Attributes:
        id: Primary key auto-incremented integer
        amount: Original transaction amount (positive decimal)
        currency: Currency code (3 chars, default 'EUR')
        amount_bgn: Amount converted to BGN (historical, for old records)
        amount_eur: Amount converted to EUR (for new records)
        date: Transaction date
        transaction_type: Type of transaction ('Expenses', 'Income', or 'Savings')
        category: Category name (validated against budget enums at Pydantic layer)
        details: Optional merchant name or description
        created_at: Timestamp when record was created (auto-generated)
        updated_at: Timestamp when record was last modified (auto-updated)

    Example:
        transaction = BudgetTransaction(
            amount=Decimal("50.00"),
            currency="EUR",
            amount_eur=Decimal("50.00"),
            date=datetime.date(2024, 11, 10),
            transaction_type="Expenses",
            category="Groceries",
            details="Kaufland"
        )
    """

    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_budget_transactions_date", "date"),
        Index("ix_budget_transactions_type", "transaction_type"),
        Index("ix_budget_transactions_category", "category"),
        CheckConstraint("amount > 0", name="check_amount_positive"),
        CheckConstraint("amount_bgn >= 0", name="check_amount_bgn_non_negative"),
        {"schema": "budget"},
    )

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    # Amount fields
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    amount_bgn: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    amount_eur: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    # Transaction metadata
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        amount_display = f"{self.amount_eur} EUR" if self.amount_eur else f"{self.amount_bgn} BGN"
        return (
            f"<BudgetTransaction(id={self.id}, "
            f"type={self.transaction_type}, "
            f"category={self.category}, "
            f"amount={amount_display}, "
            f"date={self.date})>"
        )


class BudgetPlan(Base):
    """Budget plan model for tracking planned amounts per category per month.

    Stores planned budget amounts for each transaction type and category
    combination per month. Used for budget planning spreadsheets.

    All plans are stored in the 'budget' schema namespace.

    Attributes:
        id: Primary key auto-incremented integer
        year: Budget year
        month: Budget month (1-12)
        transaction_type: Type of transaction ('Expenses', 'Income', or 'Savings')
        category: Category name (validated against budget enums at Pydantic layer)
        planned_amount: Planned amount for this category/month (non-negative decimal)
        created_at: Timestamp when record was created (auto-generated)
        updated_at: Timestamp when record was last modified (auto-updated)
    """

    __tablename__ = "plans"
    __table_args__ = (
        UniqueConstraint(
            "year",
            "month",
            "transaction_type",
            "category",
            name="uq_budget_plans_year_month_type_category",
        ),
        CheckConstraint("planned_amount >= 0", name="check_planned_amount_non_negative"),
        CheckConstraint("month >= 1 AND month <= 12", name="check_month_valid"),
        Index("ix_budget_plans_year", "year"),
        {"schema": "budget"},
    )

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    # Plan fields
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    planned_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Timestamps
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<BudgetPlan(id={self.id}, "
            f"year={self.year}, month={self.month}, "
            f"type={self.transaction_type}, "
            f"category={self.category}, "
            f"amount={self.planned_amount})>"
        )
