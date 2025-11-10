"""
邀请码管理器
处理邀请码的生成、验证和管理

功能：
- 生成邀请码（随机/自定义）
- 验证邀请码有效性
- 批量生成邀请码
- 查询邀请码使用情况
- 停用/激活邀请码
"""

import os
import random
import string
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from src.database.connection import get_connection
from src.utils.logger import default_logger


class InviteManager:
    """邀请码管理器"""

    def __init__(self, database_path: Optional[str] = None):
        """
        初始化邀请码管理器

        Args:
            database_path: 数据库文件路径（默认从环境变量读取）
        """
        self.database_path = database_path or os.getenv(
            "DATABASE_PATH", "data/dashboard.db"
        )

    def generate_code(
        self,
        code: Optional[str] = None,
        code_type: str = "beta",
        max_uses: int = 1,
        created_by: Optional[str] = None,
        expires_in_days: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        生成邀请码

        Args:
            code: 自定义邀请码（可选，不提供则随机生成）
            code_type: 邀请码类型（beta/referral/partner）
            max_uses: 最大使用次数（-1表示无限）
            created_by: 创建人邮箱（如果是referral类型）
            expires_in_days: 有效期天数（可选）

        Returns:
            Dict: 生成结果
                {
                    "success": True/False,
                    "code": "ABC123",
                    "message": "邀请码生成成功"
                }
        """
        try:
            # 如果没有提供自定义码，则随机生成
            if not code:
                code = self._generate_random_code()

            # 计算过期时间
            expires_at = None
            if expires_in_days:
                expires_at = (
                    datetime.now(timezone.utc) + timedelta(days=expires_in_days)
                ).isoformat()

            conn = get_connection(self.database_path)
            cursor = conn.cursor()

            # 检查邀请码是否已存在
            cursor.execute(
                "SELECT code FROM invite_codes WHERE code = ?", (code,)
            )
            if cursor.fetchone():
                conn.close()
                return {
                    "success": False,
                    "message": f"邀请码 {code} 已存在，请使用其他码",
                }

            # 插入邀请码
            cursor.execute(
                """
                INSERT INTO invite_codes (
                    code, code_type, max_uses, created_by, expires_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (code, code_type, max_uses, created_by, expires_at),
            )

            conn.commit()
            code_id = cursor.lastrowid
            conn.close()

            default_logger.info(
                f"邀请码生成成功: {code}",
                extra={
                    "extra_fields": {
                        "code_id": code_id,
                        "code_type": code_type,
                        "max_uses": max_uses,
                    }
                },
            )

            return {
                "success": True,
                "code": code,
                "code_id": code_id,
                "message": "邀请码生成成功",
            }

        except Exception as e:
            default_logger.error(
                f"生成邀请码失败: {str(e)}",
                extra={"extra_fields": {"error": str(e)}},
            )
            return {"success": False, "message": f"生成邀请码失败: {str(e)}"}

    def generate_batch(
        self,
        count: int,
        code_type: str = "beta",
        max_uses: int = 1,
        expires_in_days: Optional[int] = None,
        prefix: str = "",
    ) -> Dict[str, Any]:
        """
        批量生成邀请码

        Args:
            count: 生成数量
            code_type: 邀请码类型
            max_uses: 每个码的最大使用次数
            expires_in_days: 有效期天数
            prefix: 邀请码前缀（可选）

        Returns:
            Dict: 生成结果
                {
                    "success": True/False,
                    "codes": ["ABC123", "DEF456", ...],
                    "count": 50,
                    "message": "批量生成成功"
                }
        """
        codes = []
        failed = 0

        for i in range(count):
            code = prefix + self._generate_random_code()
            result = self.generate_code(
                code=code,
                code_type=code_type,
                max_uses=max_uses,
                expires_in_days=expires_in_days,
            )

            if result["success"]:
                codes.append(result["code"])
            else:
                failed += 1
                # 如果失败，重试一次（可能是重复）
                code = prefix + self._generate_random_code()
                result = self.generate_code(
                    code=code,
                    code_type=code_type,
                    max_uses=max_uses,
                    expires_in_days=expires_in_days,
                )
                if result["success"]:
                    codes.append(result["code"])

        default_logger.info(
            f"批量生成邀请码: 成功{len(codes)}个, 失败{failed}个",
            extra={"extra_fields": {"count": count, "success": len(codes)}},
        )

        return {
            "success": len(codes) > 0,
            "codes": codes,
            "count": len(codes),
            "failed": failed,
            "message": f"批量生成完成：{len(codes)}个成功, {failed}个失败",
        }

    def validate_code(self, code: str) -> Dict[str, Any]:
        """
        验证邀请码有效性

        Args:
            code: 邀请码

        Returns:
            Dict: 验证结果
                {
                    "valid": True/False,
                    "reason": "邀请码有效" / "邀请码不存在" / "邀请码已过期" / ...,
                    "code_info": {...}  # 如果有效，返回详细信息
                }
        """
        try:
            conn = get_connection(self.database_path)
            cursor = conn.cursor()

            # 查询邀请码信息
            cursor.execute(
                """
                SELECT id, code, code_type, max_uses, current_uses,
                       created_by, expires_at, created_at, is_active
                FROM invite_codes
                WHERE code = ?
                """,
                (code,),
            )

            row = cursor.fetchone()
            conn.close()

            # 邀请码不存在
            if not row:
                return {
                    "valid": False,
                    "reason": "邀请码不存在",
                }

            code_info = {
                "id": row[0],
                "code": row[1],
                "code_type": row[2],
                "max_uses": row[3],
                "current_uses": row[4],
                "created_by": row[5],
                "expires_at": row[6],
                "created_at": row[7],
                "is_active": row[8],
            }

            # 邀请码未激活
            if not code_info["is_active"]:
                return {
                    "valid": False,
                    "reason": "邀请码已被停用",
                    "code_info": code_info,
                }

            # 检查是否过期
            if code_info["expires_at"]:
                from dateutil import parser

                expires_at_dt = parser.parse(code_info["expires_at"])
                # 确保两个datetime都有时区信息以便比较
                if expires_at_dt.tzinfo is None:
                    expires_at_dt = expires_at_dt.replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) > expires_at_dt:
                    return {
                        "valid": False,
                        "reason": f"邀请码已过期（过期时间：{code_info['expires_at']}）",
                        "code_info": code_info,
                    }

            # 检查使用次数
            if code_info["max_uses"] != -1:  # -1表示无限使用
                if code_info["current_uses"] >= code_info["max_uses"]:
                    return {
                        "valid": False,
                        "reason": f"邀请码已达使用上限（{code_info['max_uses']}次）",
                        "code_info": code_info,
                    }

            # 邀请码有效
            return {
                "valid": True,
                "reason": "邀请码有效",
                "code_info": code_info,
            }

        except Exception as e:
            default_logger.error(
                f"验证邀请码失败: {str(e)}",
                extra={"extra_fields": {"code": code, "error": str(e)}},
            )
            return {
                "valid": False,
                "reason": f"验证失败: {str(e)}",
            }

    def get_code_info(self, code: str) -> Optional[Dict[str, Any]]:
        """
        查询邀请码详细信息

        Args:
            code: 邀请码

        Returns:
            Dict: 邀请码信息，如果不存在返回None
        """
        try:
            conn = get_connection(self.database_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, code, code_type, max_uses, current_uses,
                       created_by, expires_at, created_at, is_active
                FROM invite_codes
                WHERE code = ?
                """,
                (code,),
            )

            row = cursor.fetchone()
            conn.close()

            if not row:
                return None

            return {
                "id": row[0],
                "code": row[1],
                "code_type": row[2],
                "max_uses": row[3],
                "current_uses": row[4],
                "created_by": row[5],
                "expires_at": row[6],
                "created_at": row[7],
                "is_active": row[8],
            }

        except Exception as e:
            default_logger.error(
                f"查询邀请码失败: {str(e)}",
                extra={"extra_fields": {"code": code, "error": str(e)}},
            )
            return None

    def get_all_codes(
        self,
        code_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        查询所有邀请码

        Args:
            code_type: 筛选邀请码类型（可选）
            is_active: 筛选激活状态（可选）
            limit: 返回数量上限

        Returns:
            List[Dict]: 邀请码列表
        """
        try:
            conn = get_connection(self.database_path)
            cursor = conn.cursor()

            # 构建查询条件
            conditions = []
            params = []

            if code_type:
                conditions.append("code_type = ?")
                params.append(code_type)

            if is_active is not None:
                conditions.append("is_active = ?")
                params.append(1 if is_active else 0)

            where_clause = ""
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)

            query = f"""
                SELECT id, code, code_type, max_uses, current_uses,
                       created_by, expires_at, created_at, is_active
                FROM invite_codes
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ?
            """

            params.append(limit)
            cursor.execute(query, params)

            rows = cursor.fetchall()
            conn.close()

            codes = []
            for row in rows:
                codes.append(
                    {
                        "id": row[0],
                        "code": row[1],
                        "code_type": row[2],
                        "max_uses": row[3],
                        "current_uses": row[4],
                        "created_by": row[5],
                        "expires_at": row[6],
                        "created_at": row[7],
                        "is_active": row[8],
                    }
                )

            return codes

        except Exception as e:
            default_logger.error(
                f"查询邀请码列表失败: {str(e)}",
                extra={"extra_fields": {"error": str(e)}},
            )
            return []

    def deactivate_code(self, code: str) -> bool:
        """
        停用邀请码

        Args:
            code: 邀请码

        Returns:
            bool: 是否成功
        """
        return self._update_active_status(code, is_active=False)

    def activate_code(self, code: str) -> bool:
        """
        激活邀请码

        Args:
            code: 邀请码

        Returns:
            bool: 是否成功
        """
        return self._update_active_status(code, is_active=True)

    def _update_active_status(self, code: str, is_active: bool) -> bool:
        """
        更新邀请码激活状态

        Args:
            code: 邀请码
            is_active: 激活状态

        Returns:
            bool: 是否成功
        """
        try:
            conn = get_connection(self.database_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE invite_codes
                SET is_active = ?
                WHERE code = ?
                """,
                (1 if is_active else 0, code),
            )

            conn.commit()
            rows_affected = cursor.rowcount
            conn.close()

            if rows_affected > 0:
                action = "激活" if is_active else "停用"
                default_logger.info(
                    f"邀请码{action}成功: {code}",
                    extra={"extra_fields": {"code": code}},
                )
                return True
            else:
                default_logger.warning(
                    f"邀请码不存在: {code}",
                    extra={"extra_fields": {"code": code}},
                )
                return False

        except Exception as e:
            default_logger.error(
                f"更新邀请码状态失败: {str(e)}",
                extra={"extra_fields": {"code": code, "error": str(e)}},
            )
            return False

    def _generate_random_code(self, length: int = 8) -> str:
        """
        生成随机邀请码

        Args:
            length: 邀请码长度

        Returns:
            str: 随机邀请码（大写字母+数字）
        """
        # 使用大写字母和数字，排除容易混淆的字符（0O, 1Il等）
        chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        return "".join(random.choices(chars, k=length))


# 使用示例
if __name__ == "__main__":
    # 测试用例
    im = InviteManager()

    print("=== 测试1：生成单个邀请码 ===")
    result = im.generate_code(
        code_type="beta", max_uses=1, expires_in_days=30
    )
    print(f"生成结果: {result}")
    print()

    print("=== 测试2：生成自定义邀请码 ===")
    result = im.generate_code(
        code="BETA2025", code_type="beta", max_uses=100, expires_in_days=90
    )
    print(f"生成结果: {result}")
    print()

    print("=== 测试3：批量生成邀请码 ===")
    result = im.generate_batch(
        count=5, code_type="beta", max_uses=1, expires_in_days=30, prefix="TEST"
    )
    print(f"批量生成结果: {result}")
    print()

    print("=== 测试4：验证邀请码 ===")
    if result["codes"]:
        test_code = result["codes"][0]
        validation = im.validate_code(test_code)
        print(f"验证结果: {validation}")
    print()

    print("=== 测试5：查询邀请码信息 ===")
    info = im.get_code_info("BETA2025")
    print(f"邀请码信息: {info}")
    print()

    print("=== 测试6：查询所有Beta邀请码 ===")
    codes = im.get_all_codes(code_type="beta", is_active=True, limit=10)
    print(f"Beta邀请码数量: {len(codes)}")
    if codes:
        print(f"示例: {codes[0]}")
    print()

    print("=== 测试7：停用邀请码 ===")
    if result["codes"]:
        test_code = result["codes"][0]
        success = im.deactivate_code(test_code)
        print(f"停用结果: {'成功' if success else '失败'}")

        # 再次验证
        validation = im.validate_code(test_code)
        print(f"停用后验证: {validation}")
    print()

    print("\n✅ 所有测试完成！")
