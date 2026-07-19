from fastapi import APIRouter, HTTPException, Path, Query, Depends, Body
from app.schemas.task import TaskCreate, Task
from app.utils.logger import logger

router = APIRouter(prefix="/tasks", tags=["任务管理"])

def get_pagination(
    skip: int = Query(default=0, ge=0, description="跳过的记录数"),
    limit: int = Query(default=10, ge=1, le=100, description="每页记录数"),
):
    return {"skip": skip, "limit": limit}

tasks_db: list[Task] = []
next_id: int = 1


@router.post("", summary="创建任务", status_code=201)
def create_task(task: TaskCreate):
    global next_id
    new_task = Task(task_id=next_id, **task.model_dump())
    tasks_db.append(new_task)
    next_id += 1
    return new_task


@router.get("", summary="查询任务列表")
def read_tasks(pagination: dict = Depends(get_pagination)):
    skip = pagination["skip"]
    limit = pagination["limit"]
    return tasks_db[skip : skip + limit]


@router.get("/{task_id}", summary="查询指定任务")
def read_task(
    task_id: int = Path(..., gt=0, description="任务ID必须大于0"),
):
    for task in tasks_db:
        if task.task_id == task_id:
            return task
    raise HTTPException(status_code=404, detail="任务未找到")


@router.put("/{task_id}", summary="更新指定任务")
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


@router.delete("/{task_id}", summary="删除指定任务", status_code=204)
def delete_task(
    task_id: int = Path(..., gt=0, description="任务ID必须大于0"),
):
    for index, t in enumerate(tasks_db):
        if t.task_id == task_id:
            del tasks_db[index]
            return
    raise HTTPException(status_code=404, detail="任务未找到")