"""数据库初始化

执行数据库Schema创建。
"""

from pathlib import Path
from src.database.connection import execute_script
from src.utils.logger import default_logger


def init_database(database_path: str = None) -> bool:
    """初始化数据库

    读取schema.sql并执行,创建所有表和索引。

    Args:
        database_path: 数据库文件路径(默认从配置读取)

    Returns:
        True如果初始化成功,False如果失败
    """
    try:
        # 读取schema.sql
        schema_file = Path(__file__).parent / "schema.sql"
        if not schema_file.exists():
            default_logger.error(f"Schema file not found: {schema_file}")
            return False

        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        # 执行schema
        execute_script(schema_sql, database_path)

        default_logger.info(
            "Database initialized successfully",
            extra={"extra_fields": {"database_path": database_path}}
        )
        return True

    except Exception as e:
        default_logger.error(
            f"Failed to initialize database: {e}",
            extra={"extra_fields": {"error": str(e)}}
        )
        return False
