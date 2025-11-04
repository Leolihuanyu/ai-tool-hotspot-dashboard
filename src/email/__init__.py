"""邮件服务模块

提供邮件发送和内容生成功能,用于每日机会报告。
支持SMTP和SendGrid两种发送方式。
"""

from src.email.sender import EmailSender, email_sender, get_email_sender
from src.email.smtp_sender import SMTPEmailSender, smtp_sender
from src.email.generator import EmailContentGenerator, email_generator

__all__ = [
    "EmailSender",
    "email_sender",
    "SMTPEmailSender",
    "smtp_sender",
    "get_email_sender",
    "EmailContentGenerator",
    "email_generator",
]
