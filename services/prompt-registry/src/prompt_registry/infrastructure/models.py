"""SQLAlchemy ORM models. Repositories translate between these and the
domain dataclasses in `domain/entities.py`."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from prompt_registry.infrastructure.db import Base

_TZDateTime = DateTime(timezone=True)


class PromptModel(Base):
    __tablename__ = "prompts"
    __table_args__ = (Index("ix_prompts_org_name", "org_id", "name", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    org_id: Mapped[uuid.UUID]
    name: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(_TZDateTime)

    versions: Mapped[list[PromptVersionModel]] = relationship(back_populates="prompt")


class PromptVersionModel(Base):
    __tablename__ = "prompt_versions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    prompt_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("prompts.id"))
    template: Mapped[str] = mapped_column(Text)
    variables_schema: Mapped[dict[str, Any]] = mapped_column(JSON)
    semver_tag: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(_TZDateTime)

    prompt: Mapped[PromptModel] = relationship(back_populates="versions")


class PromotionEventModel(Base):
    __tablename__ = "promotion_events"
    __table_args__ = (Index("ix_promotion_events_lookup", "prompt_id", "environment", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    prompt_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("prompts.id"))
    version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("prompt_versions.id"))
    environment: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(_TZDateTime)
