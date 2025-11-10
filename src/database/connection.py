"""数据库连接管理

提供SQLite和PostgreSQL数据库连接的创建和管理。
支持通过环境变量切换数据库类型。
"""

import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator, Union, Any
from src.utils.config import config

# 尝试导入PostgreSQL驱动
try:
    import psycopg2
    import psycopg2.extras
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False

# 数据库连接类型
Connection = Union[sqlite3.Connection, Any]  # Any是为了兼容psycopg2.connection


def get_db_type() -> str:
    """获取配置的数据库类型

    Returns:
        'postgresql' 或 'sqlite'
    """
    db_type = os.getenv('DB_TYPE', 'sqlite').lower()

    if db_type == 'postgresql' and not HAS_POSTGRES:
        raise RuntimeError(
            "PostgreSQL support requested but psycopg2 is not installed. "
            "Install with: pip install psycopg2-binary"
        )

    return db_type


def get_connection(database_path: str = None) -> Connection:
    """获取数据库连接

    根据环境变量 DB_TYPE 决定使用哪种数据库：
    - DB_TYPE=postgresql: 使用PostgreSQL (从 DATABASE_URL 读取连接串)
    - DB_TYPE=sqlite: 使用SQLite (从 database_path 或 DATABASE_PATH 读取)

    Args:
        database_path: SQLite数据库文件路径(仅SQLite使用，默认从配置读取)

    Returns:
        数据库连接对象 (sqlite3.Connection 或 psycopg2.connection)
    """
    db_type = get_db_type()

    if db_type == 'postgresql':
        return _get_postgres_connection()
    else:
        return _get_sqlite_connection(database_path)


def _get_postgres_connection():
    """获取PostgreSQL连接"""
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        raise ValueError(
            "DATABASE_URL environment variable is not set. "
            "Example: postgresql://user:password@host:5432/database"
        )

    # 创建PostgreSQL连接
    conn = psycopg2.connect(database_url)

    # 使用RealDictCursor以便通过列名访问(类似SQLite的Row)
    conn.cursor_factory = psycopg2.extras.RealDictCursor

    return conn


def _get_sqlite_connection(database_path: str = None) -> sqlite3.Connection:
    """获取SQLite连接"""
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
def get_db_connection(database_path: str = None) -> Generator[Connection, None, None]:
    """数据库连接上下文管理器

    自动处理事务提交/回滚和连接关闭。
    支持SQLite和PostgreSQL。

    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")

    Args:
        database_path: SQLite数据库文件路径(仅SQLite使用，默认从配置读取)

    Yields:
        数据库连接对象
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

    注意：
    - SQLite: 使用 executescript()，支持多条语句
    - PostgreSQL: 需要手动分割语句执行

    Args:
        sql_script: SQL脚本内容
        database_path: SQLite数据库文件路径(仅SQLite使用，默认从配置读取)
    """
    db_type = get_db_type()

    with get_db_connection(database_path) as conn:
        cursor = conn.cursor()

        if db_type == 'postgresql':
            # PostgreSQL需要逐条执行语句
            # 移除注释和空行，然后按分号分割
            statements = [
                stmt.strip()
                for stmt in sql_script.split(';')
                if stmt.strip() and not stmt.strip().startswith('--')
            ]

            for statement in statements:
                if statement:
                    cursor.execute(statement)
        else:
            # SQLite可以直接使用executescript
            conn.executescript(sql_script)


def convert_placeholder(query: str, db_type: str = None) -> str:
    """转换SQL占位符

    SQLite使用 ? 作为占位符
    PostgreSQL使用 %s 作为占位符

    Args:
        query: SQL查询语句
        db_type: 数据库类型(None则自动检测)

    Returns:
        转换后的查询语句
    """
    if db_type is None:
        db_type = get_db_type()

    if db_type == 'postgresql':
        # 将 ? 替换为 %s
        return query.replace('?', '%s')

    return query


# 向后兼容的别名
get_sqlite_connection = _get_sqlite_connection
