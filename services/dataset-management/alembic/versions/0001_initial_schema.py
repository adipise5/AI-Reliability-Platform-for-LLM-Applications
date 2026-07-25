"""initial dataset_mgmt schema: datasets, dataset_items

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
    op.execute("CREATE SCHEMA IF NOT EXISTS dataset_mgmt")

    op.create_table(
        "datasets",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("current_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        schema="dataset_mgmt",
    )
    op.create_index(
        "ix_datasets_org_name", "datasets", ["org_id", "name"], unique=True, schema="dataset_mgmt"
    )

    op.create_table(
        "dataset_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("dataset_id", sa.Uuid(), sa.ForeignKey("dataset_mgmt.datasets.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("input", sa.JSON(), nullable=False),
        sa.Column("expected_output", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        schema="dataset_mgmt",
    )
    op.create_index(
        "ix_dataset_items_version",
        "dataset_items",
        ["dataset_id", "version"],
        schema="dataset_mgmt",
    )


def downgrade() -> None:
    op.drop_index("ix_dataset_items_version", table_name="dataset_items", schema="dataset_mgmt")
    op.drop_table("dataset_items", schema="dataset_mgmt")
    op.drop_index("ix_datasets_org_name", table_name="datasets", schema="dataset_mgmt")
    op.drop_table("datasets", schema="dataset_mgmt")
    op.execute("DROP SCHEMA IF EXISTS dataset_mgmt")
