"""initial trace_collector schema: spans

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
    op.execute("CREATE SCHEMA IF NOT EXISTS trace_collector")

    op.create_table(
        "spans",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("trace_id", sa.String(32), nullable=False),
        sa.Column("span_id", sa.String(16), nullable=False),
        sa.Column("parent_span_id", sa.String(16), nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(10), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attributes", sa.JSON(), nullable=False),
        schema="trace_collector",
    )
    op.create_index("ix_spans_trace_id", "spans", ["trace_id"], schema="trace_collector")
    op.create_index("ix_spans_end_time", "spans", ["end_time"], schema="trace_collector")


def downgrade() -> None:
    op.drop_index("ix_spans_end_time", table_name="spans", schema="trace_collector")
    op.drop_index("ix_spans_trace_id", table_name="spans", schema="trace_collector")
    op.drop_table("spans", schema="trace_collector")
    op.execute("DROP SCHEMA IF EXISTS trace_collector")
