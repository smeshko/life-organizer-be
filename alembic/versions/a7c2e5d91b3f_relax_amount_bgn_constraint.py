"""relax_amount_bgn_constraint

Revision ID: a7c2e5d91b3f
Revises: f3e9a3f86606
Create Date: 2026-01-19

Allow amount_bgn to be zero for new EUR transactions.
The amount_bgn field is now historical; new transactions use amount_eur.
"""

from collections.abc import Sequence
from typing import Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a7c2e5d91b3f"
down_revision: Union[str, Sequence[str], None] = "f3e9a3f86606"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Relax amount_bgn constraint to allow zero values."""
    op.drop_constraint(
        "check_amount_bgn_positive",
        "transactions",
        schema="budget",
        type_="check",
    )
    op.create_check_constraint(
        "check_amount_bgn_non_negative",
        "transactions",
        "amount_bgn >= 0",
        schema="budget",
    )


def downgrade() -> None:
    """Restore original strict positive constraint."""
    op.drop_constraint(
        "check_amount_bgn_non_negative",
        "transactions",
        schema="budget",
        type_="check",
    )
    op.create_check_constraint(
        "check_amount_bgn_positive",
        "transactions",
        "amount_bgn > 0",
        schema="budget",
    )
