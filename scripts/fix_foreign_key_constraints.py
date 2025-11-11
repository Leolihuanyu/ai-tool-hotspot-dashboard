#!/usr/bin/env python3
"""
修复数据库外键约束

问题：access_logs, referrals, invite_codes 表的外键约束缺少 ON DELETE 和 ON UPDATE 子句
导致无法删除或更新被引用的用户

解决方案：重新创建外键约束，添加 ON DELETE CASCADE 和 ON UPDATE CASCADE

使用方法：
    python scripts/fix_foreign_key_constraints.py
"""

import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import get_connection, get_db_type
from src.utils.logger import default_logger


def fix_foreign_key_constraints():
    """修复所有外键约束，添加 CASCADE 策略"""

    db_type = get_db_type()

    if db_type != 'postgresql':
        default_logger.error("此脚本仅支持 PostgreSQL 数据库")
        default_logger.info(f"当前数据库类型: {db_type}")
        return False

    default_logger.info("=" * 60)
    default_logger.info("开始修复外键约束...")
    default_logger.info("=" * 60)

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 1. 修复 access_logs 表的外键约束
        default_logger.info("\n[1/3] 修复 access_logs 表的外键约束...")

        # 删除旧约束
        cursor.execute("""
            ALTER TABLE access_logs
            DROP CONSTRAINT IF EXISTS access_logs_email_fkey
        """)
        default_logger.info("  ✓ 已删除旧的 access_logs_email_fkey 约束")

        # 重新创建约束（带 CASCADE）
        cursor.execute("""
            ALTER TABLE access_logs
            ADD CONSTRAINT access_logs_email_fkey
                FOREIGN KEY (email)
                REFERENCES users(email)
                ON DELETE CASCADE
                ON UPDATE CASCADE
        """)
        default_logger.info("  ✓ 已重新创建 access_logs_email_fkey 约束（ON DELETE CASCADE）")

        # 2. 修复 referrals 表的外键约束
        default_logger.info("\n[2/3] 修复 referrals 表的外键约束...")

        # referrer_email 约束
        cursor.execute("""
            ALTER TABLE referrals
            DROP CONSTRAINT IF EXISTS referrals_referrer_email_fkey
        """)
        default_logger.info("  ✓ 已删除旧的 referrals_referrer_email_fkey 约束")

        cursor.execute("""
            ALTER TABLE referrals
            ADD CONSTRAINT referrals_referrer_email_fkey
                FOREIGN KEY (referrer_email)
                REFERENCES users(email)
                ON DELETE CASCADE
                ON UPDATE CASCADE
        """)
        default_logger.info("  ✓ 已重新创建 referrals_referrer_email_fkey 约束（ON DELETE CASCADE）")

        # referee_email 约束
        cursor.execute("""
            ALTER TABLE referrals
            DROP CONSTRAINT IF EXISTS referrals_referee_email_fkey
        """)
        default_logger.info("  ✓ 已删除旧的 referrals_referee_email_fkey 约束")

        cursor.execute("""
            ALTER TABLE referrals
            ADD CONSTRAINT referrals_referee_email_fkey
                FOREIGN KEY (referee_email)
                REFERENCES users(email)
                ON DELETE CASCADE
                ON UPDATE CASCADE
        """)
        default_logger.info("  ✓ 已重新创建 referrals_referee_email_fkey 约束（ON DELETE CASCADE）")

        # 3. 修复 invite_codes 表的外键约束
        default_logger.info("\n[3/3] 修复 invite_codes 表的外键约束...")

        cursor.execute("""
            ALTER TABLE invite_codes
            DROP CONSTRAINT IF EXISTS invite_codes_generated_by_fkey
        """)
        default_logger.info("  ✓ 已删除旧的 invite_codes_generated_by_fkey 约束")

        cursor.execute("""
            ALTER TABLE invite_codes
            ADD CONSTRAINT invite_codes_generated_by_fkey
                FOREIGN KEY (generated_by)
                REFERENCES users(email)
                ON DELETE SET NULL
                ON UPDATE CASCADE
        """)
        default_logger.info("  ✓ 已重新创建 invite_codes_generated_by_fkey 约束（ON DELETE SET NULL）")

        # 提交更改
        conn.commit()

        # 验证约束已正确创建
        default_logger.info("\n" + "=" * 60)
        default_logger.info("验证外键约束...")
        default_logger.info("=" * 60)

        cursor.execute("""
            SELECT
                conname AS constraint_name,
                conrelid::regclass AS table_name,
                CASE confdeltype
                    WHEN 'a' THEN 'NO ACTION'
                    WHEN 'r' THEN 'RESTRICT'
                    WHEN 'c' THEN 'CASCADE'
                    WHEN 'n' THEN 'SET NULL'
                    WHEN 'd' THEN 'SET DEFAULT'
                END AS on_delete,
                CASE confupdtype
                    WHEN 'a' THEN 'NO ACTION'
                    WHEN 'r' THEN 'RESTRICT'
                    WHEN 'c' THEN 'CASCADE'
                    WHEN 'n' THEN 'SET NULL'
                    WHEN 'd' THEN 'SET DEFAULT'
                END AS on_update
            FROM pg_constraint
            WHERE conname IN (
                'access_logs_email_fkey',
                'referrals_referrer_email_fkey',
                'referrals_referee_email_fkey',
                'invite_codes_generated_by_fkey'
            )
            ORDER BY conname
        """)

        results = cursor.fetchall()

        for row in results:
            constraint_name, table_name, on_delete, on_update = row
            default_logger.info(f"  ✓ {constraint_name}")
            default_logger.info(f"    表: {table_name}")
            default_logger.info(f"    ON DELETE: {on_delete}")
            default_logger.info(f"    ON UPDATE: {on_update}")

        cursor.close()
        conn.close()

        default_logger.info("\n" + "=" * 60)
        default_logger.info("✅ 外键约束修复完成！")
        default_logger.info("=" * 60)

        return True

    except Exception as e:
        default_logger.error(f"\n❌ 修复外键约束失败: {str(e)}")
        import traceback
        default_logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = fix_foreign_key_constraints()
    sys.exit(0 if success else 1)
