"""Budget transaction database model.

This module defines the SQLAlchemy ORM model for budget transactions,
which are stored in the 'budget' schema namespace.
"""

import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, Index, Numeric, String, Text, func
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
