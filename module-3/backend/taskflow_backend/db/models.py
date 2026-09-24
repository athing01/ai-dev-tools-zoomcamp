"""SQLAlchemy ORM model for the ``tasks`` table.

The ``tasks`` table preserves the baseline logical contract:

* ``id`` — primary key, autoincrement integer.
* ``title`` — NOT NULL string.
* ``description`` — NOT NULL string, default ``""``.
* ``status`` — NOT NULL, uses the native PostgreSQL ``task_status``
  enum with exactly ``todo``, ``in_progress``, ``done``.
* ``created_at`` / ``updated_at`` — timezone-aware UTC timestamps;
  ``updated_at`` advances on update (app-managed, per A-10).

This model is imported by the repository, the Alembic env, and the
app's metadata so that Alembic can detect the schema in Phase 2.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum as SAEnum, Integer, String, func

from .base import Base
from taskflow_backend.domain.task import Task, TaskStatus


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TaskModel(Base):
    """ORM mapping for the ``tasks`` table."""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False, default="")
    status = Column(
        SAEnum(TaskStatus, values_callable=lambda obj: [e.value for e in obj], name="task_status"),
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


def row_to_task(row: TaskModel) -> Task:
    """Convert a DB row to a domain :class:`Task` dataclass.

    Enforces UTC awareness so that consumers always see timezone-aware
    values (matching the existing SQLite-based convention).
    """
    def _ensure_tz(dt: datetime | None) -> datetime | None:
        if dt and dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    return Task(
        id=row.id,
        title=row.title,
        description=row.description,
        status=row.status,
        created_at=_ensure_tz(row.created_at),
        updated_at=_ensure_tz(row.updated_at),
    )