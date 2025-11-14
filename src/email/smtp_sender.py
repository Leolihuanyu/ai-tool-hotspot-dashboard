"""SMTP邮件发送服务

使用标准SMTP协议发送邮件，支持Gmail、QQ、163、iCloud等邮箱。
遵循宪法原则I(数据可靠性 - 重试逻辑)。
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
import ssl

from src.utils.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SMTPEmailSender:
    """SMTP邮件发送器

    支持Gmail、QQ、163、iCloud等所有SMTP服务器。
    """

    # 常用SMTP服务器配置预设
    SMTP_PRESETS = {
        'gmail': {
            'server': 'smtp.gmail.com',
            'port': 587,
            'use_tls': True
        },
        'qq': {
            'server': 'smtp.qq.com',
            'port': 587,
            'use_tls': True
        },
        '163': {
            'server': 'smtp.163.com',
            'port': 465,
            'use_tls': False  # 使用SSL
        },
        'icloud': {
            'server': 'smtp.mail.me.com',
            'port': 587,
            'use_tls': True
        }
    }

    def __init__(self):
        """初始化SMTP客户端"""
        self.smtp_server = config.smtp_server
        self.smtp_port = config.smtp_port
        self.smtp_username = config.smtp_username
        self.smtp_password = config.smtp_password
        self.smtp_use_tls = config.smtp_use_tls
        self.from_email = config.email_from

        # 验证配置完整性
        is_valid, missing = self.validate_config()
        if not is_valid:
            logger.error(
                f"SMTP配置不完整，缺少以下环境变量: {', '.join(missing)}",
                extra={"extra_fields": {"missing_vars": missing}}
            )
        else:
            logger.info(
                f"SMTP客户端初始化成功: {self.smtp_server}:{self.smtp_port}",
                extra={"extra_fields": {
                    "smtp_server": self.smtp_server,
                    "smtp_port": self.smtp_port,
                    "use_tls": self.smtp_use_tls
                }}
            )

    def validate_config(self) -> tuple[bool, List[str]]:
        """验证SMTP配置

        Returns:
            (是否通过验证, 缺失的配置项列表)
        """
        missing = []

        if not self.smtp_server:
            missing.append("SMTP_SERVER")
        if not self.smtp_port:
            missing.append("SMTP_PORT")
        if not self.smtp_username:
            missing.append("SMTP_USERNAME")
        if not self.smtp_password:
            missing.append("SMTP_PASSWORD")
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
    def _send_with_retry(self, msg: MIMEMultipart, recipients: List[str]) -> Dict[str, Any]:
        """带重试逻辑的SMTP发送

        Args:
            msg: MIME邮件对象
            recipients: 收件人列表

        Returns:
            发送结果字典

        Raises:
            Exception: SMTP发送失败
        """
        try:
            # 创建SSL上下文
            context = ssl.create_default_context()

            # 根据配置选择连接方式
            if self.smtp_use_tls:
                # 使用STARTTLS（587端口）
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30)
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
            else:
                # 使用SSL（465端口）
                server = smtplib.SMTP_SSL(
                    self.smtp_server,
                    self.smtp_port,
                    context=context,
                    timeout=30
                )

            # 登录
            server.login(self.smtp_username, self.smtp_password)

            # 发送邮件
            server.send_message(msg)

            # 关闭连接
            server.quit()

            logger.info(f"SMTP邮件发送成功: {recipients}")

            return {
                'status': 'success',
                'recipients': recipients,
                'message': 'Email sent successfully via SMTP'
            }

        except smtplib.SMTPAuthenticationError as e:
            logger.exception(
                f"SMTP认证失败: {e}",
                extra={"extra_fields": {
                    "smtp_server": self.smtp_server,
                    "smtp_username": self.smtp_username,
                    "error_type": "authentication_error"
                }}
            )
            raise Exception(f"SMTP认证失败，请检查用户名和密码（Gmail需要使用应用专用密码）: {e}")
        except smtplib.SMTPException as e:
            logger.exception(
                f"SMTP发送失败: {e}",
                extra={"extra_fields": {
                    "smtp_server": self.smtp_server,
                    "recipients": recipients,
                    "error_type": "smtp_error"
                }}
            )
            raise Exception(f"SMTP发送失败: {e}")
        except Exception as e:
            logger.exception(
                f"邮件发送失败: {e}",
                extra={"extra_fields": {
                    "smtp_server": self.smtp_server,
                    "recipients": recipients,
                    "error_type": "unknown_error"
                }}
            )
            raise

    def send_html_email(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        plain_content: Optional[str] = None,
        plain_text_content: Optional[str] = None  # 兼容SendGrid接口
    ) -> Dict[str, Any]:
        """发送HTML邮件

        Args:
            to_emails: 收件人列表
            subject: 邮件主题
            html_content: HTML邮件内容
            plain_content: 纯文本内容（可选，用于不支持HTML的客户端）
            plain_text_content: 纯文本内容（兼容SendGrid接口）

        Returns:
            发送结果字典
        """
        start_time = datetime.now()

        # 兼容两种参数名
        if plain_text_content is not None:
            plain_content = plain_text_content

        try:
            # 创建MIME消息
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)

            # 添加纯文本部分（如果提供）
            if plain_content:
                part1 = MIMEText(plain_content, 'plain', 'utf-8')
                msg.attach(part1)

            # 添加HTML部分
            part2 = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part2)

            # 发送邮件（带重试）
            result = self._send_with_retry(msg, to_emails)

            # 计算发送耗时
            duration = (datetime.now() - start_time).total_seconds()

            # 记录成功日志
            logger.info(
                "SMTP邮件发送成功",
                extra={"extra_fields": {
                    'event': 'email_sent',
                    'status': 'success',
                    'recipients': to_emails,
                    'subject': subject,
                    'duration_seconds': duration,
                    'smtp_server': self.smtp_server,
                    'timestamp': start_time.isoformat()
                }}
            )

            return {
                'success': True,
                'status': 'success',
                'status_code': 250,  # SMTP成功状态码
                'recipients': to_emails,
                'subject': subject,
                'duration': duration,
                'timestamp': start_time.isoformat()
            }

        except Exception as e:
            # 计算失败耗时
            duration = (datetime.now() - start_time).total_seconds()

            # 记录失败日志
            logger.error(
                {
                    'event': 'email_sent',
                    'status': 'failed',
                    'error': str(e),
                    'recipients': to_emails,
                    'subject': subject,
                    'duration_seconds': duration,
                    'smtp_server': self.smtp_server,
                    'timestamp': start_time.isoformat()
                }
            )

            raise

    def send_test_email(self, to_email: str) -> bool:
        """发送测试邮件

        Args:
            to_email: 测试收件人

        Returns:
            是否发送成功
        """
        try:
            subject = "🧪 SMTP测试邮件 - AI工具热点仪表板"
            encryption_type = 'STARTTLS' if self.smtp_use_tls else 'SSL'
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2 style="color: #4CAF50;">✅ SMTP配置成功！</h2>
                    <p>恭喜！你的SMTP邮件服务已配置成功。</p>
                    <p><strong>配置信息：</strong></p>
                    <ul>
                        <li>SMTP服务器: {self.smtp_server}</li>
                        <li>端口: {self.smtp_port}</li>
                        <li>加密: {encryption_type}</li>
                    </ul>
                    <p>现在可以正常发送每日报告邮件了！</p>
                    <hr>
                    <p style="color: #888; font-size: 12px;">
                        由AI工具热点仪表板自动发送
                    </p>
                </body>
            </html>
            """

            plain_content = f"""
            ✅ SMTP配置成功！

            恭喜！你的SMTP邮件服务已配置成功。

            配置信息：
            - SMTP服务器: {self.smtp_server}
            - 端口: {self.smtp_port}
            - 加密: {encryption_type}

            现在可以正常发送每日报告邮件了！

            ---
            由AI工具热点仪表板自动发送
            """

            self.send_html_email([to_email], subject, html_content, plain_content)
            return True

        except Exception as e:
            logger.error(f"测试邮件发送失败: {e}")
            return False


# 全局实例缓存（懒加载模式）
# 注意：不再在模块导入时自动创建实例，避免不必要的初始化
# 使用 get_email_sender() 工厂函数获取实例，或使用 get_smtp_sender() 直接获取SMTP实例
_smtp_sender_instance = None


def get_smtp_sender():
    """获取SMTP邮件发送器实例（懒加载，单例模式）"""
    global _smtp_sender_instance
    if _smtp_sender_instance is None:
        _smtp_sender_instance = SMTPEmailSender()
    return _smtp_sender_instance


# 向后兼容：模块级别的smtp_sender变量
# 注意：标记为None，建议使用get_email_sender()或get_smtp_sender()代替
smtp_sender = None
