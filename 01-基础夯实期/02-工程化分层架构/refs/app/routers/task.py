"""
================================================================================
 routers/task.py — 任务管理接口（路由层）
================================================================================

 这个文件是"路由层"——它的工作只有一个：把 URL 请求分发给对应的处理函数。
 你可以把它想成餐厅的"服务员"：
   - 客人（客户端）说"我要点菜"（POST /tasks）
   - 服务员（路由）把菜单传给后厨（业务逻辑）
   - 后厨做完菜，服务员端给客人（返回响应）

 APIRouter 是什么？
   FastAPI 提供的"子路由器"，和 app（FastAPI 实例）功能一样，
   但更轻量，专门用来拆分不同模块的路由。
   最后在 main.py 中用 app.include_router() 把所有子路由汇总到一起。

 这个文件负责 5 个接口：
   POST   /tasks           → 创建任务（201）
   GET    /tasks           → 查询任务列表
   GET    /tasks/{task_id} → 查询单个任务
   PUT    /tasks/{task_id} → 更新任务
   DELETE /tasks/{task_id} → 删除任务（204）
================================================================================
"""

# ============================================================================
# 导入所需模块
# ============================================================================
# 这里用到了 FastAPI 的几个核心工具：
#   APIRouter      → 子路由管理器，在本文件中定义路由
#   HTTPException  → 主动抛出 HTTP 异常（比如 404 资源不存在）
#   Path, Query    → 参数校验器（限制数值范围）
#   Depends        → 依赖注入（把公共逻辑抽离出来）
# ============================================================================
from fastapi import APIRouter, HTTPException, Path, Query, Depends, Body

# 从 schemas/task.py 导入数据模型
from app.schemas.task import TaskCreate, Task

# 从 utils/logger.py 导入日志器
from app.utils.logger import logger


# ============================================================================
# 创建 APIRouter 实例（子路由器）
# ============================================================================
# prefix="/tasks" → 这个路由器的所有路径都自动加上 /tasks 前缀
#                    比如 @router.get("/") 实际匹配的是 /tasks/
# tags=["任务管理"] → 在 /docs 交互式文档中，这些接口会被归到"任务管理"分组下
# ============================================================================
router = APIRouter(prefix="/tasks", tags=["任务管理"])


# ============================================================================
# 内存数据存储
# ============================================================================
# tasks_db：Python 列表，用来存所有任务数据（程序重启后丢失）
# next_id ：自增计数器，每创建一个任务就 +1，保证每个任务 ID 唯一
#
# 注意：这两个变量是模块级的，也就是说所有请求共享同一份数据。
# 它们是"全局变量"，所以函数里修改它们需要用 global 关键字。
#
# 类型注解 list[Task] 和 int 不是强制约束，但让代码更容易理解。
# ============================================================================
tasks_db: list[Task] = []   # 任务列表，初始为空
next_id: int = 1            # 下一个任务的 ID，从 1 开始


# ============================================================================
# 依赖函数：分页参数
# ============================================================================
# 什么是依赖注入（Depends）？
#   简单说就是：把公共的参数抽出来，写成单独的函数。
#   这样多个接口可以复用同一套逻辑，不用重复写。
#
# 这个函数处理两个查询参数：
#   skip  — 跳过多少条（从第几条开始）
#   limit — 返回多少条（每页大小）
#
# 把这些参数抽离出来，在 /docs 中也能统一显示，让文档更清晰。
# ============================================================================

def get_pagination(
    skip: int = Query(
        default=0,          # 默认值 0，表示从第一条开始
        ge=0,               # ge = greater or equal，必须 >= 0
        description="跳过的记录数，用于分页",
    ),
    limit: int = Query(
        default=10,         # 默认每页 10 条
        ge=1,               # 必须 >= 1
        le=100,             # le = less or equal，最多 100 条
        description="每页返回的记录数，范围1-100",
    ),
) -> dict:
    """
    分页参数依赖注入函数。

    返回包含 skip 和 limit 的字典，
    FastAPI 会自动从 URL 查询参数中解析这两个值。

    比如 GET /tasks?skip=0&limit=20
    就会得到 {"skip": 0, "limit": 20}
    """
    return {"skip": skip, "limit": limit}


