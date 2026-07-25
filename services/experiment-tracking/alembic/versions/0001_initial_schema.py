"""initial experiment_tracking schema: experiments

Revision ID: 0001
Revises:
Create Date: 2026-07-26
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS experiment_tracking")

    op.create_table(
        "experiments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("run_ids", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        schema="experiment_tracking",
    )
    op.create_index(
        "ix_experiments_org_name",
        "experiments",
        ["org_id", "name"],
        unique=True,
        schema="experiment_tracking",
    )


def downgrade() -> None:
    op.drop_index("ix_experiments_org_name", table_name="experiments", schema="experiment_tracking")
    op.drop_table("experiments", schema="experiment_tracking")
    op.execute("DROP SCHEMA IF EXISTS experiment_tracking")
