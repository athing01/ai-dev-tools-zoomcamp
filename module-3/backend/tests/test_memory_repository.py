import pytest
from datetime import datetime, timezone, timedelta
from taskflow_backend.domain.task import TaskStatus
from taskflow_backend.repositories.memory import InMemoryTaskRepository

def test_empty_repository():
    repo = InMemoryTaskRepository()
    assert repo.list() == []

def test_create_one_task():
    repo = InMemoryTaskRepository()
    task = repo.create("Title", "Desc", TaskStatus.TODO)

    assert task.id == 1
    assert task.title == "Title"
    assert task.description == "Desc"
    assert task.status == TaskStatus.TODO
    assert task.created_at.tzinfo == timezone.utc
    assert task.updated_at == task.created_at
    assert repo.list() == [task]

def test_create_multiple_tasks_unique_ids():
    repo = InMemoryTaskRepository()
    t1 = repo.create("T1", "D1", TaskStatus.TODO)
    t2 = repo.create("T2", "D2", TaskStatus.IN_PROGRESS)

    assert t1.id == 1
    assert t2.id == 2
    assert len(repo.list()) == 2

def test_update_title():
    repo = InMemoryTaskRepository()
    t = repo.create("Old", "Desc", TaskStatus.TODO)
    updated = repo.update(t.id, title="New")

    assert updated is not None
    assert updated.title == "New"
    assert updated.description == "Desc"
    assert updated.status == TaskStatus.TODO
    assert updated.updated_at >= t.updated_at
    assert updated.created_at == t.created_at

def test_update_description():
    repo = InMemoryTaskRepository()
    t = repo.create("Title", "Old", TaskStatus.TODO)
    updated = repo.update(t.id, description="New")

    assert updated.description == "New"
    assert updated.title == "Title"

def test_update_status():
    repo = InMemoryTaskRepository()
    t = repo.create("Title", "Desc", TaskStatus.TODO)
    updated = repo.update(t.id, status=TaskStatus.DONE)

    assert updated.status == TaskStatus.DONE
    assert updated.title == "Title"

def test_update_partial_preserves_fields():
    repo = InMemoryTaskRepository()
    t = repo.create("Title", "Desc", TaskStatus.TODO)
    updated = repo.update(t.id, title="New Title")

    assert updated.title == "New Title"
    assert updated.description == "Desc"
    assert updated.status == TaskStatus.TODO

def test_update_refreshes_updated_at():
    repo = InMemoryTaskRepository()
    t = repo.create("Title", "Desc", TaskStatus.TODO)

    import time
    time.sleep(0.01)

    updated = repo.update(t.id, title="New")
    assert updated.updated_at > t.updated_at
    assert updated.created_at == t.created_at

def test_update_missing_task():
    repo = InMemoryTaskRepository()
    result = repo.update(999, title="New")
    assert result is None

def test_delete_existing_task():
    repo = InMemoryTaskRepository()
    t = repo.create("Title", "Desc", TaskStatus.TODO)

    assert repo.delete(t.id) is True
    assert len(repo.list()) == 0

def test_delete_missing_task():
    repo = InMemoryTaskRepository()
    assert repo.delete(999) is False
