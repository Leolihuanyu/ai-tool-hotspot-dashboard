#!/usr/bin/env python3
"""
测试Token刷新逻辑
验证Beta用户和付费用户的token刷新行为是否符合预期
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.user.user_manager import UserManager
from src.auth.token_manager import TokenManager
from src.email.daily_email_generator import DailyEmailGenerator
from src.database.connection import get_connection


def setup_test_users():
    """创建测试用户"""
    user_manager = UserManager()
    token_manager = TokenManager()

    # 创建测试Beta用户（token即将过期）
    beta_email = "test_beta@example.com"
    beta_token = token_manager.generate_long_term_token(expiry_days=90)

    # 设置token即将过期（5天后过期）
    generated_at = datetime.now(timezone.utc)
    expires_at = generated_at + timedelta(days=5)

    # 创建或更新Beta用户（不传timezone避免错误）
    user_manager.create_user(
        email=beta_email,
        subscription_type="beta",
        language="zh"
    )

    user_manager.update_user(
        email=beta_email,
        access_token=beta_token,
        token_generated_at=generated_at.isoformat(),
        token_expires_at=expires_at.isoformat()
    )

    print(f"✅ Beta用户创建成功: {beta_email}")
    print(f"   Token过期时间: {expires_at.isoformat()}")

    # 创建测试付费用户（token即将过期）
    paid_email = "test_paid@example.com"
    paid_token = token_manager.generate_long_term_token(expiry_days=90)

    # 创建或更新付费用户
    user_manager.create_user(
        email=paid_email,
        subscription_type="paid",
        language="zh"
    )

    # 设置订阅状态为active
    user_manager.update_user(
        email=paid_email,
        subscription_status="active"
    )

    user_manager.update_user(
        email=paid_email,
        access_token=paid_token,
        token_generated_at=generated_at.isoformat(),
        token_expires_at=expires_at.isoformat()
    )

    print(f"✅ 付费用户创建成功: {paid_email}")
    print(f"   Token过期时间: {expires_at.isoformat()}")

    return beta_email, beta_token, paid_email, paid_token


def test_beta_user_no_refresh(email):
    """测试Beta用户不刷新token"""
    print(f"\n📝 测试Beta用户token刷新行为...")

    user_manager = UserManager()

    # 获取用户当前token
    user_before = user_manager.get_user(email)
    token_before = user_before.get("access_token")
    expires_before = user_before.get("token_expires_at")

    print(f"   刷新前token前缀: {token_before[:10]}...")
    print(f"   刷新前过期时间: {expires_before}")

    # 尝试生成个性化邮件（触发token刷新检查）
    try:
        generator = DailyEmailGenerator()
        subject, html, plain = generator.generate_personalized_email(
            email=email,
            dashboard_base_url="https://test.example.com"
        )

        # 获取刷新后的token
        user_after = user_manager.get_user(email)
        token_after = user_after.get("access_token")
        expires_after = user_after.get("token_expires_at")

        print(f"   刷新后token前缀: {token_after[:10]}...")
        print(f"   刷新后过期时间: {expires_after}")

        # 验证token没有变化
        if token_before == token_after:
            print(f"   ✅ Beta用户token未刷新（符合预期）")
            return True
        else:
            print(f"   ❌ Beta用户token被错误刷新！")
            return False

    except Exception as e:
        print(f"   邮件生成失败: {str(e)}")
        # Beta用户token过期后应该抛出异常，这是预期行为
        if "Beta用户访问权限已过期" in str(e):
            print(f"   ✅ Beta用户token过期处理正确")
            return True
        return False


def test_paid_user_refresh(email):
    """测试付费用户刷新token"""
    print(f"\n📝 测试付费用户token刷新行为...")

    user_manager = UserManager()

    # 获取用户当前token
    user_before = user_manager.get_user(email)
    token_before = user_before.get("access_token")
    expires_before = user_before.get("token_expires_at")

    print(f"   刷新前token前缀: {token_before[:10]}...")
    print(f"   刷新前过期时间: {expires_before}")

    # 生成个性化邮件（触发token刷新）
    try:
        generator = DailyEmailGenerator()
        subject, html, plain = generator.generate_personalized_email(
            email=email,
            dashboard_base_url="https://test.example.com"
        )

        # 获取刷新后的token
        user_after = user_manager.get_user(email)
        token_after = user_after.get("access_token")
        expires_after = user_after.get("token_expires_at")

        print(f"   刷新后token前缀: {token_after[:10]}...")
        print(f"   刷新后过期时间: {expires_after}")

        # 验证token已经刷新
        if token_before != token_after:
            print(f"   ✅ 付费用户token已刷新（符合预期）")

            # 验证新token有效期为90天
            from dateutil import parser
            expires_dt = parser.parse(expires_after)
            now_dt = datetime.now(timezone.utc)
            days_until_expiry = (expires_dt - now_dt).days

            if 89 <= days_until_expiry <= 90:
                print(f"   ✅ 新token有效期正确: {days_until_expiry}天")
                return True
            else:
                print(f"   ❌ 新token有效期不正确: {days_until_expiry}天")
                return False
        else:
            print(f"   ❌ 付费用户token未刷新！")
            return False

    except Exception as e:
        print(f"   ❌ 邮件生成失败: {str(e)}")
        return False


def test_subscription_cancel():
    """测试取消订阅时清空token"""
    print(f"\n📝 测试取消订阅时清空token...")

    user_manager = UserManager()
    token_manager = TokenManager()

    # 创建测试用户
    test_email = "test_cancel@example.com"
    test_token = token_manager.generate_long_term_token(expiry_days=90)

    user_manager.create_user(
        email=test_email,
        subscription_type="paid",
        language="zh"
    )

    user_manager.update_user(
        email=test_email,
        subscription_status="active"
    )

    user_manager.update_access_token(
        email=test_email,
        access_token=test_token,
        expiry_days=90
    )

    print(f"   用户创建成功: {test_email}")
    print(f"   初始token前缀: {test_token[:10]}...")

    # 模拟取消订阅
    user_manager.update_user(
        email=test_email,
        subscription_status="cancelled"
    )

    # 清空token
    cleared = user_manager.clear_access_token(test_email)

    if cleared:
        print(f"   ✅ Token清空成功")

        # 验证token确实被清空
        user = user_manager.get_user(test_email)
        if user.get("access_token") is None:
            print(f"   ✅ 验证：Token已从数据库清除")
            return True
        else:
            print(f"   ❌ 验证失败：Token仍然存在！")
            return False
    else:
        print(f"   ❌ Token清空失败")
        return False


def cleanup_test_users():
    """清理测试用户"""
    print(f"\n🧹 清理测试用户...")

    conn = get_connection()
    cursor = conn.cursor()

    test_emails = [
        "test_beta@example.com",
        "test_paid@example.com",
        "test_cancel@example.com"
    ]

    for email in test_emails:
        cursor.execute("DELETE FROM users WHERE email = ?", (email,))

    conn.commit()
    cursor.close()
    conn.close()

    print(f"   ✅ 测试用户清理完成")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("Token管理系统测试")
    print("=" * 60)

    try:
        # 设置测试用户
        beta_email, beta_token, paid_email, paid_token = setup_test_users()

        # 运行测试
        results = []

        # 测试1: Beta用户不刷新
        results.append(test_beta_user_no_refresh(beta_email))

        # 测试2: 付费用户刷新
        results.append(test_paid_user_refresh(paid_email))

        # 测试3: 取消订阅清空token
        results.append(test_subscription_cancel())

        # 输出测试结果
        print("\n" + "=" * 60)
        print("测试结果总结")
        print("=" * 60)

        test_names = [
            "Beta用户不刷新token",
            "付费用户自动刷新token",
            "取消订阅清空token"
        ]

        for i, (name, result) in enumerate(zip(test_names, results)):
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{i+1}. {name}: {status}")

        # 清理测试数据
        cleanup_test_users()

        # 判断总体结果
        if all(results):
            print("\n🎉 所有测试通过！Token管理系统符合设计要求。")
            return 0
        else:
            print("\n⚠️ 部分测试失败，请检查修复。")
            return 1

    except Exception as e:
        print(f"\n❌ 测试执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)