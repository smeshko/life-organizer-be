"""create budget schema and transactions table

Revision ID: d8b5de9e7c94
Revises:
Create Date: 2025-11-10 16:51:46.325079

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d8b5de9e7c94"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create budget schema and transactions table."""
    # Create budget schema first
    op.execute("CREATE SCHEMA IF NOT EXISTS budget")

    # Create transactions table in budget schema
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="BGN"),
        sa.Column("amount_bgn", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("transaction_type", sa.String(length=20), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
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
        sa.CheckConstraint("amount > 0", name="check_amount_positive"),
        sa.CheckConstraint("amount_bgn > 0", name="check_amount_bgn_positive"),
        sa.PrimaryKeyConstraint("id"),
        schema="budget",
    )

    # Create indexes
    op.create_index(
        "ix_budget_transactions_date", "transactions", ["date"], unique=False, schema="budget"
    )
    op.create_index(
        "ix_budget_transactions_type",
        "transactions",
        ["transaction_type"],
        unique=False,
        schema="budget",
    )


def downgrade() -> None:
    """Drop transactions table and budget schema."""
    # Drop indexes
    op.drop_index("ix_budget_transactions_type", table_name="transactions", schema="budget")
    op.drop_index("ix_budget_transactions_date", table_name="transactions", schema="budget")

    # Drop table
    op.drop_table("transactions", schema="budget")

    # Drop schema
    op.execute("DROP SCHEMA IF EXISTS budget CASCADE")
