"""
推荐奖励管理器
处理推荐关系和奖励发放

功能：
- 发放推荐奖励（延长免费使用期）
- 查询推荐历史
- 更新奖励状态
- 统计推荐数据
"""

import os
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from src.database.connection import get_connection, convert_placeholder
from src.utils.logger import default_logger


class ReferralManager:
    """推荐奖励管理器"""

    # 推荐奖励：推荐人获得的额外免费天数
    REFERRAL_REWARD_DAYS = 7

    def __init__(self, database_path: Optional[str] = None):
        """
        初始化推荐奖励管理器

        Args:
            database_path: 数据库文件路径（默认从环境变量读取）
        """
        self.database_path = database_path or os.getenv(
            "DATABASE_PATH", "data/dashboard.db"
        )

    def grant_referral_reward(self, referrer_email: str, referee_email: str) -> Dict[str, Any]:
        """
        发放推荐奖励给推荐人

        逻辑：
        1. 查找推荐关系记录
        2. 验证奖励尚未发放
        3. 延长推荐人的免费使用期（+7天）
        4. 更新奖励状态为已发放

        Args:
            referrer_email: 推荐人邮箱
            referee_email: 被推荐人邮箱

        Returns:
            Dict: 操作结果
                {
                    "success": True/False,
                    "reward_days": 7,
                    "new_free_until": "2025-12-01",
                    "message": "奖励发放成功"
                }
        """
        try:
            conn = get_connection(self.database_path)
            cursor = conn.cursor()

            # 1. 查找推荐关系记录
            query = convert_placeholder("""
                SELECT id, reward_status
                FROM referrals
                WHERE referrer_email = ? AND referee_email = ?
                """)
            cursor.execute(query, (referrer_email, referee_email))

            referral = cursor.fetchone()

            if not referral:
                conn.close()
                return {
                    "success": False,
                    "message": f"未找到推荐关系记录：{referrer_email} -> {referee_email}",
                }

            # 兼容SQLite (tuple/Row) 和 PostgreSQL (dict)
            if isinstance(referral, dict):
                referral_id = referral['id']
                reward_status = referral['reward_status']
            else:
                referral_id = referral[0]
                reward_status = referral[1]

            # 2. 验证奖励尚未发放
            if reward_status == "granted":
                conn.close()
                return {
                    "success": False,
                    "message": "推荐奖励已经发放过了",
                }

            # 3. 查询推荐人当前的免费使用期
            query = convert_placeholder("""
                SELECT free_until
                FROM users
                WHERE email = ?
                """)
            cursor.execute(query, (referrer_email,))

            user = cursor.fetchone()

            if not user:
                conn.close()
                return {
                    "success": False,
                    "message": f"推荐人不存在: {referrer_email}",
                }

            # 兼容SQLite (tuple/Row) 和 PostgreSQL (dict)
            current_free_until = user['free_until'] if isinstance(user, dict) else user[0]

            # 计算新的免费使用期
            if current_free_until:
                # 如果已有免费期，在此基础上延长
                from dateutil import parser

                free_until_dt = parser.parse(current_free_until)
                # 如果免费期已过期，从当前时间开始计算
                if free_until_dt < datetime.now(timezone.utc):
                    free_until_dt = datetime.now(timezone.utc)
            else:
                # 如果没有免费期，从当前时间开始
                free_until_dt = datetime.now(timezone.utc)

            # 延长7天
            new_free_until_dt = free_until_dt + timedelta(days=self.REFERRAL_REWARD_DAYS)
            new_free_until = new_free_until_dt.isoformat()

            # 4. 更新推荐人的免费使用期
            query = convert_placeholder("""
                UPDATE users
                SET free_until = ?, updated_at = ?
                WHERE email = ?
                """)
            cursor.execute(query, (new_free_until, datetime.now(timezone.utc).isoformat(), referrer_email))

            # 5. 更新推荐关系的奖励状态
            query = convert_placeholder("""
                UPDATE referrals
                SET reward_status = 'granted',
                    reward_granted_at = ?
                WHERE id = ?
                """)
            cursor.execute(query, (datetime.now(timezone.utc).isoformat(), referral_id))

            conn.commit()
            conn.close()

            default_logger.info(
                f"推荐奖励发放成功: {referrer_email} 推荐了 {referee_email}",
                extra={
                    "extra_fields": {
                        "referrer": referrer_email,
                        "referee": referee_email,
                        "reward_days": self.REFERRAL_REWARD_DAYS,
                        "new_free_until": new_free_until,
                    }
                },
            )

            return {
                "success": True,
                "reward_days": self.REFERRAL_REWARD_DAYS,
                "new_free_until": new_free_until,
                "message": f"推荐奖励发放成功！免费使用期延长至 {new_free_until[:10]}",
            }

        except Exception as e:
            default_logger.error(
                f"发放推荐奖励失败: {str(e)}",
                extra={
                    "extra_fields": {
                        "referrer": referrer_email,
                        "referee": referee_email,
                        "error": str(e),
                    }
                },
            )
            return {"success": False, "message": f"发放推荐奖励失败: {str(e)}"}

    def get_referral_history(self, email: str, role: str = "referrer") -> List[Dict[str, Any]]:
        """
        查询推荐历史

        Args:
            email: 用户邮箱
            role: 角色类型
                - "referrer": 作为推荐人的记录（我推荐了谁）
                - "referee": 作为被推荐人的记录（谁推荐了我）

        Returns:
            List[Dict]: 推荐历史列表
        """
        try:
            conn = get_connection(self.database_path)
            cursor = conn.cursor()

            if role == "referrer":
                # 查询我推荐了谁
                query = convert_placeholder("""
                    SELECT id, referrer_email, referee_email, invite_code,
                           reward_status, reward_granted_at, created_at
                    FROM referrals
                    WHERE referrer_email = ?
                    ORDER BY created_at DESC
                    """)
                cursor.execute(query, (email,))
            else:
                # 查询谁推荐了我
                query = convert_placeholder("""
                    SELECT id, referrer_email, referee_email, invite_code,
                           reward_status, reward_granted_at, created_at
                    FROM referrals
                    WHERE referee_email = ?
                    ORDER BY created_at DESC
                    """)
                cursor.execute(query, (email,))

            rows = cursor.fetchall()
            conn.close()

            referrals = []
            for row in rows:
                # 兼容SQLite (tuple/Row) 和 PostgreSQL (dict)
                if isinstance(row, dict):
                    referrals.append({
                        "id": row['id'],
                        "referrer_email": row['referrer_email'],
                        "referee_email": row['referee_email'],
                        "invite_code": row['invite_code'],
                        "reward_status": row['reward_status'],
                        "reward_granted_at": row['reward_granted_at'],
                        "created_at": row['created_at'],
                    })
                else:
                    referrals.append({
                        "id": row[0],
                        "referrer_email": row[1],
                        "referee_email": row[2],
                        "invite_code": row[3],
                        "reward_status": row[4],
                        "reward_granted_at": row[5],
                        "created_at": row[6],
                    })

            return referrals

        except Exception as e:
            default_logger.error(
                f"查询推荐历史失败: {str(e)}",
                extra={"extra_fields": {"email": email, "role": role, "error": str(e)}},
            )
            return []

    def get_referral_stats(self, email: str) -> Dict[str, Any]:
        """
        获取推荐统计数据

        Args:
            email: 用户邮箱

        Returns:
            Dict: 统计数据
                {
                    "total_referrals": 10,  # 推荐总数
                    "pending_rewards": 2,    # 待发放奖励数
                    "granted_rewards": 8,    # 已发放奖励数
                    "total_reward_days": 56, # 累计获得奖励天数
                    "referral_list": [...]   # 推荐列表
                }
        """
        try:
            conn = get_connection(self.database_path)
            cursor = conn.cursor()

            # 查询推荐总数和各状态数量
            query = convert_placeholder("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN reward_status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN reward_status = 'granted' THEN 1 ELSE 0 END) as granted
                FROM referrals
                WHERE referrer_email = ?
                """)
            cursor.execute(query, (email,))

            row = cursor.fetchone()

            # 兼容SQLite (tuple/Row) 和 PostgreSQL (dict)
            if isinstance(row, dict):
                total_referrals = row['total'] or 0
                pending_rewards = row['pending'] or 0
                granted_rewards = row['granted'] or 0
            else:
                total_referrals = row[0] or 0
                pending_rewards = row[1] or 0
                granted_rewards = row[2] or 0

            # 计算累计获得的奖励天数
            total_reward_days = granted_rewards * self.REFERRAL_REWARD_DAYS

            # 获取推荐列表
            referral_list = self.get_referral_history(email, role="referrer")

            conn.close()

            return {
                "total_referrals": total_referrals,
                "pending_rewards": pending_rewards,
                "granted_rewards": granted_rewards,
                "total_reward_days": total_reward_days,
                "referral_list": referral_list,
            }

        except Exception as e:
            default_logger.error(
                f"获取推荐统计失败: {str(e)}",
                extra={"extra_fields": {"email": email, "error": str(e)}},
            )
            return {
                "total_referrals": 0,
                "pending_rewards": 0,
                "granted_rewards": 0,
                "total_reward_days": 0,
                "referral_list": [],
            }

    def generate_referral_code(self, referrer_email: str) -> Dict[str, Any]:
        """
        为推荐人生成专属推荐码

        Args:
            referrer_email: 推荐人邮箱

        Returns:
            Dict: 生成结果
                {
                    "success": True,
                    "code": "REF-ABC123",
                    "message": "推荐码生成成功"
                }
        """
        try:
            from src.user.invite_manager import InviteManager

            im = InviteManager()

            # 生成推荐码（前缀REF + 随机6位）
            result = im.generate_code(
                code_type="referral",
                max_uses=10,  # 每个推荐码最多使用10次
                expires_in_days=90,  # 90天有效期
                created_by=referrer_email,
            )

            if result["success"]:
                # 添加REF-前缀使推荐码更易识别
                code = result["code"]
                return {
                    "success": True,
                    "code": f"REF-{code}",
                    "message": "推荐码生成成功",
                }
            else:
                return result

        except Exception as e:
            default_logger.error(
                f"生成推荐码失败: {str(e)}",
                extra={"extra_fields": {"email": referrer_email, "error": str(e)}},
            )
            return {"success": False, "message": f"生成推荐码失败: {str(e)}"}

    def auto_grant_pending_rewards(self) -> Dict[str, Any]:
        """
        自动发放所有待处理的推荐奖励

        用途：
        - 定期任务（每日执行）
        - 确保所有成功的推荐都能获得奖励

        Returns:
            Dict: 处理结果
                {
                    "success": True,
                    "processed": 5,
                    "granted": 4,
                    "failed": 1
                }
        """
        try:
            conn = get_connection(self.database_path)
            cursor = conn.cursor()

            # 查询所有待处理的推荐奖励
            query = convert_placeholder("""
                SELECT referrer_email, referee_email
                FROM referrals
                WHERE reward_status = 'pending'
                """)
            cursor.execute(query)

            pending_referrals = cursor.fetchall()
            conn.close()

            processed = 0
            granted = 0
            failed = 0

            for row in pending_referrals:
                # 兼容SQLite (tuple/Row) 和 PostgreSQL (dict)
                if isinstance(row, dict):
                    referrer_email = row['referrer_email']
                    referee_email = row['referee_email']
                else:
                    referrer_email = row[0]
                    referee_email = row[1]

                processed += 1

                result = self.grant_referral_reward(referrer_email, referee_email)

                if result["success"]:
                    granted += 1
                else:
                    failed += 1
                    default_logger.warning(
                        f"自动发放奖励失败: {referrer_email} -> {referee_email}, 原因: {result['message']}"
                    )

            default_logger.info(
                f"自动发放推荐奖励完成: 处理{processed}个, 成功{granted}个, 失败{failed}个"
            )

            return {
                "success": True,
                "processed": processed,
                "granted": granted,
                "failed": failed,
                "message": f"自动发放完成：处理{processed}个，成功{granted}个",
            }

        except Exception as e:
            default_logger.error(
                f"自动发放推荐奖励失败: {str(e)}",
                extra={"extra_fields": {"error": str(e)}},
            )
            return {"success": False, "message": f"自动发放失败: {str(e)}"}


# 使用示例
if __name__ == "__main__":
    # 测试用例
    rm = ReferralManager()

    print("=== 测试1：发放推荐奖励 ===")
    # 假设用户A推荐了用户B
    result = rm.grant_referral_reward(
        referrer_email="alice@example.com", referee_email="bob@example.com"
    )
    print(f"发放结果: {result}")
    print()

    print("=== 测试2：查询推荐历史 ===")
    history = rm.get_referral_history("alice@example.com", role="referrer")
    print(f"推荐历史数量: {len(history)}")
    if history:
        print(f"示例: {history[0]}")
    print()

    print("=== 测试3：获取推荐统计 ===")
    stats = rm.get_referral_stats("alice@example.com")
    print(f"推荐统计: {stats}")
    print()

    print("=== 测试4：生成推荐码 ===")
    result = rm.generate_referral_code("alice@example.com")
    print(f"推荐码: {result}")
    print()

    print("=== 测试5：自动发放待处理奖励 ===")
    result = rm.auto_grant_pending_rewards()
    print(f"自动发放结果: {result}")
    print()

    print("\n✅ 所有测试完成！")
