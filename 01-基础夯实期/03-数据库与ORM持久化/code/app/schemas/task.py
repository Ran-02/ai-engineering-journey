"""
================================================================================
 schemas/task.py — Pydantic 接口模型（接口层数据格式）
================================================================================

 这个文件定义了"接口层面的数据长什么样"——也就是前端发来的 JSON 和
 后端返回的 JSON 的格式。

 ────────────────────────────────────────────────────────────────────────────
 双层模型设计（重要概念）

 项目中有两种模型，职责完全不同：

   1. db/models.py 中的 TaskDB（数据库模型）
      → 对应数据库表，面向"存"
      → 关心：字段类型、约束、索引、默认值
      → 类比：后厨的食材存储规范

   2. schemas/task.py 中的 TaskCreate / TaskResponse（接口模型）
      → 对应 API 请求/响应，面向"传"
      → 关心：字段校验规则、文档描述、哪些字段暴露给前端
      → 类比：菜单上的菜品描述

 为什么非要拆成两层？
   ├─ 数据库字段变了（比如加了 is_deleted），接口可以不变
   ├─ 接口字段变了（比如改字段名），数据库可以不变
   └─ 敏感字段（如密码哈希）不会意外暴露给前端

 ────────────────────────────────────────────────────────────────────────────
 from_attributes 配置

 这个配置是"数据库对象 → 接口模型"的桥梁：
   TaskResponse.model_validate(db_task)
   # db_task 是 SQLAlchemy 的 TaskDB 实例
   # TaskResponse 会自动读取 db_task 的同名属性

 没有这个配置的话，Pydantic 只接受字典作为输入源，
 有了它，Pydantic 就能从 ORM 对象上直接读取属性了。
 ================================================================================
"""

from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# TaskCreate — 创建任务时的请求体
# ============================================================================

class TaskCreate(BaseModel):
    """
    客户端创建任务时发送的 JSON 格式。

    不包含 task_id，因为 ID 是数据库自动生成的，前端不用管。
    """

    # title：任务标题（必填，1-50 字符）
    title: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="任务标题，长度1-50个字符",
    )

    # description：任务描述（可选，最多 500 字符）
    description: str | None = Field(
        default=None,
        max_length=500,
        description="任务描述，最多500个字符（可选）",
    )

    # priority：任务优先级（可选，默认 1，范围 1-5）
    priority: int = Field(
        default=1,
        ge=1,
        le=5,
        description="任务优先级，1-5之间",
    )


# ============================================================================
# TaskResponse — 返回给客户端的响应体
# ============================================================================
# 继承了 TaskCreate，所以拥有 title、description、priority 三个字段，
# 额外多了 task_id（数据库自动生成的 ID）。

# model_config = ConfigDict(from_attributes=True) 这句是关键：
#   它告诉 Pydantic："这个模型可以从 ORM 对象创建"。
#   有了它，我们就可以写：
#     TaskResponse.model_validate(db_task)
#   其中 db_task 是 SQLAlchemy 的 TaskDB 实例，
#   Pydantic 会自动读取 db_task.task_id、db_task.title 等属性。
# ============================================================================

class TaskResponse(TaskCreate):
    """
    返回给客户端的任务完整数据。

    包含数据库自动生成的 task_id。
    """

    # model_config 是 Pydantic v2 的配置方式
    # 在 v1 中写作 class Config: orm_mode = True
    model_config = ConfigDict(from_attributes=True)

    # task_id：任务唯一标识（必填，由数据库生成）
    task_id: int
