"""workload profiles and performance engine

Revision ID: 9f21c4b7a812
Revises: f3aec9117641
Create Date: 2026-07-13 02:30:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "9f21c4b7a812"
down_revision: Union[str, Sequence[str], None] = "f3aec9117641"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workload_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("names", sa.JSON(), nullable=False),
        sa.Column("kind", sa.String(length=30), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=False),
        sa.Column("lower_is_better", sa.Boolean(), nullable=False),
        sa.Column("accelerator", sa.String(length=20), nullable=False),
        sa.Column("default_resolution", sa.String(length=30), nullable=True),
        sa.Column("settings", sa.String(length=80), nullable=True),
        sa.Column("cpu_weight", sa.Float(), nullable=False),
        sa.Column("gpu_weight", sa.Float(), nullable=False),
        sa.Column("ram_requirement_gb", sa.Integer(), nullable=False),
        sa.Column("source_url", sa.String(length=1000), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_workload_profiles_slug"),
        "workload_profiles",
        ["slug"],
        unique=True,
    )
    op.create_index(
        op.f("ix_workload_profiles_kind"),
        "workload_profiles",
        ["kind"],
        unique=False,
    )
    op.create_index(
        op.f("ix_workload_profiles_is_active"),
        "workload_profiles",
        ["is_active"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_workload_profiles_is_active"), table_name="workload_profiles")
    op.drop_index(op.f("ix_workload_profiles_kind"), table_name="workload_profiles")
    op.drop_index(op.f("ix_workload_profiles_slug"), table_name="workload_profiles")
    op.drop_table("workload_profiles")
