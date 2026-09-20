from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing import Optional, Any
from datetime import datetime
from ..domain.task import TaskStatus

class ErrorResponse(BaseModel):
    message: str

class TaskSchema(BaseModel):
    id: int = Field(..., gt=0)
    title: str
    description: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime

class CreateTaskRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')

    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.TODO

    @model_validator(mode='before')
    @classmethod
    def reject_explicit_nulls(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for field in ["description", "status"]:
                if field in data and data[field] is None:
                    raise ValueError(f"{field.capitalize()} cannot be null.")
        return data

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Title must contain at least one non-whitespace character.")
        return trimmed

class UpdateTaskRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None

    @model_validator(mode='before')
    @classmethod
    def reject_explicit_nulls(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for field in ["title", "description", "status"]:
                if field in data and data[field] is None:
                    raise ValueError(f"{field.capitalize()} cannot be null.")
        return data

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Title must contain at least one non-whitespace character.")
        return trimmed

    @model_validator(mode='after')
    def check_min_properties(self) -> 'UpdateTaskRequest':
        if not self.model_fields_set:
            raise ValueError("At least one property must be provided for update.")
        return self
