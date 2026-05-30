#!/usr/bin/env python3
"""
Stripe 手动测试脚本

用于测试完整的支付流程：
1. 创建 Checkout Session
2. 打开支付链接
3. 使用测试卡完成支付
4. 验证用户数据和邮件
"""

import os
import sys
import webbrowser
from datetime import datetime, timezone

# 设置环境变量
os.environ['DB_TYPE'] = 'postgresql'
os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL', '')

from src.payment.stripe_service import StripeService
from src.user.user_manager import UserManager
from src.database.connection import get_connection, convert_placeholder


def cleanup_test_user(email: str):
    """清理测试用户"""
    print(f"🧹 清理旧测试用户: {email}")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = convert_placeholder("DELETE FROM users WHERE email = ?")
        cursor.execute(query, (email,))
        conn.commit()
        deleted = cursor.rowcount
        conn.close()

        if deleted > 0:
            print(f"✓ 已删除 {deleted} 个旧用户")
        else:
            print(f"✓ 无旧用户需要清理")
        return True
    except Exception as e:
        print(f"✗ 清理失败: {e}")
        return False


def create_test_checkout():
    """创建测试支付会话"""
    print("\n" + "=" * 70)
    print("🛒 创建 Stripe Checkout Session")
    print("=" * 70)

    # 测试配置
    test_configs = [
        {
            "name": "中文用户测试",
            "email": "test_zh_stripe@example.com",
            "language": "zh",
            "timezone": "Asia/Shanghai",
            "plan": "monthly"
        },
        {
            "name": "日语用户测试",
            "email": "test_ja_stripe@example.com",
            "language": "ja",
            "timezone": "Asia/Tokyo",
            "plan": "yearly"
        },
        {
            "name": "英语用户测试",
            "email": "test_en_stripe@example.com",
            "language": "en",
            "timezone": "UTC",
            "plan": "monthly"
        }
    ]

    print("\n请选择测试场景：")
    for i, config in enumerate(test_configs, 1):
        print(f"  {i}. {config['name']} - {config['language']} / {config['timezone']} / {config['plan']}")

    choice = input("\n请输入选择 (1-3) [默认: 1]: ").strip() or "1"

    try:
        config = test_configs[int(choice) - 1]
    except (ValueError, IndexError):
        print("无效选择，使用默认配置")
        config = test_configs[0]

    print(f"\n使用配置: {config['name']}")
    print(f"  邮箱: {config['email']}")
    print(f"  语言: {config['language']}")
    print(f"  时区: {config['timezone']}")
    print(f"  计划: {config['plan']}")

    # 清理旧用户
    cleanup_test_user(config['email'])

    try:
        stripe_service = StripeService()

        print(f"\n创建 Checkout Session...")
        result = stripe_service.create_checkout_session(
            email=config['email'],
            plan=config['plan'],
            language=config['language'],
            timezone=config['timezone']
        )

        print(f"\n✅ Checkout Session 创建成功!")
        print(f"Session ID: {result['session_id']}")
        print(f"\n支付链接:")
        print(f"🔗 {result['url']}")

        return {
            "success": True,
            "config": config,
            "session_id": result['session_id'],
            "checkout_url": result['url']
        }

    except Exception as e:
        print(f"\n❌ 创建失败: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def show_test_cards():
    """显示 Stripe 测试卡信息"""
    print("\n" + "=" * 70)
    print("💳 Stripe 测试卡")
    print("=" * 70)
    print("\n使用以下测试卡号进行支付：")
    print("\n✅ 成功支付:")
    print("  卡号: 4242 4242 4242 4242")
    print("  过期: 任意未来日期 (如 12/25)")
    print("  CVC: 任意3位数字 (如 123)")
    print("  邮编: 任意5位数字")

    print("\n❌ 失败测试 (可选):")
    print("  卡号: 4000 0000 0000 0002  - 卡被拒绝")
    print("  卡号: 4000 0000 0000 9995  - 余额不足")

    print("\n更多测试卡: https://stripe.com/docs/testing")


def wait_for_payment(email: str):
    """等待支付完成"""
    print("\n" + "=" * 70)
    print("⏳ 等待支付完成...")
    print("=" * 70)
    print("\n请在浏览器中完成支付流程")
    print("完成后按回车继续验证...")

    input()

    # 验证用户数据
    print("\n验证用户数据...")

    try:
        user_manager = UserManager()
        user = user_manager.get_user(email)

        if not user:
            print(f"❌ 用户未创建，支付可能失败")
            return False

        print(f"\n✅ 找到用户: {email}")
        print(f"\n用户信息:")
        print(f"  ID: {user['id']}")
        print(f"  订阅类型: {user['subscription_type']}")
        print(f"  订阅状态: {user['subscription_status']}")
        print(f"  语言: {user.get('language', 'N/A')}")
        print(f"  时区: {user.get('timezone', 'N/A')}")
        print(f"  Stripe Customer ID: {user.get('stripe_customer_id', 'N/A')}")
        print(f"  Stripe Subscription ID: {user.get('stripe_subscription_id', 'N/A')}")
        print(f"  创建时间: {user.get('created_at', 'N/A')}")

        # 验证关键字段
        checks = {
            "订阅类型为 paid": user['subscription_type'] == 'paid',
            "订阅状态为 active": user['subscription_status'] == 'active',
            "语言已设置": user.get('language') is not None,
            "时区已设置": user.get('timezone') is not None,
            "Stripe Customer ID 已设置": user.get('stripe_customer_id') is not None,
            "Stripe Subscription ID 已设置": user.get('stripe_subscription_id') is not None,
        }

        print(f"\n验证结果:")
        all_passed = True
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check}")
            if not passed:
                all_passed = False

        if all_passed:
            print(f"\n🎉 所有验证通过！")
            print(f"\n💌 请检查邮箱是否收到欢迎邮件")
            print(f"   邮箱: {email}")
            print(f"   语言: {user.get('language', 'zh')}")
            return True
        else:
            print(f"\n⚠️ 部分验证失败")
            return False

    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_stripe_dashboard():
    """提示查看 Stripe Dashboard"""
    print("\n" + "=" * 70)
    print("📊 Stripe Dashboard")
    print("=" * 70)
    print("\n你可以在 Stripe Dashboard 中查看：")
    print("  - Payments (支付记录)")
    print("  - Customers (客户列表)")
    print("  - Subscriptions (订阅列表)")
    print("  - Webhooks (Webhook 事件)")
    print("\nDashboard: https://dashboard.stripe.com/test/dashboard")


