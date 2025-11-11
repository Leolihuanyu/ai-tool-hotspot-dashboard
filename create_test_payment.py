#!/usr/bin/env python3
"""
快速创建 Stripe 测试支付链接
"""

import os
import sys

# 设置环境变量
os.environ['DB_TYPE'] = 'postgresql'
os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL', 'postgresql://postgres.pdezvkbhbynfgqtwaqaw:NG86DDhGUIehlLZ8@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres')

from src.payment.stripe_service import StripeService
from src.database.connection import get_connection, convert_placeholder


def cleanup_test_user(email: str):
    """清理测试用户"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = convert_placeholder("DELETE FROM users WHERE email = ?")
        cursor.execute(query, (email,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"清理用户失败: {e}")
        return False


def create_payment_link(email: str, language: str = "zh", timezone: str = "Asia/Shanghai", plan: str = "monthly"):
    """创建支付链接"""
    print(f"\n创建支付链接...")
    print(f"  邮箱: {email}")
    print(f"  语言: {language}")
    print(f"  时区: {timezone}")
    print(f"  计划: {plan}")

    try:
        stripe_service = StripeService()

        result = stripe_service.create_checkout_session(
            email=email,
            plan=plan,
            language=language,
            timezone=timezone
        )

        return result

    except Exception as e:
        print(f"创建失败: {e}")
        return None


def main():
    """主函数"""
    print("=" * 70)
    print("🛒 Stripe 测试支付链接生成器")
    print("=" * 70)

    # 测试配置
    test_email = "test_stripe_manual@example.com"
    test_language = "zh"  # 中文
    test_timezone = "Asia/Shanghai"  # 上海时区
    test_plan = "monthly"  # 月付

    # 清理旧用户
    print(f"\n清理旧测试用户...")
    cleanup_test_user(test_email)

    # 创建支付链接
    result = create_payment_link(test_email, test_language, test_timezone, test_plan)

    if result:
        print(f"\n✅ 支付链接创建成功！")
        print(f"\nSession ID: {result['session_id']}")
        print(f"\n" + "=" * 70)
        print("💳 支付链接:")
        print("=" * 70)
        print(f"\n{result['url']}\n")

        print("=" * 70)
        print("💳 Stripe 测试卡")
        print("=" * 70)
        print("\n使用以下信息完成支付：")
        print("  卡号: 4242 4242 4242 4242")
        print("  过期: 12/25 (任意未来日期)")
        print("  CVC: 123 (任意3位数字)")
        print("  邮编: 12345 (任意5位数字)")

        print("\n" + "=" * 70)
        print("📝 测试步骤:")
        print("=" * 70)
        print("1. 复制上面的支付链接，在浏览器中打开")
        print("2. 使用上述测试卡信息完成支付")
        print("3. 支付成功后，运行验证脚本:")
        print(f"   python verify_payment.py {test_email}")
        print("4. 检查邮箱 {test_email} 是否收到中文欢迎邮件")

        print("\n" + "=" * 70)
        print("🔗 相关链接:")
        print("=" * 70)
        print("Stripe Dashboard: https://dashboard.stripe.com/test/payments")
        print("Stripe测试卡文档: https://stripe.com/docs/testing")

        return 0
    else:
        print("\n❌ 创建失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
