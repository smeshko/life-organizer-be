"""backfill amount_eur for non-EUR transactions

Revision ID: b9d4e2a7c1f3
Revises: f82a429f3da9
Create Date: 2026-11-01 12:00:00.000000

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b9d4e2a7c1f3"
down_revision: Union[str, Sequence[str], None] = "f82a429f3da9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Rates are frozen here so the migration keeps its result if the app constants change.
BGN_PER_EUR_RATE = "1.95583"
USD_TO_EUR_RATE = "0.92"


def upgrade() -> None:
    """Recompute amount_eur for BGN and USD rows stored unconverted.

    A row is broken when amount_eur equals amount for a non-EUR currency. Other
    non-EUR codes convert 1:1 in the app, so they already hold the right value.
    """
    op.execute(
        sa.text(
            f"UPDATE budget.transactions SET amount_eur = ROUND(amount / {BGN_PER_EUR_RATE}, 2) "
            "WHERE currency = 'BGN' AND amount_eur = amount"
        )
    )
    op.execute(
        sa.text(
            f"UPDATE budget.transactions SET amount_eur = ROUND(amount * {USD_TO_EUR_RATE}, 2) "
            "WHERE currency = 'USD' AND amount_eur = amount"
        )
    )


def downgrade() -> None:
    """No-op: the backfill is a one-way data repair and the broken values are not restored."""
    pass
