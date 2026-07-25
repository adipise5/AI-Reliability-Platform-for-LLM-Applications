"""initial github schema: check_runs

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
    op.execute("CREATE SCHEMA IF NOT EXISTS github")

    op.create_table(
        "check_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("repo", sa.String(300), nullable=False),
        sa.Column("commit_sha", sa.String(40), nullable=False),
        sa.Column("github_check_run_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("conclusion", sa.String(20), nullable=True),
        sa.Column("run_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        schema="github",
    )
    op.create_index(
        "ix_check_runs_org_repo", "check_runs", ["org_id", "repo"], schema="github"
    )
    op.create_index(
        "ix_check_runs_org_repo_sha",
        "check_runs",
        ["org_id", "repo", "commit_sha"],
        schema="github",
    )


def downgrade() -> None:
    op.drop_index("ix_check_runs_org_repo_sha", table_name="check_runs", schema="github")
    op.drop_index("ix_check_runs_org_repo", table_name="check_runs", schema="github")
    op.drop_table("check_runs", schema="github")
    op.execute("DROP SCHEMA IF EXISTS github")
