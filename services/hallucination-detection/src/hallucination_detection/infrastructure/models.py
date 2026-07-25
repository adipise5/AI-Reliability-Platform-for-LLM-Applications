"""SQLAlchemy ORM model. `claims` is embedded JSON — see
evaluation-engine's models.py for the same "small, always-fetched-together
list, no independent lifecycle" reasoning; this deliberately doesn't
split into separate `claim_extractions`/`evidence_spans` tables."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from hallucination_detection.infrastructure.db import Base

_TZDateTime = DateTime(timezone=True)


class FaithfulnessCheckModel(Base):
    __tablename__ = "faithfulness_checks"
    __table_args__ = (Index("ix_faithfulness_checks_org_id", "org_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    org_id: Mapped[uuid.UUID]
    response: Mapped[str] = mapped_column(Text)
    context: Mapped[str] = mapped_column(Text)
    claims: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(_TZDateTime)
