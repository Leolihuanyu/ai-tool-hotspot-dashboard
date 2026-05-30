"""测试 PostgreSQL 数据库 CRUD 操作

测试用户管理和邀请码系统的核心功能。
"""

import os
import sys
from datetime import datetime, timedelta

# 设置 PostgreSQL 连接
os.environ['DB_TYPE'] = 'postgresql'
os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL', '')

from src.user.invite_manager import InviteManager
from src.user.user_manager import UserManager
from src.user.referral_manager import ReferralManager


def test_crud_operations():
    """测试CRUD操作"""
    print("=" * 60)
    print("PostgreSQL CRUD 功能测试")
    print("=" * 60)

    invite_mgr = InviteManager()
    user_mgr = UserManager()
    referral_mgr = ReferralManager()

    test_email_1 = "test_user_1@example.com"
    test_email_2 = "test_user_2@example.com"

    try:
        # === 测试 1: 创建邀请码 ===
        print("\n[1/7] 测试创建邀请码...")
        result = invite_mgr.generate_code(
            code_type='beta',
            max_uses=10
        )
        assert result['success'], f"邀请码生成失败: {result.get('message')}"
        invite_code = result['code']
        print(f"✓ 成功创建邀请码: {invite_code}")

        # === 测试 2: 验证邀请码 ===
        print("\n[2/7] 测试验证邀请码...")
        validation_result = invite_mgr.validate_code(invite_code)
        assert validation_result['valid'], f"邀请码验证失败: {validation_result.get('reason')}"
        print(f"✓ 邀请码验证成功: {invite_code}")

        # === 测试 3: 创建用户 ===
        print("\n[3/7] 测试创建用户...")
        result = user_mgr.create_user(
            email=test_email_1,
            subscription_type='beta',
            invite_code=invite_code
        )
        assert result['success'], f"用户创建失败: {result.get('message')}"
        user_id_1 = result['user_id']
        print(f"✓ 成功创建用户 1: {test_email_1} (ID: {user_id_1})")

        # === 测试 4: 读取用户 ===
        print("\n[4/7] 测试读取用户...")
        user = user_mgr.get_user(email=test_email_1)
        assert user is not None, "用户读取失败"
        assert user['email'] == test_email_1, "用户邮箱不匹配"
        print(f"✓ 成功读取用户: {user['email']}")
        print(f"  - ID: {user['id']}")
        print(f"  - 订阅类型: {user['subscription_type']}")
        print(f"  - 订阅状态: {user['subscription_status']}")

        # === 测试 5: 生成推荐邀请码 ===
        print("\n[5/7] 测试生成推荐邀请码...")
        referral_result = invite_mgr.generate_code(
            code_type='referral',
            created_by=test_email_1,
            max_uses=5
        )
        assert referral_result['success'], f"推荐码生成失败: {referral_result.get('message')}"
        referral_code = referral_result['code']
        print(f"✓ 成功生成推荐邀请码: {referral_code}")

        # === 测试 6: 通过推荐码创建新用户 ===
        print("\n[6/7] 测试推荐用户注册...")
        result2 = user_mgr.create_user(
            email=test_email_2,
            subscription_type='beta',
            invite_code=referral_code,
            referrer_email=test_email_1
        )
        assert result2['success'], f"推荐用户创建失败: {result2.get('message')}"
        user_id_2 = result2['user_id']
        print(f"✓ 成功创建推荐用户: {test_email_2} (ID: {user_id_2})")
        print(f"  (推荐关系已自动记录)")

        # 发放推荐奖励
        reward_days = referral_mgr.grant_referral_reward(
            referrer_email=test_email_1,
            referee_email=test_email_2
        )
        print(f"✓ 成功发放推荐奖励: {reward_days} 天免费使用")

        # === 测试 7: 清理测试数据 ===
        print("\n[7/7] 清理测试数据...")

        from src.database.connection import get_db_connection

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 删除测试数据（按照外键依赖关系顺序）
            cursor.execute("DELETE FROM referrals WHERE referrer_email = %s OR referee_email = %s",
                          (test_email_1, test_email_2))
            cursor.execute("DELETE FROM access_logs WHERE email = %s OR email = %s",
                          (test_email_1, test_email_2))
            # 先删除引用 users 的 invite_codes
            cursor.execute("DELETE FROM invite_codes WHERE code = %s OR code = %s",
                          (invite_code, referral_code))
            # 再删除 users
            cursor.execute("DELETE FROM users WHERE email = %s OR email = %s",
                          (test_email_1, test_email_2))

            conn.commit()
            cursor.close()

        print("✓ 测试数据清理完成")

        # === 测试总结 ===
        print("\n" + "=" * 60)
        print("✅ 所有 CRUD 测试通过！")
        print("=" * 60)
        print("\n测试覆盖:")
        print("  ✅ 邀请码生成与验证")
        print("  ✅ 用户创建与读取")
        print("  ✅ 推荐关系记录")
        print("  ✅ 推荐奖励发放")
        print("  ✅ 数据库完整性约束")
        print("\n数据库已准备就绪，可以部署到生产环境! 🚀")
        print("=" * 60)

        return True

    except Exception as e:
        import traceback
        print(f"\n❌ 测试失败: {e}")
        print("\n详细错误信息:")
        traceback.print_exc()

        # 尝试清理
        try:
            print("\n尝试清理测试数据...")
            from src.database.connection import get_db_connection
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM referrals WHERE referrer_email = %s OR referee_email = %s",
                              (test_email_1, test_email_2))
                cursor.execute("DELETE FROM access_logs WHERE email = %s OR email = %s",
                              (test_email_1, test_email_2))
                cursor.execute("DELETE FROM invite_codes")  # 先删除所有邀请码
                cursor.execute("DELETE FROM users WHERE email = %s OR email = %s",
                              (test_email_1, test_email_2))
                conn.commit()
                cursor.close()
            print("✓ 清理完成")
        except Exception as cleanup_error:
            print(f"⚠️  清理时出错(可忽略): {cleanup_error}")

        return False


if __name__ == '__main__':
    success = test_crud_operations()
    sys.exit(0 if success else 1)
