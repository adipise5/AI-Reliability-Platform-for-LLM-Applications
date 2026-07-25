"""SQLAlchemy ORM models. `scores` is embedded JSON on the item-result row
rather than a separate normalized table — a run item's scores are a small,
always-fetched-together list with no independent lifecycle, so a join
table would only add query complexity for no real benefit."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from evaluation_engine.infrastructure.db import Base

_TZDateTime = DateTime(timezone=True)


class EvalRunModel(Base):
    __tablename__ = "eval_runs"
    __table_args__ = (Index("ix_eval_runs_org_id", "org_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    org_id: Mapped[uuid.UUID]
    prompt_id: Mapped[uuid.UUID]
    prompt_version_id: Mapped[uuid.UUID]
    dataset_id: Mapped[uuid.UUID]
    dataset_version: Mapped[int | None]
    model: Mapped[str] = mapped_column(String(200))
    scorer_names: Mapped[list[str]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20))
    temperature: Mapped[float] = mapped_column(Float)
    max_tokens: Mapped[int | None]
    aggregate_score: Mapped[float | None] = mapped_column(Float)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(_TZDateTime)
    completed_at: Mapped[datetime | None] = mapped_column(_TZDateTime)


class RunItemResultModel(Base):
    __tablename__ = "run_item_results"
    __table_args__ = (Index("ix_run_item_results_run_id", "run_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("eval_runs.id"))
    dataset_item_id: Mapped[uuid.UUID]
    output: Mapped[str] = mapped_column(Text)
    latency_ms: Mapped[float] = mapped_column(Float)
    prompt_tokens: Mapped[int]
    completion_tokens: Mapped[int]
    scores: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(_TZDateTime)
