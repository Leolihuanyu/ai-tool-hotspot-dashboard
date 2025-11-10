#!/usr/bin/env python3
"""
邀请码系统快速测试脚本

用法：
    python scripts/test_invite_system.py

功能：
    - 测试邀请码管理模块
    - 测试用户注册流程
    - 测试推荐奖励系统
    - 生成测试报告
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.user.invite_manager import InviteManager
from src.user.user_manager import UserManager
from src.user.referral_manager import ReferralManager
from src.auth.token_manager import TokenManager


def print_header(title):
    """打印测试标题"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def print_step(step, description):
    """打印测试步骤"""
    print(f"\n[步骤 {step}] {description}")
    print("-" * 60)


def print_result(success, message):
    """打印测试结果"""
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")


def test_invite_manager():
    """测试邀请码管理模块"""
    print_header("测试1: 邀请码管理模块")

    im = InviteManager()
    results = []

    # 测试1.1: 生成单个邀请码
    print_step("1.1", "生成单个邀请码")
    result = im.generate_code(
        code="AUTOTEST2025",
        code_type="beta",
        max_uses=10,
        expires_in_days=30
    )
    success = result["success"]
    print_result(success, f"生成邀请码: {result.get('code', 'N/A')}")
    results.append(("生成单个邀请码", success))

    # 测试1.2: 批量生成邀请码
    print_step("1.2", "批量生成邀请码")
    result = im.generate_batch(
        count=5,
        code_type="beta",
        max_uses=1,
        expires_in_days=30,
        prefix="AUTO"
    )
    success = result["success"] and result["count"] == 5
    print_result(success, f"批量生成: {result['count']}/5 成功")
    if success:
        print(f"   生成的邀请码: {', '.join(result['codes'][:3])}...")
    results.append(("批量生成邀请码", success))

    # 测试1.3: 验证邀请码
    print_step("1.3", "验证邀请码")
    result = im.validate_code("AUTOTEST2025")
    success = result["valid"]
    print_result(success, f"验证结果: {result['reason']}")
    if success:
        info = result["code_info"]
        print(f"   类型: {info['code_type']}")
        print(f"   使用情况: {info['current_uses']}/{info['max_uses']}")
    results.append(("验证邀请码", success))

    # 测试1.4: 查询邀请码信息
    print_step("1.4", "查询邀请码信息")
    info = im.get_code_info("AUTOTEST2025")
    success = info is not None
    print_result(success, "查询邀请码信息")
    if success:
        print(f"   ID: {info['id']}")
        print(f"   状态: {'激活' if info['is_active'] else '停用'}")
    results.append(("查询邀请码信息", success))

    # 测试1.5: 列出所有邀请码
    print_step("1.5", "列出所有邀请码")
    codes = im.get_all_codes(is_active=True, limit=10)
    success = len(codes) > 0
    print_result(success, f"找到 {len(codes)} 个激活的邀请码")
    results.append(("列出邀请码", success))

    return results


def test_user_registration():
    """测试用户注册流程"""
    print_header("测试2: 用户注册流程")

    im = InviteManager()
    um = UserManager()
    results = []

    # 准备测试邮箱
    test_email = "autotest@example.com"

    # 测试2.1: 创建用户
    print_step("2.1", "创建测试用户")
    result = um.create_user(
        email=test_email,
        subscription_type="beta",
        invite_code="AUTOTEST2025"
    )
    success = result["success"]
    print_result(success, f"创建用户: {result.get('message', 'N/A')}")
    if success:
        print(f"   用户ID: {result['user_id']}")
    results.append(("创建用户", success))

    # 测试2.2: 查询用户信息
    print_step("2.2", "查询用户信息")
    user = um.get_user(test_email)
    success = user is not None
    print_result(success, "查询用户信息")
    if success:
        print(f"   邮箱: {user['email']}")
        print(f"   订阅类型: {user['subscription_type']}")
        print(f"   使用邀请码: {user['invite_code']}")
    results.append(("查询用户信息", success))

    # 测试2.3: 验证邀请码使用次数增加
    print_step("2.3", "验证邀请码使用次数")
    validation = im.validate_code("AUTOTEST2025")
    if validation["valid"]:
        current_uses = validation["code_info"]["current_uses"]
        success = current_uses >= 1
        print_result(success, f"使用次数: {current_uses}")
    else:
        success = False
        print_result(success, "邀请码状态异常")
    results.append(("邀请码使用次数更新", success))

    # 测试2.4: 生成访问token
    print_step("2.4", "生成访问token")
    tm = TokenManager()
    result = tm.generate_token(test_email)
    success = result["success"]
    print_result(success, "生成访问token")
    if success:
        print(f"   Token长度: {len(result['token'])} 字符")
        print(f"   Dashboard URL: {result['dashboard_url'][:60]}...")
    results.append(("生成访问token", success))

    return results


