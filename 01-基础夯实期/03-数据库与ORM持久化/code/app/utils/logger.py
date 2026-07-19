"""
================================================================================
 utils/logger.py — 结构化日志配置
================================================================================

 logging 提供了 print 做不到的四件事：
   1. 分级控制 → DEBUG / INFO / WARNING / ERROR
   2. 格式统一 → 每条日志都带时间、级别、文件名、行号
   3. 输出灵活 → 可以同时输出到控制台、文件、网络
   4. 生产可用 → 按天切割、异步写入、保留天数

 日志五级（由低到高）：
   DEBUG    10   调试信息（开发用，生产关掉）
   INFO     20   正常流程（服务启动、任务创建）
   WARNING  30   潜在问题（功能正常但需注意）
   ERROR    40   出了错误（功能受损，需排查）
   CRITICAL 50   系统要挂了（立刻处理）

 Logger、Handler、Formatter 的关系：
   Logger    = 水龙头（打开就能接水）
   Handler   = 水管（把水引到控制台、文件等地方）
   Formatter = 过滤器（决定水流出来的格式）
================================================================================
"""

import logging
import sys

# 日志格式模版
_LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | "
    "%(filename)s:%(lineno)d | %(message)s"
)
_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(name: str = "app") -> logging.Logger:
    """配置并返回一个日志器。"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 避免重复添加 Handler
    if logger.handlers:
        return logger

    # 创建格式器
    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_LOG_DATE_FORMAT)

    # 创建控制台处理器（输出到终端）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    return logger


# 模块级 logger 实例
# 其他文件中：from app.utils.logger import logger
# logger.info("xxx")  /  logger.error("xxx")  /  logger.warning("xxx")
logger = setup_logger()
