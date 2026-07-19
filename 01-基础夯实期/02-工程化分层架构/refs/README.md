# 任务管理系统 · 工程化分层升级版

第2周实战项目 — 在第一周单文件基础上完成工程化分层改造。

## 项目结构

```
code/
├── app/
│   ├── __init__.py              # Python 包标识
│   ├── main.py                  # 应用主入口（总装车间）
│   ├── routers/
│   │   ├── __init__.py
│   │   └── task.py              # 任务管理接口（5个CRUD）
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── task.py              # 数据模型（TaskCreate / Task）
│   └── utils/
│       ├── __init__.py
│       ├── exceptions.py         # 全局异常处理器
│       └── logger.py            # 结构化日志配置
└── README.md
```

## 核心能力

| 特性 | 说明 |
|---|---|
| **APIRouter 模块化** | 按业务拆分路由，prefix + tags 自动分组 |
| **分层架构** | schemas(模型) → routers(路由) → utils(工具) |
| **全局异常** | HTTPException / 422校验 / 500兜底，统一错误格式 |
| **请求耗时中间件** | 洋葱模型 + X-Process-Time 响应头 |
| **结构化日志** | logging 替代 print，分级输出 |

## 启动方式

```bash
# 安装依赖
pip install fastapi uvicorn

# 启动服务
cd code
python -m app.main
# 或
uvicorn app.main:app --reload
```

- 接口文档：http://127.0.0.1:8000/docs
- 根路径：http://127.0.0.1:8000/

## 各层职责

| 层级 | 文件 | 职责 |
|---|---|---|
| **入口层** | `main.py` | 应用创建、组件注册、启动 |
| **路由层** | `routers/task.py` | URL 分发、参数校验 |
| **模型层** | `schemas/task.py` | 数据定义、请求/响应格式 |
| **异常层** | `utils/exceptions.py` | 统一错误处理 |
| **日志层** | `utils/logger.py` | 日志配置与输出 |
