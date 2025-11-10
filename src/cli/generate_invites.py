#!/usr/bin/env python3
"""
邀请码生成CLI工具

用法：
    # 生成50个Beta邀请码，30天有效期
    python -m src.cli.generate_invites --count 50 --type beta --expires 30

    # 生成100个邀请码并导出CSV
    python -m src.cli.generate_invites --count 100 --output invites.csv

    # 生成自定义邀请码
    python -m src.cli.generate_invites --code BETA2025 --type beta --max-uses 100

    # 生成带前缀的邀请码
    python -m src.cli.generate_invites --count 20 --prefix "VIP" --type partner

功能：
- 批量生成邀请码
- 支持自定义邀请码
- 导出CSV格式
- 设置有效期和使用次数
"""

import argparse
import csv
import sys
from datetime import datetime, timezone
from src.user.invite_manager import InviteManager
from src.utils.logger import default_logger


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="邀请码生成工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 生成50个Beta邀请码
  python -m src.cli.generate_invites --count 50 --type beta --expires 30

  # 生成邀请码并导出CSV
  python -m src.cli.generate_invites --count 100 --output invites.csv

  # 生成自定义邀请码
  python -m src.cli.generate_invites --code BETA2025 --max-uses 100

  # 查看所有邀请码
  python -m src.cli.generate_invites --list

  # 验证邀请码
  python -m src.cli.generate_invites --validate BETA2025
        """,
    )

    # 生成模式参数
    parser.add_argument(
        "--count",
        type=int,
        help="生成邀请码数量（批量生成模式）",
    )

    parser.add_argument(
        "--code",
        type=str,
        help="自定义邀请码（单个生成模式）",
    )

    parser.add_argument(
        "--type",
        type=str,
        choices=["beta", "referral", "partner"],
        default="beta",
        help="邀请码类型（默认: beta）",
    )

    parser.add_argument(
        "--max-uses",
        type=int,
        default=1,
        help="最大使用次数（-1表示无限，默认: 1）",
    )

    parser.add_argument(
        "--expires",
        type=int,
        help="有效期天数（不设置则永久有效）",
    )

    parser.add_argument(
        "--prefix",
        type=str,
        default="",
        help="邀请码前缀（仅批量生成模式）",
    )

    parser.add_argument(
        "--output",
        type=str,
        help="导出CSV文件路径（例如: invites.csv）",
    )

    # 查询模式参数
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出所有邀请码",
    )

    parser.add_argument(
        "--validate",
        type=str,
        help="验证邀请码有效性",
    )

    parser.add_argument(
        "--info",
        type=str,
        help="查询邀请码详细信息",
    )

    parser.add_argument(
        "--deactivate",
        type=str,
        help="停用邀请码",
    )

    parser.add_argument(
        "--activate",
        type=str,
        help="激活邀请码",
    )

    # 筛选参数
    parser.add_argument(
        "--filter-type",
        type=str,
        choices=["beta", "referral", "partner"],
        help="筛选邀请码类型（仅--list模式）",
    )

    parser.add_argument(
        "--active-only",
        action="store_true",
        help="仅显示激活的邀请码（仅--list模式）",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="显示数量上限（仅--list模式，默认: 100）",
    )

    args = parser.parse_args()

    # 初始化邀请码管理器
    im = InviteManager()

    # ====== 查询模式 ======
    if args.list:
        list_codes(im, args)
        return 0

    if args.validate:
        validate_code(im, args.validate)
        return 0

    if args.info:
        show_code_info(im, args.info)
        return 0

    if args.deactivate:
        deactivate_code(im, args.deactivate)
        return 0

    if args.activate:
        activate_code(im, args.activate)
        return 0

    # ====== 生成模式 ======
    # 单个生成模式
    if args.code:
        generate_single(im, args)
        return 0

    # 批量生成模式
    if args.count:
        generate_batch(im, args)
        return 0

    # 如果没有指定任何操作，显示帮助
    parser.print_help()
    return 1


def generate_single(im: InviteManager, args):
    """生成单个邀请码"""
    print(f"🎫 生成自定义邀请码: {args.code}")
    print(f"   类型: {args.type}")
    print(f"   最大使用次数: {args.max_uses}")
    if args.expires:
        print(f"   有效期: {args.expires}天")

    result = im.generate_code(
        code=args.code,
        code_type=args.type,
        max_uses=args.max_uses,
        expires_in_days=args.expires,
    )

    if result["success"]:
        print(f"\n✅ 邀请码生成成功！")
        print(f"   邀请码: {result['code']}")
        print(f"   ID: {result['code_id']}")
    else:
        print(f"\n❌ 生成失败: {result['message']}")
        sys.exit(1)


def generate_batch(im: InviteManager, args):
    """批量生成邀请码"""
    print(f"🎫 批量生成邀请码")
    print(f"   数量: {args.count}")
    print(f"   类型: {args.type}")
    print(f"   最大使用次数: {args.max_uses}")
    if args.expires:
        print(f"   有效期: {args.expires}天")
    if args.prefix:
        print(f"   前缀: {args.prefix}")

    result = im.generate_batch(
        count=args.count,
        code_type=args.type,
        max_uses=args.max_uses,
        expires_in_days=args.expires,
        prefix=args.prefix,
    )

    if result["success"]:
        print(f"\n✅ 批量生成完成！")
        print(f"   成功: {result['count']}个")
        if result["failed"] > 0:
            print(f"   失败: {result['failed']}个")

        # 导出CSV
        if args.output:
            export_to_csv(im, result["codes"], args.output)
        else:
            # 显示前10个邀请码
            print(f"\n📋 生成的邀请码（前10个）:")
            for i, code in enumerate(result["codes"][:10], 1):
                print(f"   {i}. {code}")
            if len(result["codes"]) > 10:
                print(f"   ... 还有{len(result['codes']) - 10}个")
    else:
        print(f"\n❌ 批量生成失败: {result['message']}")
        sys.exit(1)


def export_to_csv(im: InviteManager, codes: list, output_path: str):
    """导出邀请码到CSV"""
    print(f"\n📁 导出到CSV: {output_path}")

    try:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # 写入表头
            writer.writerow(
                [
                    "邀请码",
                    "类型",
                    "最大使用次数",
                    "当前使用次数",
                    "有效期",
                    "创建时间",
                    "状态",
                ]
            )

            # 写入每个邀请码的详细信息
            for code in codes:
                code_info = im.get_code_info(code)
                if code_info:
                    writer.writerow(
                        [
                            code_info["code"],
                            code_info["code_type"],
                            code_info["max_uses"],
                            code_info["current_uses"],
                            code_info["expires_at"] or "永久",
                            code_info["created_at"],
                            "激活" if code_info["is_active"] else "停用",
                        ]
                    )

        print(f"✅ CSV导出成功！")
        print(f"   文件位置: {output_path}")
        print(f"   记录数: {len(codes)}")

    except Exception as e:
        print(f"❌ CSV导出失败: {str(e)}")
        sys.exit(1)


def list_codes(im: InviteManager, args):
    """列出所有邀请码"""
    print("📋 邀请码列表")

    if args.filter_type:
        print(f"   筛选类型: {args.filter_type}")
    if args.active_only:
        print(f"   仅显示激活的邀请码")

    codes = im.get_all_codes(
        code_type=args.filter_type,
        is_active=True if args.active_only else None,
        limit=args.limit,
    )

    if not codes:
        print("\n⚠️  未找到邀请码")
        return

    print(f"\n找到 {len(codes)} 个邀请码:\n")

    # 表格表头
    print(
        f"{'邀请码':<15} {'类型':<10} {'使用情况':<15} {'有效期':<25} {'状态':<6}"
    )
    print("-" * 85)

    # 打印每个邀请码
    for code_info in codes:
        code = code_info["code"]
        code_type = code_info["code_type"]
        uses = f"{code_info['current_uses']}/{code_info['max_uses'] if code_info['max_uses'] != -1 else '∞'}"
        expires = code_info["expires_at"] or "永久"
        if expires != "永久":
            # 截断ISO格式时间
            expires = expires[:19]
        status = "✅" if code_info["is_active"] else "❌"

        print(f"{code:<15} {code_type:<10} {uses:<15} {expires:<25} {status:<6}")


def validate_code(im: InviteManager, code: str):
    """验证邀请码"""
    print(f"🔍 验证邀请码: {code}")

    result = im.validate_code(code)

    if result["valid"]:
        print(f"\n✅ 邀请码有效！")
        code_info = result["code_info"]
        print(f"   类型: {code_info['code_type']}")
        print(
            f"   使用情况: {code_info['current_uses']}/{code_info['max_uses'] if code_info['max_uses'] != -1 else '无限'}"
        )
        if code_info["expires_at"]:
            print(f"   有效期至: {code_info['expires_at']}")
        else:
            print(f"   有效期: 永久")
    else:
        print(f"\n❌ 邀请码无效！")
        print(f"   原因: {result['reason']}")


def show_code_info(im: InviteManager, code: str):
    """显示邀请码详细信息"""
    print(f"🔍 查询邀请码: {code}")

    code_info = im.get_code_info(code)

    if not code_info:
        print(f"\n❌ 邀请码不存在")
        return

    print(f"\n📋 邀请码详细信息:")
    print(f"   ID: {code_info['id']}")
    print(f"   邀请码: {code_info['code']}")
    print(f"   类型: {code_info['code_type']}")
    print(
        f"   最大使用次数: {code_info['max_uses'] if code_info['max_uses'] != -1 else '无限'}"
    )
    print(f"   当前使用次数: {code_info['current_uses']}")
    if code_info["created_by"]:
        print(f"   创建人: {code_info['created_by']}")
    print(f"   有效期: {code_info['expires_at'] or '永久'}")
    print(f"   创建时间: {code_info['created_at']}")
    print(f"   状态: {'激活' if code_info['is_active'] else '停用'}")


def deactivate_code(im: InviteManager, code: str):
    """停用邀请码"""
    print(f"⏸️  停用邀请码: {code}")

    success = im.deactivate_code(code)

    if success:
        print(f"✅ 邀请码已停用")
    else:
        print(f"❌ 停用失败（邀请码可能不存在）")


def activate_code(im: InviteManager, code: str):
    """激活邀请码"""
    print(f"▶️  激活邀请码: {code}")

    success = im.activate_code(code)

    if success:
        print(f"✅ 邀请码已激活")
    else:
        print(f"❌ 激活失败（邀请码可能不存在）")


if __name__ == "__main__":
    sys.exit(main())
