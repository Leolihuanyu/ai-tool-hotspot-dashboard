"""数据库模块

导出数据库连接和初始化功能。
"""

from src.database.connection import get_connection, get_db_connection, execute_script
from src.database.init import init_database

__all__ = [
    "get_connection",
    "get_db_connection",
    "execute_script",
    "init_database",
]
