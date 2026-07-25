"""SQLAlchemy ORM model. `id` here is the row's own identity (a UUID),
separate from OTel's `trace_id`/`span_id` — see domain/entities.py."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from trace_collector.infrastructure.db import Base

_TZDateTime = DateTime(timezone=True)


class SpanModel(Base):
    __tablename__ = "spans"
    __table_args__ = (
        Index("ix_spans_trace_id", "trace_id"),
        Index("ix_spans_end_time", "end_time"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    trace_id: Mapped[str] = mapped_column(String(32))
    span_id: Mapped[str] = mapped_column(String(16))
    parent_span_id: Mapped[str | None] = mapped_column(String(16))
    name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(10))
    start_time: Mapped[datetime] = mapped_column(_TZDateTime)
    end_time: Mapped[datetime] = mapped_column(_TZDateTime)
    attributes: Mapped[dict[str, Any]] = mapped_column(JSON)
