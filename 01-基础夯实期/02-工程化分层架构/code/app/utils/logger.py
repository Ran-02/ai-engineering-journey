import logging
import sys

_LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | "
    "%(filename)s:%(lineno)d | %(message)s"
)

_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logger(name: str = "app") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  
    if logger.handlers:
        return logger  
    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_LOG_DATE_FORMAT)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG) 
    console_handler.setFormatter(formatter)  
    logger.addHandler(console_handler)

    return logger

logger = setup_logger()
