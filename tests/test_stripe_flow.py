#!/usr/bin/env python3
"""
Stripe支付流程端到端测试

测试流程：
1. 创建 Checkout Session（带 language 和 timezone）
2. 模拟支付成功 Webhook 事件
3. 验证用户数据更新（language、timezone、subscription_type）
4. 验证欢迎邮件发送

环境要求：
- 需要配置 Stripe 测试密钥
- 需要配置数据库连接（PostgreSQL）
"""

import os
import sys
import json
from datetime import datetime, timezone

# 设置环境变量
os.environ['DB_TYPE'] = 'postgresql'
os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL', '')

from src.payment.stripe_service import StripeService
from src.payment.webhook_handler import StripeWebhookHandler
from src.user.user_manager import UserManager


def cleanup_test_user(email: str):
    """清理测试用户"""
    print(f"\n🧹 清理测试用户: {email}")
    try:
        from src.database.connection import get_connection, convert_placeholder
        conn = get_connection()
        cursor = conn.cursor()

        # 删除测试用户
        query = convert_placeholder("DELETE FROM users WHERE email = ?")
        cursor.execute(query, (email,))
        conn.commit()
        deleted = cursor.rowcount
        conn.close()

        if deleted > 0:
            print(f"✓ 已删除旧测试用户")
        else:
            print(f"✓ 无需清理（用户不存在）")
        return True

    except Exception as e:
        print(f"✗ 清理失败: {e}")
        return False


