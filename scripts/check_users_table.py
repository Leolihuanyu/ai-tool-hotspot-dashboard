#!/usr/bin/env python3
"""检查 users 表结构和 access_token 字段

用于验证数据库迁移是否成功执行
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import get_db_connection


def check_users_table():
    """检查 users 表结构"""
    print("=" * 70)
    print("检查 users 表结构")
    print("=" * 70)

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 查询 users 表的所有列
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'users'
                    ORDER BY ordinal_position;
                """)

                print(f"\n{'字段名':<30} {'数据类型':<25} {'可为空':<10}")
                print('-' * 70)

                has_access_token = False
                has_token_generated_at = False
                has_token_expires_at = False

                for row in cursor.fetchall():
                    column_name, data_type, is_nullable = row
                    marker = ''

                    if column_name == 'access_token':
                        has_access_token = True
                        marker = ' ✅'
                    elif column_name == 'token_generated_at':
                        has_token_generated_at = True
                        marker = ' ✅'
                    elif column_name == 'token_expires_at':
                        has_token_expires_at = True
                        marker = ' ✅'

                    print(f'{column_name:<30} {data_type:<25} {is_nullable:<10}{marker}')

                print('=' * 70)
                print()

                # 检查结果
                all_fields_exist = has_access_token and has_token_generated_at and has_token_expires_at

                if all_fields_exist:
                    print('✅ 所有 access_token 相关字段都存在！')

                    # 检查数据
                    cursor.execute("SELECT COUNT(*) FROM users")
                    total_users = cursor.fetchone()[0]

                    cursor.execute("SELECT COUNT(*) FROM users WHERE access_token IS NOT NULL")
                    users_with_token = cursor.fetchone()[0]

                    print(f'✅ 总用户数: {total_users}')
                    print(f'✅ 已设置 access_token: {users_with_token}')
                    print(f'⚠️  未设置 access_token: {total_users - users_with_token}')

                    # 查看用户详情
                    print('\n用户 Token 状态:')
                    cursor.execute("""
                        SELECT
                            email,
                            CASE WHEN access_token IS NOT NULL THEN '有' ELSE '无' END as has_token,
                            token_expires_at,
                            subscription_type
                        FROM users
                        ORDER BY created_at DESC
                        LIMIT 10
                    """)

                    print(f"{'邮箱':<35} {'Token':<8} {'订阅类型':<10} {'过期时间'}")
                    print('-' * 70)

                    for row in cursor.fetchall():
                        email, has_tok, expires, sub_type = row
                        expires_str = str(expires)[:19] if expires else "未设置"
                        print(f'{email:<35} {has_tok:<8} {sub_type:<10} {expires_str}')

                    print('\n' + '=' * 70)
                    print('✅ 数据库迁移成功！')
                    print('=' * 70)
                    return True

                else:
                    print('❌ 缺少必需字段:')
                    if not has_access_token:
                        print('  - access_token')
                    if not has_token_generated_at:
                        print('  - token_generated_at')
                    if not has_token_expires_at:
                        print('  - token_expires_at')

                    print('\n' + '=' * 70)
                    print('❌ 需要运行迁移脚本!')
                    print('   执行: python scripts/run_migrations.py')
                    print('=' * 70)
                    return False

    except Exception as e:
        print(f'\n❌ 检查失败: {e}')
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = check_users_table()
    sys.exit(0 if success else 1)
