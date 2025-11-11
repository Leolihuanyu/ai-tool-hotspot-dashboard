#!/usr/bin/env python3
"""
数据库迁移脚本：添加language字段到users表
用于邮件多语言支持

执行方式:
    python scripts/migrate_add_language.py
"""

import sqlite3
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import default_logger


def get_db_path():
    """获取数据库路径"""
    db_path = os.getenv('DATABASE_PATH', 'data/hotspot.db')
    return db_path


def check_column_exists(cursor, table_name, column_name):
    """检查表中是否已存在指定列"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def migrate_add_language_field():
    """
    添加language字段到users表

    执行步骤：
    1. 检查language字段是否已存在
    2. 如果不存在，添加该字段
    3. 为现有用户设置默认语言为'zh'（因为历史邮件都是中文）
    """
    db_path = get_db_path()

    if not os.path.exists(db_path):
        default_logger.error(f"数据库文件不存在: {db_path}")
        return False

    default_logger.info(f"开始迁移数据库: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. 检查language字段是否已存在
        if check_column_exists(cursor, 'users', 'language'):
            default_logger.info("✅ language字段已存在，无需迁移")
            conn.close()
            return True

        default_logger.info("🔧 开始添加language字段...")

        # 2. 添加language字段
        # SQLite的ALTER TABLE ADD COLUMN语法
        alter_sql = """
        ALTER TABLE users
        ADD COLUMN language TEXT DEFAULT 'en' CHECK(language IN ('en', 'ja', 'zh'))
        """

        cursor.execute(alter_sql)
        default_logger.info("✅ language字段添加成功")

        # 3. 为所有现有用户显式设置语言为'en'（确保数据一致性）
        update_sql = """
        UPDATE users
        SET language = 'en'
        WHERE language IS NULL
        """

        cursor.execute(update_sql)
        updated_count = cursor.rowcount
        default_logger.info(f"✅ 已为 {updated_count} 个现有用户设置默认语言为'en'")

        # 4. 提交更改
        conn.commit()
        default_logger.info("✅ 数据库迁移完成！")

        # 5. 验证迁移结果
        cursor.execute("SELECT COUNT(*) FROM users WHERE language IS NOT NULL")
        total_users = cursor.fetchone()[0]
        default_logger.info(f"📊 验证：{total_users} 个用户有语言设置")

        conn.close()
        return True

    except sqlite3.Error as e:
        default_logger.error(f"❌ 数据库迁移失败: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False
    except Exception as e:
        default_logger.error(f"❌ 迁移过程出错: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False


def verify_migration():
    """验证迁移是否成功"""
    db_path = get_db_path()

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查字段是否存在
        if not check_column_exists(cursor, 'users', 'language'):
            default_logger.error("❌ 验证失败：language字段不存在")
            conn.close()
            return False

        # 检查现有用户的语言设置
        cursor.execute("SELECT language, COUNT(*) FROM users GROUP BY language")
        lang_stats = cursor.fetchall()

        default_logger.info("📊 用户语言分布：")
        for lang, count in lang_stats:
            default_logger.info(f"  - {lang}: {count} 用户")

        conn.close()
        return True

    except Exception as e:
        default_logger.error(f"❌ 验证失败: {str(e)}")
        if 'conn' in locals():
            conn.close()
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("数据库迁移：添加邮件语言偏好支持")
    print("=" * 60)

    # 执行迁移
    success = migrate_add_language_field()

    if success:
        print("\n" + "=" * 60)
        print("验证迁移结果...")
        print("=" * 60)
        verify_migration()
        print("\n✅ 迁移成功！用户表现已支持多语言邮件功能。")
    else:
        print("\n❌ 迁移失败！请检查日志并手动修复。")
        sys.exit(1)
