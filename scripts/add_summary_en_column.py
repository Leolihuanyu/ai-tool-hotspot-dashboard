#!/usr/bin/env python3
"""数据库迁移脚本：添加summary_en字段

这个脚本向所有相关表添加summary_en列，用于存储英文摘要。
支持SQLite和PostgreSQL两种数据库。
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


def add_summary_en_column():
    """添加summary_en列到所有相关表"""

    database_url = Config.DATABASE_URL

    if database_url.startswith('sqlite'):
        # SQLite数据库
        import sqlite3

        # 提取数据库路径
        db_path = database_url.replace('sqlite:///', '')
        if not os.path.exists(db_path):
            logger.error(f"数据库文件不存在: {db_path}")
            return False

        logger.info(f"连接到SQLite数据库: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            # 检查并添加列到ai_tools表
            cursor.execute("PRAGMA table_info(ai_tools)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'summary_en' not in columns:
                logger.info("添加summary_en列到ai_tools表...")
                cursor.execute("ALTER TABLE ai_tools ADD COLUMN summary_en TEXT DEFAULT ''")
                logger.info("✓ ai_tools表已更新")
            else:
                logger.info("ai_tools表已有summary_en列")

            # 检查并添加列到trending_topics表
            cursor.execute("PRAGMA table_info(trending_topics)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'summary_en' not in columns:
                logger.info("添加summary_en列到trending_topics表...")
                cursor.execute("ALTER TABLE trending_topics ADD COLUMN summary_en TEXT DEFAULT ''")
                logger.info("✓ trending_topics表已更新")
            else:
                logger.info("trending_topics表已有summary_en列")

            # 检查并添加列到pain_points表
            cursor.execute("PRAGMA table_info(pain_points)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'summary_en' not in columns:
                logger.info("添加summary_en列到pain_points表...")
                cursor.execute("ALTER TABLE pain_points ADD COLUMN summary_en TEXT DEFAULT ''")
                logger.info("✓ pain_points表已更新")
            else:
                logger.info("pain_points表已有summary_en列")

            conn.commit()
            logger.info("✅ SQLite数据库迁移完成")

        except Exception as e:
            logger.error(f"SQLite迁移失败: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    else:
        # PostgreSQL数据库
        import psycopg2

        logger.info("连接到PostgreSQL数据库...")

        try:
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()

            # 添加列到ai_tools表（IF NOT EXISTS避免重复添加）
            logger.info("检查并添加summary_en列到ai_tools表...")
            cursor.execute("""
                ALTER TABLE ai_tools
                ADD COLUMN IF NOT EXISTS summary_en TEXT DEFAULT ''
            """)

            # 添加列到trending_topics表
            logger.info("检查并添加summary_en列到trending_topics表...")
            cursor.execute("""
                ALTER TABLE trending_topics
                ADD COLUMN IF NOT EXISTS summary_en TEXT DEFAULT ''
            """)

            # 添加列到pain_points表
            logger.info("检查并添加summary_en列到pain_points表...")
            cursor.execute("""
                ALTER TABLE pain_points
                ADD COLUMN IF NOT EXISTS summary_en TEXT DEFAULT ''
            """)

            conn.commit()
            logger.info("✅ PostgreSQL数据库迁移完成")

        except Exception as e:
            logger.error(f"PostgreSQL迁移失败: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    return True


def verify_migration():
    """验证迁移是否成功"""

    database_url = Config.DATABASE_URL

    if database_url.startswith('sqlite'):
        import sqlite3
        db_path = database_url.replace('sqlite:///', '')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查各表的列
        for table in ['ai_tools', 'trending_topics', 'pain_points']:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [column[1] for column in cursor.fetchall()]
            if 'summary_en' in columns:
                logger.info(f"✓ {table}表包含summary_en列")
            else:
                logger.warning(f"✗ {table}表缺少summary_en列")

        conn.close()

    else:
        import psycopg2
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        # 检查各表的列
        for table in ['ai_tools', 'trending_topics', 'pain_points']:
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = %s AND column_name = 'summary_en'
            """, (table,))

            if cursor.fetchone():
                logger.info(f"✓ {table}表包含summary_en列")
            else:
                logger.warning(f"✗ {table}表缺少summary_en列")

        conn.close()


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("数据库迁移：添加summary_en字段")
    logger.info("=" * 50)

    # 执行迁移
    if add_summary_en_column():
        logger.info("\n验证迁移结果...")
        verify_migration()
        logger.info("\n✅ 迁移脚本执行完成")
    else:
        logger.error("\n❌ 迁移失败，请检查错误日志")
        sys.exit(1)