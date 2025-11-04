"""邮件内容生成器

从latest.json加载数据并渲染HTML邮件模板。
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List
from jinja2 import Template

from src.utils.logger import get_logger
from src.utils.config import config

logger = get_logger(__name__)


class EmailContentGenerator:
    """邮件内容生成器"""

    def __init__(
        self,
        template_path: str = "src/email/templates/daily_report.html",
        data_path: str = "data/latest.json"
    ):
        """初始化生成器

        Args:
            template_path: HTML模板文件路径
            data_path: 数据文件路径(latest.json)
        """
        self.template_path = Path(template_path)
        self.data_path = Path(data_path)

    def load_latest_data(self) -> Dict[str, Any]:
        """加载最新数据

        Returns:
            最新数据字典

        Raises:
            FileNotFoundError: 数据文件不存在
            json.JSONDecodeError: JSON解析失败
        """
        if not self.data_path.exists():
            raise FileNotFoundError(f"数据文件不存在: {self.data_path}")

        with open(self.data_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_template(self) -> Template:
        """加载HTML模板

        Returns:
            Jinja2模板对象

        Raises:
            FileNotFoundError: 模板文件不存在
        """
        if not self.template_path.exists():
            raise FileNotFoundError(f"模板文件不存在: {self.template_path}")

        with open(self.template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        return Template(template_content)

    def prepare_template_data(
        self,
        data: Dict[str, Any],
        dashboard_url: str = None
    ) -> Dict[str, Any]:
        """准备模板渲染数据

        Args:
            data: 原始数据(latest.json内容)
            dashboard_url: 仪表板URL

        Returns:
            模板变量字典
        """
        # 使用配置的Dashboard URL（如果未提供）
        if dashboard_url is None:
            dashboard_url = config.dashboard_url

        # 提取Top 10机会
        opportunities = data.get("opportunities", [])
        top_10 = sorted(
            opportunities,
            key=lambda x: x.get("opportunity_score", 0),
            reverse=True
        )[:10]

        # 创建ID到实体的映射,便于查找相关工具和热点
        tools_map = {
            tool["id"]: tool
            for tool in data.get("ai_tools", [])
        }
        topics_map = {
            topic["id"]: topic
            for topic in data.get("trending_topics", [])
        }
        pain_points_map = {
            pp["id"]: pp
            for pp in data.get("pain_points", [])
        }

        # 丰富机会数据
        enriched_opportunities = []
        for opp in top_10:
            # 获取关联的痛点
            pain_point_id = opp.get("pain_point_id")
            pain_point = pain_points_map.get(pain_point_id, {})

            # 获取相关工具名称
            related_tool_ids = opp.get("related_tools", [])
            related_tool_names = [
                tools_map[tid].get("name", "Unknown")
                for tid in related_tool_ids
                if tid in tools_map
            ]

            # 获取相关热点标题
            related_topic_ids = opp.get("related_topics", [])
            related_topic_titles = [
                topics_map[tid].get("title", "Unknown")
                for tid in related_topic_ids
                if tid in topics_map
            ]

            enriched_opportunities.append({
                **opp,
                "pain_point": pain_point,
                "related_tools": related_tool_names,
                "related_topics": related_topic_titles
            })

        # 当前时间和下次更新时间
        now = datetime.now()
        tomorrow_8am = (now + timedelta(days=1)).replace(
            hour=8, minute=0, second=0, microsecond=0
        )

        return {
            "date": now.strftime("%Y-%m-%d"),
            "generation_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "next_update_time": tomorrow_8am.strftime("%H:%M"),
            "dashboard_url": dashboard_url,
            "ai_tools_count": len(data.get("ai_tools", [])),
            "trending_topics_count": len(data.get("trending_topics", [])),
            "pain_points_count": len(data.get("pain_points", [])),
            "opportunities": enriched_opportunities
        }

    def generate_plain_text_summary(
        self,
        opportunities: List[Dict[str, Any]]
    ) -> str:
        """生成纯文本摘要(用于不支持HTML的邮件客户端)

        Args:
            opportunities: Top 10机会列表

        Returns:
            纯文本内容
        """
        lines = [
            "每日AI工具机会报告 / Daily AI Tool Opportunity Report",
            "=" * 60,
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "Top 10 产品机会:",
            ""
        ]

        for i, opp in enumerate(opportunities[:10], 1):
            pain_point = opp.get("pain_point", {})
            lines.extend([
                f"{i}. 机会评分: {opp.get('opportunity_score', 0):.1f}",
                f"   痛点: {pain_point.get('original_text', 'N/A')[:100]}...",
                f"   中文摘要: {pain_point.get('summary_cn', 'N/A')}",
                f"   MVP建议: {opp.get('mvp_suggestion_cn', 'N/A')[:100]}...",
                ""
            ])

        lines.extend([
            "=" * 60,
            "访问完整仪表板以查看更多详情",
            "",
            "此邮件由AI工具热点仪表板系统自动发送"
        ])

        return "\n".join(lines)

    def generate_email_content(
        self,
        dashboard_url: str = None
    ) -> tuple[str, str, str]:
        """生成邮件内容

        Args:
            dashboard_url: 仪表板URL

        Returns:
            (subject, html_content, plain_text_content)

        Raises:
            FileNotFoundError: 模板或数据文件不存在
            json.JSONDecodeError: JSON解析失败
            Exception: 模板渲染失败
        """
        # 使用配置的Dashboard URL（如果未提供）
        if dashboard_url is None:
            dashboard_url = config.dashboard_url

        try:
            # 加载数据
            data = self.load_latest_data()
            logger.info(f"成功加载数据: {len(data.get('opportunities', []))} 个机会")

            # 加载模板
            template = self.load_template()
            logger.info(f"成功加载模板: {self.template_path}")

            # 准备模板数据
            template_data = self.prepare_template_data(data, dashboard_url)

            # 渲染HTML
            html_content = template.render(**template_data)

            # 生成纯文本
            plain_text_content = self.generate_plain_text_summary(
                template_data["opportunities"]
            )

            # 生成主题
            date_str = datetime.now().strftime("%Y-%m-%d")
            subject = f"🚀 每日AI工具机会报告 {date_str} | Top 10 Opportunities"

            logger.info("邮件内容生成成功")
            return subject, html_content, plain_text_content

        except FileNotFoundError as e:
            logger.error(f"文件不存在: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"邮件内容生成失败: {str(e)}")
            raise


# 创建全局实例
email_generator = EmailContentGenerator()
