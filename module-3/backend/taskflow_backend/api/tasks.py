from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import List, Annotated
from ..domain.repositories import TaskRepository
from ..schemas.tasks import TaskSchema, CreateTaskRequest, UpdateTaskRequest

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])

def get_repo() -> TaskRepository:
    raise RuntimeError("Repository dependency not configured")

@router.get("", response_model=List[TaskSchema])
def list_tasks(repo: TaskRepository = Depends(get_repo)):
    return repo.list()

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
