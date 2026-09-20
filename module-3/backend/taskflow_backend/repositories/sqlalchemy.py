"""SQLAlchemy based repository for :class:`Task` objects.

This module implements ``SqlAlchemyTaskRepository`` which adheres to the
``TaskRepository`` Protocol defined in :mod:`taskflow_backend.domain.repositories`.

The repository uses a simple SQLite database.  All operations are synchronous
and a new :class:`sqlalchemy.orm.Session` is created for each call to keep the
APIs stateless and straightforward.

The implementation mirrors the behaviour of the in‑memory repository:
* ``id`` is an autoincrement primary key.
* ``description`` defaults to ``""``.
* ``status`` values are stored as strings matching :class:`TaskStatus`.
* ``created_at`` and ``updated_at`` are timezone‑aware UTC timestamps.

The tests use a temporary database file so that no global or shared state
affects other tests.
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SAEnum,
    Integer,
    String,
    create_engine,
    func,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from ..domain.task import Task, TaskStatus
from ..domain.repositories import TaskRepository

Base = declarative_base()


class _TaskRow(Base):
    """ORM mapping for the ``tasks`` table.

    The table mirrors the domain Task dataclass.  ``status`` is stored as a
    text column that accepts the three enum values defined in
    ``TaskStatus``.
    """

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False, default="")
    status = Column(
        SAEnum(TaskStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


def _row_to_task(row: _TaskRow) -> Task:
    """Convert a DB row to a domain Task dataclass.

    SQLite may return naive ``datetime`` objects.  We enforce UTC awareness
    so that consumers see timezone‑aware values.
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


class SqlAlchemyTaskRepository(TaskRepository):
    """A commit‑per‑operation SQLAlchemy repository.

    Parameters
    ----------
    db_path:
        Path to the SQLite database file.  If the file does not exist the
        repository will create it.  Tests use a temporary file.
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        # Default to in‑memory database if no path is supplied.
        if db_path is None:
            uri = "sqlite:///:memory:"
        else:
            # ``Path`` objects are accepted to ease test integration.
            path = Path(db_path)
            uri = f"sqlite:///{path.resolve()}"
        self._engine = create_engine(uri, echo=False, future=True)
        Base.metadata.create_all(self._engine)
        self._Session = sessionmaker(bind=self._engine, future=True, expire_on_commit=False)

    # ---- Utility helpers -------------------------------------------------
    def list(self) -> List[Task]:
        with self._Session() as session:
            rows = session.query(_TaskRow).order_by(_TaskRow.id).all()
            return [_row_to_task(r) for r in rows]

    def create(self, title: str, description: str, status: TaskStatus) -> Task:
        # ``now`` is a UTC‑aware timestamp.
        now = datetime.now(timezone.utc)
        new_row = _TaskRow(
            title=title,
            description=description,
            status=status,
            created_at=now,
            updated_at=now,
        )
        with self._Session() as session:
            session.add(new_row)
            session.commit()
            session.refresh(new_row)
            return _row_to_task(new_row)

    def update(self, task_id: int, **updates) -> Optional[Task]:
        with self._Session() as session:
            row = session.get(_TaskRow, task_id)
            if row is None:
                return None
            # Apply updates in-place; we explicitly set ``updated_at`` so
            # timestamps are timezone aware.
            if "title" in updates:
                row.title = updates["title"]
            if "description" in updates:
                row.description = updates["description"]
            if "status" in updates:
                row.status = updates["status"]
            row.updated_at = datetime.now(timezone.utc)
            session.commit()
            session.refresh(row)
            return _row_to_task(row)

    def delete(self, task_id: int) -> bool:
        with self._Session() as session:
            row = session.get(_TaskRow, task_id)
            if row is None:
                return False
            session.delete(row)
            session.commit()
            return True
