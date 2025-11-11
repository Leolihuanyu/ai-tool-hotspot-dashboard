#!/usr/bin/env python3
"""
验证 Stripe 支付是否成功
"""

import os
import sys

# 设置环境变量
os.environ['DB_TYPE'] = 'postgresql'
os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL', 'postgresql://postgres.pdezvkbhbynfgqtwaqaw:NG86DDhGUIehlLZ8@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres')

from src.user.user_manager import UserManager


def verify_user(email: str):
    """验证用户数据"""
    print("=" * 70)
    print(f"🔍 验证用户: {email}")
    print("=" * 70)

    try:
        user_manager = UserManager()
        user = user_manager.get_user(email)

        if not user:
            print(f"\n❌ 用户不存在")
            print(f"\n可能的原因:")
            print(f"  1. 支付未完成")
            print(f"  2. Webhook 未触发")
            print(f"  3. 邮箱地址不匹配")
            return False

        print(f"\n✅ 找到用户")
        print(f"\n" + "=" * 70)
        print("📋 用户信息:")
        print("=" * 70)
        print(f"  ID: {user['id']}")
        print(f"  邮箱: {user['email']}")
        print(f"  订阅类型: {user['subscription_type']}")
        print(f"  订阅状态: {user['subscription_status']}")
        print(f"  语言: {user.get('language', 'N/A')}")
        print(f"  时区: {user.get('timezone', 'N/A')}")
        print(f"  Stripe Customer ID: {user.get('stripe_customer_id', 'N/A')[:20]}..." if user.get('stripe_customer_id') else "  Stripe Customer ID: N/A")
        print(f"  Stripe Subscription ID: {user.get('stripe_subscription_id', 'N/A')[:20]}..." if user.get('stripe_subscription_id') else "  Stripe Subscription ID: N/A")
        print(f"  创建时间: {user.get('created_at', 'N/A')}")
        print(f"  更新时间: {user.get('updated_at', 'N/A')}")

        # 验证关键字段
        print(f"\n" + "=" * 70)
        print("✅ 验证结果:")
        print("=" * 70)

        checks = [
            ("订阅类型为 'paid'", user['subscription_type'] == 'paid'),
            ("订阅状态为 'active'", user['subscription_status'] == 'active'),
            ("语言已设置", user.get('language') is not None and user.get('language') != ''),
            ("时区已设置", user.get('timezone') is not None and user.get('timezone') != ''),
            ("Stripe Customer ID 已设置", user.get('stripe_customer_id') is not None),
            ("Stripe Subscription ID 已设置", user.get('stripe_subscription_id') is not None),
        ]

        all_passed = True
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"  {status} {check_name}")
            if not passed:
                all_passed = False

        if all_passed:
            print(f"\n" + "=" * 70)
            print("🎉 所有验证通过！")
            print("=" * 70)
            print(f"\n后续步骤:")
            print(f"  1. 检查邮箱 {email} 是否收到欢迎邮件")
            print(f"  2. 邮件语言应该是: {user.get('language', 'zh')}")
            print(f"  3. 在 Stripe Dashboard 查看订阅详情")
            print(f"     https://dashboard.stripe.com/test/subscriptions")
            return True
        else:
            print(f"\n" + "=" * 70)
            print("⚠️ 部分验证失败")
            print("=" * 70)
            print(f"\n调试建议:")
            print(f"  1. 检查 Stripe Dashboard 的 Webhooks 日志")
            print(f"     https://dashboard.stripe.com/test/webhooks")
            print(f"  2. 确认支付已完成")
            print(f"  3. 查看应用日志")
            return False

    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python verify_payment.py <email>")
        print("例如: python verify_payment.py test_stripe_manual@example.com")
        return 1

    email = sys.argv[1]
    success = verify_user(email)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
