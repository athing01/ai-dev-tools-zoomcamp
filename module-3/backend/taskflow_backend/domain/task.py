from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

@dataclass(frozen=True)
class Task:
    id: int
    title: str
    description: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
