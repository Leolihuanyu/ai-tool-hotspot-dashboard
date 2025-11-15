#!/usr/bin/env python3
"""运行数据库迁移脚本

自动运行 src/database/migrations/ 目录下的所有SQL迁移文件
"""

import os
import sys
import glob
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import get_db_connection
from src.utils.logger import default_logger


def run_migrations():
    """运行所有待执行的迁移"""
    migrations_dir = Path(__file__).parent.parent / "src" / "database" / "migrations"

    if not migrations_dir.exists():
        print(f"❌ 迁移目录不存在: {migrations_dir}")
        return False

    # 获取所有 .sql 迁移文件（按文件名排序）
    migration_files = sorted(migrations_dir.glob("*.sql"))

    if not migration_files:
        print("⚠️  没有找到迁移文件")
        return True

    print(f"📦 找到 {len(migration_files)} 个迁移文件")

    # 连接数据库
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 创建 schema_version 表（如果不存在）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version VARCHAR(10) PRIMARY KEY,
                description TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("✅ schema_version 表已就绪")

        # 运行每个迁移
        for migration_file in migration_files:
            print(f"\n🔄 正在运行迁移: {migration_file.name}")

            # 读取 SQL 文件
            with open(migration_file, 'r', encoding='utf-8') as f:
                sql = f.read()

            try:
                # 执行迁移 SQL
                cursor.execute(sql)
                conn.commit()
                print(f"   ✅ {migration_file.name} 执行成功")

                # 记录日志
                default_logger.info(
                    f"迁移成功: {migration_file.name}",
                    extra={"extra_fields": {"migration_file": str(migration_file)}}
                )

            except Exception as e:
                # 如果迁移已经运行过，可能会出错（这是正常的）
                error_msg = str(e).lower()
                if "already exists" in error_msg or "duplicate" in error_msg:
                    print(f"   ⏭️  {migration_file.name} 已经执行过（跳过）")
                else:
                    print(f"   ❌ {migration_file.name} 执行失败: {e}")
                    default_logger.error(
                        f"迁移失败: {migration_file.name}",
                        extra={"extra_fields": {
                            "migration_file": str(migration_file),
                            "error": str(e)
                        }}
                    )
                conn.rollback()

        print("\n✅ 所有迁移执行完成")
        return True

    except Exception as e:
        print(f"\n❌ 迁移执行失败: {e}")
        default_logger.error(f"迁移执行失败: {e}", exc_info=True)
        return False

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    print("=" * 50)
    print("数据库迁移工具")
    print("=" * 50)

    success = run_migrations()

    print("=" * 50)

    sys.exit(0 if success else 1)
