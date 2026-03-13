"""merge migration heads

Revision ID: f82a429f3da9
Revises: d7a3f1b52e94, e1a4b6c83d29
Create Date: 2026-03-11 11:38:10.950843

"""

from collections.abc import Sequence
from typing import Union

# revision identifiers, used by Alembic.
revision: str = "f82a429f3da9"
down_revision: Union[str, Sequence[str], None] = ("d7a3f1b52e94", "e1a4b6c83d29")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
