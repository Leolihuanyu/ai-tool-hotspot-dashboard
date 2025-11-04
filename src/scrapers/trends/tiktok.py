"""TikTok热点爬虫

从TikTok热门视频中抓取热点话题数据。
基于research.md推荐,优先使用第三方API或RSS聚合服务。
"""

from typing import List, Dict, Any
from datetime import datetime, timezone
from uuid import uuid4

from src.scrapers.base import BaseScraper
from src.models.trend import TrendingTopic


class TikTokScraper(BaseScraper):
    """TikTok热点爬虫

    注意:TikTok是JavaScript密集型站点,官方API需要认证。
    本实现提供两种模式:
    1. 使用第三方API服务(RapidAPI)
    2. 使用RSS聚合服务(fallback)

    建议在.env中配置RAPIDAPI_KEY以使用模式1。
    """

    def __init__(self):
        super().__init__(
            source_name="TikTok",
            base_url="https://www.tiktok.com"
        )

        # 从配置加载API密钥
        from src.utils.config import config
        self.rapidapi_key = getattr(config, 'rapidapi_key', None)

        # RapidAPI TikTok endpoint
        self.rapidapi_url = "https://tiktok-scraper7.p.rapidapi.com/feed/search"

        # RSS聚合服务(fallback)
        self.rss_fallback_url = "https://rsshub.app/tiktok/keyword/AI"

    def _scrape_via_rapidapi(self, limit: int = None) -> List[Dict[str, Any]]:
        """通过RapidAPI抓取数据

        Args:
            limit: 限制抓取数量

        Returns:
            原始数据列表
        """
        if not self.rapidapi_key:
            raise ValueError("RapidAPI key not configured")

        headers = {
            "X-RapidAPI-Key": self.rapidapi_key,
            "X-RapidAPI-Host": "tiktok-scraper7.p.rapidapi.com"
        }

        # 搜索关键词列表(AI相关)
        keywords = ["AI tools", "ChatGPT", "artificial intelligence"]
        results = []

        for keyword in keywords:
            try:
                params = {
                    "query": keyword,
                    "count": limit or 10
                }

                response = self.fetch_with_retry(
                    self.rapidapi_url,
                    headers=headers,
                    params=params
                )

                data = response.json()

                if 'data' in data:
                    for item in data['data']:
                        results.append({
                            'id': item.get('id'),
                            'title': item.get('desc', ''),
                            'description': item.get('desc', ''),
                            'url': f"https://www.tiktok.com/@{item.get('author', {}).get('uniqueId')}/video/{item.get('id')}",
                            'stats': item.get('stats', {}),
                            'create_time': item.get('createTime'),
                            'search_keyword': keyword
                        })

                        if limit and len(results) >= limit:
                            break

                if limit and len(results) >= limit:
                    break

            except Exception as e:
                self.logger.warning(f"Failed to fetch from RapidAPI for keyword '{keyword}': {e}")
                continue

        return results

    def _scrape_via_rss(self, limit: int = None) -> List[Dict[str, Any]]:
        """通过RSS聚合服务抓取数据(fallback)

        Args:
            limit: 限制抓取数量

        Returns:
            原始数据列表
        """
        import feedparser

        try:
            feed = feedparser.parse(self.rss_fallback_url)
            results = []

            for entry in feed.entries[:limit] if limit else feed.entries:
                results.append({
                    'id': entry.get('id', str(uuid4())),
                    'title': entry.get('title', ''),
                    'description': entry.get('description', entry.get('summary', '')),
                    'url': entry.get('link', ''),
                    'published': entry.get('published_parsed'),
                    'stats': {}  # RSS不包含详细统计
                })

            return results

        except Exception as e:
            self.logger.error(f"Failed to fetch from RSS: {e}")
            raise

    def scrape(self, limit: int = None) -> List[Dict[str, Any]]:
        """抓取TikTok热点数据

        优先使用RapidAPI,失败则fallback到RSS。

        Args:
            limit: 限制抓取数量(可选,用于测试)

        Returns:
            原始数据字典列表
        """
        # 优先使用RapidAPI
        if self.rapidapi_key:
            try:
                self.logger.info("Using RapidAPI mode")
                return self._scrape_via_rapidapi(limit=limit)
            except Exception as e:
                self.logger.warning(f"RapidAPI failed, falling back to RSS: {e}")

        # Fallback到RSS
        self.logger.info("Using RSS fallback mode")
        return self._scrape_via_rss(limit=limit)

    def normalize(self, raw_data: Dict[str, Any]) -> TrendingTopic:
        """将原始数据转换为TrendingTopic模型

        Args:
            raw_data: 原始数据字典

        Returns:
            TrendingTopic对象
        """
        # 计算热度分数(基于互动量)
        stats = raw_data.get('stats', {})
        likes = stats.get('diggCount', 0)
        comments = stats.get('commentCount', 0)
        shares = stats.get('shareCount', 0)

        # 简单的热度计算:点赞*1 + 评论*2 + 分享*3,然后归一化到0-100
        # 假设10万互动量 = 100分
        heat_score = min(100.0, (likes + comments * 2 + shares * 3) / 1000)

        # 解析时间戳
        timestamp = raw_data.get('create_time')
        if timestamp:
            if isinstance(timestamp, int):
                # Unix timestamp
                dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            else:
                dt = datetime.now(timezone.utc)
        else:
            # 如果是RSS数据,使用published字段
            published = raw_data.get('published')
            if published:
                from time import mktime
                dt = datetime.fromtimestamp(mktime(published), tz=timezone.utc)
            else:
                dt = datetime.now(timezone.utc)

        return TrendingTopic(
            id=str(uuid4()),
            title=raw_data['title'][:200],  # 限制长度
            description=raw_data['description'][:500],  # 限制长度
            source="TikTok",
            url=raw_data['url'],
            timestamp=dt,
            heat_score=heat_score,
            trend_direction="stable",  # 初始值,后续计算
            tags=["AI", "TikTok", raw_data.get('search_keyword', 'trending')],
            summary_cn="",  # 由LLM生成
            summary_ja="",  # 由LLM生成
            data_quality_score=0.7 if self.rapidapi_key else 0.5,  # API数据质量更高
            schema_version="1.1"
        )