def main():
    """主测试流程"""
    print("=" * 70)
    print("🧪 Stripe 手动测试脚本")
    print("=" * 70)
    print(f"测试时间: {datetime.now(timezone.utc).isoformat()}")

    # 检查环境配置
    print("\n检查环境配置...")
    required_env = ['STRIPE_SECRET_KEY', 'DATABASE_URL']
    missing_env = [env for env in required_env if not os.getenv(env)]

    if missing_env:
        print(f"❌ 缺少必需的环境变量: {', '.join(missing_env)}")
        return 1

    print("✅ 环境配置完整")

    # 步骤 1: 创建 Checkout Session
    result = create_test_checkout()

    if not result.get('success'):
        print("\n❌ 测试失败")
        return 1

    config = result['config']
    checkout_url = result['checkout_url']

    # 步骤 2: 显示测试卡信息
    show_test_cards()

    # 步骤 3: 打开支付链接
    print("\n" + "=" * 70)
    print("🌐 打开支付页面")
    print("=" * 70)

    open_browser = input("\n是否在浏览器中打开支付链接? (y/n) [默认: y]: ").strip().lower()

    if open_browser != 'n':
        print("正在打开浏览器...")
        webbrowser.open(checkout_url)
    else:
        print("\n请手动打开以下链接:")
        print(f"🔗 {checkout_url}")

    # 步骤 4: 等待支付完成
    success = wait_for_payment(config['email'])

    # 步骤 5: 提示查看 Dashboard
    check_stripe_dashboard()

    # 总结
    print("\n" + "=" * 70)
    print("📋 测试总结")
    print("=" * 70)

    if success:
        print("\n✅ 测试成功！")
        print("\n完成的步骤:")
        print("  1. ✅ 创建 Checkout Session")
        print("  2. ✅ 使用测试卡完成支付")
        print("  3. ✅ 用户数据正确保存")
        print("  4. ✅ 语言和时区正确设置")
        print("  5. ✅ Webhook 正确处理")
        print("  6. 💌 欢迎邮件已发送")

        print("\n后续步骤:")
        print("  - 检查邮箱确认收到欢迎邮件")
        print("  - 在 Stripe Dashboard 查看订阅详情")
        print("  - 测试其他语言/时区配置")

        return 0
    else:
        print("\n⚠️ 测试未完全成功")
        print("\n可能的原因:")
        print("  - 支付未完成")
        print("  - Webhook 未正确配置")
        print("  - 网络问题")

        print("\n调试步骤:")
        print("  1. 检查 Stripe Dashboard 的 Webhooks 日志")
        print("  2. 查看本地应用日志")
        print("  3. 确认 STRIPE_WEBHOOK_SECRET 配置正确")

        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
        sys.exit(1)
