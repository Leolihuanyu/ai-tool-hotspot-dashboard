#!/usr/bin/env python3
"""
测试发送过期提醒邮件到指定邮箱
"""

import os
from datetime import datetime, timedelta, timezone

# 设置环境变量
os.environ['DB_TYPE'] = 'postgresql'
os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL', 'postgresql://postgres.pdezvkbhbynfgqtwaqaw:NG86DDhGUIehlLZ8@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres')

from src.email.expiry_reminder import ExpiryReminderService

def send_test_email():
    """发送测试邮件"""
    print("=" * 60)
    print("📧 发送测试过期提醒邮件")
    print("=" * 60)

    service = ExpiryReminderService()

    # 创建一个模拟用户
    test_user = {
        "id": 999,
        "email": "leolihuanyu@gmail.com",
        "subscription_type": "beta",
        "free_until": (datetime.now(timezone.utc) + timedelta(days=14)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    print(f"\n发送对象: {test_user['email']}")
    print(f"过期时间: {test_user['free_until']}")

    # 测试发送 14 天提醒
    print("\n📧 发送 14 天过期提醒...")
    success_14 = service.send_expiry_reminder(test_user, 14, language="zh")

    if success_14:
        print("✓ 14天提醒邮件发送成功！")
    else:
        print("✗ 14天提醒邮件发送失败")

    # 测试发送 7 天提醒
    test_user['free_until'] = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    print("\n📧 发送 7 天过期提醒...")
    success_7 = service.send_expiry_reminder(test_user, 7, language="zh")

    if success_7:
        print("✓ 7天提醒邮件发送成功！")
    else:
        print("✗ 7天提醒邮件发送失败")

    # 测试发送 1 天提醒
    test_user['free_until'] = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    print("\n📧 发送 1 天过期提醒...")
    success_1 = service.send_expiry_reminder(test_user, 1, language="zh")

    if success_1:
        print("✓ 1天提醒邮件发送成功！")
    else:
        print("✗ 1天提醒邮件发送失败")

    print("\n" + "=" * 60)
    if success_14 and success_7 and success_1:
        print("✅ 所有测试邮件发送成功！")
        print(f"\n请检查邮箱: {test_user['email']}")
        print("你应该收到 3 封邮件：")
        print("  1. 14天提醒 - 您的 Beta 试用还剩 14 天")
        print("  2. 7天提醒 - ⚠️ 最后一周 - 您的 Beta 试用即将结束")
        print("  3. 1天提醒 - 🚨 最后 24 小时 - 您的 Beta 试用明天到期")
    else:
        print("❌ 部分邮件发送失败")
    print("=" * 60)

if __name__ == "__main__":
    send_test_email()
