import logging
import os
import time
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Path, status
from opentelemetry.trace import Status, StatusCode

from ..domain.repositories import TaskRepository
from ..observability import (
    TASKS_LIST_DURATION,
    TASKS_LIST_ERRORS,
    TASKS_LIST_REQUESTS,
    TRACER,
)
from ..schemas.tasks import TaskSchema, CreateTaskRequest, UpdateTaskRequest


router = APIRouter(prefix="/api/tasks", tags=["Tasks"])
_LOGGER = logging.getLogger(__name__)
_TASKS_LIST_OPERATION = "tasks.list"


def get_repo() -> TaskRepository:
    raise RuntimeError("Repository dependency not configured")


@router.get("", response_model=List[TaskSchema])
def list_tasks(repo: TaskRepository = Depends(get_repo)):
    environment = os.getenv("TASKFLOW_ENVIRONMENT", "unknown")
    release = os.getenv("TASKFLOW_RELEASE_SHA", "unknown")
    fault_mode = os.getenv("TASKFLOW_P4_FAULT_MODE", "off")
    started_at = time.perf_counter()
    outcome = "success"

    metric_attributes = {
        "operation": _TASKS_LIST_OPERATION,
    }

    with TRACER.start_as_current_span("tasks.list") as span:
        span.set_attribute("taskflow.operation", _TASKS_LIST_OPERATION)
        span.set_attribute("taskflow.environment", environment)
        span.set_attribute("taskflow.release", release)

        try:
            if environment == "dev" and fault_mode == "list_fail":
                outcome = "error"
                span.set_attribute("taskflow.fault_injected", True)
                span.set_status(Status(StatusCode.ERROR))

                _LOGGER.error(
                    "Task list failed: P4 controlled fault",
                    extra={
                        "operation": _TASKS_LIST_OPERATION,
                        "taskflow_environment": environment,
                        "taskflow_release": release,
                        "outcome": "error",
                        "error_type": "controlled_fault",
                    },
                )

                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Task list temporarily unavailable.",
                )

            tasks = repo.list()
            span.set_attribute("taskflow.task_count", len(tasks))

            _LOGGER.info(
                "Task list completed",
                extra={
                    "operation": _TASKS_LIST_OPERATION,
                    "taskflow_environment": environment,
                    "taskflow_release": release,
                    "outcome": "success",
                    "task_count": len(tasks),
                },
            )

            return tasks

        except HTTPException:
            outcome = "error"
            raise
        except Exception as exc:
            outcome = "error"
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR))

            _LOGGER.error(
                "Task list failed",
                extra={
                    "operation": _TASKS_LIST_OPERATION,
                    "taskflow_environment": environment,
                    "taskflow_release": release,
                    "outcome": "error",
                    "error_type": type(exc).__name__,
                },
                exc_info=True,
            )
            raise
        finally:
            duration_ms = (time.perf_counter() - started_at) * 1000

            TASKS_LIST_REQUESTS.add(
                1,
                {**metric_attributes, "outcome": outcome},
            )
            TASKS_LIST_DURATION.record(duration_ms, metric_attributes)

            if outcome == "error":
                TASKS_LIST_ERRORS.add(1, metric_attributes)

@router.post("", response_model=TaskSchema, status_code=status.HTTP_201_CREATED)
def create_task(request: CreateTaskRequest, repo: TaskRepository = Depends(get_repo)):
    return repo.create(
        title=request.title,
        description=request.description,
        status=request.status
    )

@router.patch("/{task_id}", response_model=TaskSchema)
def update_task(
    task_id: Annotated[int, Path(gt=0)],
    request: UpdateTaskRequest,
    repo: TaskRepository = Depends(get_repo)
):
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    updated_task = repo.update(task_id, **updates)
    if updated_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Task not found."}
        )
    return updated_task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: Annotated[int, Path(gt=0)],
    repo: TaskRepository = Depends(get_repo)
):
    if not repo.delete(task_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Task not found."}
        )
    return None
