from fastapi import FastAPI, HTTPException, Path, Query, Depends, Body
import uvicorn
from pydantic import BaseModel, Field

app = FastAPI(title="任务管理系统", description="第一周FastAPI核心开发实战", version="1.0.0")

# ------------------------------------------------------------
# 依赖注入：分页参数（统一处理，无需在每个接口中重复定义）
# ------------------------------------------------------------
def get_pagination(
    skip: int = Query(default=0, ge=0, description="跳过的记录数"),
    limit: int = Query(default=10, ge=1, le=100, description="每页记录数"),
):
    return {"skip": skip, "limit": limit}


# ------------------------------------------------------------
# Pydantic 模型
# ------------------------------------------------------------
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=50, description="任务标题")
    description: str | None = Field(
        default=None, max_length=500, description="任务描述"
    )
    priority: int = Field(default=1, ge=1, le=5, description="任务优先级，1-5之间")


class Task(TaskCreate):
    task_id: int


# ------------------------------------------------------------
# 内存存储
# ------------------------------------------------------------
tasks_db: list[Task] = []
next_id: int = 1


# ------------------------------------------------------------
# 欢迎接口
# ------------------------------------------------------------
@app.get("/", summary="根路径欢迎")
def root():
    return {"message": "欢迎使用任务管理系统"}


# ------------------------------------------------------------
# CRUD 接口
# ------------------------------------------------------------
@app.post("/tasks", summary="创建任务", status_code=201)
def create_task(task: TaskCreate):
    global next_id
    new_task = Task(task_id=next_id, **task.model_dump())
    tasks_db.append(new_task)
    next_id += 1
    return new_task


@app.get("/tasks", summary="查询任务列表")
def read_tasks(pagination: dict = Depends(get_pagination)):
    skip = pagination["skip"]
    limit = pagination["limit"]
    return tasks_db[skip : skip + limit]


@app.get("/tasks/{task_id}", summary="查询指定任务")
def read_task(
    task_id: int = Path(..., gt=0, description="任务ID必须大于0"),
):
    for task in tasks_db:
        if task.task_id == task_id:
            return task
    raise HTTPException(status_code=404, detail="任务未找到")


@app.put("/tasks/{task_id}", summary="更新指定任务")
def update_task(
    *,
    task_id: int = Path(..., gt=0, description="任务ID必须大于0"),
    task: TaskCreate = Body(...),
):
    for index, t in enumerate(tasks_db):
        if t.task_id == task_id:
            updated_task = Task(task_id=task_id, **task.model_dump())
            tasks_db[index] = updated_task
            return updated_task
    raise HTTPException(status_code=404, detail="任务未找到")


@app.delete("/tasks/{task_id}", summary="删除指定任务", status_code=204)
def delete_task(
    task_id: int = Path(..., gt=0, description="任务ID必须大于0"),
):
    for index, t in enumerate(tasks_db):
        if t.task_id == task_id:
            del tasks_db[index]
            return
    raise HTTPException(status_code=404, detail="任务未找到")
