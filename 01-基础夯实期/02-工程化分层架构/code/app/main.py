import time
from fastapi import FastAPI, Request
from app.routers.task import router as task_router
from app.utils.exceptions import register_exception_handlers
from app.utils.logger import logger

app = FastAPI(
    title="任务管理系统",
    description="第2周工程化分层架构实战 — APIRouter + 全局异常 + 中间件 + 结构化日志",
    version="2.0.0",
)

register_exception_handlers(app)
logger.info("✅ 异常处理器注册完成")

@app.middleware("http")
async def process_time_middleware(request: Request, call_next):
    start_time = time.perf_counter()

    logger.info(f"→ {request.method} {request.url.path}")

    response = await call_next(request)

    elapsed = time.perf_counter() - start_time

    response.headers["X-Process-Time"] = f"{elapsed:.4f}"

    logger.info(
        f"← {request.method} {request.url.path} "
        f"[{response.status_code}] {elapsed:.4f}s"
    )

    return response

app.include_router(task_router)
logger.info("✅ 路由注册完成")


@app.get("/", summary="根路径欢迎")
def root():
    return {"message": "欢迎使用任务管理系统"}

if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 启动服务: http://127.0.0.1:8000")
    logger.info("📖 接口文档: http://127.0.0.1:8000/docs")
    uvicorn.run("app.main:app", reload=True)
