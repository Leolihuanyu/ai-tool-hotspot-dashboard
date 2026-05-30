"""生成测试邀请码用于端到端测试"""

import os
import sys

# 设置PostgreSQL连接
os.environ['DB_TYPE'] = 'postgresql'
os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL', '')

from src.user.invite_manager import InviteManager

def generate_test_invite():
    """生成一个测试邀请码"""
    print("=" * 60)
    print("生成端到端测试邀请码")
    print("=" * 60)

    invite_mgr = InviteManager()

    # 生成Beta邀请码（最多使用1次）
    result = invite_mgr.generate_code(
        code_type='beta',
        max_uses=1,
        created_by='test@example.com'
    )

    if result['success']:
        invite_code = result['code']
        print(f"\n✓ 成功生成测试邀请码!")
        print(f"\n" + "=" * 60)
        print(f"邀请码: {invite_code}")
        print(f"=" * 60)
        print(f"\n使用此邀请码测试用户注册流程:")
        print(f"1. 访问前端: https://ai-tool-hotspot-dashboard.vercel.app")
        print(f"2. 输入邮箱: test_{invite_code[-4:].lower()}@example.com")
        print(f"3. 输入邀请码: {invite_code}")
        print(f"4. 完成注册")
        print(f"\n验证命令:")
        print(f"curl -X POST https://ai-tool-hotspot-dashboard.onrender.com/api/verify-invite \\")
        print(f"  -H 'Content-Type: application/json' \\")
        print(f"  -d '{{\"invite_code\": \"{invite_code}\"}}'")
        print(f"\n")
        return invite_code
    else:
        print(f"\n✗ 生成失败: {result.get('message')}")
        return None

if __name__ == '__main__':
    invite_code = generate_test_invite()
    sys.exit(0 if invite_code else 1)
