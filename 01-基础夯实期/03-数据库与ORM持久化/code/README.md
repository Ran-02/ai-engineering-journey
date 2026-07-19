# 任务管理系统 · 数据库持久化版

第3周实战项目 — 将第二周的内存存储替换为 SQLite + SQLAlchemy 持久化存储。

## 项目结构

```
code/
├── app/
│   ├── __init__.py            # Python 包标识
│   ├── main.py                # 应用主入口 + 生命周期管理
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py        # 三大组件：Engine / SessionLocal / Base + get_db
│   │   └── models.py          # 数据库模型：TaskDB（tasks 表）
│   ├── routers/
│   │   ├── __init__.py
│   │   └── task.py            # CRUD 接口（数据库版）
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── task.py            # 接口模型：TaskCreate / TaskResponse
│   └── utils/
│       ├── __init__.py
│       ├── exceptions.py      # 全局异常处理器
│       └── logger.py          # 结构化日志
├── task.db                    # SQLite 数据库文件（自动生成）
└── README.md
```

## 相比第 2 周的升级

| 特性 | 第 2 周（内存版） | 第 3 周（数据库版） |
|---|---|---|
| 数据存储 | Python 列表 | SQLite 数据库文件 |
| 数据生命周期 | 程序重启后丢失 | 持久化保存 |
| ID 生成 | `next_id` 计数器 | 数据库自增主键 |
| 查询方式 | 遍历列表 O(n) | 主键索引 O(1) |
| 新建模块 | — | `db/` 目录：database.py + models.py |
| 双层模型 | 仅接口模型 | DB 模型 + 接口模型分离 |
| 响应模型 | 直接返回 | `response_model` + `from_attributes` |
| 启动建表 | 无 | lifespan 中自动执行 |

## 启动方式

```bash
pip install fastapi uvicorn sqlalchemy

cd code
uvicorn app.main:app --reload
```

- 接口文档：http://127.0.0.1:8000/docs
- 数据库文件：项目目录下自动生成 `task.db`

## 数据持久化验证

```bash
# 1. 启动服务，创建几个任务
curl -X POST http://127.0.0.1:8000/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"title": "买菜", "priority": 3}'

# 2. 停止服务（Ctrl+C）

# 3. 重启服务
uvicorn app.main:app --reload

# 4. 查询——数据还在！
curl http://127.0.0.1:8000/tasks/
```
