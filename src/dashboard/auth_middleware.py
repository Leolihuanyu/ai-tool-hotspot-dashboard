"""
Flask认证中间件
提供token验证和访问控制功能
"""

import os
from functools import wraps
from flask import request, jsonify, redirect, url_for
from src.auth.token_manager import TokenManager
from src.user.user_manager import UserManager
from src.utils.logger import get_logger

logger = get_logger(__name__)

# 初始化Token和User管理器
token_manager = TokenManager()
user_manager = UserManager()


def verify_token_from_request():
    """
    从请求中提取并验证token

    优先级：
    1. URL参数 ?token=xxx
    2. Cookie中的token
    3. Authorization header

    Returns:
        Dict: 验证结果
            {
                "valid": True/False,
                "email": "user@example.com",
                "subscription_type": "beta/paid",
                "error": "错误信息"
            }
    """
    token = None
    email = None

    # 1. 从URL参数获取token和email
    token = request.args.get('token')
    email = request.args.get('email')

    # 2. 从Cookie获取
    if not token:
        token = request.cookies.get('access_token')
        email = request.cookies.get('user_email')

    # 3. 从Authorization header获取
    if not token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

    # 如果没有token，返回验证失败
    if not token:
        return {
            "valid": False,
            "error": "未提供访问token"
        }

    # 验证token
    # 根据环境变量决定是否启用IP验证
    require_ip_match = os.getenv("TOKEN_REQUIRE_IP_MATCH", "false").lower() == "true"
    current_ip = request.remote_addr

    # 优先尝试数据库token验证（如果同时提供了token和email）
    # 这用于邮件链接中的长期token（90天有效期）
    if email:
        db_result = token_manager.verify_database_token(
            token=token,
            email=email,
            user_manager=user_manager
        )

        # 如果数据库token验证成功，直接返回结果
        if db_result.get("valid"):
            result = db_result
            logger.info(
                f"数据库token验证成功: {email}",
                extra={"extra_fields": {"email": email, "token_type": "database"}}
            )
        else:
            # 数据库token验证失败，尝试JWT验证（向后兼容）
            logger.debug(
                f"数据库token验证失败，尝试JWT验证: {email}",
                extra={"extra_fields": {"email": email, "error": db_result.get("error")}}
            )
            result = token_manager.verify_token(
                token=token,
                require_ip_match=require_ip_match,
                current_ip=current_ip
            )
    else:
        # 没有email参数，直接使用JWT验证
        result = token_manager.verify_token(
            token=token,
            require_ip_match=require_ip_match,
            current_ip=current_ip
        )

    # 如果token有效，检查用户账户是否过期
    if result.get("valid"):
        user_email = result.get("email")
        if user_email:
            user = user_manager.get_user(user_email)
            if user:
                # 检查账户是否过期
                free_until = user.get('free_until')
                subscription_type = user.get('subscription_type')

                # Beta用户需要检查free_until
                if subscription_type == 'beta' and free_until:
                    from datetime import datetime
                    from dateutil import parser

                    free_until_dt = parser.parse(free_until)
                    if datetime.now().astimezone() > free_until_dt:
                        # 账户已过期
                        result = {
                            "valid": False,
                            "error": "您的试用期已过期，请升级为付费订阅以继续使用",
                            "expired": True
                        }

    # 记录访问日志
    if result.get("valid"):
        # 成功访问
        access_result = "success"
        error_msg = None
    else:
        # 访问失败，确定失败类型
        error = result.get("error", "")
        if "过期" in error or "试用期" in error:
            access_result = "expired"
        elif "IP地址" in error or "转发" in error:
            access_result = "ip_mismatch"
        else:
            access_result = "invalid"
        error_msg = error

    # 记录访问日志（如果有email）
    log_email = result.get("email") or email
    if log_email:
        user_agent = request.headers.get('User-Agent', '')
        user_manager.log_access(
            email=log_email,
            token=token,
            access_result=access_result,
            ip_address=current_ip,
            user_agent=user_agent,
            error_message=error_msg
        )

    return result


def require_auth(f):
    """
    装饰器：要求用户认证才能访问

    用法：
        @app.route('/protected')
        @require_auth
        def protected_route():
            return "This is protected"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 验证token
        result = verify_token_from_request()

        if not result.get("valid"):
            # 验证失败，返回错误页面或JSON
            error_message = result.get("error", "访问被拒绝")

            # 判断是API请求还是页面请求
            if request.path.startswith('/api/'):
                # API请求，返回JSON
                return jsonify({
                    "success": False,
                    "error": error_message,
                    "code": "UNAUTHORIZED"
                }), 401
            else:
                # 页面请求，重定向到过期页面
                return redirect(url_for('access_expired', error=error_message))

        # 验证成功，将用户信息注入到请求上下文
        request.user_email = result.get("email")
        request.subscription_type = result.get("subscription_type")

        return f(*args, **kwargs)

    return decorated_function


def optional_auth(f):
    """
    装饰器：可选认证
    如果提供token则验证，不提供也可以访问（用于公开页面）

    用法：
        @app.route('/public')
        @optional_auth
        def public_route():
            # 可以通过 request.user_email 判断是否已认证
            return "This is public"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 尝试验证token
        result = verify_token_from_request()

        if result.get("valid"):
            # 如果token有效，注入用户信息
            request.user_email = result.get("email")
            request.subscription_type = result.get("subscription_type")
        else:
            # token无效或未提供，设置为匿名用户
            request.user_email = None
            request.subscription_type = None

        return f(*args, **kwargs)

    return decorated_function
