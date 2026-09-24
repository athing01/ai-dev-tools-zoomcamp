"""SQLAlchemy based repository for :class:`Task` objects.

This module implements ``SqlAlchemyTaskRepository`` which adheres to the
``TaskRepository`` Protocol defined in :mod:`taskflow_backend.domain.repositories`.

The repository uses a standard SQLAlchemy database connection (PostgreSQL,
SQLite in-memory, etc.). All operations are synchronous and a new
:class:`sqlalchemy.orm.Session` is created for each call to keep the APIs
stateless and straightforward.

The implementation mirrors the behaviour of the in‑memory repository:
* ``id`` is an autoincrement primary key.
* ``description`` defaults to ``""``.
* ``status`` values are stored as strings matching :class:`TaskStatus`.
* ``created_at`` and ``updated_at`` are timezone‑aware UTC timestamps.

The tests use a SQLite in‑memory database so that no global or shared state
affects other tests (see :mod:`tests.test_sqlalchemy_repository`).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..db.base import Base
from ..db.models import TaskModel, row_to_task
from ..domain.task import TaskStatus
from ..domain.repositories import TaskRepository


class SqlAlchemyTaskRepository(TaskRepository):
    """A commit‑per‑operation SQLAlchemy repository.

    Parameters
    ----------
    database_url:
        SQLAlchemy database connection URL (e.g., ``postgresql+psycopg://…``,
        ``sqlite:///:memory:``). Unit tests use ``sqlite:///:memory:``.
    """

    def __init__(self, database_url: str) -> None:
        self._engine = create_engine(database_url, echo=False, future=True)
        # NO BASE.METADATA.CREATE_ALL() HERE — production relies on Alembic
        self._Session = sessionmaker(bind=self._engine, future=True, expire_on_commit=False)

    # ---- Core CRUD methods ------------------------------------------------
    def list(self) -> List[Task]:
        with self._Session() as session:
            rows = session.query(TaskModel).order_by(TaskModel.id).all()
            return [row_to_task(r) for r in rows]

    def create(self, title: str, description: str, status: TaskStatus) -> Task:
        # ``now`` is a UTC‑aware timestamp.
        now = datetime.now(timezone.utc)
        new_row = TaskModel(
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
            return row_to_task(new_row)

    def update(self, task_id: int, **updates) -> Task | None:
        with self._Session() as session:
            row = session.get(TaskModel, task_id)
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
            return row_to_task(row)

    def delete(self, task_id: int) -> bool:
        with self._Session() as session:
            row = session.get(TaskModel, task_id)
            if row is None:
                return False
            session.delete(row)
            session.commit()
            return True
