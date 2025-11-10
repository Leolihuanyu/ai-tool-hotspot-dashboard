"""
邮件模板管理器
负责加载多语言翻译文件并渲染HTML邮件模板

支持的语言：
- en: English
- ja: 日本語
- zh: 中文

支持的模板：
- invite_welcome: 邀请注册欢迎邮件
- subscription_welcome: 付费订阅欢迎邮件
"""

import json
import os
from pathlib import Path
from typing import Dict, Tuple, Optional
from src.utils.logger import default_logger


class EmailTemplateManager:
    """邮件模板管理器"""

    # 支持的语言列表
    SUPPORTED_LANGUAGES = ('en', 'ja', 'zh')

    # 支持的模板列表
    SUPPORTED_TEMPLATES = (
        'invite_welcome',
        'subscription_welcome',
        'expiry_reminder_14days',
        'expiry_reminder_7days',
        'expiry_reminder_1day'
    )

    def __init__(self, locales_dir: Optional[str] = None):
        """
        初始化邮件模板管理器

        Args:
            locales_dir: 翻译文件目录路径（默认为 src/email/locales/）
        """
        if locales_dir:
            self.locales_dir = Path(locales_dir)
        else:
            # 默认路径：src/email/locales/
            current_dir = Path(__file__).parent
            self.locales_dir = current_dir / 'locales'

    def _validate_language(self, language: str) -> str:
        """
        验证语言代码，返回有效的语言代码

        Args:
            language: 语言代码

        Returns:
            str: 有效的语言代码（如果无效则返回'en'）
        """
        if language not in self.SUPPORTED_LANGUAGES:
            default_logger.warning(
                f"不支持的语言: {language}，回退到英语",
                extra={"extra_fields": {"language": language}}
            )
            return 'en'
        return language

    def _validate_template(self, template_name: str) -> bool:
        """
        验证模板名称

        Args:
            template_name: 模板名称

        Returns:
            bool: 模板是否有效
        """
        if template_name not in self.SUPPORTED_TEMPLATES:
            default_logger.error(
                f"不支持的模板: {template_name}",
                extra={"extra_fields": {"template_name": template_name}}
            )
            return False
        return True

    def get_template_strings(self, template_name: str, language: str) -> Optional[Dict]:
        """
        获取指定语言的邮件翻译字符串

        Args:
            template_name: 模板名称（如 'invite_welcome'）
            language: 语言代码（'en', 'ja', 'zh'）

        Returns:
            Dict: 翻译字符串字典，如果失败返回None
        """
        # 验证参数
        if not self._validate_template(template_name):
            return None

        language = self._validate_language(language)

        # 构建翻译文件路径
        locale_file = self.locales_dir / language / f"{template_name}.json"

        if not locale_file.exists():
            default_logger.error(
                f"翻译文件不存在: {locale_file}",
                extra={"extra_fields": {
                    "template_name": template_name,
                    "language": language,
                    "file_path": str(locale_file)
                }}
            )
            return None

        try:
            with open(locale_file, 'r', encoding='utf-8') as f:
                translations = json.load(f)
                return translations

        except json.JSONDecodeError as e:
            default_logger.error(
                f"JSON解析失败: {str(e)}",
                extra={"extra_fields": {
                    "file_path": str(locale_file),
                    "error": str(e)
                }}
            )
            return None

        except Exception as e:
            default_logger.error(
                f"读取翻译文件失败: {str(e)}",
                extra={"extra_fields": {
                    "file_path": str(locale_file),
                    "error": str(e)
                }}
            )
            return None

    def render_email(
        self,
        template_name: str,
        language: str,
        **context
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        渲染邮件HTML和主题

        Args:
            template_name: 模板名称（'invite_welcome' 或 'subscription_welcome'）
            language: 语言代码（'en', 'ja', 'zh'）
            **context: 模板上下文变量
                - dashboard_url: Dashboard访问链接（必需）

        Returns:
            Tuple[subject, html_content]: 邮件主题和HTML内容
            如果失败返回 (None, None)
        """
        # 获取翻译字符串
        strings = self.get_template_strings(template_name, language)
        if not strings:
            return None, None

        # 验证必需的上下文变量
        dashboard_url = context.get('dashboard_url')
        if not dashboard_url:
            default_logger.error("缺少必需参数: dashboard_url")
            return None, None

        # 获取邮件主题
        subject = strings.get('subject', 'Welcome!')

        # 根据模板类型渲染HTML
        if template_name == 'invite_welcome':
            html_content = self._render_invite_welcome_html(strings, dashboard_url)
        elif template_name == 'subscription_welcome':
            html_content = self._render_subscription_welcome_html(strings, dashboard_url)
        else:
            default_logger.error(f"未实现的模板: {template_name}")
            return None, None

        return subject, html_content

    def _render_invite_welcome_html(self, strings: Dict, dashboard_url: str) -> str:
        """
        渲染邀请注册欢迎邮件HTML

        Args:
            strings: 翻译字符串字典
            dashboard_url: Dashboard访问链接

        Returns:
            str: HTML内容
        """
        # 渲染功能列表
        features_html = '\n'.join([
            f'                        <li>{feature}</li>'
            for feature in strings.get('features', [])
        ])

        # 渲染使用步骤
        usage_steps_html = '\n'.join([
            f'                        <li>{step}</li>'
            for step in strings.get('usage_steps', [])
        ])

        # 使用Dashboard风格的HTML模板（蓝紫渐变 + 玻璃态）
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    line-height: 1.6;
                    background: linear-gradient(to bottom right, #020617, #0f172a, #020617);
                    padding: 40px 20px;
                    color: #ffffff;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: rgba(255, 255, 255, 0.05);
                    backdrop-filter: blur(16px);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 12px;
                    overflow: hidden;
                    box-shadow: 0 20px 25px rgba(0, 0, 0, 0.3);
                }}
                .header {{
                    background: linear-gradient(to right, #0ea5e9, #d946ef);
                    padding: 40px 30px;
                    text-align: center;
                }}
                .header h1 {{
                    font-size: 28px;
                    font-weight: 700;
                    color: white;
                    margin: 0;
                }}
                .content {{
                    padding: 40px 30px;
                    background: rgba(255, 255, 255, 0.02);
                }}
                .content p {{
                    margin-bottom: 16px;
                    color: #ffffff;
                    font-size: 16px;
                }}
                .content h3 {{
                    font-size: 20px;
                    font-weight: 600;
                    margin: 30px 0 16px 0;
                    color: #ffffff;
                }}
                .content ul, .content ol {{
                    margin-left: 20px;
                    margin-bottom: 20px;
                }}
                .content li {{
                    margin-bottom: 10px;
                    color: #94a3b8;
                    font-size: 15px;
                }}
                .content strong {{
                    color: #60a5fa;
                }}
                .cta-container {{
                    text-align: center;
                    margin: 30px 0;
                }}
                .cta-button {{
                    display: inline-block;
                    background: linear-gradient(to right, #0ea5e9, #d946ef);
                    color: white;
                    padding: 16px 32px;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 16px;
                    box-shadow: 0 10px 15px rgba(0, 0, 0, 0.3);
                    transition: transform 0.2s;
                }}
                .cta-button:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 15px 20px rgba(0, 0, 0, 0.4);
                }}
                .footer {{
                    text-align: center;
                    padding: 30px;
                    background: rgba(255, 255, 255, 0.02);
                    border-top: 1px solid rgba(255, 255, 255, 0.05);
                    color: #64748b;
                    font-size: 13px;
                }}
                .footer p {{
                    margin: 8px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{strings.get('title', 'Welcome!')}</h1>
                </div>
                <div class="content">
                    <p>{strings.get('greeting', 'Hello,')}</p>
                    <p>{strings.get('intro_p1', '')}</p>
                    <p>{strings.get('intro_p2', '')}</p>

                    <h3>{strings.get('features_title', 'Features')}</h3>
                    <ul>
{features_html}
                    </ul>

                    <div class="cta-container">
                        <a href="{dashboard_url}" class="cta-button">
                            {strings.get('cta_button', 'Access Dashboard')}
                        </a>
                    </div>

                    <h3>{strings.get('usage_title', 'How to Use')}</h3>
                    <ol>
{usage_steps_html}
                    </ol>

                    <p style="margin-top: 30px; color: #94a3b8;">
                        {strings.get('feedback', '')}
                    </p>
                </div>
                <div class="footer">
                    <p>{strings.get('footer_copyright', '')}</p>
                    <p>{strings.get('footer_notice', '')}</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html_content

    def _render_subscription_welcome_html(self, strings: Dict, dashboard_url: str) -> str:
        """
        渲染付费订阅欢迎邮件HTML

        Args:
            strings: 翻译字符串字典
            dashboard_url: Dashboard访问链接

        Returns:
            str: HTML内容
        """
        # 渲染功能列表
        features_html = '\n'.join([
            f'                        <li>{feature}</li>'
            for feature in strings.get('features', [])
        ])

        # 使用Dashboard风格的HTML模板（蓝紫渐变 + 玻璃态）
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    line-height: 1.6;
                    background: linear-gradient(to bottom right, #020617, #0f172a, #020617);
                    padding: 40px 20px;
                    color: #ffffff;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: rgba(255, 255, 255, 0.05);
                    backdrop-filter: blur(16px);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 12px;
                    overflow: hidden;
                    box-shadow: 0 20px 25px rgba(0, 0, 0, 0.3);
                }}
                .header {{
                    background: linear-gradient(to right, #0ea5e9, #d946ef);
                    padding: 40px 30px;
                    text-align: center;
                }}
                .header h1 {{
                    font-size: 28px;
                    font-weight: 700;
                    color: white;
                    margin: 0;
                }}
                .content {{
                    padding: 40px 30px;
                    background: rgba(255, 255, 255, 0.02);
                }}
                .content p {{
                    margin-bottom: 16px;
                    color: #ffffff;
                    font-size: 16px;
                }}
                .content h3 {{
                    font-size: 20px;
                    font-weight: 600;
                    margin: 30px 0 16px 0;
                    color: #ffffff;
                }}
                .content ul {{
                    margin-left: 20px;
                    margin-bottom: 20px;
                }}
                .content li {{
                    margin-bottom: 10px;
                    color: #94a3b8;
                    font-size: 15px;
                }}
                .content strong {{
                    color: #60a5fa;
                }}
                .cta-container {{
                    text-align: center;
                    margin: 30px 0;
                }}
                .cta-button {{
                    display: inline-block;
                    background: linear-gradient(to right, #0ea5e9, #d946ef);
                    color: white;
                    padding: 16px 32px;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 16px;
                    box-shadow: 0 10px 15px rgba(0, 0, 0, 0.3);
                    transition: transform 0.2s;
                }}
                .cta-button:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 15px 20px rgba(0, 0, 0, 0.4);
                }}
                .footer {{
                    text-align: center;
                    padding: 30px;
                    background: rgba(255, 255, 255, 0.02);
                    border-top: 1px solid rgba(255, 255, 255, 0.05);
                    color: #64748b;
                    font-size: 13px;
                }}
                .footer p {{
                    margin: 8px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{strings.get('title', 'Welcome!')}</h1>
                </div>
                <div class="content">
                    <p>{strings.get('greeting', 'Hello,')}</p>
                    <p>{strings.get('intro_p1', '')}</p>
                    <p>{strings.get('intro_p2', '')}</p>

                    <h3>{strings.get('features_title', 'Features')}</h3>
                    <ul>
{features_html}
                    </ul>

                    <div class="cta-container">
                        <a href="{dashboard_url}" class="cta-button">
                            {strings.get('cta_button', 'Access Dashboard')}
                        </a>
                    </div>

                    <p style="margin-top: 30px; color: #94a3b8;">
                        {strings.get('access_notice', '')}
                    </p>

                    <p style="margin-top: 20px; color: #94a3b8;">
                        {strings.get('support', '')}
                    </p>
                </div>
                <div class="footer">
                    <p>{strings.get('footer_copyright', '')}</p>
                    <p>{strings.get('footer_thanks', '')}</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html_content


# 使用示例
if __name__ == '__main__':
    # 测试邮件模板管理器
    manager = EmailTemplateManager()

    # 测试中文邀请欢迎邮件
    print("=== 测试1：中文邀请欢迎邮件 ===")
    subject_zh, html_zh = manager.render_email(
        template_name='invite_welcome',
        language='zh',
        dashboard_url='https://example.com/dashboard?token=abc123'
    )
    print(f"主题: {subject_zh}")
    print(f"HTML长度: {len(html_zh) if html_zh else 0} 字符")
    print()

    # 测试英文订阅欢迎邮件
    print("=== 测试2：英文订阅欢迎邮件 ===")
    subject_en, html_en = manager.render_email(
        template_name='subscription_welcome',
        language='en',
        dashboard_url='https://example.com/dashboard?token=xyz789'
    )
    print(f"主题: {subject_en}")
    print(f"HTML长度: {len(html_en) if html_en else 0} 字符")
    print()

    # 测试日文邀请欢迎邮件
    print("=== 测试3：日文邀请欢迎邮件 ===")
    subject_ja, html_ja = manager.render_email(
        template_name='invite_welcome',
        language='ja',
        dashboard_url='https://example.com/dashboard?token=def456'
    )
    print(f"主题: {subject_ja}")
    print(f"HTML长度: {len(html_ja) if html_ja else 0} 字符")
    print()

    print("✅ 所有测试完成！")
