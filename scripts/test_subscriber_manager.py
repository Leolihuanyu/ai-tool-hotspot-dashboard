#!/usr/bin/env python3
"""测试订阅者管理功能"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.email.subscriber_manager import get_subscriber_manager
from src.utils.logger import get_logger

logger = get_logger(__name__)


def test_get_active_subscribers():
    """测试获取活跃订阅者"""
    print("=" * 60)
    print("测试：获取活跃订阅者")
    print("=" * 60)

    manager = get_subscriber_manager()

    # 测试1：获取所有活跃订阅者（Beta + Paid）
    print("\n【测试1】获取所有活跃订阅者（Beta + Paid）")
    subscribers = manager.get_active_subscribers(
        include_beta=True,
        include_paid=True
    )
    print(f"找到 {len(subscribers)} 个活跃订阅者:")
    for i, sub in enumerate(subscribers, 1):
        print(f"  {i}. {sub['email']} - {sub['subscription_type']} - 语言: {sub.get('language', 'N/A')}")

    # 测试2：仅获取Beta用户
    print("\n【测试2】仅获取Beta用户")
    beta_subscribers = manager.get_active_subscribers(
        include_beta=True,
        include_paid=False
    )
    print(f"找到 {len(beta_subscribers)} 个Beta订阅者:")
    for i, sub in enumerate(beta_subscribers, 1):
        print(f"  {i}. {sub['email']} - {sub['subscription_type']}")

    # 测试3：仅获取付费用户
    print("\n【测试3】仅获取付费用户")
    paid_subscribers = manager.get_active_subscribers(
        include_beta=False,
        include_paid=True
    )
    print(f"找到 {len(paid_subscribers)} 个付费订阅者:")
    for i, sub in enumerate(paid_subscribers, 1):
        print(f"  {i}. {sub['email']} - {sub['subscription_type']}")

    # 测试4：获取邮箱地址列表
    print("\n【测试4】获取邮箱地址列表")
    emails = manager.get_subscriber_emails(
        include_beta=True,
        include_paid=True
    )
    print(f"邮箱地址列表 ({len(emails)} 个):")
    for email in emails:
        print(f"  - {email}")

    print("\n" + "=" * 60)


def test_subscriber_count():
    """测试订阅者统计"""
    print("\n" + "=" * 60)
    print("测试：订阅者统计")
    print("=" * 60)

    manager = get_subscriber_manager()

    # 统计各种类型的订阅者
    print("\n活跃订阅者统计:")
    total_active = manager.get_subscriber_count(subscription_status='active')
    beta_count = manager.get_subscriber_count(
        subscription_type='beta',
        subscription_status='active'
    )
    paid_count = manager.get_subscriber_count(
        subscription_type='paid',
        subscription_status='active'
    )

    print(f"  总计: {total_active}")
    print(f"  Beta用户: {beta_count}")
    print(f"  付费用户: {paid_count}")

    print("\n" + "=" * 60)


def main():
    """主函数"""
    print("\n🧪 订阅者管理功能测试")
    print("=" * 60)
    print(f"数据库路径: {os.getenv('DATABASE_PATH', 'data/db.sqlite')}")
    print("=" * 60)

    try:
        # 测试获取订阅者
        test_get_active_subscribers()

        # 测试统计
        test_subscriber_count()

        print("\n✅ 所有测试完成!")
        return 0

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        logger.exception("测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
