from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.utils.logger import logger

def _build_error_response(code: int, message: str) -> dict:
    
    return {"code": code, "message": message, "data": None}

async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=_build_error_response(exc.status_code, exc.detail),
    )

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

async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"未捕获异常: {exc} | 请求路径: {request.method} {request.url.path}",
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content=_build_error_response(500, "服务器内部错误"),
    )


def register_exception_handlers(app: FastAPI):
   
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)
