"""
用户管理器
处理用户CRUD操作和访问日志记录

功能：
- 创建新用户（Beta邀请/付费订阅）
- 查询用户信息
- 更新用户订阅状态
- 记录访问日志
- 处理推荐奖励
"""

import os
import hashlib
import sqlite3
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from src.database.connection import get_connection, convert_placeholder
from src.utils.logger import default_logger


class UserManager:
    """用户管理器"""

    def __init__(self, database_path: Optional[str] = None):
        """
        初始化用户管理器

        Args:
            database_path: 数据库文件路径（默认从环境变量读取）
        """
        self.database_path = database_path or os.getenv(
            "DATABASE_PATH", "data/db.sqlite"
        )

    def create_user(
        self,
        email: str,
        subscription_type: str = "beta",
        invite_code: Optional[str] = None,
        referrer_email: Optional[str] = None,
        language: str = "en",
        timezone: str = "UTC",
    ) -> Dict[str, Any]:
        """
        创建新用户

        Args:
            email: 用户邮箱
            subscription_type: 订阅类型（beta/paid/free）
            invite_code: 使用的邀请码
            referrer_email: 推荐人邮箱（用于推荐奖励）
            language: 用户语言偏好（zh/en/ja）
            timezone: 用户时区（如 Asia/Shanghai）

        Returns:
            Dict: 创建结果
                {
                    "success": True/False,
                    "user_id": 1,
                    "message": "用户创建成功"
                }
        """
        try:
            conn = get_connection(self.database_path)
            cursor = conn.cursor()

            # 检查用户是否已存在
            query = convert_placeholder("SELECT id FROM users WHERE email = ?")
            cursor.execute(query, (email,))
            existing_user = cursor.fetchone()
            if existing_user:
                return {
                    "success": False,
                    "message": f"用户 {email} 已存在",
                }

            # 获取推荐人ID（如果提供了推荐人邮箱）
            referrer_id = None
            if referrer_email:
                query = convert_placeholder("SELECT id FROM users WHERE email = ?")
                cursor.execute(query, (referrer_email,))
                referrer = cursor.fetchone()
                if referrer:
                    # 兼容SQLite (tuple/Row) 和 PostgreSQL (dict)
                    referrer_id = referrer['id'] if isinstance(referrer, dict) else referrer[0]

            # 计算试用期截止时间（Beta用户：60天）
            free_until = None
            if subscription_type == "beta":
                from datetime import timedelta
                trial_days = int(os.getenv("BETA_TRIAL_DAYS", "60"))
                free_until = (datetime.now(timezone.utc) + timedelta(days=trial_days)).isoformat()

            # 插入新用户
            query = convert_placeholder("""
                INSERT INTO users (
                    email, subscription_type, subscription_status,
                    invite_code, referrer_id, free_until, language, timezone
                )
                VALUES (?, ?, 'active', ?, ?, ?, ?, ?)
                RETURNING id
                """)
            cursor.execute(query, (email, subscription_type, invite_code, referrer_id, free_until, language, timezone))

            # 获取新用户ID（兼容PostgreSQL和SQLite）
            result = cursor.fetchone()
            user_id = result['id'] if isinstance(result, dict) else result[0]

            # 如果使用了邀请码，更新邀请码使用次数
            if invite_code:
                query = convert_placeholder("""
                    UPDATE invite_codes
                    SET current_uses = current_uses + 1
                    WHERE code = ?
                    """)
                cursor.execute(query, (invite_code,))

            # 如果有推荐人，创建推荐关系记录
            if referrer_id and invite_code:
                query = convert_placeholder("""
                    INSERT INTO referrals (
                        referrer_email, referee_email, invite_code
                    )
                    VALUES (?, ?, ?)
                    """)
                cursor.execute(query, (referrer_email, email, invite_code))

            conn.commit()
            conn.close()

            default_logger.info(
                f"用户创建成功: {email}",
                extra={
                    "extra_fields": {
                        "user_id": user_id,
                        "subscription_type": subscription_type,
                        "free_until": free_until,
                        "language": language,
                        "timezone": timezone,
                    }
                },
            )

            return {
                "success": True,
                "user_id": user_id,
                "message": "用户创建成功",
                "free_until": free_until,
            }

        except Exception as e:
            default_logger.error(
                f"创建用户失败: {str(e)}",
                extra={"extra_fields": {"email": email, "error": str(e)}},
            )
            return {"success": False, "message": f"创建用户失败: {str(e)}"}

    def get_user(self, email: str) -> Optional[Dict[str, Any]]:
        """
        查询用户信息

        Args:
            email: 用户邮箱

        Returns:
            Dict: 用户信息，如果用户不存在返回None
        """
        try:
            conn = get_connection(self.database_path)
            cursor = conn.cursor()

            query = convert_placeholder("""
                SELECT id, email, subscription_type, subscription_status,
                       invite_code, referrer_id, free_until,
                       stripe_customer_id, stripe_subscription_id,
                       created_at, updated_at, last_accessed_at,
                       language, timezone, access_token,
                       token_generated_at, token_expires_at
                FROM users
                WHERE email = ?
                """)
            cursor.execute(query, (email,))

            row = cursor.fetchone()
            conn.close()

            if not row:
                return None

            # 兼容SQLite (tuple/Row) 和 PostgreSQL (dict)
            if isinstance(row, dict):
                return {
                    "id": row['id'],
                    "email": row['email'],
                    "subscription_type": row['subscription_type'],
                    "subscription_status": row['subscription_status'],
                    "invite_code": row['invite_code'],
                    "referrer_id": row['referrer_id'],
                    "free_until": row['free_until'],
                    "stripe_customer_id": row['stripe_customer_id'],
                    "stripe_subscription_id": row['stripe_subscription_id'],
                    "created_at": row['created_at'],
                    "updated_at": row['updated_at'],
                    "last_accessed_at": row['last_accessed_at'],
                    "language": row['language'],
                    "timezone": row['timezone'],
                    "access_token": row['access_token'],
                    "token_generated_at": row['token_generated_at'],
                    "token_expires_at": row['token_expires_at'],
                }
            else:
                return {
                    "id": row[0],
                    "email": row[1],
                    "subscription_type": row[2],
                    "subscription_status": row[3],
                    "invite_code": row[4],
                    "referrer_id": row[5],
                    "free_until": row[6],
                    "stripe_customer_id": row[7],
                    "stripe_subscription_id": row[8],
                    "created_at": row[9],
                    "updated_at": row[10],
                    "last_accessed_at": row[11],
                    "language": row[12],
                    "timezone": row[13],
                    "access_token": row[14],
                    "token_generated_at": row[15],
                    "token_expires_at": row[16],
                }

        except Exception as e:
            default_logger.error(
                f"查询用户失败: {str(e)}",
                extra={"extra_fields": {"email": email, "error": str(e)}},
            )
            return None

    def update_user(
        self,
        email: str,
        subscription_type: Optional[str] = None,
        subscription_status: Optional[str] = None,
        stripe_customer_id: Optional[str] = None,
        stripe_subscription_id: Optional[str] = None,
        language: Optional[str] = None,
        timezone: Optional[str] = None,
        access_token: Optional[str] = None,
        token_generated_at: Optional[str] = None,
        token_expires_at: Optional[str] = None,
    ) -> bool:
        """
        更新用户信息

        Args:
            email: 用户邮箱
            subscription_type: 新的订阅类型
            subscription_status: 新的订阅状态
            stripe_customer_id: Stripe客户ID
            stripe_subscription_id: Stripe订阅ID
            language: 用户语言偏好（zh/en/ja）
            timezone: 用户时区（如 Asia/Shanghai）
            access_token: 长期访问token
            token_generated_at: token生成时间（ISO格式字符串）
            token_expires_at: token过期时间（ISO格式字符串）

        Returns:
            bool: 是否更新成功
        """
        try:
            conn = get_connection(self.database_path)
            cursor = conn.cursor()

            # 构建UPDATE语句
            update_fields = []
            params = []

            if subscription_type:
                update_fields.append("subscription_type = ?")
                params.append(subscription_type)

            if subscription_status:
                update_fields.append("subscription_status = ?")
                params.append(subscription_status)

            if stripe_customer_id:
                update_fields.append("stripe_customer_id = ?")
                params.append(stripe_customer_id)

            if stripe_subscription_id:
                update_fields.append("stripe_subscription_id = ?")
                params.append(stripe_subscription_id)

            if language:
                update_fields.append("language = ?")
                params.append(language)

            if timezone:
                update_fields.append("timezone = ?")
                params.append(timezone)

            if access_token is not None:  # 允许清空token（设置为None）
                update_fields.append("access_token = ?")
                params.append(access_token)

            if token_generated_at:
                update_fields.append("token_generated_at = ?")
                params.append(token_generated_at)

            if token_expires_at:
                update_fields.append("token_expires_at = ?")
                params.append(token_expires_at)

            # 总是更新updated_at
            from datetime import timezone as tz
            update_fields.append("updated_at = ?")
            params.append(datetime.now(tz.utc).isoformat())

            params.append(email)

            query = f"""
                UPDATE users
                SET {', '.join(update_fields)}
                WHERE email = ?
            """
            query = convert_placeholder(query)

            cursor.execute(query, params)
            conn.commit()
            rows_affected = cursor.rowcount
            conn.close()

            if rows_affected > 0:
                default_logger.info(
                    f"用户更新成功: {email}",
                    extra={"extra_fields": {"email": email}},
                )
                return True
            else:
                default_logger.warning(
                    f"用户不存在或未更新: {email}",
                    extra={"extra_fields": {"email": email}},
                )
                return False

        except Exception as e:
            default_logger.error(
                f"更新用户失败: {str(e)}",
                extra={"extra_fields": {"email": email, "error": str(e)}},
            )
            return False

    def update_access_token(
        self,
        email: str,
        access_token: str,
        expiry_days: int = 90
    ) -> bool:
        """
        更新用户的访问token

        Args:
            email: 用户邮箱
            access_token: 新的访问token
            expiry_days: token有效期（天），默认90天

        Returns:
            bool: 是否更新成功
        """
        try:
            from datetime import timedelta, timezone as tz

            generated_at = datetime.now(tz.utc)
            expires_at = generated_at + timedelta(days=expiry_days)

            success = self.update_user(
                email=email,
                access_token=access_token,
                token_generated_at=generated_at.isoformat(),
                token_expires_at=expires_at.isoformat()
            )

            if success:
                default_logger.info(
                    f"访问token更新成功: {email}",
                    extra={"extra_fields": {
                        "email": email,
                        "token_expires_at": expires_at.isoformat()
                    }}
                )

            return success

        except Exception as e:
            default_logger.error(
                f"更新访问token失败: {str(e)}",
                extra={"extra_fields": {"email": email, "error": str(e)}}
            )
            return False

    def get_user_token(self, email: str) -> Optional[str]:
        """
        获取用户的访问token

        Args:
            email: 用户邮箱

        Returns:
            str: 访问token，如果用户不存在或没有token则返回None
        """
        user = self.get_user(email)
        if user:
            return user.get("access_token")
        return None

    def clear_access_token(self, email: str) -> bool:
        """
        清空用户的访问token（用于撤销访问权限）

        Args:
            email: 用户邮箱

        Returns:
            bool: 是否清空成功
        """
        return self.update_user(
            email=email,
            access_token=None,
            token_generated_at=None,
            token_expires_at=None
        )

    def log_access(
        self,
        email: str,
        token: str,
        access_result: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        记录访问日志

        Args:
            email: 用户邮箱
            token: 访问token
            access_result: 访问结果（success/expired/invalid/ip_mismatch）
            ip_address: IP地址
            user_agent: User Agent
            error_message: 错误信息（如果验证失败）

        Returns:
            bool: 是否记录成功
        """
        try:
            conn = get_connection(self.database_path)
            cursor = conn.cursor()

            # 计算token的SHA256哈希值（隐私保护）
            token_hash = hashlib.sha256(token.encode()).hexdigest()

            # 插入访问日志
            query = convert_placeholder("""
                INSERT INTO access_logs (
                    email, token_hash, ip_address, user_agent,
                    access_result, error_message
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """)
            cursor.execute(query, (email, token_hash, ip_address, user_agent, access_result, error_message))

            # 如果访问成功，更新用户的last_accessed_at
            if access_result == "success":
                query = convert_placeholder("""
                    UPDATE users
                    SET last_accessed_at = ?
                    WHERE email = ?
                    """)
                cursor.execute(query, (datetime.now(timezone.utc).isoformat(), email))

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            default_logger.error(
                f"记录访问日志失败: {str(e)}",
                extra={"extra_fields": {"email": email, "error": str(e)}},
            )
            return False

    def get_access_logs(
        self, email: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        查询访问日志

        Args:
            email: 用户邮箱（可选，不提供则返回所有用户的日志）
            limit: 返回记录数上限

        Returns:
            List[Dict]: 访问日志列表
        """
        try:
            conn = get_connection(self.database_path)
            cursor = conn.cursor()

            if email:
                query = convert_placeholder("""
                    SELECT id, email, token_hash, accessed_at, ip_address,
                           user_agent, access_result, error_message
                    FROM access_logs
                    WHERE email = ?
                    ORDER BY accessed_at DESC
                    LIMIT ?
                    """)
                cursor.execute(query, (email, limit))
            else:
                query = convert_placeholder("""
                    SELECT id, email, token_hash, accessed_at, ip_address,
                           user_agent, access_result, error_message
                    FROM access_logs
                    ORDER BY accessed_at DESC
                    LIMIT ?
                    """)
                cursor.execute(query, (limit,))

            rows = cursor.fetchall()
            conn.close()

            logs = []
            for row in rows:
                # 兼容SQLite (tuple/Row) 和 PostgreSQL (dict)
                if isinstance(row, dict):
                    logs.append({
                        "id": row['id'],
                        "email": row['email'],
                        "token_hash": row['token_hash'],
                        "accessed_at": row['accessed_at'],
                        "ip_address": row['ip_address'],
                        "user_agent": row['user_agent'],
                        "access_result": row['access_result'],
                        "error_message": row['error_message'],
                    })
                else:
                    logs.append({
                        "id": row[0],
                        "email": row[1],
                        "token_hash": row[2],
                        "accessed_at": row[3],
                        "ip_address": row[4],
                        "user_agent": row[5],
                        "access_result": row[6],
                        "error_message": row[7],
                    })

            return logs

        except Exception as e:
            default_logger.error(
                f"查询访问日志失败: {str(e)}",
                extra={"extra_fields": {"error": str(e)}},
            )
            return []

    def get_all_active_users(self) -> List[Dict[str, Any]]:
        """
        获取所有活跃用户（用于每日邮件发送）

        Returns:
            List[Dict]: 活跃用户列表
        """
        try:
            conn = get_connection(self.database_path)
            cursor = conn.cursor()

            query = convert_placeholder("""
                SELECT id, email, subscription_type, free_until
                FROM users
                WHERE subscription_status = 'active'
                  AND subscription_type IN ('beta', 'paid')
                ORDER BY created_at DESC
                """)
            cursor.execute(query)

            rows = cursor.fetchall()
            conn.close()

            users = []
            for row in rows:
                # 兼容SQLite (tuple/Row) 和 PostgreSQL (dict)
                if isinstance(row, dict):
                    user_id = row['id']
                    email = row['email']
                    subscription_type = row['subscription_type']
                    free_until = row['free_until']
                else:
                    user_id = row[0]
                    email = row[1]
                    subscription_type = row[2]
                    free_until = row[3]

                # 检查免费期是否过期
                is_valid = True

                if free_until:
                    from dateutil import parser

                    free_until_dt = parser.parse(free_until)
                    if datetime.now(timezone.utc) > free_until_dt:
                        is_valid = False

                if is_valid:
                    users.append({
                        "id": user_id,
                        "email": email,
                        "subscription_type": subscription_type,
                    })

            return users

        except Exception as e:
            default_logger.error(
                f"查询活跃用户失败: {str(e)}",
                extra={"extra_fields": {"error": str(e)}},
            )
            return []


# 使用示例
if __name__ == "__main__":
    # 测试用例
    um = UserManager()

    # 1. 创建用户
    print("=== 测试1：创建用户 ===")
    result = um.create_user(
        email="test@example.com", subscription_type="beta", invite_code="BETA2025"
    )
    print(f"创建结果: {result}")
    print()

    # 2. 查询用户
    print("=== 测试2：查询用户 ===")
    user = um.get_user("test@example.com")
    print(f"用户信息: {user}")
    print()

    # 3. 记录访问日志
    print("=== 测试3：记录访问日志 ===")
    success = um.log_access(
        email="test@example.com",
        token="test-token-12345",
        access_result="success",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0",
    )
    print(f"日志记录: {'成功' if success else '失败'}")
    print()

    # 4. 查询访问日志
    print("=== 测试4：查询访问日志 ===")
    logs = um.get_access_logs("test@example.com")
    print(f"访问日志数量: {len(logs)}")
    if logs:
        print(f"最近一次访问: {logs[0]}")
    print()

    # 5. 获取所有活跃用户
    print("=== 测试5：获取活跃用户 ===")
    active_users = um.get_all_active_users()
    print(f"活跃用户数: {len(active_users)}")

    print("\n✅ 所有测试完成！")
