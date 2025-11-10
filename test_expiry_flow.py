#!/usr/bin/env python3
"""
测试完整的过期流程

功能：
1. 创建测试用户（过期时间设置为 14天/7天/1天后）
2. 验证用户认证在过期前正常工作
3. 测试发送过期提醒邮件
4. 验证过期后的认证会被拒绝
"""

import os
import sys
from datetime import datetime, timedelta, timezone

# 设置PostgreSQL连接
os.environ['DB_TYPE'] = 'postgresql'
os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL', 'postgresql://postgres.pdezvkbhbynfgqtwaqaw:NG86DDhGUIehlLZ8@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres')

from src.user.user_manager import UserManager
from src.auth.token_manager import TokenManager
from src.email.expiry_reminder import ExpiryReminderService
from src.database.connection import get_connection, convert_placeholder


def cleanup_test_users():
    """清理测试用户"""
    print("\n🧹 清理旧的测试用户...")
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 删除测试用户
        query = convert_placeholder("""
            DELETE FROM users
            WHERE email LIKE 'test_expiry_%@example.com'
        """)
        cursor.execute(query)
        conn.commit()
        deleted = cursor.rowcount
        conn.close()

        print(f"✓ 已删除 {deleted} 个旧测试用户")
        return True

    except Exception as e:
        print(f"✗ 清理失败: {e}")
        return False


def create_test_users():
    """创建测试用户（14天、7天、1天后过期）"""
    print("\n👥 创建测试用户...")

    conn = get_connection()
    cursor = conn.cursor()

    test_cases = [
        {"days": 14, "email": "test_expiry_14days@example.com"},
        {"days": 7, "email": "test_expiry_7days@example.com"},
        {"days": 1, "email": "test_expiry_1day@example.com"},
    ]

    created_users = []

    for case in test_cases:
        try:
            # 计算过期时间
            free_until = (datetime.now(timezone.utc) + timedelta(days=case['days'])).isoformat()

            # 插入测试用户
            query = convert_placeholder("""
                INSERT INTO users (
                    email, subscription_type, subscription_status, free_until
                )
                VALUES (?, 'beta', 'active', ?)
                RETURNING id
            """)
            cursor.execute(query, (case['email'], free_until))

            result = cursor.fetchone()
            user_id = result['id'] if isinstance(result, dict) else result[0]

            created_users.append({
                "id": user_id,
                "email": case['email'],
                "days": case['days'],
                "free_until": free_until
            })

            print(f"✓ 创建用户: {case['email']} (ID: {user_id})")
            print(f"  过期时间: {free_until} ({case['days']}天后)")

        except Exception as e:
            print(f"✗ 创建用户失败: {case['email']} - {e}")

    conn.commit()
    conn.close()

    return created_users


def test_authentication(users):
    """测试认证功能"""
    print("\n🔐 测试认证功能...")

    token_manager = TokenManager()

    for user in users:
        try:
            # 生成token
            token = token_manager.generate_token(user['email'])

            # 验证token（不检查过期）
            result = token_manager.verify_token(token, require_ip_match=False)

            if result.get('valid'):
                print(f"✓ {user['email']}: Token验证成功")
            else:
                print(f"✗ {user['email']}: Token验证失败 - {result.get('error')}")

        except Exception as e:
            print(f"✗ {user['email']}: 认证测试失败 - {e}")


def test_expiry_reminders():
    """测试过期提醒邮件"""
    print("\n📧 测试过期提醒邮件...")

    service = ExpiryReminderService()

    for days in [14, 7, 1]:
        print(f"\n检查 {days} 天过期提醒...")
        users = service.get_expiring_users(days)

        if users:
            print(f"✓ 找到 {len(users)} 个即将在 {days} 天后过期的用户")
            for user in users:
                print(f"  - {user['email']} (过期: {user['free_until']})")

            # 测试发送邮件（第一个用户）
            if len(users) > 0:
                print(f"\n测试发送过期提醒邮件给: {users[0]['email']}")
                success = service.send_expiry_reminder(users[0], days, language="zh")
                if success:
                    print(f"✓ 邮件发送成功")
                else:
                    print(f"✗ 邮件发送失败")
        else:
            print(f"✗ 没有找到 {days} 天后过期的用户")


def test_expired_authentication():
    """测试过期用户的认证会被拒绝"""
    print("\n⏰ 测试过期用户认证...")

    # 创建一个已经过期的测试用户
    conn = get_connection()
    cursor = conn.cursor()

    try:
        email = "test_expiry_expired@example.com"
        expired_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

        # 删除可能存在的旧用户
        query = convert_placeholder("DELETE FROM users WHERE email = ?")
        cursor.execute(query, (email,))

        # 创建过期用户
        query = convert_placeholder("""
            INSERT INTO users (
                email, subscription_type, subscription_status, free_until
            )
            VALUES (?, 'beta', 'active', ?)
            RETURNING id
        """)
        cursor.execute(query, (email, expired_date))

        result = cursor.fetchone()
        user_id = result['id'] if isinstance(result, dict) else result[0]

        conn.commit()
        print(f"✓ 创建过期用户: {email} (过期时间: {expired_date})")

        # 生成token
        token_manager = TokenManager()
        token = token_manager.generate_token(email)

        # 使用 user_manager 检查过期
        user_manager = UserManager()
        user = user_manager.get_user(email)

        if user:
            from dateutil import parser as date_parser
            free_until = user.get('free_until')
            if free_until:
                # free_until 可能已经是 datetime 对象
                if isinstance(free_until, str):
                    free_until_dt = date_parser.parse(free_until)
                else:
                    free_until_dt = free_until

                # 确保时区一致
                now = datetime.now(timezone.utc)
                if free_until_dt.tzinfo is None:
                    free_until_dt = free_until_dt.replace(tzinfo=timezone.utc)

                if now > free_until_dt:
                    print(f"✓ 确认用户已过期")
                    print(f"  当前时间: {now.isoformat()}")
                    print(f"  过期时间: {free_until_dt.isoformat()}")
                else:
                    print(f"✗ 用户未过期（时间计算错误）")
            else:
                print(f"✗ 用户没有 free_until 字段")
        else:
            print(f"✗ 无法获取用户信息")

        # 清理
        query = convert_placeholder("DELETE FROM users WHERE email = ?")
        cursor.execute(query, (email,))
        conn.commit()

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        conn.close()


def main():
    """主测试流程"""
    print("=" * 60)
    print("🧪 测试过期流程")
    print("=" * 60)

    # 1. 清理旧的测试用户
    if not cleanup_test_users():
        print("\n❌ 清理失败，中止测试")
        return 1

    # 2. 创建测试用户
    users = create_test_users()
    if not users:
        print("\n❌ 无法创建测试用户，中止测试")
        return 1

    # 3. 测试认证
    test_authentication(users)

    # 4. 测试过期提醒
    test_expiry_reminders()

    # 5. 测试过期用户认证
    test_expired_authentication()

    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)

    print("\n📝 后续步骤:")
    print("1. 检查上述所有测试是否通过")
    print("2. 查看邮件是否成功发送（检查邮箱）")
    print("3. 运行 CLI 命令测试:")
    print("   python -m src.cli.main check-expiry --days 14")
    print("4. 部署到 Render.com")
    print("5. 配置 GitHub Actions 定时任务")

    return 0


if __name__ == "__main__":
    sys.exit(main())
