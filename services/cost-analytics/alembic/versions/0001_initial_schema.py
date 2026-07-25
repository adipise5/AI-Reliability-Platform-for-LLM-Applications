"""initial cost_analytics schema: usage_records, budgets

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
    op.execute("CREATE SCHEMA IF NOT EXISTS cost_analytics")

    op.create_table(
        "usage_records",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model", sa.String(200), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False),
        sa.Column("completion_tokens", sa.Integer(), nullable=False),
        sa.Column("cost_usd", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        schema="cost_analytics",
    )
    op.create_index(
        "ix_usage_records_org_created",
        "usage_records",
        ["org_id", "created_at"],
        schema="cost_analytics",
    )

    op.create_table(
        "budgets",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("monthly_limit_usd", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        schema="cost_analytics",
    )
    op.create_index(
        "ix_budgets_org_id", "budgets", ["org_id"], unique=True, schema="cost_analytics"
    )


def downgrade() -> None:
    op.drop_index("ix_budgets_org_id", table_name="budgets", schema="cost_analytics")
    op.drop_table("budgets", schema="cost_analytics")
    op.drop_index("ix_usage_records_org_created", table_name="usage_records", schema="cost_analytics")
    op.drop_table("usage_records", schema="cost_analytics")
    op.execute("DROP SCHEMA IF EXISTS cost_analytics")