# ============================================================================
# 以下是 5 个 CRUD 接口
# ============================================================================


# ============================================================================
# POST /tasks — 创建任务
# ============================================================================
# status_code=201 表示"创建成功"（HTTP 语义，比 200 更精确）
# 客户端（前端）发送 JSON 请求体，格式由 TaskCreate 模型定义
# ============================================================================

@router.post("/", summary="创建任务", status_code=201)
def create_task(task_data: TaskCreate):
    """
    创建一个新任务。

    参数:
        task_data: 请求体，格式由 TaskCreate 模型定义（title, description, priority）

    返回:
        创建好的完整任务对象（包含自动生成的 task_id）

    流程:
        1. 接收客户端发送的任务数据（task_data）
        2. 生成一个新的 task_id（自增）
        3. 把数据组装成 Task 对象（带 ID）
        4. 存入内存列表 tasks_db
        5. 计数器 +1
        6. 日志记录
        7. 返回创建好的任务
    """
    # 用到 next_id 这个全局变量，必须用 global 声明
    global next_id

    # 创建一个完整的 Task 对象
    # task_data.model_dump() 把 TaskCreate 对象转成字典
    # 比如 TaskCreate(title="买菜", priority=3)
    # 变成 {"title": "买菜", "description": None, "priority": 3}
    # 然后用 ** 展开这个字典，再加一个 task_id 字段
    new_task = Task(task_id=next_id, **task_data.model_dump())

    # 存到内存列表里
    tasks_db.append(new_task)

    # ID 自增，下次创建任务用新的 ID
    next_id += 1

    # 记录日志（用 logging 替代 print）
    logger.info(f"创建任务成功: id={new_task.task_id}, title={new_task.title}")

    # FastAPI 会自动把 Task 对象转成 JSON 返回给客户端
    return new_task


# ============================================================================
# GET /tasks — 查询任务列表（分页）
# ============================================================================
# 这里的 pagination 参数使用了依赖注入 Depends(get_pagination)
# FastAPI 会在调用这个函数之前，先调用 get_pagination()，
# 然后把返回值注入到 pagination 参数中
# ============================================================================

@router.get("/", summary="查询任务列表")
def read_tasks(pagination: dict = Depends(get_pagination)):
    """
    分页查询任务列表。

    查询参数（通过 Depends 自动注入）:
        skip:  跳过的记录数（默认 0）
        limit: 每页记录数（默认 10，最大 100）

    返回:
        当前页的任务列表（Python 列表切片）

    示例:
        GET /tasks?skip=0&limit=5 → 返回第 1~5 条任务
        GET /tasks?skip=5&limit=5 → 返回第 6~10 条任务
    """
    skip = pagination["skip"]
    limit = pagination["limit"]

    # 列表切片操作：tasks_db[开始:结束]
    # 比如 skip=0, limit=10 就是 tasks_db[0:10]，返回前 10 条
    result = tasks_db[skip : skip + limit]

    logger.info(f"查询任务列表: skip={skip}, limit={limit}, 返回{len(result)}条")
    return result


# ============================================================================
# GET /tasks/{task_id} — 查询单个任务
# ============================================================================
# {task_id} 是路径参数，在 URL 路径中传递
# 比如 GET /tasks/3 表示查询 ID 为 3 的任务
# 我们用 Path(..., gt=0) 确保 task_id 必须是正数
# ============================================================================

