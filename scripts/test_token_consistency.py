#!/usr/bin/env python3
"""
测试Token一致性
验证多次发送邮件时token是否保持不变
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.user.user_manager import UserManager
from src.email.daily_email_generator import DailyEmailGenerator


def test_token_consistency():
    """测试多次邮件生成时token的一致性"""
    user_manager = UserManager()
    generator = DailyEmailGenerator()

    print("=" * 60)
    print("测试Token一致性")
    print("=" * 60)

    # 使用真实用户测试
    test_email = "leolihuanyu@gmail.com"

    # 获取初始状态
    user = user_manager.get_user(test_email)
    if not user:
        print(f"❌ 用户不存在: {test_email}")
        return

    initial_token = user.get("access_token")
    token_expires_at = user.get("token_expires_at")

    print(f"\n用户信息:")
    print(f"  邮箱: {test_email}")
    print(f"  订阅类型: {user.get('subscription_type')}")
    print(f"  订阅状态: {user.get('subscription_status')}")
    print(f"  Token过期时间: {token_expires_at}")
    print(f"  Token过期时间类型: {type(token_expires_at).__name__}")
    print(f"  初始Token前缀: {initial_token[:20] if initial_token else 'None'}...")

    # 测试连续3次生成邮件
    print("\n测试连续生成邮件...")
    tokens = []

    for i in range(3):
        print(f"\n第{i+1}次生成邮件:")
        try:
            # 生成邮件
            subject, html, plain = generator.generate_personalized_email(
                email=test_email,
                dashboard_base_url="https://ai-tool-hotspot-dashboard.vercel.app"
            )

            # 获取当前token
            user = user_manager.get_user(test_email)
            current_token = user.get("access_token")
            tokens.append(current_token)

            print(f"  ✅ 邮件生成成功")
            print(f"  Token前缀: {current_token[:20] if current_token else 'None'}...")

            # 检查token是否变化
            if i > 0:
                if tokens[i] == tokens[i-1]:
                    print(f"  ✅ Token保持不变（正确）")
                else:
                    print(f"  ❌ Token发生变化（错误！）")
                    print(f"     之前: {tokens[i-1][:20]}...")
                    print(f"     现在: {tokens[i][:20]}...")

        except Exception as e:
            print(f"  ❌ 邮件生成失败: {str(e)}")

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    if len(set(tokens)) == 1:
        print("✅ 所有token都相同，修复成功！")
        print(f"   Token在3次邮件生成中保持一致")
        return True
    else:
        print("❌ Token发生了变化，问题仍然存在！")
        print(f"   发现了{len(set(tokens))}个不同的token")
        for i, token in enumerate(tokens):
            print(f"   第{i+1}次: {token[:20] if token else 'None'}...")
        return False


def test_datetime_type_handling():
    """测试不同数据类型的处理"""
    from datetime import datetime, timezone, timedelta
    from dateutil import parser

    print("\n" + "=" * 60)
    print("测试DateTime类型处理")
    print("=" * 60)

    # 测试字符串类型
    test_str = "2026-02-13T13:28:53.780251+00:00"
    print(f"\n测试字符串类型: {test_str}")
    try:
        if isinstance(test_str, str):
            result = parser.parse(test_str)
            print(f"  ✅ 字符串解析成功: {result}")
    except Exception as e:
        print(f"  ❌ 字符串解析失败: {e}")

    # 测试datetime对象
    test_dt = datetime.now(timezone.utc) + timedelta(days=90)
    print(f"\n测试datetime对象: {test_dt}")
    try:
        if isinstance(test_dt, str):
            result = parser.parse(test_dt)
            print(f"  解析结果: {result}")
        else:
            print(f"  ✅ 识别为datetime对象，直接使用")
    except Exception as e:
        print(f"  如果直接parse会失败: {e}")

    # 测试时区处理
    naive_dt = datetime.now()  # 没有时区信息
    print(f"\n测试无时区datetime: {naive_dt}")
    if naive_dt.tzinfo is None:
        aware_dt = naive_dt.replace(tzinfo=timezone.utc)
        print(f"  ✅ 添加UTC时区: {aware_dt}")


if __name__ == "__main__":
    # 运行测试
    test_token_consistency()
    test_datetime_type_handling()