def test_create_checkout_session():
    """测试创建 Checkout Session"""
    print("\n" + "=" * 60)
    print("测试 1: 创建 Stripe Checkout Session")
    print("=" * 60)

    try:
        stripe_service = StripeService()

        # 测试数据
        test_email = "stripe_test@example.com"
        test_language = "ja"  # 测试日语
        test_timezone = "Asia/Tokyo"  # 测试东京时区
        test_plan = "monthly"

        print(f"\n创建 Checkout Session:")
        print(f"  邮箱: {test_email}")
        print(f"  语言: {test_language}")
        print(f"  时区: {test_timezone}")
        print(f"  计划: {test_plan}")

        # 创建 Checkout Session
        result = stripe_service.create_checkout_session(
            email=test_email,
            plan=test_plan,
            language=test_language,
            timezone=test_timezone
        )

        print(f"\n✓ Checkout Session 创建成功!")
        print(f"  Session ID: {result['session_id']}")
        print(f"  Checkout URL: {result['url']}")

        return {
            "success": True,
            "session_id": result['session_id'],
            "checkout_url": result['url'],
            "test_email": test_email,
            "test_language": test_language,
            "test_timezone": test_timezone
        }

    except Exception as e:
        print(f"\n✗ 创建失败: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def test_simulate_webhook():
    """测试模拟 Webhook 事件"""
    print("\n" + "=" * 60)
    print("测试 2: 模拟支付成功 Webhook")
    print("=" * 60)

    try:
        import stripe

        # 获取测试用的 Session ID
        test_email = "stripe_test@example.com"
        test_language = "ja"
        test_timezone = "Asia/Tokyo"

        # 先清理旧用户
        cleanup_test_user(test_email)

        # 创建一个模拟的 Checkout Session（仅用于测试）
        stripe_service = StripeService()
        result = stripe_service.create_checkout_session(
            email=test_email,
            plan="monthly",
            language=test_language,
            timezone=test_timezone
        )

        session_id = result['session_id']
        print(f"\n使用 Session ID: {session_id}")

        # 获取完整的 Session 对象
        session = stripe.checkout.Session.retrieve(session_id)

        print(f"\nSession 详情:")
        print(f"  Customer: {session.customer}")
        print(f"  Email: {session.customer_details.email if session.customer_details else 'N/A'}")
        print(f"  Metadata: {session.metadata}")

        # 模拟 checkout.session.completed 事件
        print(f"\n模拟处理 checkout.session.completed 事件...")

        webhook_handler = StripeWebhookHandler()

        # 创建模拟的 Event 对象
        event_data = {
            "id": "evt_test_123",
            "type": "checkout.session.completed",
            "data": {
                "object": session
            }
        }

        # 使用 stripe.Event.construct_from 创建 Event 对象
        event = stripe.Event.construct_from(event_data, stripe.api_key)

        # 处理事件
        webhook_result = webhook_handler.handle_event(event)

        if webhook_result.get("success"):
            print(f"✓ Webhook 处理成功: {webhook_result.get('message')}")

            # 验证用户数据
            print(f"\n验证用户数据...")
            user_manager = UserManager()
            user = user_manager.get_user(test_email)

            if user:
                print(f"\n用户信息:")
                print(f"  ID: {user['id']}")
                print(f"  Email: {user['email']}")
                print(f"  订阅类型: {user['subscription_type']}")
                print(f"  订阅状态: {user['subscription_status']}")
                print(f"  语言: {user.get('language', 'N/A')}")
                print(f"  时区: {user.get('timezone', 'N/A')}")
                print(f"  Stripe Customer ID: {user.get('stripe_customer_id', 'N/A')}")
                print(f"  Stripe Subscription ID: {user.get('stripe_subscription_id', 'N/A')}")

                # 验证数据正确性
                checks = {
                    "subscription_type == 'paid'": user['subscription_type'] == 'paid',
                    "subscription_status == 'active'": user['subscription_status'] == 'active',
                    f"language == '{test_language}'": user.get('language') == test_language,
                    f"timezone == '{test_timezone}'": user.get('timezone') == test_timezone,
                    "stripe_customer_id 已设置": user.get('stripe_customer_id') is not None,
                    "stripe_subscription_id 已设置": user.get('stripe_subscription_id') is not None,
                }

                print(f"\n验证结果:")
                all_passed = True
                for check, passed in checks.items():
                    status = "✓" if passed else "✗"
                    print(f"  {status} {check}")
                    if not passed:
                        all_passed = False

                if all_passed:
                    print(f"\n✅ 所有验证通过！")
                    return {"success": True, "user": user}
                else:
                    print(f"\n⚠️ 部分验证失败")
                    return {"success": False, "error": "部分验证失败", "user": user}
            else:
                print(f"✗ 用户创建失败")
                return {"success": False, "error": "用户未创建"}
        else:
            print(f"✗ Webhook 处理失败: {webhook_result.get('message')}")
            return {"success": False, "error": webhook_result.get('message')}

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def test_subscription_metadata():
    """测试订阅元数据传递"""
    print("\n" + "=" * 60)
    print("测试 3: 验证元数据传递")
    print("=" * 60)

    try:
        import stripe

        stripe_service = StripeService()

        # 创建不同语言和时区的测试
        test_cases = [
            {"email": "test_zh@example.com", "language": "zh", "timezone": "Asia/Shanghai"},
            {"email": "test_en@example.com", "language": "en", "timezone": "UTC"},
            {"email": "test_ja@example.com", "language": "ja", "timezone": "Asia/Tokyo"},
        ]

        results = []

        for case in test_cases:
            print(f"\n测试用例: {case['language']} - {case['timezone']}")

            # 创建 Checkout Session
            result = stripe_service.create_checkout_session(
                email=case['email'],
                plan="monthly",
                language=case['language'],
                timezone=case['timezone']
            )

            # 获取 Session 并检查 metadata
            session = stripe.checkout.Session.retrieve(result['session_id'])
            metadata = session.metadata

            print(f"  Metadata: {metadata}")

            # 验证 metadata
            checks = {
                "language": metadata.get('language') == case['language'],
                "timezone": metadata.get('timezone') == case['timezone'],
            }

            all_passed = all(checks.values())
            status = "✓" if all_passed else "✗"
            print(f"  {status} 元数据验证{'通过' if all_passed else '失败'}")

            results.append({
                "case": case,
                "passed": all_passed,
                "metadata": metadata
            })

        # 总结
        print(f"\n总结:")
        passed_count = sum(1 for r in results if r['passed'])
        total_count = len(results)
        print(f"  通过: {passed_count}/{total_count}")

        if passed_count == total_count:
            print(f"\n✅ 所有元数据测试通过！")
            return {"success": True, "results": results}
        else:
            print(f"\n⚠️ 部分元数据测试失败")
            return {"success": False, "results": results}

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def main():
    """主测试流程"""
    print("=" * 60)
    print("🧪 Stripe 支付流程端到端测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now(timezone.utc).isoformat()}")

    # 检查环境配置
    print("\n检查环境配置...")
    required_env = ['STRIPE_SECRET_KEY', 'DATABASE_URL']
    missing_env = [env for env in required_env if not os.getenv(env)]

    if missing_env:
        print(f"❌ 缺少必需的环境变量: {', '.join(missing_env)}")
        print("\n请在 .env 文件中配置以下变量:")
        for env in missing_env:
            print(f"  - {env}")
        return 1

    print("✓ 环境配置完整")

    # 运行测试
    results = {}

    # 测试 1: 创建 Checkout Session
    results['test1'] = test_create_checkout_session()

    # 测试 2: 模拟 Webhook
    results['test2'] = test_simulate_webhook()

    # 测试 3: 验证元数据传递
    results['test3'] = test_subscription_metadata()

    # 总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)

    test_names = {
        'test1': '创建 Checkout Session',
        'test2': '模拟支付成功 Webhook',
        'test3': '验证元数据传递'
    }

    passed = 0
    total = len(results)

    for test_id, test_name in test_names.items():
        result = results.get(test_id, {})
        success = result.get('success', False)
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {test_name}")
        if success:
            passed += 1

    print(f"\n通过率: {passed}/{total} ({passed/total*100:.0f}%)")

    if passed == total:
        print("\n✅ 所有测试通过！")
        print("\n后续步骤:")
        print("1. 在 Stripe Dashboard 中查看测试订阅")
        print("2. 在数据库中验证用户数据")
        print("3. 检查是否收到欢迎邮件")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查日志")
        return 1


if __name__ == "__main__":
    sys.exit(main())
