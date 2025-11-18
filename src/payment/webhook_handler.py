"""
Stripe Webhook事件处理器
处理订阅生命周期相关的webhook事件

支持的事件：
- checkout.session.completed - 支付成功
- customer.subscription.updated - 订阅更新
- customer.subscription.deleted - 订阅取消
- invoice.payment_failed - 支付失败
"""

import os
import stripe
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from src.user.user_manager import UserManager
from src.auth.token_manager import TokenManager
from src.email.sender import get_email_sender
from src.utils.logger import default_logger


class StripeWebhookHandler:
    """Stripe Webhook事件处理器"""

    def __init__(self):
        """初始化webhook处理器"""
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        if not self.webhook_secret:
            default_logger.warning("STRIPE_WEBHOOK_SECRET未配置，webhook签名验证将被跳过")

        self.user_manager = UserManager()
        self.token_manager = TokenManager()

        # 初始化邮件发送器（根据 EMAIL_PROVIDER 自动选择 SendGrid 或 SMTP）
        try:
            self.email_sender = get_email_sender()
            email_provider = os.getenv("EMAIL_PROVIDER", "smtp")
            default_logger.info(f"邮件发送器初始化成功 (provider: {email_provider})")
        except Exception as e:
            default_logger.exception(f"邮件发送器初始化失败: {str(e)}")
            self.email_sender = None

    def verify_signature(
        self,
        payload: bytes,
        signature: str
    ) -> Optional[stripe.Event]:
        """
        验证Webhook签名

        Args:
            payload: 请求体（字节）
            signature: Stripe-Signature头部值

        Returns:
            验证后的Event对象，验证失败返回None
        """
        if not self.webhook_secret:
            default_logger.warning("跳过webhook签名验证（未配置STRIPE_WEBHOOK_SECRET）")
            # 开发环境可以跳过验证，直接解析payload
            import json
            try:
                event_dict = json.loads(payload.decode('utf-8'))
                return stripe.Event.construct_from(event_dict, stripe.api_key)
            except Exception as e:
                default_logger.error(f"解析webhook payload失败: {str(e)}")
                return None

        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            default_logger.info(
                f"Webhook签名验证成功: {event.type}",
                extra={"extra_fields": {"event_id": event.id}}
            )
            return event

        except ValueError as e:
            default_logger.error(f"无效的webhook payload: {str(e)}")
            return None
        except stripe.error.SignatureVerificationError as e:
            default_logger.error(f"Webhook签名验证失败: {str(e)}")
            return None

    def handle_event(self, event: stripe.Event) -> Dict[str, Any]:
        """
        处理Stripe事件

        Args:
            event: Stripe Event对象

        Returns:
            Dict: 处理结果
                {
                    "success": True/False,
                    "message": "处理成功"
                }
        """
        event_type = event.type
        event_data = event.data.object

        default_logger.info(
            f"处理Stripe事件: {event_type}",
            extra={"extra_fields": {"event_id": event.id, "event_type": event_type}}
        )

        # 根据事件类型分发处理
        handlers = {
            "checkout.session.completed": self._handle_checkout_completed,
            "customer.subscription.updated": self._handle_subscription_updated,
            "customer.subscription.deleted": self._handle_subscription_deleted,
            "invoice.payment_failed": self._handle_payment_failed,
        }

        handler = handlers.get(event_type)
        if handler:
            return handler(event_data)
        else:
            default_logger.info(f"未处理的事件类型: {event_type}")
            return {
                "success": True,
                "message": f"事件类型 {event_type} 已接收但未处理"
            }

    def _handle_checkout_completed(self, session: stripe.checkout.Session) -> Dict[str, Any]:
        """
        处理支付成功事件

        Args:
            session: Checkout Session对象

        Returns:
            Dict: 处理结果
        """
        try:
            customer_id = session.customer
            customer_email = session.customer_details.email if session.customer_details else session.get("metadata", {}).get("email")
            subscription_id = session.subscription

            if not customer_email:
                # 尝试从Stripe Customer获取邮箱
                customer = stripe.Customer.retrieve(customer_id)
                customer_email = customer.email

            if not customer_email:
                default_logger.error("无法获取用户邮箱")
                return {"success": False, "message": "无法获取用户邮箱"}

            # 从 session metadata 获取语言和时区，并进行智能推断
            metadata = session.get("metadata", {})
            language = metadata.get("language")
            timezone = metadata.get("timezone")

            # 智能推断language和timezone
            from src.utils.locale_helper import (
                infer_language_from_timezone,
                infer_timezone_from_language,
                is_timezone_language_compatible
            )

            # 情况1: 都未提供，使用默认值（优先中国时区）
            if not language and not timezone:
                language = 'en'
                timezone = 'Asia/Shanghai'  # 修改：默认使用中国时区而非UTC
            # 情况2: 只提供了timezone，根据timezone推断language
            elif timezone and not language:
                language = infer_language_from_timezone(timezone)
                default_logger.info(f"根据timezone {timezone} 推断language为 {language}")
            # 情况3: 只提供了language，根据language推断timezone
            elif language and not timezone:
                timezone = infer_timezone_from_language(language)
                default_logger.info(f"根据language {language} 推断timezone为 {timezone}")
            # 情况4: 都提供了，检查兼容性
            else:
                if not is_timezone_language_compatible(timezone, language):
                    suggested_language = infer_language_from_timezone(timezone)
                    default_logger.warning(
                        f"时区和语言可能不匹配: timezone={timezone}, language={language}, "
                        f"建议language={suggested_language}",
                        extra={"extra_fields": {
                            "email": customer_email,
                            "timezone": timezone,
                            "language": language,
                            "suggested_language": suggested_language
                        }}
                    )

            # 更新用户订阅状态
            user = self.user_manager.get_user(customer_email)
            if not user:
                default_logger.warning(f"用户不存在，创建新用户: {customer_email}")
                # 创建新用户（付费订阅）
                result = self.user_manager.create_user(
                    email=customer_email,
                    subscription_type="paid",
                    language=language,
                    timezone=timezone
                )
                if not result.get("success"):
                    return {"success": False, "message": "创建用户失败"}

            # 更新订阅信息
            self.user_manager.update_user(
                email=customer_email,
                subscription_type="paid",
                subscription_status="active",
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id
            )

            default_logger.info(
                f"订阅激活成功: {customer_email}",
                extra={"extra_fields": {
                    "email": customer_email,
                    "subscription_id": subscription_id
                }}
            )

            # 发送欢迎邮件
            self._send_subscription_welcome_email(customer_email)

            # 处理推荐奖励（如果有推荐人）
            if user and user.get("referrer_id"):
                self._process_referral_reward(user["referrer_id"])

            return {
                "success": True,
                "message": f"订阅激活成功: {customer_email}"
            }

        except Exception as e:
            default_logger.error(
                f"处理checkout.session.completed失败: {str(e)}",
                extra={"extra_fields": {"error": str(e)}}
            )
            return {"success": False, "message": str(e)}

    def _handle_subscription_updated(self, subscription: stripe.Subscription) -> Dict[str, Any]:
        """
        处理订阅更新事件

        Args:
            subscription: Subscription对象

        Returns:
            Dict: 处理结果
        """
        try:
            customer_id = subscription.customer
            subscription_id = subscription.id
            status = subscription.status

            # 获取客户邮箱
            customer = stripe.Customer.retrieve(customer_id)
            customer_email = customer.email

            if not customer_email:
                return {"success": False, "message": "无法获取用户邮箱"}

            # 更新订阅状态
            # Stripe订阅状态: active, past_due, unpaid, canceled, incomplete, incomplete_expired, trialing
            # 映射到我们的状态: active, cancelled, expired
            if status in ["active", "trialing"]:
                db_status = "active"
            elif status in ["canceled"]:
                db_status = "cancelled"
            elif status in ["past_due", "unpaid"]:
                db_status = "active"  # 保持active，但可以发送警告邮件
            else:
                db_status = "expired"

            self.user_manager.update_user(
                email=customer_email,
                subscription_status=db_status
            )

            default_logger.info(
                f"订阅更新: {customer_email} -> {status}",
                extra={"extra_fields": {
                    "email": customer_email,
                    "subscription_id": subscription_id,
                    "status": status
                }}
            )

            # 如果订阅状态异常，发送通知邮件
            if status in ["past_due", "unpaid"]:
                self._send_payment_issue_email(customer_email, status)

            return {
                "success": True,
                "message": f"订阅状态更新: {status}"
            }

        except Exception as e:
            default_logger.error(
                f"处理customer.subscription.updated失败: {str(e)}",
                extra={"extra_fields": {"error": str(e)}}
            )
            return {"success": False, "message": str(e)}

    def _handle_subscription_deleted(self, subscription: stripe.Subscription) -> Dict[str, Any]:
        """
        处理订阅取消/删除事件

        Args:
            subscription: Subscription对象

        Returns:
            Dict: 处理结果
        """
        try:
            customer_id = subscription.customer
            subscription_id = subscription.id

            # 获取客户邮箱
            customer = stripe.Customer.retrieve(customer_id)
            customer_email = customer.email

            if not customer_email:
                return {"success": False, "message": "无法获取用户邮箱"}

            # 更新订阅状态为cancelled
            self.user_manager.update_user(
                email=customer_email,
                subscription_status="cancelled"
            )

            # 清空用户的访问token（撤销访问权限）
            token_cleared = self.user_manager.clear_access_token(customer_email)
            if token_cleared:
                default_logger.info(
                    f"用户访问token已清空: {customer_email}",
                    extra={"extra_fields": {
                        "email": customer_email,
                        "subscription_id": subscription_id
                    }}
                )
            else:
                default_logger.warning(
                    f"清空用户访问token失败: {customer_email}",
                    extra={"extra_fields": {
                        "email": customer_email,
                        "subscription_id": subscription_id
                    }}
                )

            default_logger.info(
                f"订阅已取消: {customer_email}",
                extra={"extra_fields": {
                    "email": customer_email,
                    "subscription_id": subscription_id,
                    "token_cleared": token_cleared
                }}
            )

            # 发送取消确认邮件
            self._send_subscription_cancelled_email(customer_email)

            return {
                "success": True,
                "message": f"订阅已取消: {customer_email}"
            }

        except Exception as e:
            default_logger.error(
                f"处理customer.subscription.deleted失败: {str(e)}",
                extra={"extra_fields": {"error": str(e)}}
            )
            return {"success": False, "message": str(e)}

    def _handle_payment_failed(self, invoice: stripe.Invoice) -> Dict[str, Any]:
        """
        处理支付失败事件

        Args:
            invoice: Invoice对象

        Returns:
            Dict: 处理结果
        """
        try:
            customer_id = invoice.customer
            subscription_id = invoice.subscription

            # 获取客户邮箱
            customer = stripe.Customer.retrieve(customer_id)
            customer_email = customer.email

            if not customer_email:
                return {"success": False, "message": "无法获取用户邮箱"}

            default_logger.warning(
                f"支付失败: {customer_email}",
                extra={"extra_fields": {
                    "email": customer_email,
                    "subscription_id": subscription_id,
                    "invoice_id": invoice.id
                }}
            )

            # 发送支付失败通知邮件
            self._send_payment_failed_email(customer_email)

            return {
                "success": True,
                "message": f"支付失败通知已发送: {customer_email}"
            }

        except Exception as e:
            default_logger.error(
                f"处理invoice.payment_failed失败: {str(e)}",
                extra={"extra_fields": {"error": str(e)}}
            )
            return {"success": False, "message": str(e)}

    def _process_referral_reward(self, referrer_id: int):
        """
        处理推荐奖励
        付费订阅成功后，给推荐人延长7天免费期

        Args:
            referrer_id: 推荐人用户ID
        """
        try:
            from src.user.referral_manager import ReferralManager
            referral_manager = ReferralManager()

            # 这里应该通过referral_manager来处理奖励
            # 但由于我们在webhook中只有referrer_id，需要关联到具体的推荐记录
            # 简化处理：直接通过数据库操作延长免费期

            default_logger.info(f"处理推荐奖励: referrer_id={referrer_id}")
            # 实际实现需要与ReferralManager集成

        except Exception as e:
            default_logger.error(f"处理推荐奖励失败: {str(e)}")

    # === 邮件发送方法 ===

    def _send_subscription_welcome_email(self, email: str):
        """发送多语言订阅欢迎邮件（带Dashboard访问链接）"""
        if not self.email_sender:
            default_logger.error(
                f"无法发送欢迎邮件: 邮件发送器未初始化 (收件人: {email})",
                extra={"extra_fields": {"email": email, "reason": "email_sender_not_initialized"}}
            )
            return

        try:
            # 从数据库查询用户信息
            user = self.user_manager.get_user(email)
            language = user.get('language', 'en') if user else 'en'
            subscription_type = user.get('subscription_type', 'paid') if user else 'paid'

            # 从数据库读取已保存的access_token（如果有）
            db_access_token = user.get("access_token") if user else None
            token_expires_at = user.get("token_expires_at") if user else None

            # 检查数据库中的token是否有效（未过期）
            token_is_valid = False
            if db_access_token and token_expires_at:
                from dateutil import parser
                try:
                    expires_dt = parser.parse(token_expires_at)
                    if datetime.now(timezone.utc) < expires_dt:
                        # 数据库中的token仍然有效，直接使用
                        long_term_token = db_access_token
                        token_is_valid = True
                        default_logger.info(
                            f"使用数据库中已有的access_token: {email}",
                            extra={"extra_fields": {"email": email, "expires_at": token_expires_at}}
                        )
                except Exception as e:
                    default_logger.warning(f"解析token过期时间失败: {e}")

            # 如果数据库中没有有效token，生成新的
            if not token_is_valid:
                long_term_token = self.token_manager.generate_long_term_token(expiry_days=90)
                token_saved = self.user_manager.update_access_token(
                    email=email,
                    access_token=long_term_token,
                    expiry_days=90
                )

                if token_saved:
                    default_logger.info(
                        f"长期访问token已生成并保存: {email}",
                        extra={"extra_fields": {"email": email, "expiry_days": 90}}
                    )
                else:
                    default_logger.error(
                        f"保存访问token失败: {email}",
                        extra={"extra_fields": {"email": email}}
                    )
                    raise Exception("无法保存访问token，请稍后重试")

            # 优先使用 DASHBOARD_BASE_URL（前端地址），向后兼容 DASHBOARD_URL
            dashboard_base_url = os.getenv('DASHBOARD_BASE_URL') or os.getenv('DASHBOARD_URL', 'https://ai-tool-hotspot-dashboard.vercel.app')
            dashboard_url = f"{dashboard_base_url}/dashboard?token={long_term_token}&email={email}"

            # 使用EmailTemplateManager渲染多语言邮件
            from src.email.template_manager import EmailTemplateManager
            template_manager = EmailTemplateManager()
            subject, html_content = template_manager.render_email(
                template_name='subscription_welcome',
                language=language,
                dashboard_url=dashboard_url
            )

            if not subject or not html_content:
                raise Exception("邮件模板渲染失败")


            self.email_sender.send_html_email(
                to_emails=[email],
                subject=subject,
                html_content=html_content
            )

            default_logger.info(f"订阅欢迎邮件已发送至: {email} (语言: {language})")

        except Exception as e:
            default_logger.exception(
                f"发送欢迎邮件失败: {str(e)}",
                extra={"extra_fields": {"email": email, "error": str(e)}}
            )

    def _send_subscription_cancelled_email(self, email: str):
        """发送订阅取消确认邮件（多语言支持）"""
        if not self.email_sender:
            default_logger.error(
                f"无法发送取消确认邮件: 邮件发送器未初始化 (收件人: {email})",
                extra={"extra_fields": {"email": email, "reason": "email_sender_not_initialized"}}
            )
            return

        try:
            # 从数据库获取用户语言偏好
            user = self.user_manager.get_user(email)
            language = user.get('language', 'en') if user else 'en'

            # 使用 EmailTemplateManager 渲染多语言邮件
            from src.email.template_manager import EmailTemplateManager
            template_manager = EmailTemplateManager()
            subject, html_content = template_manager.render_email(
                template_name='subscription_cancelled',
                language=language
            )

            self.email_sender.send_html_email(
                to_emails=[email],
                subject=subject,
                html_content=html_content
            )
            default_logger.info(f"订阅取消确认邮件已发送至: {email} (语言: {language})")

        except Exception as e:
            default_logger.exception(
                f"发送取消确认邮件失败: {str(e)}",
                extra={"extra_fields": {"email": email, "error": str(e)}}
            )

    def _send_payment_failed_email(self, email: str):
        """发送支付失败通知邮件（多语言支持）"""
        if not self.email_sender:
            default_logger.error(
                f"无法发送支付失败通知邮件: 邮件发送器未初始化 (收件人: {email})",
                extra={"extra_fields": {"email": email, "reason": "email_sender_not_initialized"}}
            )
            return

        try:
            # 从数据库获取用户语言偏好
            user = self.user_manager.get_user(email)
            language = user.get('language', 'en') if user else 'en'

            # 使用 EmailTemplateManager 渲染多语言邮件
            from src.email.template_manager import EmailTemplateManager
            template_manager = EmailTemplateManager()
            subject, html_content = template_manager.render_email(
                template_name='payment_failed',
                language=language
            )

            self.email_sender.send_html_email(
                to_emails=[email],
                subject=subject,
                html_content=html_content
            )
            default_logger.info(f"支付失败通知邮件已发送至: {email} (语言: {language})")

        except Exception as e:
            default_logger.exception(
                f"发送支付失败邮件失败: {str(e)}",
                extra={"extra_fields": {"email": email, "error": str(e)}}
            )

    def _send_payment_issue_email(self, email: str, status: str):
        """发送支付问题警告邮件（多语言支持）"""
        if not self.email_sender:
            default_logger.error(
                f"无法发送支付问题警告邮件: 邮件发送器未初始化 (收件人: {email})",
                extra={"extra_fields": {"email": email, "status": status, "reason": "email_sender_not_initialized"}}
            )
            return

        try:
            # 从数据库获取用户语言偏好
            user = self.user_manager.get_user(email)
            language = user.get('language', 'en') if user else 'en'

            # 使用 EmailTemplateManager 渲染多语言邮件
            from src.email.template_manager import EmailTemplateManager
            template_manager = EmailTemplateManager()
            subject, html_content = template_manager.render_email(
                template_name='payment_issue',
                language=language
            )

            self.email_sender.send_html_email(
                to_emails=[email],
                subject=subject,
                html_content=html_content
            )
            default_logger.info(f"支付问题警告邮件已发送至: {email} (状态: {status}, 语言: {language})")

        except Exception as e:
            default_logger.exception(
                f"发送支付问题邮件失败: {str(e)}",
                extra={"extra_fields": {"email": email, "status": status, "error": str(e)}}
            )
