#!/usr/bin/env python3
"""
简化的Token刷新测试
专注于验证核心功能
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_email_generation():
    """测试邮件生成时的token刷新逻辑"""
    from src.user.user_manager import UserManager
    from src.auth.token_manager import TokenManager
    from src.email.daily_email_generator import DailyEmailGenerator

    user_manager = UserManager()

    print("=" * 60)
    print("测试Token刷新逻辑")
    print("=" * 60)

    # 使用现有用户 - 从日志看test_paid@example.com已存在
    test_email = "user@example.com"  # 使用您提到的实际用户

    # 获取用户信息
    user = user_manager.get_user(test_email)

    if user:
        print(f"\n✅ 找到用户: {test_email}")
        print(f"   订阅类型: {user.get('subscription_type')}")
        print(f"   订阅状态: {user.get('subscription_status')}")
        print(f"   Token过期时间: {user.get('token_expires_at')}")

        # 测试邮件生成（会触发token刷新逻辑）
        try:
            generator = DailyEmailGenerator()

            print("\n📧 生成邮件测试...")

            # 记录原始token
            old_token = user.get("access_token")

            # 生成邮件（触发刷新检查）
            subject, html, plain = generator.generate_personalized_email(
                email=test_email,
                dashboard_base_url="https://ai-tool-hotspot-dashboard.vercel.app"
            )

            # 重新获取用户信息
            user_after = user_manager.get_user(test_email)
            new_token = user_after.get("access_token")

            print(f"   邮件生成成功")
            print(f"   Token变化: {old_token != new_token}")

            if user.get('subscription_type') == 'beta':
                if old_token == new_token:
                    print(f"   ✅ Beta用户token未刷新（符合预期）")
                else:
                    print(f"   ❌ Beta用户token被错误刷新！")
            elif user.get('subscription_type') == 'paid':
                # 检查是否需要刷新（7天内过期）
                from dateutil import parser
                expires_at = user.get('token_expires_at')
                if expires_at:
                    expires_dt = parser.parse(expires_at)
                    now_dt = datetime.now(timezone.utc)
                    days_until_expiry = (expires_dt - now_dt).days

                    if days_until_expiry < 7:
                        if old_token != new_token:
                            print(f"   ✅ 付费用户token已刷新（符合预期）")
                        else:
                            print(f"   ❌ 付费用户token应该刷新但未刷新！")
                    else:
                        print(f"   ℹ️ Token还有{days_until_expiry}天过期，无需刷新")

        except Exception as e:
            print(f"   ⚠️ 邮件生成失败: {str(e)}")
            if "Beta用户访问权限已过期" in str(e):
                print(f"   ✅ Beta用户过期处理正确")
    else:
        print(f"❌ 用户不存在: {test_email}")

    # 测试特定的test用户
    print("\n" + "=" * 60)
    print("测试特定场景")
    print("=" * 60)

    # 创建测试Beta用户
    print("\n1. 创建测试Beta用户")
    token_manager = TokenManager()

    # 直接使用SQL创建用户避免API问题
    from src.database.connection import get_connection
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 删除旧的测试用户
        cursor.execute("DELETE FROM users WHERE email = ?", ("test_beta_90day@example.com",))

        # 创建新用户
        test_token = token_manager.generate_long_term_token(expiry_days=90)
        expires_at = datetime.now(timezone.utc) + timedelta(days=5)  # 5天后过期

        cursor.execute("""
            INSERT INTO users (email, subscription_type, subscription_status,
                             access_token, token_generated_at, token_expires_at,
                             language, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "test_beta_90day@example.com",
            "beta",
            "active",
            test_token,
            datetime.now(timezone.utc).isoformat(),
            expires_at.isoformat(),
            "zh",
            datetime.now(timezone.utc).isoformat(),
            datetime.now(timezone.utc).isoformat()
        ))
        conn.commit()

        print(f"   ✅ Beta测试用户创建成功")
        print(f"   Token将在5天后过期")

        # 测试Beta用户刷新逻辑
        generator = DailyEmailGenerator()
        try:
            subject, html, plain = generator.generate_personalized_email(
                email="test_beta_90day@example.com",
                dashboard_base_url="https://test.example.com"
            )

            # 检查token是否变化
            cursor.execute("SELECT access_token FROM users WHERE email = ?",
                         ("test_beta_90day@example.com",))
            result = cursor.fetchone()
            if result and result[0] == test_token:
                print(f"   ✅ Beta用户token未被刷新（正确）")
            else:
                print(f"   ❌ Beta用户token被刷新了（错误）")

        except Exception as e:
            print(f"   邮件生成异常: {str(e)}")

    finally:
        # 清理测试用户
        cursor.execute("DELETE FROM users WHERE email = ?", ("test_beta_90day@example.com",))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"   🧹 测试用户已清理")

if __name__ == "__main__":
    test_email_generation()