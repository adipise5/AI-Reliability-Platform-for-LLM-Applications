from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from regression_detection.infrastructure.db import Base

_TZDateTime = DateTime(timezone=True)


class BaselineModel(Base):
    __tablename__ = "baselines"
    __table_args__ = (Index("ix_baselines_org_prompt", "org_id", "prompt_id", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    org_id: Mapped[uuid.UUID]
    prompt_id: Mapped[uuid.UUID]
    mean_score: Mapped[float] = mapped_column(Float)
    stddev_score: Mapped[float] = mapped_column(Float)
    sample_size: Mapped[int]
    updated_at: Mapped[datetime] = mapped_column(_TZDateTime)


class GateDecisionModel(Base):
    __tablename__ = "gate_decisions"
    __table_args__ = (Index("ix_gate_decisions_run_id", "run_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    org_id: Mapped[uuid.UUID]
    prompt_id: Mapped[uuid.UUID]
    run_id: Mapped[uuid.UUID]
    observed_score: Mapped[float] = mapped_column(Float)
    baseline_mean: Mapped[float] = mapped_column(Float)
    baseline_stddev: Mapped[float] = mapped_column(Float)
    verdict: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(_TZDateTime)
