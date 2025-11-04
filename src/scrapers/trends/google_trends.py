"""Google Trends热点爬虫

从Google Trends抓取热点搜索话题。
基于research.md推荐,使用pytrends非官方库。
"""

from typing import List, Dict, Any
from datetime import datetime, timezone
from uuid import uuid4

from src.scrapers.base import BaseScraper
from src.models.trend import TrendingTopic


class GoogleTrendsScraper(BaseScraper):
    """Google Trends热点爬虫

    使用pytrends非官方库抓取Google搜索趋势数据。
    注意:Google Trends有严格的速率限制,需要谨慎使用。
    """

    def __init__(self):
        super().__init__(
            source_name="Google Trends",
            base_url="https://trends.google.com"
        )

        # AI相关搜索关键词
        self.search_keywords = [
            "AI tools",
            "ChatGPT",
            "artificial intelligence",
            "machine learning",
            "LLM"
        ]

        # 初始化pytrends
        self._init_pytrends()

    def _init_pytrends(self):
        """初始化pytrends客户端"""
        try:
            from pytrends.request import TrendReq
        except ImportError:
            raise ImportError("pytrends not installed. Run: pip install pytrends")

        try:
            # 初始化TrendReq
            # hl: Host Language, tz: Timezone
            # 注意：移除了retries和backoff_factor参数以兼容新版urllib3
            self.pytrends = TrendReq(
                hl='en-US',
                tz=360,
                timeout=(10, 25)  # Connect and read timeout
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize pytrends: {e}")
            raise

    def _get_trending_searches(self, geo: str = 'united_states') -> List[Dict[str, Any]]:
        """获取趋势搜索

        Args:
            geo: 地理位置(country code或区域名)

        Returns:
            趋势搜索数据列表
        """
        try:
            # 获取今日趋势搜索
            trending_searches_df = self.pytrends.trending_searches(pn=geo)

            results = []
            for search_term in trending_searches_df[0].tolist():
                results.append({
                    'keyword': search_term,
                    'geo': geo,
                    'type': 'trending_search'
                })

            return results

        except Exception as e:
            self.logger.warning(f"Failed to get trending searches for {geo}: {e}")
            return []

    def _get_interest_over_time(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """获取关键词的搜索热度随时间变化

        Args:
            keywords: 搜索关键词列表(最多5个)

        Returns:
            热度数据列表
        """
        try:
            # 构建搜索payload
            # timeframe: 'today 1-m'(过去1个月), 'today 3-m'(过去3个月)
            self.pytrends.build_payload(
                keywords,
                cat=0,  # 类别:0=所有类别
                timeframe='today 1-m',  # 过去1个月
                geo='',  # 全球
                gprop=''  # Google property: '' = web search
            )

            # 获取随时间变化的热度
            interest_over_time_df = self.pytrends.interest_over_time()

            if interest_over_time_df.empty:
                return []

            results = []

            # 获取最近的数据点
            latest_data = interest_over_time_df.iloc[-1]

            for keyword in keywords:
                if keyword in latest_data:
                    # 获取当前和上周的热度值计算趋势
                    current_value = latest_data[keyword]

                    # 计算过去7天的平均值作为对比
                    historical_avg = interest_over_time_df[keyword].iloc[-7:].mean()

                    # 计算趋势方向
                    if current_value > historical_avg * 1.2:
                        trend_direction = "rising"
                    elif current_value < historical_avg * 0.8:
                        trend_direction = "falling"
                    else:
                        trend_direction = "stable"

                    results.append({
                        'keyword': keyword,
                        'heat_score': int(current_value),  # Google Trends使用0-100刻度
                        'trend_direction': trend_direction,
                        'type': 'interest_over_time'
                    })

            return results

        except Exception as e:
            self.logger.warning(f"Failed to get interest over time: {e}")
            return []

    def _get_related_queries(self, keyword: str) -> List[Dict[str, Any]]:
        """获取相关查询

        Args:
            keyword: 搜索关键词

        Returns:
            相关查询数据列表
        """
        try:
            # 构建搜索payload
            self.pytrends.build_payload(
                [keyword],
                cat=0,
                timeframe='today 1-m',
                geo='',
                gprop=''
            )

            # 获取相关查询
            related_queries_dict = self.pytrends.related_queries()

            if keyword not in related_queries_dict:
                return []

            results = []

            # 获取rising queries(上升查询)
            rising_df = related_queries_dict[keyword]['rising']
            if rising_df is not None and not rising_df.empty:
                for _, row in rising_df.head(5).iterrows():  # 取前5个
                    results.append({
                        'keyword': row['query'],
                        'value': row['value'],  # 上升百分比或"Breakout"
                        'type': 'rising_query',
                        'parent_keyword': keyword
                    })

            return results

        except Exception as e:
            self.logger.warning(f"Failed to get related queries for '{keyword}': {e}")
            return []

    def scrape(self, limit: int = None) -> List[Dict[str, Any]]:
        """抓取Google Trends热点数据

        Args:
            limit: 限制抓取数量(可选,用于测试)

        Returns:
            原始数据字典列表
        """
        results = []

        # 1. 获取美国和日本的趋势搜索
        for geo in ['united_states', 'japan']:
            trending = self._get_trending_searches(geo=geo)
            results.extend(trending)

            if limit and len(results) >= limit:
                results = results[:limit]
                return results

        # 2. 获取预定义关键词的热度
        # pytrends限制:每次最多5个关键词
        for i in range(0, len(self.search_keywords), 5):
            batch = self.search_keywords[i:i+5]
            interest_data = self._get_interest_over_time(batch)
            results.extend(interest_data)

            if limit and len(results) >= limit:
                results = results[:limit]
                return results

        # 3. 获取相关上升查询(可选)
        for keyword in self.search_keywords[:2]:  # 只查询前2个关键词以节省API配额
            related = self._get_related_queries(keyword)
            results.extend(related)

            if limit and len(results) >= limit:
                results = results[:limit]
                break

        self.logger.info(f"Scraped {len(results)} Google Trends items")
        return results

    def normalize(self, raw_data: Dict[str, Any]) -> TrendingTopic:
        """将原始数据转换为TrendingTopic模型

        Args:
            raw_data: 原始数据字典

        Returns:
            TrendingTopic对象
        """
        keyword = raw_data['keyword']
        data_type = raw_data.get('type', 'unknown')

        # 热度分数
        heat_score = float(raw_data.get('heat_score', 50.0))  # 默认50分

        # 趋势方向
        trend_direction = raw_data.get('trend_direction', 'stable')

        # 构建标题和描述
        if data_type == 'trending_search':
            title = f"Trending: {keyword}"
            description = f"Currently trending search term in {raw_data.get('geo', 'global')}"
        elif data_type == 'interest_over_time':
            title = f"Search Interest: {keyword}"
            description = f"Search interest for '{keyword}' over the past month"
        elif data_type == 'rising_query':
            title = f"Rising: {keyword}"
            description = f"Rising query related to '{raw_data.get('parent_keyword', '')}'"
        else:
            title = keyword
            description = f"Google Trends data for '{keyword}'"

        # Google Trends URL
        url = f"https://trends.google.com/trends/explore?q={keyword.replace(' ', '+')}"

        return TrendingTopic(
            id=str(uuid4()),
            title=title[:200],
            description=description[:500],
            source="Google Trends",
            url=url,
            timestamp=datetime.now(timezone.utc),
            heat_score=heat_score,
            trend_direction=trend_direction,
            tags=["Google Trends", keyword, data_type],
            summary_cn="",  # 由LLM生成
            summary_ja="",  # 由LLM生成
            data_quality_score=0.85,  # Google官方数据,质量高
            schema_version="1.1"
        )
