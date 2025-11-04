"""数据库连接管理

提供SQLite数据库连接的创建和管理。
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator
from src.utils.config import config


def get_connection(database_path: str = None) -> sqlite3.Connection:
    """获取数据库连接

    Args:
        database_path: 数据库文件路径(默认从配置读取)

    Returns:
        SQLite连接对象
    """
    if database_path is None:
        database_path = config.database_path

    # 确保数据库目录存在
    db_path = Path(database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # 创建连接
    conn = sqlite3.connect(database_path)

    # 设置Row Factory以便通过列名访问
    conn.row_factory = sqlite3.Row

    # 启用外键约束
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


@contextmanager
def get_db_connection(database_path: str = None) -> Generator[sqlite3.Connection, None, None]:
    """数据库连接上下文管理器

    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ai_tools")

    Args:
        database_path: 数据库文件路径(默认从配置读取)

    Yields:
        SQLite连接对象
    """
    conn = get_connection(database_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute_script(sql_script: str, database_path: str = None) -> None:
    """执行SQL脚本

    Args:
        sql_script: SQL脚本内容
        database_path: 数据库文件路径(默认从配置读取)
    """
    with get_db_connection(database_path) as conn:
        conn.executescript(sql_script)
