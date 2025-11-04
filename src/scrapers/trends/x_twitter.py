"""X (Twitter) 热点爬虫

从X(Twitter)抓取热点话题数据。
基于research.md推荐,使用Nitter实例或RSS Bridge作为fallback。
"""

from typing import List, Dict, Any
from datetime import datetime, timezone
from uuid import uuid4
from time import mktime
import feedparser

from src.scrapers.base import BaseScraper
from src.models.trend import TrendingTopic


class XTwitterScraper(BaseScraper):
    """X (Twitter) 热点爬虫

    由于X官方API v2需要认证且费用高,本实现使用:
    1. Nitter实例(开源Twitter前端)
    2. RSS Bridge作为fallback

    注意:Nitter实例可能不稳定,需要配置多个备用实例。
    """

    def __init__(self):
        super().__init__(
            source_name="X",
            base_url="https://twitter.com"
        )

        # Nitter实例列表(公共实例可能不稳定,建议自建)
        self.nitter_instances = [
            "https://nitter.net",
            "https://nitter.it",
            "https://nitter.privacydev.net"
        ]

        # RSS Bridge instance
        self.rss_bridge_url = "https://rss-bridge.org/bridge01"

        # 搜索关键词
        self.search_keywords = ["AI tools", "ChatGPT", "artificial intelligence"]

    def _scrape_via_nitter(self, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
        """通过Nitter实例抓取数据

        Args:
            keyword: 搜索关键词
            limit: 结果数量限制

        Returns:
            推文数据列表
        """
        for instance in self.nitter_instances:
            try:
                # Nitter提供RSS feed
                # 格式: https://nitter.net/search/rss?q=AI+tools
                search_url = f"{instance}/search/rss?q={keyword.replace(' ', '+')}"

                self.logger.info(f"Trying Nitter instance: {instance}")

                feed = feedparser.parse(search_url)

                if not feed.entries:
                    continue

                results = []
                for entry in feed.entries[:limit]:
                    # 提取推文信息
                    title = entry.get('title', '')
                    description = entry.get('description', entry.get('summary', ''))
                    link = entry.get('link', '')

                    # 从Nitter链接提取Twitter链接
                    twitter_link = link.replace(instance, "https://twitter.com")

                    results.append({
                        'id': entry.get('id', str(uuid4())),
                        'title': title,
                        'description': description,
                        'url': twitter_link,
                        'published': entry.get('published_parsed'),
                        'author': entry.get('author', 'Unknown'),
                        'keyword': keyword
                    })

                self.logger.info(f"Successfully fetched {len(results)} tweets from {instance}")
                return results

            except Exception as e:
                self.logger.warning(f"Failed to fetch from {instance}: {e}")
                continue

        raise Exception("All Nitter instances failed")

    def _scrape_via_rss_bridge(self, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
        """通过RSS Bridge抓取数据(fallback)

        Args:
            keyword: 搜索关键词
            limit: 结果数量限制

        Returns:
            推文数据列表
        """
        try:
            # RSS Bridge Twitter search
            # 格式: https://rss-bridge.org/bridge01/?action=display&bridge=Twitter&context=By+keyword&q=AI+tools&format=Atom
            search_url = f"{self.rss_bridge_url}/?action=display&bridge=Twitter&context=By+keyword&q={keyword.replace(' ', '+')}&format=Atom"

            feed = feedparser.parse(search_url)

            results = []
            for entry in feed.entries[:limit]:
                results.append({
                    'id': entry.get('id', str(uuid4())),
                    'title': entry.get('title', ''),
                    'description': entry.get('description', entry.get('summary', '')),
                    'url': entry.get('link', ''),
                    'published': entry.get('published_parsed'),
                    'author': entry.get('author', 'Unknown'),
                    'keyword': keyword
                })

            return results

        except Exception as e:
            self.logger.error(f"Failed to fetch from RSS Bridge: {e}")
            raise

    def scrape(self, limit: int = None) -> List[Dict[str, Any]]:
        """抓取X(Twitter)热点数据

        优先使用Nitter,失败则fallback到RSS Bridge。

        Args:
            limit: 限制抓取数量(可选,用于测试)

        Returns:
            原始数据字典列表
        """
        results = []

        for keyword in self.search_keywords:
            try:
                # 优先使用Nitter
                tweets = self._scrape_via_nitter(keyword, limit=limit or 10)
                results.extend(tweets)

            except Exception as e:
                self.logger.warning(f"Nitter failed for '{keyword}', trying RSS Bridge: {e}")

                try:
                    # Fallback到RSS Bridge
                    tweets = self._scrape_via_rss_bridge(keyword, limit=limit or 10)
                    results.extend(tweets)

                except Exception as e2:
                    self.logger.error(f"RSS Bridge also failed for '{keyword}': {e2}")
                    continue

            if limit and len(results) >= limit:
                results = results[:limit]
                break

        self.logger.info(f"Scraped {len(results)} tweets")
        return results

    def normalize(self, raw_data: Dict[str, Any]) -> TrendingTopic:
        """将原始数据转换为TrendingTopic模型

        Args:
            raw_data: 原始数据字典

        Returns:
            TrendingTopic对象
        """
        # RSS feed没有详细统计,使用默认热度
        # 实际部署时可以考虑使用Twitter API v2获取互动数据
        heat_score = 50.0  # 默认中等热度

        # 解析发布时间
        published = raw_data.get('published')
        if published:
            from time import mktime
            dt = datetime.fromtimestamp(mktime(published), tz=timezone.utc)
        else:
            dt = datetime.now(timezone.utc)

        # 提取标题和描述
        title = raw_data['title']
        if not title:
            # 如果标题为空,使用描述的前100字符
            title = raw_data['description'][:100]

        return TrendingTopic(
            id=str(uuid4()),
            title=title[:200],  # 限制长度
            description=raw_data['description'][:500],  # 限制长度
            source="X",
            url=raw_data['url'],
            timestamp=dt,
            heat_score=heat_score,
            trend_direction="stable",  # 初始值,后续计算
            tags=["X", "Twitter", raw_data.get('keyword', 'trending')],
            summary_cn="",  # 由LLM生成
            summary_ja="",  # 由LLM生成
            data_quality_score=0.6,  # RSS数据质量中等
            schema_version="1.1"
        )

    def scrape_pain_points(self, limit: int = None) -> List[Dict[str, Any]]:
        """从X(Twitter)抓取痛点相关的推文

        使用特定关键词搜索表达痛点的推文

        Args:
            limit: 限制抓取的推文数量

        Returns:
            推文数据列表,包含text, context_title, source, url, timestamp等字段
        """
        # 痛点相关搜索关键词
        pain_point_keywords = [
            "need a tool for",
            "wish there was a tool",
            "looking for a solution",
            "struggling with",
            "can't find a tool",
            "frustrating that"
        ]

        tweets_data = []
        tweets_per_keyword = (limit or 30) // len(pain_point_keywords)

        for keyword in pain_point_keywords:
            try:
                # 使用Nitter或RSS Bridge抓取
                raw_tweets = []

                # 尝试Nitter
                try:
                    raw_tweets = self._scrape_via_nitter(keyword, limit=tweets_per_keyword)
                except Exception as e:
                    self.logger.warning(f"Nitter失败,尝试RSS Bridge: {e}")
                    try:
                        raw_tweets = self._scrape_via_rss_bridge(keyword, limit=tweets_per_keyword)
                    except Exception as e2:
                        self.logger.error(f"RSS Bridge也失败: {e2}")
                        continue

                # 转换为痛点数据格式
                for tweet in raw_tweets:
                    tweets_data.append({
                        'text': tweet['description'],
                        'context_title': keyword,  # 使用搜索关键词作为上下文
                        'source': 'X',
                        'url': tweet['url'],
                        'timestamp': datetime.fromtimestamp(
                            mktime(tweet['published']),
                            tz=timezone.utc
                        ) if tweet.get('published') else datetime.now(timezone.utc),
                        'engagement_score': 50.0,  # RSS数据无法获取准确互动数
                        'author_metadata': {
                            'username': tweet.get('author', 'Unknown')
                        }
                    })

                    if limit and len(tweets_data) >= limit:
                        break

            except Exception as e:
                self.logger.warning(f"从X提取痛点失败(关键词: {keyword}): {e}")
                continue

            if limit and len(tweets_data) >= limit:
                break

        self.logger.info(f"共从X提取{len(tweets_data)}条痛点推文")
        return tweets_data
