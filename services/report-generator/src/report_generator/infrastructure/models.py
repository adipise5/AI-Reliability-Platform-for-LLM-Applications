from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from report_generator.infrastructure.db import Base

_TZDateTime = DateTime(timezone=True)


class ReportModel(Base):
    __tablename__ = "reports"
    __table_args__ = (Index("ix_reports_org_experiment", "org_id", "experiment_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    org_id: Mapped[uuid.UUID]
    experiment_id: Mapped[uuid.UUID]
    format: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20))
    content: Mapped[bytes | None] = mapped_column(LargeBinary, default=None)
    error_message: Mapped[str | None] = mapped_column(String(2000), default=None)
    created_at: Mapped[datetime] = mapped_column(_TZDateTime)
    completed_at: Mapped[datetime | None] = mapped_column(_TZDateTime, default=None)
