"""
================================================================================
 routers/task.py — 任务管理接口（数据库版）
================================================================================

 这是第 3 周改造的核心文件。
 对比第 2 周，最大的变化是：

   ✅ 内存操作 → 数据库操作
      tasks_db: list[Task] = []              →  db: Session = Depends(get_db)
      tasks_db.append(new_task)              →  db.add(db_task); db.commit()
      for task in tasks_db:                  →  db.query(TaskDB).all()
      next_id += 1                           →  数据库自增主键

   ✅ 接口模型转换
      return task                            →  return TaskResponse.model_validate(db_task)
      （直接返回 Python 对象）                  （ORM 对象 → Pydantic 模型）

   ✅ 响应模型文档化
      无                                    →  response_model=TaskResponse
                                               /docs 中自动显示返回格式

 ────────────────────────────────────────────────────────────────────────────
 数据流对比

 第 2 周（内存版）：
   客户端 → 路由 → 操作列表 → 返回 Python 对象

 第 3 周（数据库版）：
   客户端 → 路由 → 依赖注入 get_db → 操作数据库 → ORM 对象 → 转 Pydantic 模型 → 返回
================================================================================
"""

from fastapi import APIRouter, HTTPException, Path, Query, Depends
from sqlalchemy.orm import Session

from app.schemas.task import TaskCreate, TaskResponse
from app.db.models import TaskDB
from app.db.database import get_db
from app.utils.logger import logger

# ============================================================================
# APIRouter 实例
# ============================================================================
router = APIRouter(prefix="/tasks", tags=["任务管理"])


# ============================================================================
# 依赖函数：分页参数（和之前一样，没有变化）
# ============================================================================
def get_pagination(
    skip: int = Query(default=0, ge=0, description="跳过的记录数"),
    limit: int = Query(default=10, ge=1, le=100, description="每页记录数"),
) -> dict:
    return {"skip": skip, "limit": limit}


# ============================================================================
# POST /tasks — 创建任务
# ============================================================================
# 【数据库改造要点】
#   之前：Task(task_id=next_id, **task_data.model_dump()) + tasks_db.append()
#   现在：TaskDB(**task_data.model_dump()) + db.add() + db.commit() + db.refresh()
#
# 关键区别：
#   - TaskDB 没有 task_id 参数，因为数据库自增主键会自动生成
#   - commit() 提交事务，数据才真正写入数据库文件
#   - refresh() 从数据库重新读取，获取自动生成的 task_id 值
# ============================================================================

@router.post("/", response_model=TaskResponse, status_code=201, summary="创建任务")
def create_task(task_data: TaskCreate, db: Session = Depends(get_db)):
    """
    创建一个新任务。

    改造说明：
      以前 task_id 是 Python 自增计数器生成的（程序重启后重置）。
      现在是数据库自增主键生成的（程序重启后从上次的值继续）。
    """
    # 1. 创建数据库模型实例
    # task_data.model_dump() 把请求体转成字典
    # ** 把字典展开为关键字参数
    # 比如 TaskCreate(title="买菜", priority=3)
    # → TaskDB(title="买菜", description=None, priority=3)
    db_task = TaskDB(**task_data.model_dump())

    # 2. 添加到会话（还没有写入数据库）
    db.add(db_task)

    # 3. 提交事务（真正写入数据库）
    # 这一步执行 INSERT SQL 语句
    db.commit()

    # 4. 刷新对象（获取数据库生成的值）
    # 提交后，db_task.task_id 从 None 变为实际值（如 1）
    db.refresh(db_task)

    logger.info(f"创建任务成功: id={db_task.task_id}, title={db_task.title}")

    # 5. 返回响应（ORM 对象 → Pydantic 模型）
    return db_task


# ============================================================================
# GET /tasks — 查询任务列表（分页）
# ============================================================================
# 【数据库改造要点】
#   之前：tasks_db[skip : skip + limit]（Python 列表切片）
#   现在：db.query(TaskDB).offset(skip).limit(limit).all()（数据库分页）
#
# offset().limit() 翻译成 SQL 就是：SELECT ... LIMIT ? OFFSET ?
# 数据量大的时候，数据库分页比 Python 切片快得多。
# ============================================================================

@router.get("/", response_model=list[TaskResponse], summary="查询任务列表")
def read_tasks(
    pagination: dict = Depends(get_pagination),
    db: Session = Depends(get_db),
):
    """
    分页查询任务列表。

    查询参数:
        skip:  跳过的记录数（默认 0）
        limit: 每页记录数（默认 10）

    返回:
        当前页的任务列表
    """
    skip = pagination["skip"]
    limit = pagination["limit"]

    # 数据库分页查询
    # .query(TaskDB)     → SELECT * FROM tasks
    # .offset(skip)      → 跳过前面 skip 条
    # .limit(limit)      → 最多返回 limit 条
    # .all()             → 执行查询，返回列表
    tasks = db.query(TaskDB).offset(skip).limit(limit).all()

    logger.info(f"查询任务列表: skip={skip}, limit={limit}, 返回{len(tasks)}条")
    return tasks


