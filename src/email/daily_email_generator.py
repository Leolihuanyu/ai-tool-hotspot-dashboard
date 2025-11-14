"""每日邮件个性化生成器

为每个订阅者生成包含个人访问token的个性化邮件。
"""

import os
from typing import Dict, Any, Tuple
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

            # 获取用户的长期token
            access_token = user.get("access_token")

            # 如果没有token，生成一个新的（这是一个后备机制）
            if not access_token:
                logger.warning(
                    f"用户没有访问token，生成新token: {email}",
                    extra={"extra_fields": {"email": email}}
                )
                access_token = self.token_manager.generate_long_term_token(expiry_days=90)
                # 保存到数据库
                self.user_manager.update_access_token(
                    email=email,
                    access_token=access_token,
                    expiry_days=90
                )

            # 获取用户语言偏好
            language = user.get("language", "en")

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

            # 添加个性化参数到模板数据
            template_data['personalized_params'] = personalized_params

            # 渲染HTML
            html_content = template.render(**template_data)

            # 生成纯文本摘要
            plain_text_content = self.base_generator.generate_plain_text_summary(
                template_data["opportunities"]
            )

            # 生成主题
            from datetime import datetime
            date_str = datetime.now().strftime("%Y-%m-%d")
            subject = f"🚀 每日AI工具机会报告 {date_str} | Top 10 Opportunities"

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
