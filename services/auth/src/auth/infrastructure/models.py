"""SQLAlchemy ORM models — the only place that knows about table/column
shapes. Repositories translate between these and the domain dataclasses in
`domain/entities.py`; nothing outside this module imports these classes.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auth.infrastructure.db import Base

_TZDateTime = DateTime(timezone=True)


class OrgModel(Base):
    __tablename__ = "orgs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(_TZDateTime)

    users: Mapped[list[UserModel]] = relationship(back_populates="org")
    api_keys: Mapped[list[ApiKeyModel]] = relationship(back_populates="org")


class UserModel(Base):
    __tablename__ = "users"
    __table_args__ = (Index("ix_users_email", "email", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orgs.id"))
    email: Mapped[str] = mapped_column(String(320))
    password_hash: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(_TZDateTime)

    org: Mapped[OrgModel] = relationship(back_populates="users")


class ApiKeyModel(Base):
    __tablename__ = "api_keys"
    __table_args__ = (Index("ix_api_keys_prefix", "prefix", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orgs.id"))
    name: Mapped[str] = mapped_column(String(200))
    prefix: Mapped[str] = mapped_column(String(64))
    secret_hash: Mapped[str] = mapped_column(String(200))
    scopes: Mapped[list[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(_TZDateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(_TZDateTime)

    org: Mapped[OrgModel] = relationship(back_populates="api_keys")
