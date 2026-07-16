"""catalog sources and offer metadata

Revision ID: c3a0b66f30f1
Revises: 9f21c4b7a812
Create Date: 2026-07-14 17:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c3a0b66f30f1"
down_revision: Union[str, Sequence[str], None] = "9f21c4b7a812"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "offers",
        sa.Column("source_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )


def downgrade() -> None:
    op.drop_column("offers", "source_metadata")
