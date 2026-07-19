"""
================================================================================
 utils/exceptions.py — 全局异常体系
================================================================================

 本文件负责两件事：
   1. 定义统一的错误响应格式
   2. 注册全局异常处理器，捕获三类异常

 ────────────────────────────────────────────────────────────────────────────
 为什么需要全局异常处理？

 默认情况下，FastAPI 返回的错误长这样：
   {"detail": [{"loc": ["body", "title"], "msg": "field required", ...}]}

 而我们项目统一的返回格式是：
   {"code": 422, "message": "请求参数校验失败", "data": null}

 前者前端用起来很麻烦，后者格式统一、前端好处理。
 全局异常处理器就像是"总客服"——不管哪层抛了异常，都由它统一包装成标准格式返回。

 ────────────────────────────────────────────────────────────────────────────
 三类异常处理器

 这里处理三种情况，按优先级从高到低：

   1. HTTPException（业务异常）
      → 比如"任务未找到"这种情况，是"可以预料的错误"
      → 状态码：404（或者其他业务状态码）
      → 包装为统一格式返回，不记录 ERROR 日志（因为这是预期行为）

   2. RequestValidationError（参数校验异常）
      → 比如用户传了一个超出范围的数字，或者缺少必填字段
      → 状态码：422
      → 格式化为易读的错误信息，告诉用户"哪个字段错了、为什么错"

   3. Exception 兜底（未知异常）
      → 比如代码里有 bug、数据库连不上
      → 状态码：500
      → 不暴露堆栈等敏感信息给客户端，但要在日志里记录完整错误
================================================================================
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.utils.logger import logger


# ============================================================================
# 统一的错误响应格式
# ============================================================================
# 整个项目所有错误都返回同一格式的 JSON：
#   {
#     "code":    状态码，比如 404, 422, 500
#     "message": 人类可读的错误描述
#     "data":    null（预留字段，未来可以放错误详情）
#   }
# ============================================================================

def _build_error_response(code: int, message: str) -> dict:
    """生成统一格式的错误响应体。

    参数:
        code:    HTTP 状态码
        message: 错误描述文字

    返回:
        符合项目规范的错误字典
    """
    return {"code": code, "message": message, "data": None}


# ============================================================================
# 处理器 1：HTTPException（业务异常）— 比如"任务未找到"
# ============================================================================
# FastAPI 的 HTTPException 是"预期中的异常"，
# 比如用户查了一个不存在的任务，我们主动抛出 HTTPException(status_code=404)。
# 这种情况不需要记 ERROR 日志，因为不是程序出了 bug。
# ============================================================================

async def http_exception_handler(request: Request, exc: HTTPException):
    """
    处理业务异常（HTTPException）。

    什么时候触发：
      - 用户在代码里执行了 raise HTTPException(status_code=404, detail="xxx")

    做什么：
      1. 用统一的格式包装错误信息
      2. 返回对应的状态码

    不做什么：
      - 不记录 ERROR 日志（因为是预期的业务行为，不是程序故障）
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=_build_error_response(exc.status_code, exc.detail),
    )


# ============================================================================
# 处理器 2：RequestValidationError（参数校验异常）— 比如必填字段缺失
# ============================================================================
# 当用户传的参数不符合 Pydantic 模型的校验规则时，
# FastAPI 会自动抛出 RequestValidationError。
#
# 这种错误也不会记 ERROR 日志，因为属于"用户操作不当"，
# 不是程序本身的 bug。但我们需要把错误信息整理得易读一些。
# ============================================================================

async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    """
    处理请求参数校验异常。

    什么时候触发：
      - title 字段没传（必填）
      - priority 传了 10（超出 1-5 范围）
      - task_id 传了 -1（路径参数 gt=0 校验失败）

    做什么：
      1. 提取每个字段的错误原因
      2. 组装成易读的列表
      3. 返回 422 状态码

    举例：
      用户传了 {"title": "", "priority": 10}
      返回：
      {
        "code": 422,
        "message": "请求参数校验失败: title -> 字符串长度至少为1; priority -> 输入值应小于等于5",
        "data": null
      }
    """
    # exc.errors() 返回的是一个列表，每个元素包含：
    #   loc  → 哪个字段，比如 ["body", "title"]
    #   msg  → 错误描述，比如 "field required"
    #   type → 错误类型，比如 "value_error.missing"
    errors = exc.errors()

    # 把错误列表转换成人类易读的字符串
    # 比如：title -> 字段必填; priority -> 输入值应小于等于5
    error_messages = []
    for err in errors:
        # loc 最后一个是字段名，比如 ["body", "title"] → "title"
        field = ".".join(str(x) for x in err["loc"])
        error_messages.append(f"{field} -> {err['msg']}")

    message = "请求参数校验失败: " + "; ".join(error_messages)

    return JSONResponse(
        status_code=422,
        content=_build_error_response(422, message),
    )


# ============================================================================
# 处理器 3：Exception 全局兜底 — 比如代码里有 bug
# ============================================================================
# 这是最后一道防线。当异常没有被上面两个处理器捕获时，
# 就会走到这里。这种情况通常意味着程序有 bug 或外部依赖挂了。
#
# 重要：必须记录 ERROR 日志，方便开发人员排查问题。
# 但返回给客户端的信息不能暴露堆栈细节（安全考虑）。
# ============================================================================

async def global_exception_handler(request: Request, exc: Exception):
    """
    "最后一道防线" — 处理所有未被捕获的异常。

    什么时候触发：
      - 代码里有未捕获的 bug（比如空指针、类型错误）
      - 外部服务不可用（比如数据库连不上）
      - 任何意料之外的异常

    做什么：
      1. 记录 ERROR 日志（包含完整的堆栈信息，方便排查）
      2. 返回 500 状态码，但不暴露堆栈等敏感信息

    安全原则：
      永远不要把 Python 的异常堆栈（traceback）直接返回给客户端，
      否则黑客可以利用这些信息攻击系统。
      堆栈只应该出现在日志里。
    """
    # 记录错误日志，exc_info=True 会把完整的堆栈信息也写进日志
    logger.error(
        f"未捕获异常: {exc} | 请求路径: {request.method} {request.url.path}",
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content=_build_error_response(500, "服务器内部错误"),
    )


# ============================================================================
# 注册函数 — 在 main.py 中调用
# ============================================================================
# 这个函数把上面三个处理器注册到 FastAPI 应用上。
# 注册顺序有讲究，后面再细说。
# ============================================================================

def register_exception_handlers(app: FastAPI):
    """
    将所有异常处理器注册到 FastAPI 应用。

    参数:
        app: FastAPI 应用实例

    用法（在 main.py 中）：
        from app.utils.exceptions import register_exception_handlers
        register_exception_handlers(app)

    注册顺序说明（越具体越优先）：
      1. HTTPException              → 精确匹配业务异常
      2. RequestValidationError      → 精确匹配参数校验异常
      3. Exception                  → 兜底，匹配以上都未捕获的异常

      FastAPI 匹配异常处理器时，按"最具体优先"的原则。
      Exception 是万能的父类，但前两个更具体，所以会优先匹配。
    """
    # 注意：exception_handler 的注册顺序和匹配顺序无关
    # FastAPI 内部按异常类型的继承关系决定谁优先
    # 所以 Exception 兜底虽然写在最后，但不会抢前面的
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)
