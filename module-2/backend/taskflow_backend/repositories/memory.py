from datetime import datetime, timezone
from typing import List, Optional, Dict
from ..domain.task import Task, TaskStatus
from ..domain.repositories import TaskRepository

class InMemoryTaskRepository(TaskRepository):
    def __init__(self) -> None:
        self._tasks: Dict[int, Task] = {}
        self._next_id: int = 1

    def list(self) -> List[Task]:
        return list(self._tasks.values())

    def create(self, title: str, description: str, status: TaskStatus) -> Task:
        now = datetime.now(timezone.utc)
        task = Task(
            id=self._next_id,
            title=title,
            description=description,
            status=status,
            created_at=now,
            updated_at=now,
        )
        self._tasks[self._next_id] = task
        self._next_id += 1
        return task

    def update(self, task_id: int, **updates) -> Optional[Task]:
        task = self._tasks.get(task_id)
        if task is None:
            return None

        # Create updated version by replacing provided fields
        updated_data = {
            "id": task.id,
            "title": updates.get("title", task.title),
            "description": updates.get("description", task.description),
            "status": updates.get("status", task.status),
            "created_at": task.created_at,
            "updated_at": datetime.now(timezone.utc),
        }
        
        updated_task = Task(**updated_data)
        self._tasks[task_id] = updated_task
        return updated_task

    def delete(self, task_id: int) -> bool:
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False
