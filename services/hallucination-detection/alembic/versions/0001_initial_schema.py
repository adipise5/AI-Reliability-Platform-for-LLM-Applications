"""initial hallucination schema: faithfulness_checks

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
    op.execute("CREATE SCHEMA IF NOT EXISTS hallucination")

    op.create_table(
        "faithfulness_checks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("response", sa.Text(), nullable=False),
        sa.Column("context", sa.Text(), nullable=False),
        sa.Column("claims", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        schema="hallucination",
    )
    op.create_index(
        "ix_faithfulness_checks_org_id", "faithfulness_checks", ["org_id"], schema="hallucination"
    )


def downgrade() -> None:
    op.drop_index(
        "ix_faithfulness_checks_org_id", table_name="faithfulness_checks", schema="hallucination"
    )
    op.drop_table("faithfulness_checks", schema="hallucination")
    op.execute("DROP SCHEMA IF EXISTS hallucination")
