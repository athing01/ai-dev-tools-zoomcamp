import pytest
from fastapi.testclient import TestClient

from taskflow_backend.app import create_app


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c

def test_get_tasks_empty(client):
    response = client.get("/api/tasks")
    assert response.status_code == 200
    assert response.json() == []

def test_get_tasks_multiple(client):
    client.post("/api/tasks", json={"title": "T1"})
    client.post("/api/tasks", json={"title": "T2"})
    response = client.get("/api/tasks")
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_create_task_success(client):
    payload = {"title": "Test Task", "description": "Desc", "status": "todo"}
    response = client.post("/api/tasks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["description"] == "Desc"
    assert data["status"] == "todo"
    assert "id" in data
    assert "created_at" in data

def test_create_task_response_shape(client):
    response = client.post("/api/tasks", json={"title": "T"})
    data = response.json()
    expected_fields = {"id", "title", "description", "status", "created_at", "updated_at"}
    assert set(data.keys()) == expected_fields
    assert isinstance(data["id"], int)

def test_create_task_defaults(client):
    payload = {"title": "Default Task"}
    response = client.post("/api/tasks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["description"] == ""
    assert data["status"] == "todo"

def test_create_task_explicit_status(client):
    payload = {"title": "Status Task", "status": "in_progress"}
    response = client.post("/api/tasks", json=payload)
    assert response.status_code == 201
    assert response.json()["status"] == "in_progress"

def test_create_task_trim_title(client):
    payload = {"title": "  Trimmed Title  "}
    response = client.post("/api/tasks", json=payload)
    assert response.status_code == 201
    assert response.json()["title"] == "Trimmed Title"

def test_create_task_invalid_title(client):
    payload = {"title": "   "}
    response = client.post("/api/tasks", json=payload)
    assert response.status_code == 422
    assert "message" in response.json()

def test_create_task_invalid_status(client):
    payload = {"title": "T", "status": "invalid"}
    response = client.post("/api/tasks", json=payload)
    assert response.status_code == 422

def test_create_task_unknown_field(client):
    payload = {"title": "T", "unknown": "field"}
    response = client.post("/api/tasks", json=payload)
    assert response.status_code == 422

def test_create_task_null_description(client):
    payload = {"title": "T", "description": None}
    response = client.post("/api/tasks", json=payload)
    assert response.status_code == 422

def test_patch_task_title(client):
    c_res = client.post("/api/tasks", json={"title": "Old"})
    task_id = c_res.json()["id"]

    response = client.patch(f"/api/tasks/{task_id}", json={"title": "New"})
    assert response.status_code == 200
    assert response.json()["title"] == "New"

def test_patch_task_response_shape(client):
    c_res = client.post("/api/tasks", json={"title": "T"})
    task_id = c_res.json()["id"]

    response = client.patch(f"/api/tasks/{task_id}", json={"title": "New"})
    data = response.json()
    expected_fields = {"id", "title", "description", "status", "created_at", "updated_at"}
    assert set(data.keys()) == expected_fields
    assert isinstance(data["id"], int)

def test_patch_task_description(client):
    c_res = client.post("/api/tasks", json={"title": "T", "description": "Old"})
    task_id = c_res.json()["id"]

    response = client.patch(f"/api/tasks/{task_id}", json={"description": "New"})
    assert response.status_code == 200
    assert response.json()["description"] == "New"

def test_patch_task_status(client):
    c_res = client.post("/api/tasks", json={"title": "T", "status": "todo"})
    task_id = c_res.json()["id"]

    response = client.patch(f"/api/tasks/{task_id}", json={"status": "done"})
    assert response.status_code == 200
    assert response.json()["status"] == "done"

def test_patch_task_partial_preserves(client):
    c_res = client.post("/api/tasks", json={"title": "T", "description": "D", "status": "todo"})
    task_id = c_res.json()["id"]

    response = client.patch(f"/api/tasks/{task_id}", json={"title": "New"})
    data = response.json()
    assert data["title"] == "New"
    assert data["description"] == "D"
    assert data["status"] == "todo"

def test_patch_task_not_found(client):
    response = client.patch("/api/tasks/999", json={"title": "New"})
    assert response.status_code == 404
    assert response.json() == {"message": "Task not found."}

def test_patch_task_empty_payload(client):
    c_res = client.post("/api/tasks", json={"title": "T"})
    task_id = c_res.json()["id"]

    response = client.patch(f"/api/tasks/{task_id}", json={})
    assert response.status_code == 422

def test_patch_task_null_field(client):
    c_res = client.post("/api/tasks", json={"title": "T"})
    task_id = c_res.json()["id"]

    response = client.patch(f"/api/tasks/{task_id}", json={"title": None})
    assert response.status_code == 422

def test_patch_task_unknown_field(client):
    c_res = client.post("/api/tasks", json={"title": "T"})
    task_id = c_res.json()["id"]

    response = client.patch(f"/api/tasks/{task_id}", json={"unknown": "field"})
    assert response.status_code == 422

def test_patch_task_blank_title(client):
    c_res = client.post("/api/tasks", json={"title": "T"})
    task_id = c_res.json()["id"]

    response = client.patch(f"/api/tasks/{task_id}", json={"title": "  "})
    assert response.status_code == 422

def test_delete_task_success(client):
    c_res = client.post("/api/tasks", json={"title": "T"})
    task_id = c_res.json()["id"]

    response = client.delete(f"/api/tasks/{task_id}")
    assert response.status_code == 204
    assert response.text == ""

    list_res = client.get("/api/tasks")
    assert len(list_res.json()) == 0

def test_delete_task_not_found(client):
    response = client.delete("/api/tasks/999")
    assert response.status_code == 404
    assert response.json() == {"message": "Task not found."}

def test_no_single_task_get(client):
    c_res = client.post("/api/tasks", json={"title": "T"})
    task_id = c_res.json()["id"]

    response = client.get(f"/api/tasks/{task_id}")
    assert response.status_code in [404, 405]

def test_patch_task_invalid_id(client):
    for tid in [0, -1]:
        response = client.patch(f"/api/tasks/{tid}", json={"title": "New"})
        assert response.status_code == 422

def test_delete_task_invalid_id(client):
    for tid in [0, -1]:
        response = client.delete(f"/api/tasks/{tid}")
        assert response.status_code == 422

def test_patch_task_missing_body(client):
    c_res = client.post("/api/tasks", json={"title": "T"})
    task_id = c_res.json()["id"]

    response = client.patch(f"/api/tasks/{task_id}")

    assert response.status_code == 422
    assert "message" in response.json()