# ============================================================================
# GET /tasks/{task_id} — 查询单个任务
# ============================================================================
# 【数据库改造要点】
#   之前：遍历列表逐条比对
#   现在：db.get(TaskDB, task_id) — 按主键查询
#
# db.get() 比遍历列表高效得多：
#   - 列表遍历：O(n)，数据越多越慢
#   - 主键查询：O(1)，不论多少数据都一样快
#   - 因为数据库对主键自动建立了索引
# ============================================================================

@router.get("/{task_id}", response_model=TaskResponse, summary="查询指定任务")
def read_task(
    task_id: int = Path(..., gt=0, description="任务ID，必须大于0"),
    db: Session = Depends(get_db),
):
    """
    根据 ID 查询单个任务。

    参数:
        task_id: 任务 ID（路径参数，必须大于 0）

    返回:
        匹配的任务对象，或 404
    """
    # db.get(TaskDB, task_id) 按主键查询
    # 等价于 SQL: SELECT * FROM tasks WHERE task_id = ?
    # 找不到返回 None
    task = db.get(TaskDB, task_id)

    if not task:
        logger.warning(f"查询任务失败: id={task_id} 不存在")
        raise HTTPException(status_code=404, detail="任务未找到")

    logger.info(f"查询任务成功: id={task_id}")
    return task


# ============================================================================
# PUT /tasks/{task_id} — 更新任务
# ============================================================================
# 【数据库改造要点】
#   之前：遍历列表找到后直接替换
#   现在：查到后修改字段 → commit()
#
# 更新操作分三步：
#   1. db.get(TaskDB, task_id)       — 查出来
#   2. 修改对象的属性                   — 改值
#   3. db.commit()                   — 提交（不需要再 add，因为对象被跟踪了）
#
# SQLAlchemy 的"自动跟踪"机制：
#   从数据库查出来的对象，会被 Session 跟踪。
#   你修改它的属性后，Session 知道它变了。
#   commit() 时，Session 会自动生成 UPDATE 语句。
# ============================================================================

@router.put("/{task_id}", response_model=TaskResponse, summary="更新指定任务")
def update_task(
    task_id: int = Path(..., gt=0, description="任务ID，必须大于0"),
    task_data: TaskCreate = ...,
    db: Session = Depends(get_db),
):
    """
    更新一个已存在的任务。

    流程:
        1. 查数据库 → 找到要更新的任务
        2. 逐个字段赋值
        3. 提交事务（自动生成 UPDATE 语句）
        4. 刷新对象（获取数据库更新后的值）
    """
    # 第 1 步：查询
    task = db.get(TaskDB, task_id)
    if not task:
        logger.warning(f"更新任务失败: id={task_id} 不存在")
        raise HTTPException(status_code=404, detail="任务未找到")

    # 第 2 步：逐个字段赋值
    # task_data.model_dump() 返回字典
    # 遍历字典，用 setattr 设置对象的每个属性
    # 好处：新增字段时不用改这里的代码
    for field, value in task_data.model_dump().items():
        setattr(task, field, value)

    # 第 3 步：提交事务
    db.commit()

    # 第 4 步：刷新（确保返回的数据是最新的）
    db.refresh(task)

    logger.info(f"更新任务成功: id={task_id}")
    return task


# ============================================================================
# DELETE /tasks/{task_id} — 删除任务
# ============================================================================
# 【数据库改造要点】
#   之前：del tasks_db[index]
#   现在：db.delete(task) + db.commit()
#
# 删除操作分三步：
#   1. db.get(TaskDB, task_id)  — 查出来
#   2. db.delete(task)          — 标记删除
#   3. db.commit()              — 提交（生成 DELETE 语句）
#
# 状态码 204 = 删除成功，无响应体
# ============================================================================

@router.delete("/{task_id}", status_code=204, summary="删除指定任务")
def delete_task(
    task_id: int = Path(..., gt=0, description="任务ID，必须大于0"),
    db: Session = Depends(get_db),
):
    """
    删除一个已存在的任务。

    流程:
        1. 查数据库 → 找到要删除的任务
        2. 调用 db.delete() 标记删除
        3. 提交事务（生成 DELETE 语句）
    """
    task = db.get(TaskDB, task_id)
    if not task:
        logger.warning(f"删除任务失败: id={task_id} 不存在")
        raise HTTPException(status_code=404, detail="任务未找到")

    # 标记删除（还没真正删）
    db.delete(task)

    # 提交事务（真正执行 DELETE）
    db.commit()

    logger.info(f"删除任务成功: id={task_id}")
    return
