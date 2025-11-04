"""Futurepedia RSS爬虫

从Futurepedia的RSS feed抓取AI工具信息。
数据源: https://www.futurepedia.io/rss
"""

import feedparser
from typing import List, Dict, Any
from datetime import datetime
from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper
from src.models.tool import AITool


class FuturepediaScraper(BaseScraper):
    """Futurepedia RSS爬虫

    通过RSS feed抓取AI工具数据。
    RSS格式稳定,无需反爬虫处理。
    """

    def __init__(self):
        """初始化Futurepedia爬虫"""
        super().__init__(
            source_name="Futurepedia",
            base_url="https://www.futurepedia.io"
        )
        self.rss_url = "https://www.futurepedia.io/rss"

    def scrape(self, limit: int = None) -> List[Dict[str, Any]]:
        """抓取RSS feed数据

        Args:
            limit: 限制抓取数量(可选,用于测试)

        Returns:
            原始数据字典列表

        Raises:
            Exception: RSS解析失败
        """
        try:
            self.logger.info(f"Fetching RSS feed from {self.rss_url}")

            # 使用feedparser解析RSS
            feed = feedparser.parse(self.rss_url)

            if feed.bozo:
                # RSS格式错误
                self.logger.warning(f"RSS feed has errors: {feed.bozo_exception}")

            entries = feed.entries

            if limit:
                entries = entries[:limit]

            self.logger.info(f"Parsed {len(entries)} entries from RSS feed")

            # 转换为标准格式
            raw_data_list = []
            for entry in entries:
                raw_data = {
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'description': entry.get('summary', ''),
                    'published': entry.get('published', ''),
                    'published_parsed': entry.get('published_parsed', None),
                    'tags': [tag.term for tag in entry.get('tags', [])],
                    'content': entry.get('content', [{}])[0].get('value', '') if entry.get('content') else ''
                }
                raw_data_list.append(raw_data)

            return raw_data_list

        except Exception as e:
            self.logger.error(f"Failed to scrape RSS feed: {e}")
            raise

    def normalize(self, raw_data: Dict[str, Any]) -> AITool:
        """将RSS entry转换为AITool模型

        Args:
            raw_data: RSS entry数据

        Returns:
            AITool对象

        Raises:
            ValidationError: 数据验证失败
        """
        # 解析时间
        if raw_data.get('published_parsed'):
            timestamp = datetime(*raw_data['published_parsed'][:6])
        else:
            # 解析ISO格式时间
            try:
                timestamp = datetime.fromisoformat(raw_data['published'].replace('Z', '+00:00'))
            except:
                timestamp = datetime.now()

        # 从description或content提取纯文本
        description_html = raw_data.get('content') or raw_data.get('description', '')
        if description_html:
            soup = BeautifulSoup(description_html, 'html.parser')
            description = soup.get_text(strip=True)
        else:
            description = raw_data.get('title', '')

        # 初步提取features(从描述中猜测)
        # TODO: 可以用LLM更精确地提取
        features = []
        feature_keywords = [
            'text-to-image', 'image-generation', 'video-generation',
            'text-generation', 'code-generation', 'translation',
            'summarization', 'chat', 'voice', 'audio'
        ]
        description_lower = description.lower()
        for keyword in feature_keywords:
            if keyword.replace('-', ' ') in description_lower or keyword in description_lower:
                features.append(keyword)

        if not features:
            features = ['ai-tool']  # 默认标签

        # 推测定价模式(默认freemium)
        # TODO: 可以用LLM更精确地提取
        pricing_model = 'freemium'
        pricing_keywords = {
            'free': ['free', 'open source', 'open-source'],
            'paid': ['paid', 'premium', 'one-time'],
            'subscription': ['subscription', 'monthly', 'yearly', 'plan']
        }
        for model, keywords in pricing_keywords.items():
            if any(kw in description_lower for kw in keywords):
                pricing_model = model
                break

        # 计算数据质量评分
        # Futurepedia RSS是可靠数据源
        source_reliability = 0.9  # RSS源=0.9
        content_completeness = 1.0 if (raw_data.get('title') and raw_data.get('link') and description) else 0.7
        data_freshness = 1.0 if (datetime.now() - timestamp).days < 1 else 0.7

        data_quality_score = (
            source_reliability * 0.4 +
            content_completeness * 0.4 +
            data_freshness * 0.2
        )

        # 构建AITool对象
        tool = AITool(
            name=raw_data['title'],
            description=description[:500],  # 限制长度
            source="Futurepedia",
            url=raw_data['link'],
            timestamp=timestamp,
            tags=raw_data.get('tags', ['ai-tool']),
            features=features,
            pricing_model=pricing_model,
            summary_cn="",  # 待LLM生成
            summary_ja="",  # 待LLM生成
            data_quality_score=round(data_quality_score, 2)
        )

        return tool
