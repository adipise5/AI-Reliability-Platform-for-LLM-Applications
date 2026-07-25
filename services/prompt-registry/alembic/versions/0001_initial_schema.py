"""initial prompt_registry schema: prompts, prompt_versions, promotion_events

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
    op.execute("CREATE SCHEMA IF NOT EXISTS prompt_registry")

    op.create_table(
        "prompts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        schema="prompt_registry",
    )
    op.create_index(
        "ix_prompts_org_name", "prompts", ["org_id", "name"], unique=True, schema="prompt_registry"
    )

    op.create_table(
        "prompt_versions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("prompt_id", sa.Uuid(), sa.ForeignKey("prompt_registry.prompts.id"), nullable=False),
        sa.Column("template", sa.Text(), nullable=False),
        sa.Column("variables_schema", sa.JSON(), nullable=False),
        sa.Column("semver_tag", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        schema="prompt_registry",
    )

    op.create_table(
        "promotion_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("prompt_id", sa.Uuid(), sa.ForeignKey("prompt_registry.prompts.id"), nullable=False),
        sa.Column(
            "version_id", sa.Uuid(), sa.ForeignKey("prompt_registry.prompt_versions.id"), nullable=False
        ),
        sa.Column("environment", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        schema="prompt_registry",
    )
    op.create_index(
        "ix_promotion_events_lookup",
        "promotion_events",
        ["prompt_id", "environment", "created_at"],
        schema="prompt_registry",
    )


def downgrade() -> None:
    op.drop_index("ix_promotion_events_lookup", table_name="promotion_events", schema="prompt_registry")
    op.drop_table("promotion_events", schema="prompt_registry")
    op.drop_table("prompt_versions", schema="prompt_registry")
    op.drop_index("ix_prompts_org_name", table_name="prompts", schema="prompt_registry")
    op.drop_table("prompts", schema="prompt_registry")
    op.execute("DROP SCHEMA IF EXISTS prompt_registry")
