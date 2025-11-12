"""订阅者管理服务

从数据库查询活跃订阅者,用于发送每日报告邮件。
"""

import os
from typing import List, Dict, Any
from src.database.connection import get_connection, convert_placeholder
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SubscriberManager:
    """订阅者管理器"""

    def __init__(self, database_path: str = None):
        """
        初始化订阅者管理器

        Args:
            database_path: 数据库路径
        """
        self.database_path = database_path or os.getenv(
            "DATABASE_PATH", "data/db.sqlite"
        )

    def get_active_subscribers(
        self,
        include_beta: bool = True,
        include_paid: bool = True
    ) -> List[Dict[str, Any]]:
        """
        获取所有活跃订阅者

        Args:
            include_beta: 是否包含Beta用户
            include_paid: 是否包含付费用户

        Returns:
            List[Dict]: 订阅者列表,每个订阅者包含:
                - id: 用户ID
                - email: 邮箱地址
                - subscription_type: 订阅类型(beta/paid)
                - language: 语言偏好(zh/en/ja)
                - timezone: 时区
        """
        try:
            conn = get_connection(self.database_path)
            cursor = conn.cursor()

            # 构建订阅类型过滤条件
            subscription_types = []
            if include_beta:
                subscription_types.append('beta')
            if include_paid:
                subscription_types.append('paid')

            if not subscription_types:
                logger.warning("未指定任何订阅类型,返回空列表")
                return []

            # 生成占位符（?, ?, ...）
            placeholders = ', '.join(['?' for _ in subscription_types])

            # 查询活跃订阅者
            # 注意：language和timezone字段可能不存在，使用COALESCE提供默认值
            query = convert_placeholder(f"""
                SELECT
                    id,
                    email,
                    subscription_type,
                    COALESCE(language, 'en') as language,
                    COALESCE(timezone, 'UTC') as timezone
                FROM users
                WHERE subscription_status = 'active'
                  AND subscription_type IN ({placeholders})
                ORDER BY created_at ASC
            """)

            cursor.execute(query, subscription_types)
            rows = cursor.fetchall()
            conn.close()

            subscribers = []
            for row in rows:
                # 兼容SQLite (tuple/Row) 和 PostgreSQL (dict)
                if isinstance(row, dict):
                    subscriber = {
                        "id": row['id'],
                        "email": row['email'],
                        "subscription_type": row['subscription_type'],
                        "language": row.get('language', 'en'),  # 默认英文
                        "timezone": row.get('timezone', 'UTC'),  # 默认UTC
                    }
                else:
                    subscriber = {
                        "id": row[0],
                        "email": row[1],
                        "subscription_type": row[2],
                        "language": row[3] if len(row) > 3 else 'en',  # 默认英文
                        "timezone": row[4] if len(row) > 4 else 'UTC',  # 默认UTC
                    }
                subscribers.append(subscriber)

            logger.info(
                f"找到 {len(subscribers)} 个活跃订阅者 "
                f"(Beta: {include_beta}, Paid: {include_paid})",
                extra={"extra_fields": {
                    "subscriber_count": len(subscribers),
                    "include_beta": include_beta,
                    "include_paid": include_paid
                }}
            )

            return subscribers

        except Exception as e:
            logger.error(f"获取活跃订阅者失败: {str(e)}")
            return []

    def get_subscribers_by_timezones(
        self,
        target_timezones: List[str],
        include_beta: bool = True,
        include_paid: bool = True
    ) -> List[Dict[str, Any]]:
        """
        获取指定时区的活跃订阅者

        Args:
            target_timezones: 目标时区列表，例如 ['Asia/Shanghai', 'Asia/Tokyo', 'America/New_York']
            include_beta: 是否包含Beta用户
            include_paid: 是否包含付费用户

        Returns:
            List[Dict]: 订阅者列表，只包含时区在目标列表中的用户
        """
        try:
            conn = get_connection(self.database_path)
            cursor = conn.cursor()

            # 构建订阅类型过滤条件
            subscription_types = []
            if include_beta:
                subscription_types.append('beta')
            if include_paid:
                subscription_types.append('paid')

            if not subscription_types:
                logger.warning("未指定任何订阅类型，返回空列表")
                return []

            if not target_timezones:
                logger.warning("未指定目标时区，返回空列表")
                return []

            # 生成占位符
            sub_placeholders = ', '.join(['?' for _ in subscription_types])
            tz_placeholders = ', '.join(['?' for _ in target_timezones])

            # 查询指定时区的活跃订阅者
            query = convert_placeholder(f"""
                SELECT
                    id,
                    email,
                    subscription_type,
                    COALESCE(language, 'en') as language,
                    COALESCE(timezone, 'UTC') as timezone
                FROM users
                WHERE subscription_status = 'active'
                  AND subscription_type IN ({sub_placeholders})
                  AND COALESCE(timezone, 'UTC') IN ({tz_placeholders})
                ORDER BY created_at ASC
            """)

            cursor.execute(query, subscription_types + target_timezones)
            rows = cursor.fetchall()
            conn.close()

            subscribers = []
            for row in rows:
                # 兼容SQLite (tuple/Row) 和 PostgreSQL (dict)
                if isinstance(row, dict):
                    subscriber = {
                        "id": row['id'],
                        "email": row['email'],
                        "subscription_type": row['subscription_type'],
                        "language": row.get('language', 'en'),
                        "timezone": row.get('timezone', 'UTC'),
                    }
                else:
                    subscriber = {
                        "id": row[0],
                        "email": row[1],
                        "subscription_type": row[2],
                        "language": row[3] if len(row) > 3 else 'en',
                        "timezone": row[4] if len(row) > 4 else 'UTC',
                    }
                subscribers.append(subscriber)

            logger.info(
                f"找到 {len(subscribers)} 个活跃订阅者 "
                f"(时区: {', '.join(target_timezones)})",
                extra={"extra_fields": {
                    "subscriber_count": len(subscribers),
                    "target_timezones": target_timezones
                }}
            )

            return subscribers

        except Exception as e:
            logger.error(f"按时区获取订阅者失败: {str(e)}")
            return []

    def get_subscriber_emails(
        self,
        include_beta: bool = True,
        include_paid: bool = True
    ) -> List[str]:
        """
        获取所有活跃订阅者的邮箱地址列表

        Args:
            include_beta: 是否包含Beta用户
            include_paid: 是否包含付费用户

        Returns:
            List[str]: 邮箱地址列表
        """
        subscribers = self.get_active_subscribers(include_beta, include_paid)
        emails = [sub['email'] for sub in subscribers]

        logger.info(f"获取到 {len(emails)} 个订阅者邮箱地址")
        return emails

    def get_subscriber_count(
        self,
        subscription_type: str = None,
        subscription_status: str = 'active'
    ) -> int:
        """
        获取订阅者数量统计

        Args:
            subscription_type: 订阅类型过滤(beta/paid/free),None表示所有类型
            subscription_status: 订阅状态过滤(active/cancelled/expired)

        Returns:
            int: 订阅者数量
        """
        try:
            conn = get_connection(self.database_path)
            cursor = conn.cursor()

            # 构建查询
            if subscription_type:
                query = convert_placeholder("""
                    SELECT COUNT(*) FROM users
                    WHERE subscription_type = ?
                      AND subscription_status = ?
                """)
                cursor.execute(query, (subscription_type, subscription_status))
            else:
                query = convert_placeholder("""
                    SELECT COUNT(*) FROM users
                    WHERE subscription_status = ?
                """)
                cursor.execute(query, (subscription_status,))

            count = cursor.fetchone()[0]
            conn.close()

            logger.info(
                f"订阅者统计: {count} 个 "
                f"(类型: {subscription_type or '全部'}, 状态: {subscription_status})"
            )
            return count

        except Exception as e:
            logger.error(f"获取订阅者统计失败: {str(e)}")
            return 0


# 全局实例（懒加载）
_subscriber_manager_instance = None


def get_subscriber_manager() -> SubscriberManager:
    """获取订阅者管理器实例（懒加载，单例模式）"""
    global _subscriber_manager_instance
    if _subscriber_manager_instance is None:
        _subscriber_manager_instance = SubscriberManager()
    return _subscriber_manager_instance
