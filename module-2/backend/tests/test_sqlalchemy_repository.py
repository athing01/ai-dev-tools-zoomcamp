# Standard library imports – none required

import pytest
from datetime import timezone

from taskflow_backend.domain.task import TaskStatus
from taskflow_backend.repositories.sqlalchemy import SqlAlchemyTaskRepository


def _create_repo(tmp_path):
    # Use a file in the temporary directory so each test gets a fresh database
    db_file = tmp_path / "test.db"
    return SqlAlchemyTaskRepository(db_file)


def test_empty_repository(tmp_path):
    repo = _create_repo(tmp_path)
    assert repo.list() == []


def test_create_one_task(tmp_path):
    repo = _create_repo(tmp_path)
    task = repo.create("Title", "Desc", TaskStatus.TODO)
    assert task.id == 1
    assert task.title == "Title"
    assert task.description == "Desc"
    assert task.status == TaskStatus.TODO
    assert task.created_at.tzinfo == timezone.utc
    assert task.updated_at == task.created_at
    assert repo.list() == [task]


def test_create_multiple_tasks_unique_ids(tmp_path):
    repo = _create_repo(tmp_path)
    t1 = repo.create("T1", "D1", TaskStatus.TODO)
    t2 = repo.create("T2", "D2", TaskStatus.IN_PROGRESS)
    assert t1.id == 1
    assert t2.id == 2
    assert len(repo.list()) == 2


def test_update_title(tmp_path):
    repo = _create_repo(tmp_path)
    t = repo.create("Old", "Desc", TaskStatus.TODO)
    updated = repo.update(t.id, title="New")
    assert updated is not None
    assert updated.title == "New"
    assert updated.description == "Desc"
    assert updated.status == TaskStatus.TODO
    assert updated.updated_at >= t.updated_at
    assert updated.created_at == t.created_at


def test_update_description(tmp_path):
    repo = _create_repo(tmp_path)
    t = repo.create("Title", "Old", TaskStatus.TODO)
    updated = repo.update(t.id, description="New")
    assert updated.description == "New"
    assert updated.title == "Title"


def test_update_status(tmp_path):
    repo = _create_repo(tmp_path)
    t = repo.create("Title", "Desc", TaskStatus.TODO)
    updated = repo.update(t.id, status=TaskStatus.DONE)
    assert updated.status == TaskStatus.DONE
    assert updated.title == "Title"


def test_update_partial_preserves_fields(tmp_path):
    repo = _create_repo(tmp_path)
    t = repo.create("Title", "Desc", TaskStatus.TODO)
    updated = repo.update(t.id, title="New Title")
    assert updated.title == "New Title"
    assert updated.description == "Desc"
    assert updated.status == TaskStatus.TODO


def test_update_refreshes_updated_at(tmp_path):
    repo = _create_repo(tmp_path)
    t = repo.create("Title", "Desc", TaskStatus.TODO)
    import time
    time.sleep(0.01)
    updated = repo.update(t.id, title="New")
    assert updated.updated_at > t.updated_at
    assert updated.created_at == t.created_at


def test_update_missing_task(tmp_path):
    repo = _create_repo(tmp_path)
    result = repo.update(999, title="New")
    assert result is None


def test_delete_existing_task(tmp_path):
    repo = _create_repo(tmp_path)
    t = repo.create("Title", "Desc", TaskStatus.TODO)
    assert repo.delete(t.id) is True
    assert len(repo.list()) == 0


def test_delete_missing_task(tmp_path):
    repo = _create_repo(tmp_path)
    assert repo.delete(999) is False


@pytest.mark.parametrize(
    "status,expected_str",
    [
        (TaskStatus.TODO, "todo"),
        (TaskStatus.IN_PROGRESS, "in_progress"),
        (TaskStatus.DONE, "done"),
    ],
)
def test_status_persistence(tmp_path, status, expected_str):
    """Persisted status strings must match the exact contract value."""
    repo = _create_repo(tmp_path)
    repo.create("Title", "Desc", status)
    db_file = tmp_path / "test.db"
    from sqlalchemy import create_engine, text
    engine = create_engine(f"sqlite:///{db_file.resolve()}")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT status FROM tasks")).fetchone()
        assert result is not None
        stored_status = result[0]
        assert stored_status == expected_str
