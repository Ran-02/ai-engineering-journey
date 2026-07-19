"""
================================================================================
 utils/exceptions.py — 全局异常处理器
================================================================================

 本文件处理三类异常，统一返回格式为：
   {
     "code":    HTTP 状态码,
     "message": 人类可读的错误描述,
     "data":    null
   }

 三类异常的优先级：
   1. HTTPException（业务异常） — 如 404 资源未找到
   2. RequestValidationError（参数校验异常） — 如字段缺失或越界
   3. Exception 兜底（未知异常） — 如代码里有 bug，返回 500 但不暴露堆栈
================================================================================
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.utils.logger import logger


def _build_error_response(code: int, message: str) -> dict:
    """生成统一格式的错误响应体。"""
    return {"code": code, "message": message, "data": None}


# ============================================================================
# 处理器 1：HTTPException（业务异常）
# ============================================================================
# 比如"任务未找到"这种可预料的业务异常。
# 不记 ERROR 日志，因为是预期行为，不是程序 bug。
# ============================================================================

async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=_build_error_response(exc.status_code, exc.detail),
    )


# ============================================================================
# 处理器 2：RequestValidationError（参数校验异常）
# ============================================================================
# 比如 title 超长、priority 越界、task_id 为负数等。
# 把 FastAPI 默认的校验错误格式化为人类易读的文字。
# ============================================================================

async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    errors = exc.errors()
    error_messages = []
    for err in errors:
        field = ".".join(str(x) for x in err["loc"])
        error_messages.append(f"{field} -> {err['msg']}")

    message = "请求参数校验失败: " + "; ".join(error_messages)

    return JSONResponse(
        status_code=422,
        content=_build_error_response(422, message),
    )


# ============================================================================
# 处理器 3：Exception 全局兜底
# ============================================================================
# 最后一道防线，捕获所有意料之外的异常。
# 记录 ERROR 日志（含完整堆栈），但返回给客户端的只有通用提示。
# ============================================================================

async def global_exception_handler(request: Request, exc: Exception):
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

def register_exception_handlers(app: FastAPI):
    """将所有异常处理器注册到 FastAPI 应用。"""
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)
