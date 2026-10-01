from typing import Protocol, List, Optional
from .task import Task, TaskStatus

class TaskRepository(Protocol):
    def list(self) -> List[Task]:
        ...

    def create(self, title: str, description: str, status: TaskStatus) -> Task:
        ...

    def update(self, task_id: int, **updates) -> Optional[Task]:
        ...

    def delete(self, task_id: int) -> bool:
        ...
