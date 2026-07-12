from fastapi import FastAPI, HTTPException, Path, Query, Depends
from pydantic import BaseModel, Field

app = FastAPI(
    title="任务管理系统",
    description="第一周FastAPI开发实战",
    version="1.0.0"
)

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=50, description="任务标题")
    description: str | None = Field(default=None, max_length=500, description="任务描述")
    priority: int = Field(default=1, ge=1, le=5, description="任务优先级，1-5之间")

class Task(TaskCreate):
    task_id: int

def get_pagination(
    skip: int = Query(default=0, ge=0, description="跳过条数"),
    limit: int = Query(default=10, ge=1, le=100, description="每页条数")
):
    return {"skip": skip, "limit": limit}

tasks_db = []
next_id = 1

@app.get("/", summary="根路径欢迎")
def root():
    return {"message": "欢迎使用任务管理系统"}


@app.post("/tasks", summary="创建任务", status_code=201)
def create_task(task: TaskCreate):
    global next_id
    new_task = Task(
        task_id=next_id,
        title=task.title,
        description=task.description,
        priority=task.priority
    )
    tasks_db.append(new_task)
    next_id += 1
    return new_task


@app.get("/tasks", summary="分页查询任务列表")
def get_task_list(pagination: dict = Depends(get_pagination)):
    skip = pagination["skip"]
    limit = pagination["limit"]
    task_list = tasks_db[skip : skip + limit]
    return {
        "total": len(tasks_db),
        "list": task_list
    }


@app.get("/tasks/{task_id}", summary="查询指定任务")
def get_single_task(task_id: int = Path(gt=0, description="任务ID，必须大于0")):
    for task in tasks_db:
        if task.task_id == task_id:
            return task
    raise HTTPException(status_code=404, detail="任务未找到")


@app.put("/tasks/{task_id}", summary="更新指定任务")
def update_task(
    task: TaskCreate,
    task_id: int = Path(gt=0, description="任务ID，必须大于0")
):
    for index, t in enumerate(tasks_db):
        if t.task_id == task_id:
            updated_task = Task(
                task_id=task_id,
                title=task.title,
                description=task.description,
                priority=task.priority
            )
            tasks_db[index] = updated_task
            return updated_task
    raise HTTPException(status_code=404, detail="任务未找到")


@app.delete("/tasks/{task_id}", summary="删除指定任务", status_code=204)
def delete_task(task_id: int = Path(gt=0, description="任务ID，必须大于0")):
    for index, t in enumerate(tasks_db):
        if t.task_id == task_id:
            tasks_db.pop(index)
            return
    raise HTTPException(status_code=404, detail="任务未找到")