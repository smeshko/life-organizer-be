"""add_amount_eur_column

Revision ID: f3e9a3f86606
Revises: d8b5de9e7c94
Create Date: 2025-12-30 23:13:38.372166

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f3e9a3f86606"
down_revision: Union[str, Sequence[str], None] = "d8b5de9e7c94"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add amount_eur column for EUR currency support."""
    op.add_column(
        "transactions",
        sa.Column("amount_eur", sa.Numeric(precision=10, scale=2), nullable=True),
        schema="budget",
    )


def downgrade() -> None:
    """Remove amount_eur column."""
    op.drop_column("transactions", "amount_eur", schema="budget")
