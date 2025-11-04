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

        if not self.smtp_server:
            logger.warning("SMTP_SERVER未配置，邮件功能将不可用")
        if not self.smtp_username:
            logger.warning("SMTP_USERNAME未配置，邮件功能将不可用")
        if not self.smtp_password:
            logger.warning("SMTP_PASSWORD未配置，邮件功能将不可用")

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

        to_list = config.email_to_list
        if not to_list:
            missing.append("EMAIL_TO_LIST")

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
            logger.error(f"SMTP认证失败: {e}")
            raise Exception(f"SMTP认证失败，请检查用户名和密码（Gmail需要使用应用专用密码）: {e}")
        except smtplib.SMTPException as e:
            logger.error(f"SMTP发送失败: {e}")
            raise Exception(f"SMTP发送失败: {e}")
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
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
            html_content = """
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2 style="color: #4CAF50;">✅ SMTP配置成功！</h2>
                    <p>恭喜！你的SMTP邮件服务已配置成功。</p>
                    <p><strong>配置信息：</strong></p>
                    <ul>
                        <li>SMTP服务器: {server}</li>
                        <li>端口: {port}</li>
                        <li>加密: {'STARTTLS' if self.smtp_use_tls else 'SSL'}</li>
                    </ul>
                    <p>现在可以正常发送每日报告邮件了！</p>
                    <hr>
                    <p style="color: #888; font-size: 12px;">
                        由AI工具热点仪表板自动发送
                    </p>
                </body>
            </html>
            """.format(
                server=self.smtp_server,
                port=self.smtp_port,
                self=self
            )

            plain_content = f"""
            ✅ SMTP配置成功！

            恭喜！你的SMTP邮件服务已配置成功。

            配置信息：
            - SMTP服务器: {self.smtp_server}
            - 端口: {self.smtp_port}
            - 加密: {'STARTTLS' if self.smtp_use_tls else 'SSL'}

            现在可以正常发送每日报告邮件了！

            ---
            由AI工具热点仪表板自动发送
            """

            self.send_html_email([to_email], subject, html_content, plain_content)
            return True

        except Exception as e:
            logger.error(f"测试邮件发送失败: {e}")
            return False


# 创建全局实例
smtp_sender = SMTPEmailSender()
