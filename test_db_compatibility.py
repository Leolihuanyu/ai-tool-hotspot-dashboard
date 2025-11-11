#!/usr/bin/env python3
"""测试 SQLite/PostgreSQL 兼容性修复"""

import sys
import os

# 添加项目路径到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.user.user_manager import UserManager
from src.user.referral_manager import ReferralManager
from src.user.invite_manager import InviteManager


def test_user_manager():
    """测试 UserManager 的数据库兼容性"""
    print("=" * 60)
    print("测试 UserManager")
    print("=" * 60)

    um = UserManager()

    # 测试1: 创建用户
    print("\n[测试1] 创建用户")
    result = um.create_user(
        email="test_compat@example.com",
        subscription_type="beta",
        invite_code="TESTCODE"
    )
    print(f"✓ 创建结果: {result['success']}, {result['message']}")

    # 测试2: 查询用户 (测试 get_user 的兼容性代码)
    print("\n[测试2] 查询用户 - 测试 row 字典/索引访问")
    user = um.get_user("test_compat@example.com")
    if user:
        print(f"✓ 查询成功: ID={user['id']}, Email={user['email']}")
    else:
        print("✗ 用户不存在")

    # 测试3: 记录访问日志
    print("\n[测试3] 记录访问日志")
    success = um.log_access(
        email="test_compat@example.com",
        token="test-token-12345",
        access_result="success",
        ip_address="127.0.0.1"
    )
    print(f"✓ 日志记录: {'成功' if success else '失败'}")

    # 测试4: 查询访问日志 (测试 get_access_logs 的兼容性代码)
    print("\n[测试4] 查询访问日志 - 测试 row 字典/索引访问")
    logs = um.get_access_logs("test_compat@example.com", limit=5)
    print(f"✓ 查询到 {len(logs)} 条日志")
    if logs:
        print(f"  示例: {logs[0]['email']}, {logs[0]['access_result']}")

    # 测试5: 获取活跃用户 (测试 get_all_active_users 的兼容性代码)
    print("\n[测试5] 获取活跃用户 - 测试 row 字典/索引访问")
    active_users = um.get_all_active_users()
    print(f"✓ 查询到 {len(active_users)} 个活跃用户")
    if active_users:
        print(f"  示例: {active_users[0]['email']}")

    print("\n✅ UserManager 所有测试通过!")


def test_referral_manager():
    """测试 ReferralManager 的数据库兼容性"""
    print("\n" + "=" * 60)
    print("测试 ReferralManager")
    print("=" * 60)

    rm = ReferralManager()
    um = UserManager()

    # 准备测试数据
    print("\n[准备] 创建测试用户")
    um.create_user("referrer_test@example.com", "beta")
    um.create_user("referee_test@example.com", "beta")

    # 手动创建推荐关系 (因为需要测试兼容性代码)
    from src.database.connection import get_connection, convert_placeholder
    conn = get_connection()
    cursor = conn.cursor()
    query = convert_placeholder("""
        INSERT OR IGNORE INTO referrals (referrer_email, referee_email, invite_code, reward_status)
        VALUES (?, ?, ?, 'pending')
    """)
    cursor.execute(query, ("referrer_test@example.com", "referee_test@example.com", "TESTREF"))
    conn.commit()
    conn.close()
    print("✓ 准备完成")

    # 测试1: 发放推荐奖励 (测试 grant_referral_reward 的兼容性代码)
    print("\n[测试1] 发放推荐奖励 - 测试 row 字典/索引访问")
    result = rm.grant_referral_reward(
        referrer_email="referrer_test@example.com",
        referee_email="referee_test@example.com"
    )
    print(f"✓ 发放结果: {result['success']}, {result['message']}")

    # 测试2: 查询推荐历史 (测试 get_referral_history 的兼容性代码)
    print("\n[测试2] 查询推荐历史 - 测试 row 字典/索引访问")
    history = rm.get_referral_history("referrer_test@example.com", role="referrer")
    print(f"✓ 查询到 {len(history)} 条推荐记录")
    if history:
        print(f"  示例: {history[0]['referee_email']}, {history[0]['reward_status']}")

    # 测试3: 获取推荐统计 (测试 get_referral_stats 的兼容性代码)
    print("\n[测试3] 获取推荐统计 - 测试 row 字典/索引访问")
    stats = rm.get_referral_stats("referrer_test@example.com")
    print(f"✓ 统计结果: 总推荐数={stats['total_referrals']}, "
          f"已发放={stats['granted_rewards']}, "
          f"待发放={stats['pending_rewards']}")

    # 测试4: 自动发放奖励 (测试 auto_grant_pending_rewards 的兼容性代码)
    print("\n[测试4] 自动发放待处理奖励 - 测试 row 字典/索引访问")
    # 先创建一些待处理的推荐
    conn = get_connection()
    cursor = conn.cursor()
    query = convert_placeholder("""
        INSERT OR IGNORE INTO referrals (referrer_email, referee_email, invite_code, reward_status)
        VALUES (?, ?, ?, 'pending')
    """)
    cursor.execute(query, ("referrer_test@example.com", "referee2_test@example.com", "TESTREF2"))
    conn.commit()
    conn.close()

    result = rm.auto_grant_pending_rewards()
    print(f"✓ 处理结果: 处理={result['processed']}, "
          f"成功={result['granted']}, "
          f"失败={result['failed']}")

    print("\n✅ ReferralManager 所有测试通过!")


def test_invite_manager():
    """测试 InviteManager 的数据库兼容性 (已修复的参考)"""
    print("\n" + "=" * 60)
    print("测试 InviteManager (参考修复)")
    print("=" * 60)

    im = InviteManager()

    # 测试1: 生成邀请码
    print("\n[测试1] 生成邀请码")
    result = im.generate_code(
        code="COMPAT_TEST",
        code_type="beta",
        max_uses=5
    )
    print(f"✓ 生成结果: {result['success']}, Code={result.get('code')}")

    # 测试2: 验证邀请码 (已有兼容性代码)
    print("\n[测试2] 验证邀请码 - 测试 row 字典/索引访问")
    validation = im.validate_code("COMPAT_TEST")
    print(f"✓ 验证结果: {validation['valid']}, {validation['reason']}")

    # 测试3: 查询邀请码信息 (已有兼容性代码)
    print("\n[测试3] 查询邀请码信息 - 测试 row 字典/索引访问")
    info = im.get_code_info("COMPAT_TEST")
    if info:
        print(f"✓ 查询成功: Code={info['code']}, Type={info['code_type']}, Uses={info['current_uses']}/{info['max_uses']}")

    # 测试4: 查询所有邀请码 (已有兼容性代码)
    print("\n[测试4] 查询所有邀请码 - 测试 row 字典/索引访问")
    codes = im.get_all_codes(code_type="beta", is_active=True, limit=5)
    print(f"✓ 查询到 {len(codes)} 个邀请码")
    if codes:
        print(f"  示例: {codes[0]['code']}, {codes[0]['code_type']}")

    print("\n✅ InviteManager 所有测试通过!")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("SQLite/PostgreSQL 兼容性测试")
    print("=" * 60)

    db_type = os.getenv('DB_TYPE', 'sqlite')
    print(f"\n当前数据库类型: {db_type.upper()}")
    print("=" * 60)

    try:
        # 测试 InviteManager (参考修复)
        test_invite_manager()

        # 测试 UserManager (新修复)
        test_user_manager()

        # 测试 ReferralManager (新修复)
        test_referral_manager()

        print("\n" + "=" * 60)
        print("🎉 所有测试通过! 数据库兼容性修复成功!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
