"""Baseline for the existing Supabase schema.

The database predates Alembic and is the source of truth. This revision is
intentionally empty; record it with `alembic stamp head`, not `upgrade`.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20261027_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
