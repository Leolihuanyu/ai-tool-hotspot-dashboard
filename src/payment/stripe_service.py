"""
Stripe支付服务
处理订阅创建、管理和状态查询

功能：
- 创建Stripe Customer
- 创建Checkout Session（月付/年付）
- 查询订阅状态
- 取消订阅
- 创建客户门户会话
"""

import os
import stripe
from typing import Optional, Dict, Any
from src.user.user_manager import UserManager
from src.utils.logger import default_logger


class StripeService:
    """Stripe支付服务类"""

    def __init__(self):
        """
        初始化Stripe服务
        从环境变量读取Stripe配置
        """
        # Stripe API密钥
        self.secret_key = os.getenv("STRIPE_SECRET_KEY")
        if not self.secret_key:
            raise ValueError("缺少环境变量: STRIPE_SECRET_KEY")

        stripe.api_key = self.secret_key

        # 价格ID
        self.price_id_monthly = os.getenv("STRIPE_PRICE_ID_MONTHLY")
        self.price_id_yearly = os.getenv("STRIPE_PRICE_ID_YEARLY")

        if not self.price_id_monthly or not self.price_id_yearly:
            default_logger.warning(
                "Stripe价格ID未配置，请设置STRIPE_PRICE_ID_MONTHLY和STRIPE_PRICE_ID_YEARLY"
            )

        # Dashboard基础URL（用于回调）
        self.dashboard_base_url = os.getenv("DASHBOARD_BASE_URL", "http://localhost:5000")

        # 用户管理器
        self.user_manager = UserManager()

    def create_or_get_customer(
        self,
        email: str,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        创建或获取Stripe Customer

        Args:
            email: 用户邮箱
            user_id: 用户ID（可选，用于metadata）

        Returns:
            Dict: 包含customer_id和是否新创建的信息
                {
                    "customer_id": "cus_xxx",
                    "is_new": True/False
                }
        """
        try:
            # 检查用户是否已有Stripe Customer ID
            user = self.user_manager.get_user(email)
            if user and user.get("stripe_customer_id"):
                default_logger.info(
                    f"用户已有Stripe Customer ID: {user['stripe_customer_id']}",
                    extra={"extra_fields": {"email": email}}
                )
                return {
                    "customer_id": user["stripe_customer_id"],
                    "is_new": False
                }

            # 创建新的Stripe Customer
            metadata = {"email": email}
            if user_id:
                metadata["user_id"] = str(user_id)

            customer = stripe.Customer.create(
                email=email,
                metadata=metadata,
                description=f"AI工具热点Dashboard用户 - {email}"
            )

            customer_id = customer.id

            # 保存到数据库
            if user:
                self.user_manager.update_user(
                    email=email,
                    stripe_customer_id=customer_id
                )

            default_logger.info(
                f"创建Stripe Customer成功: {customer_id}",
                extra={"extra_fields": {"email": email, "customer_id": customer_id}}
            )

            return {
                "customer_id": customer_id,
                "is_new": True
            }

        except Exception as e:
            default_logger.error(
                f"创建Stripe Customer失败: {str(e)}",
                extra={"extra_fields": {"email": email, "error": str(e)}}
            )
            raise

    def create_checkout_session(
        self,
        email: Optional[str] = None,
        price_type: str = "monthly",
        plan: Optional[str] = None,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
        language: str = "zh",
        timezone: str = "UTC"
    ) -> Dict[str, Any]:
        """
        创建Stripe Checkout Session

        Args:
            email: 用户邮箱（可选，用于预填充或关联已有Customer）
            price_type: 价格类型（monthly/yearly）
            plan: plan别名，与price_type相同（为了兼容性）
            success_url: 支付成功后的跳转URL
            cancel_url: 支付取消后的跳转URL
            language: 用户语言偏好（zh/en/ja）
            timezone: 用户时区（如 Asia/Shanghai）

        Returns:
            Dict: Checkout session信息
                {
                    "session_id": "cs_xxx",
                    "url": "https://checkout.stripe.com/xxx"
                }

        注意：
        - 如果提供email且用户已存在，会关联到现有Customer
        - 如果提供email但用户不存在，会创建新Customer并预填充email
        - 如果不提供email，Stripe Checkout会自动收集email
        """
        try:
            # plan 参数与 price_type 兼容（优先使用 plan）
            if plan:
                price_type = plan

            # 选择价格ID
            if price_type == "yearly":
                price_id = self.price_id_yearly
            else:
                price_id = self.price_id_monthly

            if not price_id:
                raise ValueError(f"未配置{price_type}订阅的价格ID")

            # 获取或创建Customer（如果提供了email）
            customer_id = None
            if email:
                customer_result = self.create_or_get_customer(email)
                customer_id = customer_result["customer_id"]

            # 设置回调URL
            if not success_url:
                success_url = f"{self.dashboard_base_url}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}"
            if not cancel_url:
                cancel_url = f"{self.dashboard_base_url}/checkout/cancelled"

            # 构建Session参数
            session_params = {
                "payment_method_types": ["card"],
                "line_items": [
                    {
                        "price": price_id,
                        "quantity": 1,
                    }
                ],
                "mode": "subscription",
                "success_url": success_url,
                "cancel_url": cancel_url,
                "metadata": {
                    "price_type": price_type,
                    "language": language,
                    "timezone": timezone
                },
                # 自动应用促销码
                "allow_promotion_codes": True,
                # 收集账单地址
                "billing_address_collection": "auto",
            }

            # 如果有Customer ID，关联到Session
            if customer_id:
                session_params["customer"] = customer_id
                session_params["metadata"]["email"] = email
            # 如果没有Customer ID但有email，预填充email
            elif email:
                session_params["customer_email"] = email
                session_params["metadata"]["email"] = email

            # 创建Checkout Session
            session = stripe.checkout.Session.create(**session_params)

            default_logger.info(
                f"创建Checkout Session成功: {session.id}",
                extra={"extra_fields": {
                    "email": email,
                    "session_id": session.id,
                    "price_type": price_type
                }}
            )

            return {
                "session_id": session.id,
                "url": session.url
            }

        except Exception as e:
            default_logger.error(
                f"创建Checkout Session失败: {str(e)}",
                extra={"extra_fields": {"email": email, "error": str(e)}}
            )
            raise

    def get_subscription_status(
        self,
        subscription_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        查询订阅状态

        Args:
            subscription_id: Stripe订阅ID

        Returns:
            Dict: 订阅详情
                {
                    "id": "sub_xxx",
                    "status": "active",
                    "current_period_end": 1234567890,
                    "cancel_at_period_end": False,
                    "price_id": "price_xxx"
                }
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)

            return {
                "id": subscription.id,
                "status": subscription.status,
                "current_period_end": subscription.current_period_end,
                "current_period_start": subscription.current_period_start,
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "price_id": subscription["items"]["data"][0]["price"]["id"] if subscription.get("items") else None,
                "customer_id": subscription.customer
            }

        except Exception as e:
            default_logger.error(
                f"查询订阅状态失败: {str(e)}",
                extra={"extra_fields": {"subscription_id": subscription_id, "error": str(e)}}
            )
            return None

    def cancel_subscription(
        self,
        subscription_id: str,
        immediately: bool = False
    ) -> Dict[str, Any]:
        """
        取消订阅

        Args:
            subscription_id: Stripe订阅ID
            immediately: 是否立即取消（True）还是在周期结束时取消（False）

        Returns:
            Dict: 取消结果
                {
                    "success": True/False,
                    "message": "订阅将在周期结束时取消",
                    "cancel_at": 1234567890
                }
        """
        try:
            if immediately:
                # 立即取消
                subscription = stripe.Subscription.cancel(subscription_id)
                message = "订阅已立即取消"
            else:
                # 在周期结束时取消
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
                message = "订阅将在当前周期结束时取消"

            default_logger.info(
                f"取消订阅成功: {subscription_id}",
                extra={"extra_fields": {
                    "subscription_id": subscription_id,
                    "immediately": immediately
                }}
            )

            return {
                "success": True,
                "message": message,
                "cancel_at": subscription.current_period_end if not immediately else None
            }

        except Exception as e:
            default_logger.error(
                f"取消订阅失败: {str(e)}",
                extra={"extra_fields": {"subscription_id": subscription_id, "error": str(e)}}
            )
            return {
                "success": False,
                "message": f"取消订阅失败: {str(e)}"
            }

    def create_portal_session(
        self,
        customer_id: str,
        return_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建Stripe客户门户会话
        用户可以在门户中管理订阅、查看发票、更新支付方式等

        Args:
            customer_id: Stripe Customer ID
            return_url: 返回URL（用户从门户返回时跳转的页面）

        Returns:
            Dict: 门户会话信息
                {
                    "url": "https://billing.stripe.com/xxx"
                }
        """
        try:
            if not return_url:
                return_url = f"{self.dashboard_base_url}/account"

            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )

            default_logger.info(
                f"创建客户门户会话成功: {customer_id}",
                extra={"extra_fields": {"customer_id": customer_id}}
            )

            return {
                "url": session.url
            }

        except Exception as e:
            default_logger.error(
                f"创建客户门户会话失败: {str(e)}",
                extra={"extra_fields": {"customer_id": customer_id, "error": str(e)}}
            )
            raise

    def get_customer_subscriptions(
        self,
        customer_id: str
    ) -> list:
        """
        获取客户的所有订阅

        Args:
            customer_id: Stripe Customer ID

        Returns:
            List[Dict]: 订阅列表
        """
        try:
            subscriptions = stripe.Subscription.list(
                customer=customer_id,
                limit=10
            )

            return [
                {
                    "id": sub.id,
                    "status": sub.status,
                    "current_period_end": sub.current_period_end,
                    "cancel_at_period_end": sub.cancel_at_period_end
                }
                for sub in subscriptions.data
            ]

        except Exception as e:
            default_logger.error(
                f"获取客户订阅失败: {str(e)}",
                extra={"extra_fields": {"customer_id": customer_id, "error": str(e)}}
            )
            return []
