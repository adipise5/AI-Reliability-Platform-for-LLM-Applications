from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from github_integration.infrastructure.db import Base

_TZDateTime = DateTime(timezone=True)


class CheckRunModel(Base):
    __tablename__ = "check_runs"
    __table_args__ = (
        Index("ix_check_runs_org_repo", "org_id", "repo"),
        Index("ix_check_runs_org_repo_sha", "org_id", "repo", "commit_sha"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    org_id: Mapped[uuid.UUID]
    repo: Mapped[str] = mapped_column(String(300))
    commit_sha: Mapped[str] = mapped_column(String(40))
    github_check_run_id: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(20))
    conclusion: Mapped[str | None] = mapped_column(String(20), default=None)
    run_id: Mapped[uuid.UUID | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(_TZDateTime)
    completed_at: Mapped[datetime | None] = mapped_column(_TZDateTime, default=None)
