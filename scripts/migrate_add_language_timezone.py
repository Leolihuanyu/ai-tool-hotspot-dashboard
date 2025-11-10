#!/usr/bin/env python3
"""
数据库迁移：添加 language 和 timezone 字段到 users 表

支持：
- PostgreSQL (Supabase生产环境)
- SQLite (本地开发)
"""

import os
import sys

# 设置环境变量（如果需要）
if len(sys.argv) > 1 and sys.argv[1] == '--production':
    os.environ['DB_TYPE'] = 'postgresql'
    print("🔧 模式：生产环境（PostgreSQL）")
else:
    print("🔧 模式：本地开发（SQLite）")

from src.database.connection import get_connection, convert_placeholder
from src.utils.logger import get_logger

logger = get_logger(__name__)


def check_column_exists(cursor, table_name: str, column_name: str) -> bool:
    """检查列是否已存在"""
    try:
        # PostgreSQL
        if os.getenv('DB_TYPE') == 'postgresql':
            query = """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = %s AND column_name = %s
            """
            cursor.execute(query, (table_name, column_name))
        # SQLite
        else:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            return column_name in columns

        result = cursor.fetchone()
        return result is not None
    except Exception as e:
        logger.error(f"检查列失败: {e}")
        return False


def migrate():
    """执行迁移"""
    print("=" * 60)
    print("数据库迁移：添加 language 和 timezone 字段")
    print("=" * 60)

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 检查 language 字段
        print("\n[1/2] 检查 language 字段...")
        if check_column_exists(cursor, 'users', 'language'):
            print("✓ language 字段已存在，跳过")
        else:
            print("  添加 language 字段...")
            if os.getenv('DB_TYPE') == 'postgresql':
                cursor.execute("""
                    ALTER TABLE users
                    ADD COLUMN language VARCHAR(10) DEFAULT 'zh'
                """)
            else:
                cursor.execute("""
                    ALTER TABLE users
                    ADD COLUMN language TEXT DEFAULT 'zh'
                """)
            print("✓ language 字段添加成功")

        # 检查 timezone 字段
        print("\n[2/2] 检查 timezone 字段...")
        if check_column_exists(cursor, 'users', 'timezone'):
            print("✓ timezone 字段已存在，跳过")
        else:
            print("  添加 timezone 字段...")
            if os.getenv('DB_TYPE') == 'postgresql':
                cursor.execute("""
                    ALTER TABLE users
                    ADD COLUMN timezone VARCHAR(50) DEFAULT 'UTC'
                """)
            else:
                cursor.execute("""
                    ALTER TABLE users
                    ADD COLUMN timezone TEXT DEFAULT 'UTC'
                """)
            print("✓ timezone 字段添加成功")

        # 提交事务
        conn.commit()

        # 验证
        print("\n[验证] 检查users表结构...")
        if os.getenv('DB_TYPE') == 'postgresql':
            cursor.execute("""
                SELECT column_name, data_type, column_default
                FROM information_schema.columns
                WHERE table_name = 'users'
                  AND column_name IN ('language', 'timezone')
                ORDER BY column_name
            """)
            for row in cursor.fetchall():
                col_name = row[0] if isinstance(row, tuple) else row['column_name']
                data_type = row[1] if isinstance(row, tuple) else row['data_type']
                col_default = row[2] if isinstance(row, tuple) else row['column_default']
                print(f"  ✓ {col_name}: {data_type}, 默认值={col_default}")
        else:
            cursor.execute("PRAGMA table_info(users)")
            columns = cursor.fetchall()
            for col in columns:
                if col[1] in ['language', 'timezone']:
                    print(f"  ✓ {col[1]}: {col[2]}, 默认值={col[4]}")

        conn.close()

        print("\n" + "=" * 60)
        print("✅ 迁移完成！")
        print("=" * 60)
        print("\n新增字段：")
        print("  - language: 用户语言偏好（zh/en/ja）")
        print("  - timezone: 用户时区（如 Asia/Shanghai）")
        print("\n影响：")
        print("  - 注册时可以保存用户语言和时区")
        print("  - 过期提醒邮件可以按时区发送")
        print("  - 邮件内容使用用户语言")

        return True

    except Exception as e:
        logger.error(f"迁移失败: {str(e)}")
        print(f"\n❌ 迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
