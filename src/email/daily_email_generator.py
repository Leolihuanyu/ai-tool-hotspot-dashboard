"""每日邮件个性化生成器

为每个订阅者生成包含个人访问token的个性化邮件。
"""

import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, Tuple
from pathlib import Path
from src.email.generator import EmailContentGenerator
from src.user.user_manager import UserManager
from src.auth.token_manager import TokenManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DailyEmailGenerator:
    """每日邮件个性化生成器"""

    def __init__(
        self,
        template_path: str = "src/email/templates/daily_report.html",
        data_path: str = "data/latest.json"
    ):
        """初始化个性化邮件生成器

        Args:
            template_path: HTML模板文件路径
            data_path: 数据文件路径(latest.json)
        """
        self.base_generator = EmailContentGenerator(template_path, data_path)
        self.user_manager = UserManager()
        self.token_manager = TokenManager()
        self.locales_dir = Path(__file__).parent / "locales"

    def _load_translations(self, language: str) -> Dict[str, Any]:
        """加载指定语言的翻译文件

        Args:
            language: 语言代码 (en/zh/ja)

        Returns:
            Dict: 翻译文本字典
        """
        try:
            locale_file = self.locales_dir / language / "daily_report.json"
            if not locale_file.exists():
                logger.warning(
                    f"翻译文件不存在，使用英文: {locale_file}",
                    extra={"extra_fields": {"language": language}}
                )
                locale_file = self.locales_dir / "en" / "daily_report.json"

            with open(locale_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(
                f"加载翻译文件失败: {str(e)}",
                extra={"extra_fields": {"language": language, "error": str(e)}}
            )
            # 返回默认英文翻译
            return {
                "subject": "🚀 Daily AI Tool Opportunity Report {date} | Top 10 Opportunities",
                "title": "🚀 Daily AI Tool Opportunity Report",
                "subtitle": "Report Date: {date}",
                "stats_labels": {
                    "ai_tools": "AI Tools",
                    "trending_topics": "Trending Topics",
                    "pain_points": "Pain Points",
                    "top_opportunities": "Top Opportunities"
                },
                "sections": {
                    "top_opportunities_title": "📊 Top 10 Product Opportunities"
                },
                "opportunity_card": {
                    "mvp_title": "🎯 MVP Suggestion",
                    "related_tools_label": "🔧 Related AI Tools:",
                    "related_topics_label": "📈 Related Trends:",
                    "view_details_button": "View Dashboard"
                },
                "footer": {
                    "generation_time": "📅 Report Generated: {time}",
                    "data_sources": "📊 Data Sources: Futurepedia, ProductHunt, There's an AI for That, Reddit, X, Google Trends",
                    "powered_by": "🤖 Powered by AI Tool Hotspot Dashboard",
                    "automated_notice": "This email is automatically sent by the AI Tool Hotspot Dashboard system",
                    "unsubscribe": "To unsubscribe from this email, please contact the administrator"
                }
            }

    def generate_personalized_email(
        self,
        email: str,
        dashboard_base_url: str = None
    ) -> Tuple[str, str, str]:
        """为单个订阅者生成个性化邮件

        Args:
            email: 订阅者邮箱
            dashboard_base_url: Dashboard基础URL（如未提供则从环境变量读取）

        Returns:
            Tuple[str, str, str]: (subject, html_content, plain_text_content)

        Raises:
            Exception: 邮件生成失败
        """
        try:
            # 从数据库获取用户信息
            user = self.user_manager.get_user(email)
            if not user:
                raise Exception(f"用户不存在: {email}")

            # 获取用户的长期token和订阅类型
            access_token = user.get("access_token")
            token_expires_at = user.get("token_expires_at")
            subscription_type = user.get("subscription_type", "beta")  # 默认为beta

            # 检查token是否需要刷新（不存在 或 已过期 或 即将过期）
            should_refresh = False
            token_expired = False

            if not access_token:
                should_refresh = True
                logger.warning(
                    f"用户没有访问token，生成新token: {email}",
                    extra={"extra_fields": {"email": email, "subscription_type": subscription_type}}
                )
            elif token_expires_at:
                # 检查token是否已过期或即将过期（提前7天刷新）
                from dateutil import parser
                from datetime import datetime, timedelta, timezone
                try:
                    # 处理不同数据库返回的数据类型
                    if isinstance(token_expires_at, str):
                        # SQLite返回字符串，需要解析
                        expires_dt = parser.parse(token_expires_at)
                    else:
                        # PostgreSQL返回datetime对象，直接使用
                        expires_dt = token_expires_at

                    # 确保有时区信息
                    if expires_dt.tzinfo is None:
                        expires_dt = expires_dt.replace(tzinfo=timezone.utc)

                    now_dt = datetime.now(timezone.utc)
                    refresh_threshold = now_dt + timedelta(days=7)

                    # 检查token是否已经过期
                    if expires_dt < now_dt:
                        token_expired = True
                        should_refresh = True
                        logger.warning(
                            f"Token已过期: {email} (订阅类型: {subscription_type})",
                            extra={"extra_fields": {
                                "email": email,
                                "subscription_type": subscription_type,
                                "expires_at": str(token_expires_at)
                            }}
                        )
                    # 检查token是否即将过期（7天内）
                    elif expires_dt < refresh_threshold:
                        should_refresh = True
                        logger.info(
                            f"Token即将过期: {email} (订阅类型: {subscription_type})",
                            extra={"extra_fields": {
                                "email": email,
                                "subscription_type": subscription_type,
                                "expires_at": str(token_expires_at),
                                "days_until_expiry": (expires_dt - now_dt).days
                            }}
                        )
                except Exception as e:
                    logger.error(
                        f"解析token过期时间失败: {e}",
                        extra={"extra_fields": {
                            "email": email,
                            "token_expires_at": str(token_expires_at),
                            "type": type(token_expires_at).__name__,
                            "error": str(e)
                        }}
                    )
                    # 不要因为解析失败就刷新token！
                    # 只有真的没有token或确实过期时才刷新
                    should_refresh = False  # 修复：解析失败不应该触发刷新

            # 根据订阅类型决定是否刷新token
            if should_refresh:
                if subscription_type == "paid":
                    # 订阅用户：刷新token
                    access_token = self.token_manager.generate_long_term_token(expiry_days=90)
                    # 保存到数据库
                    self.user_manager.update_access_token(
                        email=email,
                        access_token=access_token,
                        expiry_days=90
                    )
                    logger.info(
                        f"订阅用户token已刷新: {email}",
                        extra={"extra_fields": {
                            "email": email,
                            "subscription_type": subscription_type,
                            "new_token_prefix": access_token[:10] + "..." if access_token else None
                        }}
                    )
                elif subscription_type == "beta":
                    # Beta用户：不刷新，让token自然过期
                    if token_expired:
                        # Token已经过期，抛出异常阻止邮件发送
                        error_msg = f"Beta用户访问权限已过期: {email}"
                        logger.warning(
                            error_msg,
                            extra={"extra_fields": {
                                "email": email,
                                "subscription_type": subscription_type,
                                "token_expires_at": token_expires_at
                            }}
                        )
                        raise Exception(error_msg)
                    else:
                        # Token即将过期但还未过期，记录日志但继续发送邮件
                        logger.info(
                            f"Beta用户token即将过期，不刷新: {email}",
                            extra={"extra_fields": {
                                "email": email,
                                "subscription_type": subscription_type,
                                "token_expires_at": token_expires_at
                            }}
                        )
                        # Beta用户即将过期时仍使用现有token
                        # access_token保持不变
                else:
                    # 其他类型（如free）：根据情况处理
                    logger.warning(
                        f"未知订阅类型，默认不刷新token: {email} (type: {subscription_type})",
                        extra={"extra_fields": {
                            "email": email,
                            "subscription_type": subscription_type
                        }}
                    )

            # 获取用户语言偏好
            language = user.get("language", "en")

            # 加载该语言的翻译
            translations = self._load_translations(language)

            # 确定 Dashboard URL
            if dashboard_base_url is None:
                dashboard_base_url = os.getenv('DASHBOARD_URL', 'https://ai-tool-hotspot-dashboard.vercel.app')

            # 构建个性化参数
            personalized_params = f"?token={access_token}&email={email}"

            # 加载数据和模板
            data = self.base_generator.load_latest_data()
            template = self.base_generator.load_template()

            # 准备模板数据（传递基础URL）
            template_data = self.base_generator.prepare_template_data(
                data=data,
                dashboard_url=dashboard_base_url
            )

            # 根据用户语言为每个机会选择正确的摘要和MVP建议
            language_suffix_map = {
                'en': '_en',
                'zh': '_cn',
                'ja': '_ja'
            }
            suffix = language_suffix_map.get(language, '_en')

            for opp in template_data['opportunities']:
                # 选择对应语言的摘要
                opp['summary'] = opp['pain_point'].get(f'summary{suffix}', opp['pain_point'].get('summary_en', ''))
                # 选择对应语言的MVP建议
                opp['mvp_suggestion'] = opp.get(f'mvp_suggestion{suffix}', opp.get('mvp_suggestion_en', ''))

            # 添加个性化参数和翻译到模板数据
            template_data['personalized_params'] = personalized_params
            template_data['t'] = translations
            template_data['language'] = language

            # 渲染HTML
            html_content = template.render(**template_data)

            # 生成纯文本摘要
            plain_text_content = self.base_generator.generate_plain_text_summary(
                template_data["opportunities"]
            )

            # 生成主题（使用翻译）
            from datetime import datetime
            date_str = datetime.now().strftime("%Y-%m-%d")
            subject = translations['subject'].replace('{date}', date_str)

            logger.info(
                f"个性化邮件生成成功: {email}",
                extra={"extra_fields": {
                    "email": email,
                    "language": language,
                    "has_token": bool(access_token)
                }}
            )

            return subject, html_content, plain_text_content

        except Exception as e:
            logger.error(
                f"生成个性化邮件失败: {str(e)}",
                extra={"extra_fields": {"email": email, "error": str(e)}}
            )
            raise

    def generate_batch_emails(
        self,
        subscribers: list,
        dashboard_base_url: str = None
    ) -> Dict[str, Tuple[str, str, str]]:
        """批量生成个性化邮件

        Args:
            subscribers: 订阅者列表，每个元素包含 {'email': 'xxx@example.com', ...}
            dashboard_base_url: Dashboard基础URL

        Returns:
            Dict: 邮箱 -> (subject, html_content, plain_text_content) 的映射
        """
        results = {}
        failed_emails = []

        for subscriber in subscribers:
            email = subscriber.get("email")
            if not email:
                logger.warning("订阅者数据中缺少email字段", extra={"extra_fields": {"subscriber": subscriber}})
                continue

            try:
                subject, html, plain = self.generate_personalized_email(
                    email=email,
                    dashboard_base_url=dashboard_base_url
                )
                results[email] = (subject, html, plain)
            except Exception as e:
                logger.error(
                    f"为订阅者生成邮件失败: {email}",
                    extra={"extra_fields": {"email": email, "error": str(e)}}
                )
                failed_emails.append(email)

        if failed_emails:
            logger.warning(
                f"批量生成邮件完成，{len(failed_emails)}个失败",
                extra={"extra_fields": {
                    "total": len(subscribers),
                    "success": len(results),
                    "failed": len(failed_emails),
                    "failed_emails": failed_emails
                }}
            )
        else:
            logger.info(
                f"批量生成邮件完成，全部成功",
                extra={"extra_fields": {
                    "total": len(subscribers),
                    "success": len(results)
                }}
            )

        return results


# 使用示例
if __name__ == "__main__":
    # 测试用例
    import sys

    # 设置测试环境变量
    os.environ["JWT_SECRET_KEY"] = "test-secret-key"
    os.environ["DATABASE_PATH"] = "data/db.sqlite"
    os.environ["DASHBOARD_URL"] = "https://test-dashboard.com"

    generator = DailyEmailGenerator()

    # 测试单个邮件生成
    try:
        email = "test@example.com"
        subject, html, plain = generator.generate_personalized_email(email)
        print(f"✅ 邮件生成成功")
        print(f"主题: {subject}")
        print(f"HTML长度: {len(html)} 字符")
        print(f"纯文本长度: {len(plain)} 字符")
    except Exception as e:
        print(f"❌ 邮件生成失败: {e}")
        sys.exit(1)

    print("\n✅ 所有测试通过！")
