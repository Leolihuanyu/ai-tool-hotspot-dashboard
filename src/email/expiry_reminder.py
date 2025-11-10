"""
过期提醒服务
检查即将过期的Beta用户，发送提醒邮件
"""

import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from dateutil import parser
from src.database.connection import get_connection, convert_placeholder
from src.email.smtp_sender import SMTPEmailSender
from src.email.template_manager import EmailTemplateManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ExpiryReminderService:
    """过期提醒服务"""

    def __init__(self, database_path: str = None):
        """
        初始化过期提醒服务

        Args:
            database_path: 数据库路径
        """
        self.database_path = database_path or os.getenv(
            "DATABASE_PATH", "data/db.sqlite"
        )
        self.email_sender = SMTPEmailSender()
        self.template_manager = EmailTemplateManager()

    def get_expiring_users(
        self,
        days_until_expiry: int,
        filter_by_timezone: bool = False,
        target_hour: int = 9
    ) -> List[Dict[str, Any]]:
        """
        获取距离过期还有指定天数的用户

        Args:
            days_until_expiry: 距离过期的天数（14/7/1）
            filter_by_timezone: 是否按时区过滤（仅返回当地时间在目标小时的用户）
            target_hour: 目标小时（默认9点，仅在filter_by_timezone=True时有效）

        Returns:
            List[Dict]: 即将过期的用户列表
        """
        try:
            conn = get_connection(self.database_path)
            cursor = conn.cursor()

            # 计算目标日期范围（UTC时间）
            # 使用更宽松的时间窗口：前后各 12 小时
            now = datetime.now(timezone.utc)
            target_date_center = now + timedelta(days=days_until_expiry)
            target_date_start = target_date_center - timedelta(hours=12)
            target_date_end = target_date_center + timedelta(hours=12)

            # 查询即将过期的Beta用户（包含timezone字段）
            query = convert_placeholder("""
                SELECT id, email, subscription_type, free_until, created_at, timezone, language
                FROM users
                WHERE subscription_type = 'beta'
                  AND subscription_status = 'active'
                  AND free_until >= ?
                  AND free_until < ?
                ORDER BY free_until ASC
            """)

            cursor.execute(
                query,
                (target_date_start.isoformat(), target_date_end.isoformat())
            )

            rows = cursor.fetchall()
            conn.close()

            users = []
            for row in rows:
                # 兼容SQLite (tuple/Row) 和 PostgreSQL (dict)
                if isinstance(row, dict):
                    user_data = {
                        "id": row['id'],
                        "email": row['email'],
                        "subscription_type": row['subscription_type'],
                        "free_until": row['free_until'],
                        "created_at": row['created_at'],
                        "timezone": row.get('timezone', 'UTC'),
                        "language": row.get('language', 'zh'),
                    }
                else:
                    user_data = {
                        "id": row[0],
                        "email": row[1],
                        "subscription_type": row[2],
                        "free_until": row[3],
                        "created_at": row[4],
                        "timezone": row[5] if len(row) > 5 else 'UTC',
                        "language": row[6] if len(row) > 6 else 'zh',
                    }

                # 如果需要按时区过滤
                if filter_by_timezone:
                    if self._is_user_in_target_hour(user_data['timezone'], target_hour):
                        users.append(user_data)
                else:
                    users.append(user_data)

            logger.info(
                f"找到 {len(users)} 个将在 {days_until_expiry} 天后过期的用户"
                f"{' (已按时区过滤)' if filter_by_timezone else ''}"
            )
            return users

        except Exception as e:
            logger.error(f"获取即将过期用户失败: {str(e)}")
            return []

    def _is_user_in_target_hour(self, user_timezone: str, target_hour: int) -> bool:
        """
        检查用户当地时间是否在目标小时内

        Args:
            user_timezone: 用户时区（如 Asia/Shanghai）
            target_hour: 目标小时（0-23）

        Returns:
            bool: 是否在目标小时内
        """
        try:
            from zoneinfo import ZoneInfo

            # 获取当前UTC时间
            now_utc = datetime.now(timezone.utc)

            # 转换到用户时区
            user_tz = ZoneInfo(user_timezone)
            now_user_tz = now_utc.astimezone(user_tz)

            # 检查当前小时是否为目标小时
            return now_user_tz.hour == target_hour

        except Exception as e:
            logger.warning(f"时区转换失败 ({user_timezone}): {str(e)}，跳过该用户")
            return False

    def send_expiry_reminder(
        self,
        user: Dict[str, Any],
        days_until_expiry: int,
        language: str = None
    ) -> bool:
        """
        发送过期提醒邮件

        Args:
            user: 用户信息（应包含 language 字段）
            days_until_expiry: 距离过期天数（14/7/1）
            language: 语言（zh/en/ja），如果为None则从用户数据中获取

        Returns:
            bool: 是否发送成功
        """
        try:
            email = user['email']
            free_until = user.get('free_until')

            if not free_until:
                logger.warning(f"用户 {email} 没有 free_until 信息，跳过")
                return False

            # 如果未提供language参数，从用户数据中获取
            if language is None:
                language = user.get('language', 'zh')

            # 解析过期时间（可能是字符串或 datetime 对象）
            if isinstance(free_until, str):
                expiry_dt = parser.parse(free_until)
            else:
                expiry_dt = free_until

            # 根据天数选择模板
            if days_until_expiry == 14:
                template_name = "expiry_reminder_14days"
            elif days_until_expiry == 7:
                template_name = "expiry_reminder_7days"
            elif days_until_expiry == 1:
                template_name = "expiry_reminder_1day"
            else:
                logger.error(f"不支持的提醒天数: {days_until_expiry}")
                return False

            # 加载邮件模板
            template = self.template_manager.get_template_strings(template_name, language)
            if not template:
                logger.error(f"加载邮件模板失败: {template_name} ({language})")
                return False

            # 准备模板变量
            template_vars = {
                "expiry_date": expiry_dt.strftime("%Y-%m-%d %H:%M UTC"),
                "opportunities_count": "50+",  # TODO: 从数据库获取真实统计
                "tools_count": "100+",
                "hours_saved": "20+",
            }

            # 渲染邮件内容
            subject = template.get("subject", "").format(**template_vars)
            html_content = self._render_html_email(template, template_vars)

            # 发送邮件
            result = self.email_sender.send_html_email(
                to_emails=[email],
                subject=subject,
                html_content=html_content
            )

            if result.get("success"):
                logger.info(
                    f"成功发送 {days_until_expiry} 天过期提醒: {email}",
                    extra={"extra_fields": {"user_id": user['id']}}
                )
                return True
            else:
                logger.error(
                    f"发送过期提醒失败: {email} - {result.get('error')}",
                    extra={"extra_fields": {"user_id": user['id']}}
                )
                return False

        except Exception as e:
            logger.error(f"发送过期提醒异常: {str(e)}")
            return False

    def _render_html_email(
        self,
        template: Dict[str, Any],
        vars: Dict[str, str]
    ) -> str:
        """
        渲染HTML邮件内容

        Args:
            template: 邮件模板
            vars: 模板变量

        Returns:
            str: HTML内容
        """
        # 简化版HTML模板（实际应用中可使用更复杂的HTML模板）
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                           color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; }}
                .cta-button {{ display: inline-block; background: #667eea; color: white;
                               padding: 15px 30px; text-decoration: none; border-radius: 5px;
                               margin: 20px 0; font-weight: bold; }}
                .stats {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .warning {{ background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107;
                            margin: 20px 0; border-radius: 4px; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                ul {{ list-style: none; padding: 0; }}
                li {{ padding: 8px 0; }}
                li:before {{ content: "✓ "; color: #667eea; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{template.get('title', '')}</h1>
                </div>
                <div class="content">
                    <p><strong>{template.get('greeting', '')}</strong></p>
                    <p>{template.get('intro_p1', '').format(**vars)}</p>
                    <p>{template.get('intro_p2', '').format(**vars)}</p>
        """

        # 添加统计信息（如果有）
        if 'stats_title' in template:
            html += f"""
                    <div class="stats">
                        <h3>{template['stats_title']}</h3>
                        <ul>
            """
            for stat in template.get('stats', []):
                html += f"<li>{stat.format(**vars)}</li>"
            html += """
                        </ul>
                    </div>
            """

        # 添加价值点（如果有）
        if 'value_title' in template:
            html += f"""
                    <h3>{template['value_title']}</h3>
                    <ul>
            """
            for point in template.get('value_points', []):
                html += f"<li>{point}</li>"
            html += "</ul>"

        # 添加紧急提醒（如果有）
        if 'urgent_title' in template:
            html += f"""
                    <h3>{template['urgent_title']}</h3>
            """
            if 'urgent_message' in template:
                html += f"<p>{template['urgent_message']}</p>"
            if 'urgent_points' in template:
                html += "<ul>"
                for point in template['urgent_points']:
                    html += f"<li>{point}</li>"
                html += "</ul>"

        # 添加CTA按钮
        upgrade_url = os.getenv(
            "UPGRADE_URL",
            "https://ai-tool-hotspot-dashboard.vercel.app/upgrade"
        )
        html += f"""
                    <div style="text-align: center;">
                        <a href="{upgrade_url}" class="cta-button">
                            {template.get('cta_button', '立即升级')}
                        </a>
                    </div>
        """

        # 添加价格信息（如果有）
        if 'pricing_title' in template:
            html += f"""
                    <h3>{template['pricing_title']}</h3>
                    <p>{template.get('pricing_info', '').format(**vars)}</p>
                    <ul>
            """
            for plan in template.get('pricing_plans', []):
                html += f"<li>{plan}</li>"
            html += "</ul>"

        # 添加警告信息（如果有）
        if 'reminder' in template:
            html += f"""
                    <div class="warning">
                        <p><strong>{template['reminder']}</strong></p>
                    </div>
            """

        # 结束内容
        html += f"""
                    <p>{template.get('support', '')}</p>
                </div>
                <div class="footer">
                    <p>{template.get('footer_copyright', '')}</p>
                    <p>{template.get('footer_notice', '')}</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def run_daily_check(self, use_timezone_filter: bool = True, target_hour: int = 9) -> Dict[str, Any]:
        """
        执行每日过期检查和提醒

        Args:
            use_timezone_filter: 是否按用户时区过滤（仅在当地上午9点发送）
            target_hour: 目标小时（默认9点）

        Returns:
            Dict: 执行结果统计
        """
        logger.info(
            f"开始执行过期提醒检查... "
            f"{'(按时区过滤，目标时间: ' + str(target_hour) + ':00)' if use_timezone_filter else '(不过滤时区)'}"
        )

        results = {
            "14_days": {"sent": 0, "failed": 0},
            "7_days": {"sent": 0, "failed": 0},
            "1_day": {"sent": 0, "failed": 0},
        }

        # 检查并发送 14 天提醒
        users_14days = self.get_expiring_users(
            14,
            filter_by_timezone=use_timezone_filter,
            target_hour=target_hour
        )
        for user in users_14days:
            # 从用户数据中获取语言偏好
            if self.send_expiry_reminder(user, 14):
                results["14_days"]["sent"] += 1
            else:
                results["14_days"]["failed"] += 1

        # 检查并发送 7 天提醒
        users_7days = self.get_expiring_users(
            7,
            filter_by_timezone=use_timezone_filter,
            target_hour=target_hour
        )
        for user in users_7days:
            if self.send_expiry_reminder(user, 7):
                results["7_days"]["sent"] += 1
            else:
                results["7_days"]["failed"] += 1

        # 检查并发送 1 天提醒
        users_1day = self.get_expiring_users(
            1,
            filter_by_timezone=use_timezone_filter,
            target_hour=target_hour
        )
        for user in users_1day:
            if self.send_expiry_reminder(user, 1):
                results["1_day"]["sent"] += 1
            else:
                results["1_day"]["failed"] += 1

        total_sent = sum(r["sent"] for r in results.values())
        total_failed = sum(r["failed"] for r in results.values())

        logger.info(
            f"过期提醒检查完成: 成功 {total_sent}, 失败 {total_failed}",
            extra={"extra_fields": results}
        )

        return {
            "success": True,
            "total_sent": total_sent,
            "total_failed": total_failed,
            "details": results
        }


# 使用示例
if __name__ == "__main__":
    service = ExpiryReminderService()
    result = service.run_daily_check()
    print(f"过期提醒执行结果: {result}")
