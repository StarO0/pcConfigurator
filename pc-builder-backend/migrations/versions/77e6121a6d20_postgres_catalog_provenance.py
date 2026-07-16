"""PostgreSQL catalogue provenance and product gallery

Revision ID: 77e6121a6d20
Revises: 5bd7a3e9c210
Create Date: 2026-07-15 14:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "77e6121a6d20"
down_revision: Union[str, Sequence[str], None] = "5bd7a3e9c210"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("products", sa.Column("gallery_urls", sa.JSON(), nullable=True))
    op.add_column("products", sa.Column("canonical_source", sa.String(length=50), nullable=True))
    op.add_column("products", sa.Column("canonical_id", sa.String(length=120), nullable=True))
    op.add_column("products", sa.Column("source_url", sa.String(length=1000), nullable=True))
    op.execute("UPDATE products SET gallery_urls = '[]' WHERE gallery_urls IS NULL")
    op.alter_column("products", "gallery_urls", nullable=False)
    op.create_index(
        "ix_products_canonical_source_id",
        "products",
        ["canonical_source", "canonical_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_products_canonical_source_id", table_name="products")
    op.drop_column("products", "source_url")
    op.drop_column("products", "canonical_id")
    op.drop_column("products", "canonical_source")
    op.drop_column("products", "gallery_urls")