@router.get("/{task_id}", summary="查询指定任务")
def read_task(
    # task_id 从 URL 路径中获取
    # Path(...) 表示这个参数是路径参数，且是必填的
    # gt=0 表示必须大于 0（不能查 ID 为负数或 0 的任务）
    task_id: int = Path(..., gt=0, description="任务ID，必须大于0"),
):
    """
    根据 ID 查询单个任务。

    参数:
        task_id: 任务 ID（路径参数，必须大于 0）

    返回:
        匹配的任务对象

    异常:
        404: 如果任务不存在

    遍历整个列表查找，时间复杂度 O(n)。
    正式项目会用数据库索引来优化，这里用内存列表先实现功能。
    """
    # 遍历 tasks_db 列表，查找 ID 匹配的任务
    for task in tasks_db:
        if task.task_id == task_id:
            logger.info(f"查询任务成功: id={task_id}")
            return task

    # 如果遍历完都没找到，说明这个 ID 不存在
    # 抛出 404 异常，由全局异常处理器统一包装返回
    logger.warning(f"查询任务失败: id={task_id} 不存在")
    raise HTTPException(status_code=404, detail="任务未找到")


# ============================================================================
# PUT /tasks/{task_id} — 更新指定任务
# ============================================================================
# PUT 是"全量替换"——客户端要传完整的任务数据，然后服务端用新数据替换旧数据
# 这里同时用到了路径参数（task_id）和请求体（task_data）
# ============================================================================

@router.put("/{task_id}", summary="更新指定任务")
def update_task(
    # task_id 来自 URL 路径，必须大于 0
    task_id: int = Path(..., gt=0, description="任务ID，必须大于0"),
    # task_data 来自请求体（JSON），格式由 TaskCreate 模型定义
    task_data: TaskCreate = Body(...),
):
    """
    更新一个已存在的任务。

    参数:
        task_id:   要更新的任务 ID（路径参数）
        task_data: 新的任务数据（请求体 JSON）

    返回:
        更新后的完整任务对象

    异常:
        404: 如果任务不存在

    流程:
        1. 遍历任务列表，找到要更新的任务
        2. 用新数据替换旧数据（保留原来的 task_id）
        3. 日志记录
        4. 返回更新后的任务
    """
    for index, t in enumerate(tasks_db):
        if t.task_id == task_id:
            # 创建一个新的 Task 对象替换旧的
            # 新对象用 task_data 的数据，但保留原来的 task_id
            updated_task = Task(task_id=task_id, **task_data.model_dump())

            # 替换列表中对应位置的数据
            tasks_db[index] = updated_task

            logger.info(f"更新任务成功: id={task_id}")
            return updated_task

    # 没找到对应 ID 的任务
    logger.warning(f"更新任务失败: id={task_id} 不存在")
    raise HTTPException(status_code=404, detail="任务未找到")


# ============================================================================
# DELETE /tasks/{task_id} — 删除指定任务
# ============================================================================
# status_code=204 表示"删除成功，没有返回内容"
# 和 200 的区别：204 的响应体是空的，客户端不需要读取任何数据
# ============================================================================

@router.delete("/{task_id}", summary="删除指定任务", status_code=204)
def delete_task(
    task_id: int = Path(..., gt=0, description="任务ID，必须大于0"),
):
    """
    删除一个已存在的任务。

    参数:
        task_id: 要删除的任务 ID（路径参数）

    返回:
        None（状态码 204，没有响应体）

    异常:
        404: 如果任务不存在

    流程:
        1. 遍历任务列表，找到要删除的任务
        2. 从列表中删除
        3. 日志记录
        4. 不返回任何内容（状态码 204）
    """
    for index, t in enumerate(tasks_db):
        if t.task_id == task_id:
            # 从列表中删除
            del tasks_db[index]

            logger.info(f"删除任务成功: id={task_id}")
            # 返回 None，FastAPI 会自动处理 204 状态码
            return

    # 没找到对应 ID 的任务
    logger.warning(f"删除任务失败: id={task_id} 不存在")
    raise HTTPException(status_code=404, detail="任务未找到")
