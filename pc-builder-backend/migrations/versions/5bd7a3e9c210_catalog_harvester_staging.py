"""catalog harvester staging and crawl queue

Revision ID: 5bd7a3e9c210
Revises: c3a0b66f30f1
Create Date: 2026-07-14 18:30:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "5bd7a3e9c210"
down_revision: Union[str, Sequence[str], None] = "c3a0b66f30f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "crawl_queue",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("store_id", sa.Uuid(), nullable=False),
        sa.Column("url", sa.String(length=1500), nullable=False),
        sa.Column("url_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("not_before", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_http_status", sa.Integer(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("store_id", "url_hash", name="uq_crawl_store_url_hash"),
    )
    op.create_index("ix_crawl_queue_store_id", "crawl_queue", ["store_id"])
    op.create_index("ix_crawl_queue_status", "crawl_queue", ["status"])
    op.create_index(
        "ix_crawl_status_priority", "crawl_queue", ["status", "priority", "not_before"]
    )
    op.create_table(
        "harvest_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("store_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=True),
        sa.Column("source_url", sa.String(length=1500), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("normalized_payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("match_confidence", sa.Float(), nullable=False),
        sa.Column("match_method", sa.String(length=40), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("store_id", "fingerprint", name="uq_harvest_store_fingerprint"),
    )
    op.create_index("ix_harvest_records_store_id", "harvest_records", ["store_id"])
    op.create_index("ix_harvest_records_product_id", "harvest_records", ["product_id"])
    op.create_index("ix_harvest_records_external_id", "harvest_records", ["external_id"])
    op.create_index("ix_harvest_records_status", "harvest_records", ["status"])
    op.create_index(
        "ix_harvest_status_discovered", "harvest_records", ["status", "discovered_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_harvest_status_discovered", table_name="harvest_records")
    op.drop_index("ix_harvest_records_status", table_name="harvest_records")
    op.drop_index("ix_harvest_records_external_id", table_name="harvest_records")
    op.drop_index("ix_harvest_records_product_id", table_name="harvest_records")
    op.drop_index("ix_harvest_records_store_id", table_name="harvest_records")
    op.drop_table("harvest_records")
    op.drop_index("ix_crawl_status_priority", table_name="crawl_queue")
    op.drop_index("ix_crawl_queue_status", table_name="crawl_queue")
    op.drop_index("ix_crawl_queue_store_id", table_name="crawl_queue")
    op.drop_table("crawl_queue")
