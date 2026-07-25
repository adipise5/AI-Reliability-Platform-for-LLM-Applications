"""initial notifications schema: channels, notifications

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
    op.execute("CREATE SCHEMA IF NOT EXISTS notifications")

    op.create_table(
        "channels",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("channel_type", sa.String(20), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("target", sa.String(2000), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        schema="notifications",
    )
    op.create_index("ix_channels_org_id", "channels", ["org_id"], schema="notifications")

    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column(
            "channel_id",
            sa.Uuid(),
            sa.ForeignKey("notifications.channels.id"),
            nullable=False,
        ),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("error_message", sa.String(2000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        schema="notifications",
    )
    op.create_index(
        "ix_notifications_org_channel",
        "notifications",
        ["org_id", "channel_id"],
        schema="notifications",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_notifications_org_channel", table_name="notifications", schema="notifications"
    )
    op.drop_table("notifications", schema="notifications")
    op.drop_index("ix_channels_org_id", table_name="channels", schema="notifications")
    op.drop_table("channels", schema="notifications")
    op.execute("DROP SCHEMA IF EXISTS notifications")
