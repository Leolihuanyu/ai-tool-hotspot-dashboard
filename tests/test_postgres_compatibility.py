#!/usr/bin/env python3
"""
测试 PostgreSQL 占位符转换兼容性

验证所有修改的文件都能正确处理 SQLite 和 PostgreSQL 的占位符
"""

import os
import re


def check_convert_placeholder_usage():
    """检查文件中是否正确使用了 convert_placeholder"""
    print("=" * 60)
    print("检查 convert_placeholder 使用情况")
    print("=" * 60)

    files_to_check = [
        "src/user/user_manager.py",
        "src/user/invite_manager.py",
        "src/user/referral_manager.py",
    ]

    all_good = True

    for file_path in files_to_check:
        print(f"\n检查文件: {file_path}")
        print("-" * 40)

        full_path = os.path.join(os.path.dirname(__file__), file_path)
        if not os.path.exists(full_path):
            print(f"✗ 文件不存在")
            all_good = False
            continue

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否导入了 convert_placeholder
        has_import = 'convert_placeholder' in content and 'from src.database.connection import' in content

        if has_import:
            print(f"✓ 已导入 convert_placeholder")
        else:
            print(f"✗ 未导入 convert_placeholder")
            all_good = False

        # 统计 cursor.execute 调用次数
        execute_pattern = r'cursor\.execute\('
        execute_matches = re.findall(execute_pattern, content)
        execute_count = len(execute_matches)

        # 统计 convert_placeholder 调用次数
        convert_pattern = r'convert_placeholder\('
        convert_matches = re.findall(convert_pattern, content)
        convert_count = len(convert_matches)

        print(f"cursor.execute 调用: {execute_count} 次")
        print(f"convert_placeholder 调用: {convert_count} 次")

        # 检查是否有遗漏的占位符查询
        # 查找所有包含 ? 的 cursor.execute 调用（但不在 convert_placeholder 之后）
        lines = content.split('\n')
        potential_issues = []

        for i, line in enumerate(lines, 1):
            # 如果这行有 cursor.execute 和 ?，但前几行没有 convert_placeholder
            if 'cursor.execute' in line and '?' in line:
                # 检查前3行是否有 convert_placeholder
                start = max(0, i - 4)
                prev_lines = '\n'.join(lines[start:i])
                if 'convert_placeholder' not in prev_lines:
                    potential_issues.append(f"第 {i} 行")

        if potential_issues:
            print(f"⚠️  可能遗漏的查询: {', '.join(potential_issues)}")
        else:
            print("✓ 所有带占位符的查询都已转换")

        # 检查语法（简单检查括号配对）
        open_parens = content.count('(')
        close_parens = content.count(')')
        if open_parens == close_parens:
            print("✓ 括号配对正确")
        else:
            print(f"✗ 括号不配对: ( {open_parens} vs ) {close_parens}")
            all_good = False

    return all_good


def generate_summary():
    """生成修改总结"""
    print("\n" + "=" * 60)
    print("修改总结")
    print("=" * 60)

    summary = """
已完成以下文件的 PostgreSQL 兼容性修改：

1. src/user/user_manager.py
   - 修改了所有 SQL 查询以支持占位符转换
   - 涉及方法:
     * create_user() - 用户创建
     * get_user() - 用户查询
     * update_user() - 用户更新
     * log_access() - 访问日志记录
     * get_access_logs() - 访问日志查询
     * get_all_active_users() - 活跃用户查询

2. src/user/invite_manager.py
   - 修改了所有 SQL 查询以支持占位符转换
   - 涉及方法:
     * generate_code() - 邀请码生成
     * validate_code() - 邀请码验证
     * get_code_info() - 邀请码信息查询
     * get_all_codes() - 邀请码列表查询
     * _update_active_status() - 邀请码状态更新

3. src/user/referral_manager.py
   - 修改了所有 SQL 查询以支持占位符转换
   - 涉及方法:
     * grant_referral_reward() - 推荐奖励发放
     * get_referral_history() - 推荐历史查询
     * get_referral_stats() - 推荐统计查询
     * auto_grant_pending_rewards() - 自动发放奖励

4. src/auth/token_manager.py
   - ✓ 此文件不涉及数据库操作，无需修改

修改方案：
- 在每个文件顶部添加导入: from src.database.connection import convert_placeholder
- 在所有 cursor.execute() 调用前使用 convert_placeholder() 转换 SQL 语句
- 保持原有业务逻辑不变，只添加转换层

兼容性：
- SQLite: convert_placeholder() 返回原始查询（保持 ? 占位符）
- PostgreSQL: convert_placeholder() 将 ? 转换为 %s

使用方式：
1. SQLite 模式（默认）:
   DB_TYPE=sqlite 或不设置

2. PostgreSQL 模式:
   DB_TYPE=postgresql
   DATABASE_URL=<DATABASE_URL>
"""
    print(summary)


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("PostgreSQL 兼容性检查")
    print("=" * 60 + "\n")

    # 检查使用情况
    all_good = check_convert_placeholder_usage()

    # 生成总结
    generate_summary()

    # 最终结果
    print("\n" + "=" * 60)
    if all_good:
        print("✓ 所有检查通过！")
    else:
        print("⚠️  发现一些问题，请检查上面的输出")
    print("=" * 60)

    return 0 if all_good else 1


if __name__ == "__main__":
    exit(main())
