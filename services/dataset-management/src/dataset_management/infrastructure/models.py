"""SQLAlchemy ORM models. Repositories translate between these and the
domain dataclasses in `domain/entities.py`."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dataset_management.infrastructure.db import Base

_TZDateTime = DateTime(timezone=True)


class DatasetModel(Base):
    __tablename__ = "datasets"
    __table_args__ = (Index("ix_datasets_org_name", "org_id", "name", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    org_id: Mapped[uuid.UUID]
    name: Mapped[str] = mapped_column(String(200))
    current_version: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(_TZDateTime)

    items: Mapped[list[DatasetItemModel]] = relationship(back_populates="dataset")


class DatasetItemModel(Base):
    __tablename__ = "dataset_items"
    __table_args__ = (Index("ix_dataset_items_version", "dataset_id", "version"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    dataset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("datasets.id"))
    version: Mapped[int]
    input: Mapped[dict[str, Any]] = mapped_column(JSON)
    expected_output: Mapped[Any] = mapped_column(JSON, nullable=True)
    # Named `item_metadata` on the Python side: `metadata` is reserved by
    # SQLAlchemy's DeclarativeBase (it's the class-level MetaData object).
    # The column itself is still named `metadata`.
    item_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON)
    created_at: Mapped[datetime] = mapped_column(_TZDateTime)

    dataset: Mapped[DatasetModel] = relationship(back_populates="items")
