from pathlib import Path

from fastapi.testclient import TestClient

from taskflow_backend.app import create_app
from taskflow_backend.repositories.sqlalchemy import SqlAlchemyTaskRepository


def _make_app(tmp_path: Path) -> TestClient:
    """Return a TestClient using a SQLite db located in *tmp_path*.

    A dedicated repository instance is created for each call, but both apps
    share the same underlying database file which persists after the client
    context exits.
    """
    db_file = tmp_path / "test.db"
    repo = SqlAlchemyTaskRepository(db_path=str(db_file))
    app = create_app(repo=repo)
    return TestClient(app)


def test_sqlite_persistence(tmp_path: Path):
    client1 = _make_app(tmp_path)

    # Create a task via the API
    r = client1.post("/api/tasks", json={"title": "T", "description": "D"})
    assert r.status_code == 201
    created = r.json()
    assert created["title"] == "T"

    # Retrieve the created task via the same app
    r2 = client1.get("/api/tasks")
    assert r2.status_code == 200
    tasks = r2.json()
    assert len(tasks) == 1
    assert tasks[0]["id"] == created["id"]

    task_id = created["id"]

    # Update the task via the API to a valid status
    r3 = client1.patch(f"/api/tasks/{task_id}", json={"status": "done"})
    assert r3.status_code == 200
    updated = r3.json()
    assert updated["status"] == "done"

    # Start a new app instance pointing to the same database file
    client2 = _make_app(tmp_path)
    r5 = client2.get("/api/tasks")
    assert r5.status_code == 200
    tasks2 = r5.json()
    assert len(tasks2) == 1
    assert tasks2[0]["status"] == "done"
    assert tasks2[0]["id"] == task_id

    # Delete the task via the second app
    r6 = client2.delete(f"/api/tasks/{task_id}")
    assert r6.status_code == 204

    # Third app: ensure the task is gone
    client3 = _make_app(tmp_path)
    r7 = client3.get("/api/tasks")
    assert r7.status_code == 200
    assert len(r7.json()) == 0
