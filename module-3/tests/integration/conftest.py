"""Shared fixtures for the P3 PostgreSQL integration test suite.

Locked fixture lifecycle:
  TEST_DATABASE_URL
    -> verify PostgreSQL is reachable (fail loudly)
    -> alembic upgrade head
    -> clear task data between tests
    -> create SqlAlchemyTaskRepository(TEST_DATABASE_URL)
    -> create_app(repo=...)
    -> execute tests
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Generator

import pytest
import sqlalchemy
from sqlalchemy import text

# Ensure taskflow_backend is importable from tests/integration/
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from taskflow_backend.app import create_app  # noqa: E402
from taskflow_backend.repositories.sqlalchemy import SqlAlchemyTaskRepository  # noqa: E402


def _get_test_database_url() -> str:
    """Return TEST_DATABASE_URL or skip with a clear diagnostic."""
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.fail(
            "TEST_DATABASE_URL is not set. "
            "Set it to a reachable PostgreSQL URL, e.g. "
            "postgresql+psycopg://postgres:test@127.0.0.1:55002/taskflow_test"
        )
    return url


def _wait_for_postgres(url: str, timeout: int = 30) -> None:
    """Block until PostgreSQL accepts connections or raise TimeoutError."""
    deadline = time.time() + timeout
    last_err: Exception | None = None
    while time.time() < deadline:
        try:
            engine = sqlalchemy.create_engine(url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except Exception as exc:
            last_err = exc
            time.sleep(0.5)
    raise TimeoutError(
        f"PostgreSQL unreachable at {url!r} after {timeout}s: {last_err}"
    )


def _run_alembic_upgrade(url: str) -> None:
    """Run alembic upgrade head against the test database."""
    env = os.environ.copy()
    env["DATABASE_URL"] = url
    backend_dir = str(Path(__file__).resolve().parent.parent.parent / "backend")
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=backend_dir,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"alembic upgrade head failed:\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


def _clear_tasks(url: str) -> None:
    """Delete all rows from the tasks table for test isolation."""
    engine = sqlalchemy.create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM tasks"))


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """Verify PostgreSQL is reachable and return the test database URL."""
    url = _get_test_database_url()
    _wait_for_postgres(url)
    return url


@pytest.fixture(scope="session")
def alembic_migrated(test_database_url: str) -> str:
    """Run Alembic upgrade head once per test session."""
    _run_alembic_upgrade(test_database_url)
    return test_database_url


@pytest.fixture(autouse=True)
def clear_task_data(alembic_migrated: str) -> Generator[str, None, None]:
    """Clear task data before and after each test for isolation."""
    url = alembic_migrated
    _clear_tasks(url)
    yield url
    _clear_tasks(url)


@pytest.fixture
def repo(clear_task_data: str) -> Generator[SqlAlchemyTaskRepository, None, None]:
    """Create a SQLAlchemy repository backed by the test database."""
    yield SqlAlchemyTaskRepository(clear_task_data)


@pytest.fixture
def app(repo: SqlAlchemyTaskRepository):
    """Create the FastAPI app wired with the SQLAlchemy repository."""
    return create_app(repo=repo)
