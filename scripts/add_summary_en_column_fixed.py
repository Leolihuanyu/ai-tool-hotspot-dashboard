#!/usr/bin/env python3
"""数据库迁移脚本：添加summary_en字段

这个脚本向所有相关表添加summary_en列，用于存储英文摘要。
支持SQLite和PostgreSQL两种数据库。
"""

import os
import sys
import sqlite3

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


def add_summary_en_column():
    """添加summary_en列到所有相关表"""

    config = Config()
    db_path = config.database_path

    # 检查数据库文件是否存在
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

    return True


def verify_migration():
    """验证迁移是否成功"""

    config = Config()
    db_path = config.database_path

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