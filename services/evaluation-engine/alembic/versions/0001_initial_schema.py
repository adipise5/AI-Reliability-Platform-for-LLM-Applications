"""initial eval_engine schema: eval_runs, run_item_results

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
    op.execute("CREATE SCHEMA IF NOT EXISTS eval_engine")

    op.create_table(
        "eval_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("prompt_id", sa.Uuid(), nullable=False),
        sa.Column("prompt_version_id", sa.Uuid(), nullable=False),
        sa.Column("dataset_id", sa.Uuid(), nullable=False),
        sa.Column("dataset_version", sa.Integer(), nullable=True),
        sa.Column("model", sa.String(200), nullable=False),
        sa.Column("scorer_names", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=False),
        sa.Column("max_tokens", sa.Integer(), nullable=True),
        sa.Column("aggregate_score", sa.Float(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        schema="eval_engine",
    )
    op.create_index("ix_eval_runs_org_id", "eval_runs", ["org_id"], schema="eval_engine")

    op.create_table(
        "run_item_results",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("run_id", sa.Uuid(), sa.ForeignKey("eval_engine.eval_runs.id"), nullable=False),
        sa.Column("dataset_item_id", sa.Uuid(), nullable=False),
        sa.Column("output", sa.Text(), nullable=False),
        sa.Column("latency_ms", sa.Float(), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False),
        sa.Column("completion_tokens", sa.Integer(), nullable=False),
        sa.Column("scores", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        schema="eval_engine",
    )
    op.create_index(
        "ix_run_item_results_run_id", "run_item_results", ["run_id"], schema="eval_engine"
    )


def downgrade() -> None:
    op.drop_index("ix_run_item_results_run_id", table_name="run_item_results", schema="eval_engine")
    op.drop_table("run_item_results", schema="eval_engine")
    op.drop_index("ix_eval_runs_org_id", table_name="eval_runs", schema="eval_engine")
    op.drop_table("eval_runs", schema="eval_engine")
    op.execute("DROP SCHEMA IF EXISTS eval_engine")
