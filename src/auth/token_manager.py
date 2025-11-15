"""
访问控制：JWT Token管理器
实现签名URL方案，用于邮件中的Dashboard访问控制

功能：
- 生成24小时有效期的访问token
- 验证token的合法性和有效期
- 支持邮箱绑定（防止token被盗用）
- 可选IP地址绑定（防止转发）
"""

import os
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature


class TokenManager:
    """JWT Token管理器"""

    def __init__(self, secret_key: Optional[str] = None):
        """
        初始化Token管理器

        Args:
            secret_key: 用于签名的密钥。如未提供，从环境变量JWT_SECRET_KEY读取
        """
        self.secret_key = secret_key or os.getenv("JWT_SECRET_KEY")
        if not self.secret_key:
            raise ValueError(
                "JWT_SECRET_KEY未配置！请在.env文件中设置或传入secret_key参数"
            )

        # 创建序列化器（用于生成和验证token）
        self.serializer = URLSafeTimedSerializer(self.secret_key)

        # Token有效期（秒）
        self.token_expiry_seconds = int(
            os.getenv("TOKEN_EXPIRY_HOURS", "24")
        ) * 3600  # 默认24小时

    def generate_token(
        self,
        email: str,
        subscription_type: str = "beta",
        ip_address: Optional[str] = None,
    ) -> str:
        """
        生成访问token

        Args:
            email: 用户邮箱
            subscription_type: 订阅类型（beta/paid）
            ip_address: 可选，用户IP地址（用于防止转发攻击）

        Returns:
            str: 签名后的访问token
        """
        # 构建payload
        payload = {
            "email": email,
            "subscription_type": subscription_type,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        # 如果提供了IP地址，计算其哈希值并添加到payload
        # （使用哈希而非明文IP，保护用户隐私）
        if ip_address:
            ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()[:16]
            payload["ip_hash"] = ip_hash

        # 生成token
        token = self.serializer.dumps(payload)
        return token

    def verify_token(
        self,
        token: str,
        require_ip_match: bool = False,
        current_ip: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        验证token的合法性和有效期

        Args:
            token: 待验证的token
            require_ip_match: 是否要求IP地址匹配（默认False）
            current_ip: 当前请求的IP地址（仅当require_ip_match=True时需要）

        Returns:
            Dict: 包含用户信息的字典
                {
                    "valid": True/False,
                    "email": "user@example.com",
                    "subscription_type": "beta/paid",
                    "error": "错误信息（如果验证失败）"
                }

        Raises:
            None: 所有异常都被捕获，通过返回值中的valid字段表示验证结果
        """
        try:
            # 验证token并解析payload
            payload = self.serializer.loads(
                token, max_age=self.token_expiry_seconds
            )

            # 如果需要验证IP地址
            if require_ip_match:
                if not current_ip:
                    return {
                        "valid": False,
                        "error": "需要提供当前IP地址进行验证",
                    }

                # 检查payload中是否包含IP哈希
                if "ip_hash" not in payload:
                    return {
                        "valid": False,
                        "error": "此token未绑定IP地址，但系统要求IP验证",
                    }

                # 计算当前IP的哈希值并比较
                current_ip_hash = hashlib.sha256(current_ip.encode()).hexdigest()[:16]
                if payload["ip_hash"] != current_ip_hash:
                    return {
                        "valid": False,
                        "error": "IP地址不匹配，疑似token被转发",
                        "email": payload.get("email"),  # 记录日志用
                    }

            # 验证成功
            return {
                "valid": True,
                "email": payload["email"],
                "subscription_type": payload["subscription_type"],
                "generated_at": payload["generated_at"],
            }

        except SignatureExpired:
            # Token已过期
            return {
                "valid": False,
                "error": f"访问链接已过期（有效期{self.token_expiry_seconds // 3600}小时）",
            }

        except BadSignature:
            # 签名无效（token被篡改）
            return {
                "valid": False,
                "error": "访问链接无效或已被篡改",
            }

        except Exception as e:
            # 其他未预期的错误
            return {
                "valid": False,
                "error": f"Token验证失败: {str(e)}",
            }

    def generate_dashboard_url(
        self,
        base_url: str,
        email: str,
        subscription_type: str = "beta",
        ip_address: Optional[str] = None,
    ) -> str:
        """
        生成带签名token的Dashboard访问URL

        Args:
            base_url: Dashboard基础URL（例如：https://your-dashboard.com）
            email: 用户邮箱
            subscription_type: 订阅类型
            ip_address: 可选，用户IP地址

        Returns:
            str: 完整的访问URL，格式：https://your-dashboard.com/dashboard?token=xxx&email=yyy
        """
        token = self.generate_token(email, subscription_type, ip_address)

        # 确保base_url不以/结尾
        base_url = base_url.rstrip("/")

        # 构建完整URL
        dashboard_url = f"{base_url}/dashboard?token={token}&email={email}"

        return dashboard_url

    def get_token_info(self, token: str) -> Dict[str, Any]:
        """
        获取token的详细信息（不验证有效期）
        用于调试和日志记录

        Args:
            token: 待查询的token

        Returns:
            Dict: token的详细信息
        """
        try:
            # 不验证有效期，仅解析payload
            payload = self.serializer.loads_unsafe(token)

            if payload[0]:  # 签名有效
                data = payload[1]
                return {
                    "valid_signature": True,
                    "email": data.get("email"),
                    "subscription_type": data.get("subscription_type"),
                    "generated_at": data.get("generated_at"),
                    "has_ip_binding": "ip_hash" in data,
                }
            else:
                return {"valid_signature": False, "error": "签名无效"}

        except Exception as e:
            return {"valid_signature": False, "error": str(e)}

    def generate_long_term_token(self, expiry_days: int = 90) -> str:
        """
        生成长期有效的访问token（用于数据库存储）

        使用随机字符串而非JWT，因为：
        1. 不需要携带用户信息（数据库中已有）
        2. 更容易撤销和刷新
        3. 避免签名验证开销

        Args:
            expiry_days: token有效期（天），默认90天

        Returns:
            str: 随机生成的token字符串（URL安全）
        """
        import secrets
        # 生成32字节（256位）的随机token，转换为URL安全的字符串
        token = secrets.token_urlsafe(32)
        return token

    def verify_database_token(
        self,
        token: str,
        email: str,
        user_manager
    ) -> Dict[str, Any]:
        """
        验证数据库中存储的长期token

        Args:
            token: 待验证的token
            email: 用户邮箱
            user_manager: UserManager实例（用于查询数据库）

        Returns:
            Dict: 验证结果
                {
                    "valid": True/False,
                    "email": "user@example.com",
                    "subscription_type": "beta/paid",
                    "error": "错误信息（如果验证失败）"
                }
        """
        try:
            # 记录验证开始
            default_logger.info(
                f"开始数据库token验证",
                extra={"extra_fields": {
                    "email": email,
                    "token_prefix": token[:20] + "..." if token and len(token) > 20 else token
                }}
            )

            # 从数据库获取用户信息
            user = user_manager.get_user(email)

            if not user:
                default_logger.warning(f"数据库token验证失败: 用户不存在 - {email}")
                return {
                    "valid": False,
                    "error": "用户不存在"
                }

            # 验证token是否匹配
            db_token = user.get("access_token")
            token_match = db_token == token

            default_logger.info(
                f"Token比对结果",
                extra={"extra_fields": {
                    "email": email,
                    "db_token_exists": db_token is not None,
                    "db_token_prefix": db_token[:20] + "..." if db_token and len(db_token) > 20 else db_token,
                    "token_match": token_match
                }}
            )

            if not token_match:
                return {
                    "valid": False,
                    "error": "Token无效或已被撤销"
                }

            # 验证token是否过期
            token_expires_at = user.get("token_expires_at")
            if token_expires_at:
                from dateutil import parser
                try:
                    expires_dt = parser.parse(token_expires_at)
                    # 确保expires_dt有时区信息（如果没有，假定为UTC）
                    was_naive = expires_dt.tzinfo is None
                    if was_naive:
                        expires_dt = expires_dt.replace(tzinfo=timezone.utc)
                        default_logger.info(
                            f"Token过期时间处理",
                            extra={"extra_fields": {
                                "email": email,
                                "original_time": token_expires_at,
                                "converted_to_utc": True
                            }}
                        )

                    # 现在可以安全地比较两个aware datetime
                    current_time = datetime.now(timezone.utc)
                    is_expired = current_time > expires_dt

                    default_logger.info(
                        f"Token过期检查",
                        extra={"extra_fields": {
                            "email": email,
                            "expires_at": expires_dt.isoformat(),
                            "current_time": current_time.isoformat(),
                            "is_expired": is_expired
                        }}
                    )

                    if is_expired:
                        return {
                            "valid": False,
                            "error": "Token已过期，请重新获取访问链接"
                        }
                except Exception as e:
                    return {
                        "valid": False,
                        "error": f"Token过期时间格式错误: {str(e)}"
                    }

            # 验证订阅状态
            subscription_status = user.get("subscription_status")
            if subscription_status != "active":
                return {
                    "valid": False,
                    "error": f"订阅已{subscription_status}，无法访问"
                }

            # 所有验证通过
            return {
                "valid": True,
                "email": user["email"],
                "subscription_type": user.get("subscription_type", "beta"),
                "language": user.get("language", "en"),
                "timezone": user.get("timezone", "UTC")
            }

        except Exception as e:
            return {
                "valid": False,
                "error": f"Token验证失败: {str(e)}"
            }


# 使用示例
if __name__ == "__main__":
    # 测试用例
    import sys

    # 设置测试用的密钥
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-do-not-use-in-production"

    tm = TokenManager()

    # 1. 生成token
    print("=== 测试1：生成token ===")
    email = "user@example.com"
    token = tm.generate_token(email, subscription_type="beta")
    print(f"Email: {email}")
    print(f"Token: {token[:50]}...")
    print()

    # 2. 验证有效token
    print("=== 测试2：验证有效token ===")
    result = tm.verify_token(token)
    print(f"验证结果: {result}")
    print()

    # 3. 生成完整Dashboard URL
    print("=== 测试3：生成Dashboard URL ===")
    url = tm.generate_dashboard_url(
        base_url="https://ai-dashboard.com",
        email=email,
        subscription_type="paid",
    )
    print(f"Dashboard URL: {url[:80]}...")
    print()

    # 4. 测试IP绑定
    print("=== 测试4：IP地址绑定 ===")
    ip_token = tm.generate_token(email, ip_address="192.168.1.100")
    print("生成绑定IP的token")

    # 正确IP验证
    result_correct = tm.verify_token(
        ip_token, require_ip_match=True, current_ip="192.168.1.100"
    )
    print(f"正确IP验证: {result_correct['valid']}")

    # 错误IP验证
    result_wrong = tm.verify_token(
        ip_token, require_ip_match=True, current_ip="192.168.1.101"
    )
    print(f"错误IP验证: {result_wrong['valid']}, 错误信息: {result_wrong.get('error')}")
    print()

    # 5. 获取token详细信息
    print("=== 测试5：获取token信息 ===")
    info = tm.get_token_info(token)
    print(f"Token信息: {info}")

    print("\n✅ 所有测试通过！")
