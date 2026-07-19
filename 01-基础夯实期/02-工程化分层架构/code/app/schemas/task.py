from pydantic import BaseModel, Field

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=50, description="任务标题")
    description: str | None = Field(
        default=None, max_length=500, description="任务描述"
    )
    priority: int = Field(default=1, ge=1, le=5, description="任务优先级，1-5之间")


class Task(TaskCreate):
    task_id: int