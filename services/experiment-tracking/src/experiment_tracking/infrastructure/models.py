"""SQLAlchemy ORM model. `run_ids` is embedded JSON — a small,
append-mostly list with no independent lifecycle of its own, same
reasoning as every other embedded-list column in this platform (see e.g.
evaluation-engine's `scores` column)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from experiment_tracking.infrastructure.db import Base

_TZDateTime = DateTime(timezone=True)


class ExperimentModel(Base):
    __tablename__ = "experiments"
    __table_args__ = (Index("ix_experiments_org_name", "org_id", "name", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    org_id: Mapped[uuid.UUID]
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    run_ids: Mapped[list[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(_TZDateTime)
