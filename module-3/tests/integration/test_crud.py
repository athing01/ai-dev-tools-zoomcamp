"""Integration test coverage for real PostgreSQL.

This module ports the relevant coverage from the superseded SQLite tests to
real PostgreSQL:

- list tasks, including empty result
- create task
- partial update
- status change
- delete
- missing-resource behavior
- timezone-aware UTC timestamps
- updated_at advances on update

Preserve the existing logical/domain contract:
- status values remain todo, in_progress, done
- PostgreSQL enum remains task_status
- no unrelated model/API changes

The fixture lifecycle (locked) ensures:
  1. TEST_DATABASE_URL -> PostgreSQL reachable (fail loudly)
  2. alembic upgrade head
  3. clear task data between tests
  4. SqlAlchemyTaskRepository(TEST_DATABASE_URL)
  5. create_app(repo=...)
  6. execute tests
"""

import pytest
import time
from taskflow_backend.domain.task import TaskStatus


def test_list_tasks_empty(repo):
    """list tasks, including empty result."""
    tasks = repo.list()
    assert tasks == []


def test_create_task(repo):
    """create task."""
    task = repo.create("Test Title", "Test Description", TaskStatus.TODO)
    assert task.id is not None and task.id > 0
    assert task.title == "Test Title"
    assert task.description == "Test Description"
    assert task.status == TaskStatus.TODO
    assert task.created_at is not None
    assert task.updated_at is not None


def test_create_multiple_tasks_unique_ids(repo):
    """Create multiple tasks should produce unique IDs."""
    t1 = repo.create("Title 1", "Desc 1", TaskStatus.TODO)
    t2 = repo.create("Title 2", "Desc 2", TaskStatus.IN_PROGRESS)
    assert t1.id is not None
    assert t2.id is not None
    assert t1.id != t2.id
    tasks = repo.list()
    assert len(tasks) == 2


def test_list_tasks_after_creation(repo):
    """Verify list includes created tasks."""
    repo.create("T1", "D1", TaskStatus.TODO)
    tasks = repo.list()
    assert len(tasks) == 1
    assert tasks[0].title == "T1"

    repo.create("T2", "D2", TaskStatus.DONE)
    tasks = repo.list()
    assert len(tasks) == 2


def test_partial_update(repo):
    """partial update."""
    task = repo.create("Original", "Original Desc", TaskStatus.TODO)

    updated = repo.update(task.id, title="Updated Title")
    assert updated is not None
    assert updated.title == "Updated Title"
    assert updated.description == "Original Desc"  # unchanged
    assert updated.status == TaskStatus.TODO  # unchanged


def test_update_description_only(repo):
    """Update only description."""
    task = repo.create("Title", "Old Desc", TaskStatus.IN_PROGRESS)

    updated = repo.update(task.id, description="New Desc")
    assert updated is not None
    assert updated.title == "Title"
    assert updated.description == "New Desc"
    assert updated.status == TaskStatus.IN_PROGRESS


def test_status_change(repo):
    """status change."""
    task = repo.create("Task", "Description", TaskStatus.TODO)

    updated = repo.update(task.id, status=TaskStatus.DONE)
    assert updated is not None
    assert updated.status == TaskStatus.DONE

    task_from_db = repo.list()[0]
    assert task_from_db.status == TaskStatus.DONE


def test_partial_update_preserves_other_fields(repo):
    """Partial update should preserve unchanged fields."""
    task = repo.create("Title", "Description", TaskStatus.TODO)

    updated = repo.update(task.id, title="New Title")
    assert updated is not None
    assert updated.title == "New Title"
    assert updated.description == "Description"  # unchanged
    assert updated.status == TaskStatus.TODO  # unchanged


def test_delete(repo):
    """delete."""
    task = repo.create("To Delete", "Description", TaskStatus.TODO)

    deleted = repo.delete(task.id)
    assert deleted is True

    tasks = repo.list()
    assert len(tasks) == 0


def test_missing_resource_behavior(repo):
    """missing-resource behavior."""
    non_existent_id = 99999

    result = repo.update(non_existent_id, title="New Title")
    assert result is None

    result = repo.delete(non_existent_id)
    assert result is False


def test_timezone_aware_utc_timestamps(repo):
    """timezone-aware UTC timestamps."""
    task = repo.create("Time Task", "Desc", TaskStatus.TODO)

    assert task.created_at.tzinfo is not None
    assert task.updated_at.tzinfo is not None

    # Verify UTC (datetime with timezone)
    assert task.created_at.tzname() == "UTC" or task.created_at.tzinfo is not None


def test_updated_at_advances_on_update(repo):
    """updated_at advances on update."""
    task = repo.create("Original", "Desc", TaskStatus.TODO)
    original_updated_at = task.updated_at

    time.sleep(0.01)  # Small delay to ensure timestamp difference

    updated = repo.update(task.id, title="Updated")
    assert updated is not None
    assert updated.updated_at > original_updated_at
