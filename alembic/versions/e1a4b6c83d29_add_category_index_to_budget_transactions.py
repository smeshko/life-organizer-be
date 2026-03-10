"""add_category_index_to_budget_transactions

Revision ID: e1a4b6c83d29
Revises: c5d2f7a41e89
Create Date: 2026-03-10

"""

from collections.abc import Sequence
from typing import Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e1a4b6c83d29"
down_revision: Union[str, Sequence[str], None] = "c5d2f7a41e89"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add index on category column for faster transaction queries."""
    op.create_index(
        "ix_budget_transactions_category",
        "transactions",
        ["category"],
        schema="budget",
    )


def downgrade() -> None:
    """Remove category index."""
    op.drop_index(
        "ix_budget_transactions_category",
        table_name="transactions",
        schema="budget",
    )
