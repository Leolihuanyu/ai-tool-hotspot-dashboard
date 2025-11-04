"""YouTube Shorts热点爬虫

从YouTube Shorts中抓取热点话题数据。
基于research.md推荐,使用YouTube Data API v3。
"""

from typing import List, Dict, Any
from datetime import datetime, timezone
from uuid import uuid4

from src.scrapers.base import BaseScraper
from src.models.trend import TrendingTopic


class YouTubeScraper(BaseScraper):
    """YouTube Shorts热点爬虫

    使用YouTube Data API v3抓取Shorts视频数据。
    需要在.env中配置YOUTUBE_API_KEY。
    """

    def __init__(self):
        super().__init__(
            source_name="YouTube",
            base_url="https://www.youtube.com"
        )

        # 从配置加载API密钥
        from src.utils.config import config
        self.youtube_api_key = getattr(config, 'youtube_api_key', None)

        # YouTube Data API v3 endpoint
        self.api_base_url = "https://www.googleapis.com/youtube/v3"

    def _search_shorts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """搜索YouTube Shorts视频

        Args:
            query: 搜索关键词
            limit: 结果数量限制

        Returns:
            视频数据列表
        """
        if not self.youtube_api_key:
            raise ValueError("YouTube API key not configured")

        # 搜索请求
        search_url = f"{self.api_base_url}/search"
        search_params = {
            'key': self.youtube_api_key,
            'part': 'snippet',
            'q': query + ' #shorts',  # 添加#shorts标签过滤
            'type': 'video',
            'videoDefinition': 'high',
            'videoDuration': 'short',  # 短视频(< 4分钟)
            'maxResults': min(limit, 50),  # API限制
            'order': 'date',  # 按日期排序，获取最新视频
            'regionCode': 'US'  # 可配置
        }

        response = self.fetch_with_retry(search_url, params=search_params)
        search_data = response.json()

        if 'items' not in search_data:
            return []

        # 提取视频ID
        video_ids = [item['id']['videoId'] for item in search_data['items']]

        # 获取视频详细信息(包含统计数据)
        return self._get_video_details(video_ids)

    def _get_video_details(self, video_ids: List[str]) -> List[Dict[str, Any]]:
        """获取视频详细信息

        Args:
            video_ids: 视频ID列表

        Returns:
            视频详细数据列表
        """
        if not video_ids:
            return []

        videos_url = f"{self.api_base_url}/videos"
        videos_params = {
            'key': self.youtube_api_key,
            'part': 'snippet,statistics,contentDetails',
            'id': ','.join(video_ids)
        }

        response = self.fetch_with_retry(videos_url, params=videos_params)
        videos_data = response.json()

        results = []
        for item in videos_data.get('items', []):
            results.append({
                'id': item['id'],
                'title': item['snippet']['title'],
                'description': item['snippet']['description'],
                'channel': item['snippet']['channelTitle'],
                'published_at': item['snippet']['publishedAt'],
                'url': f"https://www.youtube.com/shorts/{item['id']}",
                'statistics': item.get('statistics', {}),
                'duration': item.get('contentDetails', {}).get('duration', ''),
                'tags': item['snippet'].get('tags', [])
            })

        return results

    def scrape(self, limit: int = None) -> List[Dict[str, Any]]:
        """抓取YouTube Shorts热点数据

        Args:
            limit: 限制抓取数量(可选,用于测试)

        Returns:
            原始数据字典列表
        """
        if not self.youtube_api_key:
            self.logger.error("YouTube API key not configured. Please set YOUTUBE_API_KEY in .env")
            return []

        # AI相关搜索关键词 - 更新为更精准和时效性强的关键词
        keywords = [
            "AI tools 2025",         # 加上年份，获取最新内容
            "new AI tools",          # 明确要新工具
            "AI SaaS tools",         # 更精准的B2B工具
            "AI productivity tools", # 生产力工具
            "AI automation tools"    # 自动化工具
        ]
        results = []

        for keyword in keywords:
            try:
                self.logger.info(f"Searching for: {keyword}")
                videos = self._search_shorts(
                    query=keyword,
                    limit=limit or 10
                )
                results.extend(videos)

                if limit and len(results) >= limit:
                    results = results[:limit]
                    break

            except Exception as e:
                self.logger.warning(f"Failed to search for '{keyword}': {e}")
                continue

        self.logger.info(f"Scraped {len(results)} YouTube Shorts")
        return results

    def normalize(self, raw_data: Dict[str, Any]) -> TrendingTopic:
        """将原始数据转换为TrendingTopic模型

        Args:
            raw_data: 原始数据字典

        Returns:
            TrendingTopic对象
        """
        # 计算热度分数(基于观看量、点赞数、评论数)
        stats = raw_data.get('statistics', {})
        views = int(stats.get('viewCount', 0))
        likes = int(stats.get('likeCount', 0))
        comments = int(stats.get('commentCount', 0))

        # 热度计算:观看*0.001 + 点赞*0.1 + 评论*0.5,归一化到0-100
        # 假设100万观看+1万点赞+1000评论 = 100分
        heat_score = min(100.0, (views * 0.001 + likes * 0.1 + comments * 0.5) / 20)

        # 解析发布时间
        published_at = raw_data.get('published_at')
        if published_at:
            dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
        else:
            dt = datetime.now(timezone.utc)

        return TrendingTopic(
            id=str(uuid4()),
            title=raw_data['title'][:200],  # 限制长度
            description=raw_data['description'][:500],  # 限制长度
            source="YouTube",
            url=raw_data['url'],
            timestamp=dt,
            heat_score=heat_score,
            trend_direction="stable",  # 初始值,后续计算
            tags=raw_data.get('tags', [])[:5] + ["YouTube", "Shorts"],  # 限制标签数量
            summary_cn="",  # 由LLM生成
            summary_ja="",  # 由LLM生成
            data_quality_score=0.9,  # 官方API数据质量高
            schema_version="1.1"
        )
