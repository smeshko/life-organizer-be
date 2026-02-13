"""create feedback schema and misclassifications table

Revision ID: b4f1c8e23a67
Revises: a7c2e5d91b3f
Create Date: 2026-02-13

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b4f1c8e23a67"
down_revision: Union[str, Sequence[str], None] = "a7c2e5d91b3f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create feedback schema and misclassifications table."""
    # Create feedback schema first
    op.execute("CREATE SCHEMA IF NOT EXISTS feedback")

    # Create misclassifications table in feedback schema
    op.create_table(
        "misclassifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("original_input", sa.Text(), nullable=False),
        sa.Column("wrong_category", sa.String(length=50), nullable=False),
        sa.Column("correct_category", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="feedback",
    )


def downgrade() -> None:
    """Drop misclassifications table and feedback schema."""
    # Drop table
    op.drop_table("misclassifications", schema="feedback")

    # Drop schema
    op.execute("DROP SCHEMA IF EXISTS feedback CASCADE")
