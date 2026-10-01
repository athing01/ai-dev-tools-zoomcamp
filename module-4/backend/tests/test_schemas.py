import pytest
from pydantic import ValidationError
from taskflow_backend.schemas.tasks import CreateTaskRequest, UpdateTaskRequest, TaskSchema
from taskflow_backend.domain.task import TaskStatus
from datetime import datetime, timezone

def test_create_task_request_valid():
    req = CreateTaskRequest(title="Valid Title", description="Some desc", status=TaskStatus.TODO)
    assert req.title == "Valid Title"
    assert req.description == "Some desc"
    assert req.status == TaskStatus.TODO

def test_create_task_request_trim_title():
    req = CreateTaskRequest(title="  Trim Me  ", description="desc")
    assert req.title == "Trim Me"

def test_create_task_request_empty_title():
    with pytest.raises(ValueError, match="Title must contain at least one non-whitespace character."):
        CreateTaskRequest(title="   ")

def test_create_task_request_omitted_description():
    req = CreateTaskRequest(title="Title")
    assert req.description == ""

def test_create_task_request_omitted_status():
    req = CreateTaskRequest(title="Title")
    assert req.status == TaskStatus.TODO

def test_create_task_request_all_statuses():
    for status in TaskStatus:
        req = CreateTaskRequest(title="Title", status=status)
        assert req.status == status

def test_create_task_request_invalid_status():
    with pytest.raises(ValidationError):
        CreateTaskRequest(title="Title", status="invalid")

def test_create_task_request_null_description():
    with pytest.raises(ValidationError):
        CreateTaskRequest(title="Title", description=None)

def test_create_task_request_unknown_fields():
    with pytest.raises(ValidationError):
        CreateTaskRequest(title="Title", unknown="field")

def test_update_task_request_title_only():
    req = UpdateTaskRequest(title="New Title")
    assert req.title == "New Title"
    assert req.description is None
    assert req.status is None

def test_update_task_request_description_only():
    req = UpdateTaskRequest(description="New Desc")
    assert req.description == "New Desc"
    assert req.title is None
    assert req.status is None

def test_update_task_request_status_only():
    req = UpdateTaskRequest(status=TaskStatus.DONE)
    assert req.status == TaskStatus.DONE
    assert req.title is None
    assert req.description is None

def test_update_task_request_multiple_fields():
    req = UpdateTaskRequest(title="T", status=TaskStatus.DONE)
    assert req.title == "T"
    assert req.status == TaskStatus.DONE
    assert req.description is None

def test_update_task_request_empty_payload():
    with pytest.raises(ValueError, match="At least one property must be provided for update."):
        UpdateTaskRequest()

def test_update_task_request_unknown_fields():
    with pytest.raises(ValidationError):
        UpdateTaskRequest(title="Title", unknown="field")

def test_update_task_request_whitespace_title():
    with pytest.raises(ValueError, match="Title must contain at least one non-whitespace character."):
        UpdateTaskRequest(title="   ")

def test_update_task_request_trim_title():
    req = UpdateTaskRequest(title="  Trim Me  ")
    assert req.title == "Trim Me"

def test_update_task_request_null_title():
    with pytest.raises(ValidationError):
        UpdateTaskRequest(title=None)

def test_update_task_request_null_description():
    with pytest.raises(ValidationError):
        UpdateTaskRequest(description=None)

def test_update_task_request_null_status():
    with pytest.raises(ValidationError):
        UpdateTaskRequest(status=None)

def test_update_task_request_valid_empty_description():
    req = UpdateTaskRequest(description="")
    assert req.description == ""

def test_task_schema_positive_id():
    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError):
        TaskSchema(id=0, title="T", description="D", status=TaskStatus.TODO, created_at=now, updated_at=now)

def test_task_schema_required_fields():
    with pytest.raises(ValidationError):
        TaskSchema(id=1)

def test_task_schema_valid_status():
    now = datetime.now(timezone.utc)
    task = TaskSchema(id=1, title="T", description="D", status=TaskStatus.IN_PROGRESS, created_at=now, updated_at=now)
    assert task.status == TaskStatus.IN_PROGRESS