def test_referral_system():
    """测试推荐奖励系统"""
    print_header("测试3: 推荐奖励系统")

    im = InviteManager()
    um = UserManager()
    rm = ReferralManager()
    results = []

    # 准备测试数据
    referrer_email = "autotest@example.com"
    referee_email = "autotest.referred@example.com"

    # 测试3.1: 生成推荐码
    print_step("3.1", "为用户生成推荐码")

    # 先确保推荐人存在
    referrer = um.get_user(referrer_email)
    if not referrer:
        um.create_user(referrer_email, subscription_type="beta")

    result = rm.generate_referral_code(referrer_email)
    success = result["success"]
    print_result(success, f"生成推荐码: {result.get('code', 'N/A')}")
    referral_code = result.get("code", "").replace("REF-", "")
    results.append(("生成推荐码", success))

    # 测试3.2: 使用推荐码注册
    print_step("3.2", "使用推荐码注册新用户")

    # 先创建推荐邀请码
    im.generate_code(
        code=referral_code,
        code_type="referral",
        max_uses=5,
        created_by=referrer_email,
        expires_in_days=90
    )

    result = um.create_user(
        email=referee_email,
        subscription_type="beta",
        invite_code=referral_code,
        referrer_email=referrer_email
    )
    success = result["success"]
    print_result(success, f"注册新用户: {result.get('message', 'N/A')}")
    results.append(("推荐注册", success))

    # 测试3.3: 发放推荐奖励
    print_step("3.3", "发放推荐奖励")
    result = rm.grant_referral_reward(referrer_email, referee_email)
    success = result["success"]
    print_result(success, f"奖励发放: {result.get('message', 'N/A')}")
    if success:
        print(f"   奖励天数: {result['reward_days']}天")
        print(f"   新免费期至: {result['new_free_until'][:19]}")
    results.append(("发放推荐奖励", success))

    # 测试3.4: 查询推荐统计
    print_step("3.4", "查询推荐统计")
    stats = rm.get_referral_stats(referrer_email)
    success = stats["total_referrals"] >= 1
    print_result(success, "查询推荐统计")
    if success:
        print(f"   推荐总数: {stats['total_referrals']}")
        print(f"   已发放奖励: {stats['granted_rewards']}")
        print(f"   累计奖励天数: {stats['total_reward_days']}")
    results.append(("查询推荐统计", success))

    # 测试3.5: 查询推荐历史
    print_step("3.5", "查询推荐历史")
    history = rm.get_referral_history(referrer_email, role="referrer")
    success = len(history) >= 1
    print_result(success, f"推荐历史记录: {len(history)}条")
    if history:
        print(f"   最近推荐: {history[0]['referee_email']}")
        print(f"   奖励状态: {history[0]['reward_status']}")
    results.append(("查询推荐历史", success))

    return results


def print_summary(all_results):
    """打印测试总结"""
    print_header("测试总结")

    total_tests = sum(len(results) for results in all_results.values())
    passed_tests = sum(
        sum(1 for _, success in results if success)
        for results in all_results.values()
    )

    print(f"\n总测试数: {total_tests}")
    print(f"通过: {passed_tests}")
    print(f"失败: {total_tests - passed_tests}")
    print(f"成功率: {passed_tests/total_tests*100:.1f}%")

    print("\n详细结果:")
    for category, results in all_results.items():
        print(f"\n{category}:")
        for name, success in results:
            icon = "✅" if success else "❌"
            print(f"  {icon} {name}")

    print("\n" + "="*60)
    if passed_tests == total_tests:
        print("🎉 所有测试通过！邀请码系统运行正常。")
    else:
        print(f"⚠️  {total_tests - passed_tests} 个测试失败，请检查日志。")
    print("="*60)


def main():
    """主函数"""
    print("\n🚀 开始测试邀请码系统...")

    try:
        # 运行所有测试
        all_results = {
            "邀请码管理": test_invite_manager(),
            "用户注册": test_user_registration(),
            "推荐奖励": test_referral_system(),
        }

        # 打印总结
        print_summary(all_results)

        # 返回退出码
        total_tests = sum(len(results) for results in all_results.values())
        passed_tests = sum(
            sum(1 for _, success in results if success)
            for results in all_results.values()
        )

        return 0 if passed_tests == total_tests else 1

    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
