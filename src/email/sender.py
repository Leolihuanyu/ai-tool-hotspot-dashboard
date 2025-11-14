"""邮件发送服务

支持SendGrid API和SMTP两种发送方式,遵循宪法原则I(数据可靠性 - 重试逻辑)。
"""

import os
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

from src.utils.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class EmailSender:
    """邮件发送器"""

    def __init__(self):
        """初始化SendGrid客户端"""
        self.api_key = config.sendgrid_api_key
        self.from_email = config.email_from

        if not self.api_key:
            logger.warning("SENDGRID_API_KEY未配置,邮件功能将不可用")
        if not self.from_email:
            logger.warning("EMAIL_FROM未配置,邮件功能将不可用")

        self.client = SendGridAPIClient(self.api_key) if self.api_key else None

    def validate_config(self) -> tuple[bool, List[str]]:
        """验证邮件配置

        Returns:
            (是否通过验证, 缺失的配置项列表)
        """
        missing = []

        if not self.api_key:
            missing.append("SENDGRID_API_KEY")
        if not self.from_email:
            missing.append("EMAIL_FROM")

        # EMAIL_TO_LIST 只在批量发送时需要，不在此强制要求
        # 单个邮件发送时会通过 to_emails 参数指定收件人

        return len(missing) == 0, missing

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def _send_with_retry(self, message: Mail) -> Dict[str, Any]:
        """带重试的邮件发送

        Args:
            message: SendGrid Mail对象

        Returns:
            发送响应

        Raises:
            Exception: 发送失败
        """
        if not self.client:
            raise ValueError("SendGrid客户端未初始化,请检查SENDGRID_API_KEY配置")

        try:
            response = self.client.send(message)
            return {
                "status_code": response.status_code,
                "body": response.body,
                "headers": dict(response.headers)
            }
        except Exception as e:
            logger.error(f"邮件发送失败: {str(e)}")
            raise

    def send_html_email(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        plain_text_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """发送HTML邮件

        Args:
            to_emails: 收件人邮箱列表
            subject: 邮件主题
            html_content: HTML内容
            plain_text_content: 纯文本内容(可选,用于不支持HTML的邮件客户端)

        Returns:
            发送结果 {
                "success": bool,
                "status_code": int,
                "message": str,
                "timestamp": str,
                "recipients": List[str],
                "errors": List[str]
            }
        """
        start_time = datetime.now()

        # 验证配置
        is_valid, missing = self.validate_config()
        if not is_valid:
            error_msg = f"邮件配置缺失: {', '.join(missing)}"
            logger.error(error_msg)
            return {
                "success": False,
                "status_code": 0,
                "message": error_msg,
                "timestamp": start_time.isoformat(),
                "recipients": to_emails,
                "errors": [error_msg]
            }

        try:
            # 创建邮件
            message = Mail(
                from_email=Email(self.from_email),
                to_emails=[To(email) for email in to_emails],
                subject=subject,
                html_content=Content("text/html", html_content)
            )

            # 添加纯文本备选内容
            if plain_text_content:
                message.add_content(Content("text/plain", plain_text_content))

            # 发送邮件(带重试)
            response = self._send_with_retry(message)

            # 计算耗时
            duration = (datetime.now() - start_time).total_seconds()

            # 记录成功日志
            logger.info({
                "event": "email_sent",
                "status": "success",
                "status_code": response["status_code"],
                "recipients": to_emails,
                "subject": subject,
                "duration_seconds": duration,
                "timestamp": start_time.isoformat()
            })

            return {
                "success": True,
                "status_code": response["status_code"],
                "message": "邮件发送成功",
                "timestamp": start_time.isoformat(),
                "recipients": to_emails,
                "errors": []
            }

        except Exception as e:
            # 计算耗时
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)

            # 记录失败日志
            logger.error({
                "event": "email_sent",
                "status": "failed",
                "error": error_msg,
                "recipients": to_emails,
                "subject": subject,
                "duration_seconds": duration,
                "timestamp": start_time.isoformat()
            })

            return {
                "success": False,
                "status_code": 0,
                "message": f"邮件发送失败: {error_msg}",
                "timestamp": start_time.isoformat(),
                "recipients": to_emails,
                "errors": [error_msg]
            }

    def send_failure_alert(
        self,
        admin_email: str,
        failure_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """发送失败告警邮件给管理员

        Args:
            admin_email: 管理员邮箱
            failure_details: 失败详情

        Returns:
            发送结果
        """
        subject = "⚠️ AI工具热点仪表板 - 邮件发送失败告警"

        html_content = f"""
        <html>
        <body>
            <h2>邮件发送失败告警</h2>
            <p><strong>时间:</strong> {failure_details.get('timestamp', 'N/A')}</p>
            <p><strong>收件人:</strong> {', '.join(failure_details.get('recipients', []))}</p>
            <p><strong>主题:</strong> {failure_details.get('subject', 'N/A')}</p>
            <p><strong>错误信息:</strong></p>
            <pre>{chr(10).join(failure_details.get('errors', []))}</pre>
            <p><strong>重试次数:</strong> 已尝试3次</p>
            <hr>
            <p><em>此邮件由AI工具热点仪表板系统自动发送</em></p>
        </body>
        </html>
        """

        plain_text = f"""
        邮件发送失败告警

        时间: {failure_details.get('timestamp', 'N/A')}
        收件人: {', '.join(failure_details.get('recipients', []))}
        主题: {failure_details.get('subject', 'N/A')}
        错误信息:
        {chr(10).join(failure_details.get('errors', []))}
        重试次数: 已尝试3次

        此邮件由AI工具热点仪表板系统自动发送
        """

        return self.send_html_email(
            to_emails=[admin_email],
            subject=subject,
            html_content=html_content,
            plain_text_content=plain_text
        )


# 全局实例缓存（懒加载，避免模块导入时的副作用）
_email_sender_cache = None


def get_email_sender() -> Union['EmailSender', 'SMTPEmailSender']:
    """根据配置获取邮件发送器（懒加载，单例模式）

    根据 EMAIL_PROVIDER 环境变量自动选择：
    - "sendgrid": 使用SendGrid邮件发送器（HTTP API）
    - "smtp": 使用SMTP邮件发送器（Gmail等）
    - 其他: 默认使用SMTP

    Returns:
        EmailSender或SMTPEmailSender实例
    """
    global _email_sender_cache

    provider = config.email_provider.lower()

    if provider == "smtp":
        # 使用SMTP发送器（懒加载）
        from src.email.smtp_sender import get_smtp_sender
        logger.info("使用SMTP邮件发送器")
        return get_smtp_sender()
    elif provider == "sendgrid":
        # 使用SendGrid发送器（懒加载）
        if _email_sender_cache is None:
            _email_sender_cache = EmailSender()
        logger.info("使用SendGrid邮件发送器")
        return _email_sender_cache
    else:
        logger.warning(f"未知的邮件提供商: {provider}，使用默认SMTP")
        from src.email.smtp_sender import get_smtp_sender
        return get_smtp_sender()


# 为了向后兼容，提供获取默认SendGrid发送器的函数
# 注意：不再在模块加载时自动创建实例，避免不必要的初始化
def get_sendgrid_sender():
    """获取SendGrid邮件发送器实例（懒加载）"""
    global _email_sender_cache
    if _email_sender_cache is None:
        _email_sender_cache = EmailSender()
    return _email_sender_cache

# 向后兼容：模块级别的email_sender变量
# 注意：此变量在首次访问时才会初始化，而非模块导入时
email_sender = None  # 标记为None，使用get_email_sender()或get_sendgrid_sender()代替
