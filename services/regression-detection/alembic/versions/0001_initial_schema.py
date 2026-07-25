"""initial regression schema: baselines, gate_decisions

Revision ID: 0001
Revises:
Create Date: 2026-07-25
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
    op.execute("CREATE SCHEMA IF NOT EXISTS regression")

    op.create_table(
        "baselines",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("prompt_id", sa.Uuid(), nullable=False),
        sa.Column("mean_score", sa.Float(), nullable=False),
        sa.Column("stddev_score", sa.Float(), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        schema="regression",
    )
    op.create_index(
        "ix_baselines_org_prompt",
        "baselines",
        ["org_id", "prompt_id"],
        unique=True,
        schema="regression",
    )

    op.create_table(
        "gate_decisions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("prompt_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("observed_score", sa.Float(), nullable=False),
        sa.Column("baseline_mean", sa.Float(), nullable=False),
        sa.Column("baseline_stddev", sa.Float(), nullable=False),
        sa.Column("verdict", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        schema="regression",
    )
    op.create_index(
        "ix_gate_decisions_run_id", "gate_decisions", ["run_id"], schema="regression"
    )


def downgrade() -> None:
    op.drop_index("ix_gate_decisions_run_id", table_name="gate_decisions", schema="regression")
    op.drop_table("gate_decisions", schema="regression")
    op.drop_index("ix_baselines_org_prompt", table_name="baselines", schema="regression")
    op.drop_table("baselines", schema="regression")
    op.execute("DROP SCHEMA IF EXISTS regression")
