from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from cost_analytics.infrastructure.db import Base

_TZDateTime = DateTime(timezone=True)


class UsageRecordModel(Base):
    __tablename__ = "usage_records"
    __table_args__ = (Index("ix_usage_records_org_created", "org_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    org_id: Mapped[uuid.UUID]
    provider: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(200))
    prompt_tokens: Mapped[int]
    completion_tokens: Mapped[int]
    cost_usd: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(_TZDateTime)


class BudgetModel(Base):
    __tablename__ = "budgets"
    __table_args__ = (Index("ix_budgets_org_id", "org_id", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    org_id: Mapped[uuid.UUID]
    monthly_limit_usd: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(_TZDateTime)
    updated_at: Mapped[datetime] = mapped_column(_TZDateTime)
