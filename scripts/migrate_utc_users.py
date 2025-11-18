#!/usr/bin/env python3
"""
数据迁移脚本：修复timezone为UTC的用户

将所有timezone=UTC的活跃用户的timezone更新为合适的支持时区：
- Asia/Tokyo (日本时间)
- Asia/Shanghai (中国时间)
- America/New_York (美东时间)

根据用户的language字段来推断合适的timezone：
- language='zh' → timezone='Asia/Shanghai'
- language='ja' → timezone='Asia/Tokyo'
- language='en' → timezone='America/New_York'
- 其他情况 → timezone='Asia/Shanghai' (默认)
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import get_connection, convert_placeholder
from src.utils.logger import default_logger


def migrate_utc_users(dry_run: bool = True):
    """
    迁移UTC用户到支持的时区

    Args:
        dry_run: 如果为True，只显示将要执行的操作，不实际修改数据库
    """
    try:
        database_path = os.getenv("DATABASE_PATH", "data/db.sqlite")
        conn = get_connection(database_path)
        cursor = conn.cursor()

        # 查询所有timezone为UTC的活跃用户
        query = convert_placeholder("""
            SELECT id, email, language, timezone, subscription_type, subscription_status
            FROM users
            WHERE timezone = 'UTC' AND subscription_status = 'active'
            ORDER BY created_at ASC
        """)
        cursor.execute(query)
        utc_users = cursor.fetchall()

        if not utc_users:
            print("✅ 没有需要迁移的UTC用户")
            conn.close()
            return

        print(f"\n📊 找到 {len(utc_users)} 个需要迁移的UTC用户:\n")
        print(f"{'ID':<5} {'邮箱':<30} {'语言':<8} {'当前时区':<15} {'新时区':<20}")
        print("-" * 85)

        # 统计信息
        migration_plan = []

        for user in utc_users:
            # 兼容SQLite (tuple/Row) 和 PostgreSQL (dict)
            if isinstance(user, dict):
                user_id = user['id']
                email = user['email']
                language = user.get('language', 'en')
                current_tz = user['timezone']
            else:
                user_id = user[0]
                email = user[1]
                language = user[2] if len(user) > 2 else 'en'
                current_tz = user[3]

            # 根据language推断新的timezone
            if language == 'zh':
                new_timezone = 'Asia/Shanghai'
            elif language == 'ja':
                new_timezone = 'Asia/Tokyo'
            elif language == 'en':
                new_timezone = 'America/New_York'
            else:
                # 未知语言默认使用中国时区
                new_timezone = 'Asia/Shanghai'

            print(f"{user_id:<5} {email:<30} {language:<8} {current_tz:<15} {new_timezone:<20}")
            migration_plan.append((user_id, email, new_timezone))

        print("\n" + "=" * 85)
        print(f"📈 迁移统计:")
        timezone_counts = {}
        for _, _, new_tz in migration_plan:
            timezone_counts[new_tz] = timezone_counts.get(new_tz, 0) + 1

        for tz, count in sorted(timezone_counts.items()):
            print(f"  → {tz}: {count} 个用户")

        if dry_run:
            print("\n⚠️  DRY RUN 模式：以上是将要执行的操作，数据库未被修改")
            print("   如需实际执行，请使用: python scripts/migrate_utc_users.py --execute")
            conn.close()
            return

        # 实际执行迁移
        print("\n🚀 开始执行数据库迁移...")
        success_count = 0
        failed_count = 0

        for user_id, email, new_timezone in migration_plan:
            try:
                update_query = convert_placeholder("""
                    UPDATE users
                    SET timezone = ?
                    WHERE id = ?
                """)
                cursor.execute(update_query, (new_timezone, user_id))
                success_count += 1
                default_logger.info(
                    f"用户timezone迁移成功: {email} (UTC → {new_timezone})",
                    extra={"extra_fields": {
                        "user_id": user_id,
                        "email": email,
                        "old_timezone": "UTC",
                        "new_timezone": new_timezone
                    }}
                )
            except Exception as e:
                failed_count += 1
                default_logger.error(
                    f"用户timezone迁移失败: {email} - {str(e)}",
                    extra={"extra_fields": {
                        "user_id": user_id,
                        "email": email,
                        "error": str(e)
                    }}
                )

        conn.commit()
        conn.close()

        print("\n" + "=" * 85)
        print("✅ 迁移完成!")
        print(f"  成功: {success_count} 个用户")
        if failed_count > 0:
            print(f"  失败: {failed_count} 个用户")
        print("=" * 85)

    except Exception as e:
        default_logger.error(f"数据迁移过程出错: {str(e)}")
        print(f"\n❌ 迁移失败: {str(e)}")
        sys.exit(1)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='迁移timezone为UTC的用户到支持的时区'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='实际执行迁移（默认为dry-run模式）'
    )

    args = parser.parse_args()

    print("=" * 85)
    print("🔧 UTC用户时区迁移脚本")
    print("=" * 85)

    if args.execute:
        print("\n⚠️  警告：即将执行实际的数据库修改操作！")
        response = input("是否继续？(yes/no): ")
        if response.lower() != 'yes':
            print("❌ 取消操作")
            sys.exit(0)

    migrate_utc_users(dry_run=not args.execute)


if __name__ == "__main__":
    main()
