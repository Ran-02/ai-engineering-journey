"""
================================================================================
 utils/logger.py — 结构化日志配置
================================================================================

 为什么不用 print？看一个对比：

     print(f"创建任务：{title}")        ← 只有文字，不知道时间、不知道在哪打印的
     logger.info(f"创建任务：{title}")   ← 有颜色、有时间、有文件名、有行号

 logging 模块提供了四个关键能力：
   1. 分级控制 → DEBUG / INFO / WARNING / ERROR，可以按级别过滤
   2. 格式统一 → 每条日志都包含时间、级别、模块名、内容
   3. 输出灵活 → 同时输出到控制台和文件
   4. 生产可用 → 按天切割、保留天数、异步写入

 日志五级（由低到高）：
   DEBUG    10   调试信息，开发时用的（生产环境关掉）
   INFO     20   正常流程，比如"服务已启动"、"任务创建成功"
   WARNING  30   潜在问题，功能正常但需要注意
   ERROR    40   出了错误，功能受影响，需要排查
   CRITICAL 50   系统要挂了，立刻处理

 通俗理解：日志就是给程序装了一个"黑匣子"，
 出了问题时翻日志就像飞机失事找黑匣子一样，能知道当时发生了什么。
================================================================================
"""

import logging
import sys

# ============================================================================
# 日志格式模板
# ============================================================================
# 这是一个模版字符串，Python 会在打印日志时自动填充这些占位符。
#
# 各个占位符的含义：
#   %(asctime)s       → 时间，比如 "2026-01-15 14:30:22"
#   %(levelname)-8s   → 日志级别（-8s 表示固定宽度8个字符，右对齐）
#                       输出效果：INFO    ERROR
#   %(name)s          → Logger 的名字，这里是 "app"
#   %(filename)s      → 哪个文件打的日志，比如 "task.py"
#   %(lineno)d        → 哪一行代码打的日志，比如 "42"
#   %(message)s       → 日志正文内容
#
# 最终效果类似：
#   2026-01-15 14:30:22 | INFO    | app | task.py:42 | 创建任务成功
# ============================================================================
_LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | "
    "%(filename)s:%(lineno)d | %(message)s"
)

_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# ============================================================================
# setup_logger — 创建一个配置好的日志器
# ============================================================================
# 这个函数封装了 logging 的初始化配置，项目启动时调用一次即可。
# 之后在其他文件中只需要 from app.utils.logger import logger 就能用了。
#
# Logger、Handler、Formatter 的关系（记住三个角色）：
#   Logger      = 水龙头（你打开它就能接水）
#   Handler     = 水管（把水引到不同地方：控制台、文件、网络）
#   Formatter   = 过滤器（决定水流出来的样子：加不加时间戳）
# ============================================================================

def setup_logger(name: str = "app") -> logging.Logger:
    """
    配置并返回一个日志器。

    参数:
        name: Logger 的名称，默认 "app"。
              用名字区分不同模块的日志，方便排查。

    返回:
        一个配置好的 Logger 实例。
    """

    # ---- 1. 创建 Logger（水龙头） ----
    # getLogger 是"单例模式"：同名 Logger 只会创建一次，后面都是获取同一个
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # 最低接收 DEBUG 级别，往上都接收

    # ========================================================================
    # 小知识：为什么要判断 handlers 是否为空？
    # 因为 getLogger("app") 在同一个进程内是单例，
    # 如果多次调用 setup_logger，会重复添加 Handler，导致日志打两遍。
    # 这个判断保证了只添加一次。
    # ========================================================================
    if logger.handlers:
        return logger  # 已经有处理器了，直接返回

    # ---- 2. 创建 Formatter（过滤器） ----
    # 决定日志长什么样
    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_LOG_DATE_FORMAT)

    # ---- 3. 创建 Handler（水管）----
    # 这里只创建一个"控制台 Handler"，
    # 所有日志都会打印到终端（就是运行 uvicorn 的那个黑窗口）

    # StreamHandler 默认输出到 sys.stderr
    # 我们用 sys.stdout 让它输出到标准输出（和控制台直接显示的内容在一起）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)  # 这个处理器接收 DEBUG 及以上
    console_handler.setFormatter(formatter)  # 套上我们定义的格式

    # ---- 4. 把 Handler 装到 Logger 上 ----
    # 相当于：水龙头（Logger） + 水管（Handler）+ 过滤器（Formatter）
    # 这样一打开 Logger，日志就会按我们定义的格式输出到控制台
    logger.addHandler(console_handler)

    return logger


# ============================================================================
# 模块级别的 logger 实例
# ============================================================================
# 在其他文件中这样用：
#   from app.utils.logger import logger
#   logger.info("xxx")       # 普通信息
#   logger.error("xxx")      # 错误信息
#   logger.warning("xxx")    # 警告信息
#   logger.debug("xxx")      # 调试信息（开发用）
#   logger.exception("xxx")  # 错误信息 + 自动附加异常堆栈（只在 except 块里用）
# ============================================================================
logger = setup_logger()
