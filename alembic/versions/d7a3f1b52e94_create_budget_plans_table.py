"""create budget plans table

Revision ID: d7a3f1b52e94
Revises: c5d2f7a41e89
Create Date: 2026-03-10

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d7a3f1b52e94"
down_revision: Union[str, Sequence[str], None] = "c5d2f7a41e89"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create budget.plans table for budget plan entries."""
    op.create_table(
        "plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("transaction_type", sa.String(length=20), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("planned_amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "year",
            "month",
            "transaction_type",
            "category",
            name="uq_budget_plans_year_month_type_category",
        ),
        sa.CheckConstraint("planned_amount >= 0", name="check_planned_amount_non_negative"),
        sa.CheckConstraint("month >= 1 AND month <= 12", name="check_month_valid"),
        schema="budget",
    )

    op.create_index(
        "ix_budget_plans_year",
        "plans",
        ["year"],
        unique=False,
        schema="budget",
    )


def downgrade() -> None:
    """Drop budget.plans table."""
    op.drop_index("ix_budget_plans_year", table_name="plans", schema="budget")
    op.drop_table("plans", schema="budget")
