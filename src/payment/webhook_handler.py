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

            # 从 session metadata 获取语言和时区
            metadata = session.get("metadata", {})
            language = metadata.get("language", "zh")
            timezone = metadata.get("timezone", "UTC")

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

            default_logger.info(
                f"订阅已取消: {customer_email}",
                extra={"extra_fields": {
                    "email": customer_email,
                    "subscription_id": subscription_id
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
            # 从数据库查询用户语言偏好
            user = self.user_manager.get_user(email)
            language = user.get('language', 'zh') if user else 'zh'

            # 生成带token的Dashboard访问链接
            token = self.token_manager.generate_token(email)
            # 优先使用 DASHBOARD_BASE_URL（前端地址），向后兼容 DASHBOARD_URL
            dashboard_base_url = os.getenv('DASHBOARD_BASE_URL') or os.getenv('DASHBOARD_URL', 'https://ai-tool-hotspot-dashboard.vercel.app')
            dashboard_url = f"{dashboard_base_url}?token={token}"

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
        """发送订阅取消确认邮件"""
        if not self.email_sender:
            default_logger.error(
                f"无法发送取消确认邮件: 邮件发送器未初始化 (收件人: {email})",
                extra={"extra_fields": {"email": email, "reason": "email_sender_not_initialized"}}
            )
            return

        try:
            subject = "订阅已取消 - AI工具热点Dashboard"
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2>订阅已取消</h2>
                <p>您好，</p>
                <p>您的AI工具热点Dashboard订阅已被取消。</p>
                <p>我们很遗憾看到您离开。如果您有任何反馈或建议，欢迎随时告诉我们。</p>
                <p>如果您改变主意，随时欢迎重新订阅！</p>

                <p style="margin-top: 30px;">
                    祝好！<br>
                    AI工具热点Dashboard团队
                </p>
            </body>
            </html>
            """

            self.email_sender.send_html_email(
                to_emails=[email],
                subject=subject,
                html_content=html_content
            )
            default_logger.info(f"订阅取消确认邮件已发送至: {email}")

        except Exception as e:
            default_logger.exception(
                f"发送取消确认邮件失败: {str(e)}",
                extra={"extra_fields": {"email": email, "error": str(e)}}
            )

    def _send_payment_failed_email(self, email: str):
        """发送支付失败通知邮件"""
        if not self.email_sender:
            default_logger.error(
                f"无法发送支付失败通知邮件: 邮件发送器未初始化 (收件人: {email})",
                extra={"extra_fields": {"email": email, "reason": "email_sender_not_initialized"}}
            )
            return

        try:
            subject = "⚠️ 支付失败 - AI工具热点Dashboard"
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2 style="color: #DC2626;">支付失败通知</h2>
                <p>您好，</p>
                <p>您的AI工具热点Dashboard订阅续费失败。</p>

                <h3>可能的原因：</h3>
                <ul>
                    <li>信用卡余额不足</li>
                    <li>信用卡已过期</li>
                    <li>支付信息需要更新</li>
                </ul>

                <p>请尽快更新您的支付信息以继续享受服务。</p>
                <p>您可以在账户设置中管理您的支付方式。</p>

                <p style="margin-top: 30px;">
                    如有疑问请联系我们。<br>
                    AI工具热点Dashboard团队
                </p>
            </body>
            </html>
            """

            self.email_sender.send_html_email(
                to_emails=[email],
                subject=subject,
                html_content=html_content
            )
            default_logger.info(f"支付失败通知邮件已发送至: {email}")

        except Exception as e:
            default_logger.exception(
                f"发送支付失败邮件失败: {str(e)}",
                extra={"extra_fields": {"email": email, "error": str(e)}}
            )

    def _send_payment_issue_email(self, email: str, status: str):
        """发送支付问题警告邮件"""
        if not self.email_sender:
            default_logger.error(
                f"无法发送支付问题警告邮件: 邮件发送器未初始化 (收件人: {email})",
                extra={"extra_fields": {"email": email, "status": status, "reason": "email_sender_not_initialized"}}
            )
            return

        try:
            subject = "⚠️ 订阅状态异常 - AI工具热点Dashboard"
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2 style="color: #F59E0B;">订阅状态异常</h2>
                <p>您好，</p>
                <p>您的AI工具热点Dashboard订阅状态为: <strong>{status}</strong></p>
                <p>这可能会影响您的服务访问。请检查您的支付信息。</p>

                <p style="margin-top: 30px;">
                    如有疑问请联系我们。<br>
                    AI工具热点Dashboard团队
                </p>
            </body>
            </html>
            """

            self.email_sender.send_html_email(
                to_emails=[email],
                subject=subject,
                html_content=html_content
            )
            default_logger.info(f"支付问题警告邮件已发送至: {email} (状态: {status})")

        except Exception as e:
            default_logger.exception(
                f"发送支付问题邮件失败: {str(e)}",
                extra={"extra_fields": {"email": email, "status": status, "error": str(e)}}
            )
