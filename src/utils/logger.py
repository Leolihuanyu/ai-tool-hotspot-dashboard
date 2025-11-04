"""结构化日志工具

实现JSON格式的结构化日志,遵循宪法原则VI(可重现性)。
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """JSON格式的日志格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        """将日志记录格式化为JSON

        Args:
            record: 日志记录对象

        Returns:
            JSON格式的日志字符串
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 添加额外字段
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data, ensure_ascii=False)


def setup_logger(
    name: str,
    log_level: str = "INFO",
    log_file: str = None,
    json_format: bool = True
) -> logging.Logger:
    """设置并返回配置好的日志记录器

    Args:
        name: 日志记录器名称
        log_level: 日志级别(DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径(可选)
        json_format: 是否使用JSON格式

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))

    if json_format:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )

    logger.addHandler(console_handler)

    # 文件处理器(可选)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, log_level.upper()))

        if json_format:
            file_handler.setFormatter(JSONFormatter())
        else:
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )

        logger.addHandler(file_handler)

    return logger


def log_with_context(logger: logging.Logger, level: str, message: str, **kwargs) -> None:
    """记录带上下文信息的日志

    Args:
        logger: 日志记录器
        level: 日志级别
        message: 日志消息
        **kwargs: 额外的上下文字段
    """
    log_func = getattr(logger, level.lower())
    extra = {"extra_fields": kwargs}
    log_func(message, extra=extra)


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志记录器(便捷函数)

    Args:
        name: 日志记录器名称

    Returns:
        配置好的日志记录器
    """
    return setup_logger(
        name=name,
        log_level="INFO",
        log_file="logs/app.log",
        json_format=True
    )


# 创建默认日志记录器
default_logger = setup_logger(
    "ai-dashboard",
    log_level="INFO",
    log_file="logs/app.log",
    json_format=True
)
