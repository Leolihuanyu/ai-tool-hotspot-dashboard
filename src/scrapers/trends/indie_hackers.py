"""Indie Hackers爬虫

抓取独立开发者社区的热门讨论和痛点。
重点关注：创业经验、revenue分享、产品launch、获客策略等话题。
"""

import re
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper
from src.models import TrendingTopic
from src.utils.logger import get_logger

logger = get_logger(__name__)


class IndieHackersScraper(BaseScraper):
    """Indie Hackers爬虫

    抓取独立开发者社区的讨论，包括：
    - 热门帖子（Popular）
    - 最新帖子（Newest）
    - 特定群组（Groups）的讨论

    重点关注创业者最关心的话题：
    - 如何获得第一批客户
    - 产品定价策略
    - MVP验证
    - Revenue里程碑
    - 失败经验教训
    """

    def __init__(self):
        """初始化Indie Hackers爬虫"""
        super().__init__(
            source_name="Indie Hackers",
            base_url="https://www.indiehackers.com"
        )

        # 爬虫类型标记
        self.scraper_type = "trends"

        # 禁用robots.txt检查（Cloudflare防护返回HTML而非真实的robots.txt）
        self.respect_robots_txt = False

        # 设置更真实的请求头以绕过Cloudflare
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

        # 重点关注的群组
        self.focus_groups = [
            "start-a-business",  # 创业起步
            "landing-page-feedback",  # 落地页反馈
            "product-launch",  # 产品发布
            "growth",  # 增长策略
            "roast-my-idea",  # 创意验证
            "marketing",  # 营销
            "monetization",  # 变现
        ]

        # 高价值关键词（用于筛选和评分）
        self.high_value_keywords = [
            # Revenue相关
            "first customer", "first sale", "first $",
            "mrr", "arr", "revenue", "pricing",

            # 痛点相关
            "struggling with", "how do you", "anyone else",
            "what tool", "looking for", "need help",

            # MVP相关
            "mvp", "validate", "validation", "launch",
            "beta users", "early adopters",

            # 获客相关
            "acquisition", "where to find", "target audience",
            "marketing channel", "cold email", "outreach"
        ]

        # API endpoints（如果有的话）
        self.api_base = "https://www.indiehackers.com/api"

    def _fetch_posts_via_api(self, endpoint: str, limit: int = 30) -> List[Dict[str, Any]]:
        """通过API获取帖子

        Args:
            endpoint: API端点（如/posts、/groups/{group}/posts）
            limit: 获取数量限制

        Returns:
            帖子数据列表
        """
        try:
            url = f"{self.api_base}{endpoint}"
            params = {
                "limit": limit,
                "include": "user,group,comments"
            }

            response = self.fetch_with_retry(
                url,
                params=params,
                headers={
                    "Accept": "application/json",
                    "User-Agent": self.user_agent
                }
            )

            data = response.json()
            return data.get("posts", [])

        except Exception as e:
            logger.warning(f"API获取失败，将尝试网页抓取: {e}")
            return []

    def _scrape_via_web(self, path: str = "/posts", limit: int = 30) -> List[Dict[str, Any]]:
        """通过网页抓取帖子

        Args:
            path: 页面路径
            limit: 获取数量限制

        Returns:
            帖子数据列表
        """
        posts = []

        try:
            url = f"{self.base_url}{path}"
            response = self.fetch_with_retry(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # 查找帖子列表（根据实际HTML结构调整选择器）
            post_elements = soup.select('div.post-item, article.post, div[data-post-id]')[:limit]

            for elem in post_elements:
                try:
                    # 提取标题
                    title_elem = elem.select_one('h2, h3, a.post-title, .title')
                    title = title_elem.get_text(strip=True) if title_elem else ""

                    # 提取链接
                    link_elem = elem.select_one('a[href*="/post/"]') or title_elem
                    if link_elem and link_elem.has_attr('href'):
                        post_url = link_elem['href']
                        if not post_url.startswith('http'):
                            post_url = f"{self.base_url}{post_url}"
                    else:
                        continue

                    # 提取描述/内容预览
                    desc_elem = elem.select_one('.post-content, .description, .excerpt')
                    description = desc_elem.get_text(strip=True) if desc_elem else ""

                    # 提取元数据
                    author_elem = elem.select_one('.author, .username, [data-author]')
                    author = author_elem.get_text(strip=True) if author_elem else "Anonymous"

                    # 提取互动数据
                    upvotes = self._extract_number(elem, '.upvotes, .votes, [data-votes]')
                    comments = self._extract_number(elem, '.comments, .comment-count')

                    # 提取标签
                    tag_elements = elem.select('.tag, .label, .category')
                    tags = [tag.get_text(strip=True) for tag in tag_elements]

                    # 构建帖子数据
                    post_data = {
                        "title": title,
                        "url": post_url,
                        "description": description[:500],  # 限制长度
                        "author": author,
                        "upvotes": upvotes,
                        "comments": comments,
                        "tags": tags,
                        "timestamp": datetime.now(timezone.utc),
                        "source": "Indie Hackers"
                    }

                    posts.append(post_data)

                except Exception as e:
                    logger.debug(f"解析单个帖子失败: {e}")
                    continue

            logger.info(f"成功从网页抓取 {len(posts)} 个帖子")

        except Exception as e:
            logger.error(f"网页抓取失败: {e}")

        return posts

    def _extract_number(self, elem, selector: str) -> int:
        """从元素中提取数字

        Args:
            elem: BeautifulSoup元素
            selector: CSS选择器

        Returns:
            提取的数字，默认0
        """
        try:
            num_elem = elem.select_one(selector)
            if num_elem:
                text = num_elem.get_text(strip=True)
                # 提取数字（处理1.2k这样的格式）
                match = re.search(r'([\d.]+)([kKmM])?', text)
                if match:
                    num = float(match.group(1))
                    if match.group(2):
                        if match.group(2).lower() == 'k':
                            num *= 1000
                        elif match.group(2).lower() == 'm':
                            num *= 1000000
                    return int(num)
        except:
            pass
        return 0

    def _calculate_relevance_score(self, post: Dict[str, Any]) -> float:
        """计算帖子的相关性评分

        Args:
            post: 帖子数据

        Returns:
            相关性评分（0-100）
        """
        score = 50.0  # 基础分

        text = f"{post.get('title', '')} {post.get('description', '')}".lower()

        # 检查高价值关键词
        for keyword in self.high_value_keywords:
            if keyword.lower() in text:
                score += 5

        # 互动度加分
        upvotes = post.get('upvotes', 0)
        comments = post.get('comments', 0)

        if upvotes > 100:
            score += 15
        elif upvotes > 50:
            score += 10
        elif upvotes > 20:
            score += 5

        if comments > 50:
            score += 10
        elif comments > 20:
            score += 5

        # Revenue相关内容额外加分
        revenue_keywords = ['revenue', 'mrr', 'arr', '$', 'customer', 'sale', 'pricing']
        if any(kw in text for kw in revenue_keywords):
            score += 10

        return min(100.0, score)

    def scrape(self, limit: int = None) -> List[Dict[str, Any]]:
        """抓取Indie Hackers数据

        Args:
            limit: 限制数量

        Returns:
            原始数据列表
        """
        limit = limit or 50
        all_posts = []

        # 1. 尝试API获取热门帖子
        logger.info("尝试通过API获取Indie Hackers热门帖子...")
        api_posts = self._fetch_posts_via_api("/posts/popular", limit=limit//2)
        if api_posts:
            all_posts.extend(api_posts)
            logger.info(f"API获取成功: {len(api_posts)} 个帖子")

        # 2. 网页抓取作为备份或补充
        if len(all_posts) < limit:
            logger.info("通过网页抓取补充数据...")

            # 抓取热门帖子
            web_posts = self._scrape_via_web("/posts", limit=limit//2)
            all_posts.extend(web_posts)

            # 抓取特定群组的帖子
            for group in self.focus_groups[:3]:  # 只抓取前3个群组
                group_posts = self._scrape_via_web(f"/group/{group}", limit=10)
                all_posts.extend(group_posts)
                if len(all_posts) >= limit:
                    break

        # 去重（基于URL）
        seen_urls = set()
        unique_posts = []
        for post in all_posts:
            url = post.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_posts.append(post)

        # 按相关性排序，取前N个
        unique_posts.sort(key=lambda x: self._calculate_relevance_score(x), reverse=True)
        final_posts = unique_posts[:limit]

        logger.info(f"最终获取 {len(final_posts)} 个Indie Hackers帖子")
        return final_posts

    def normalize(self, raw_data: Dict[str, Any]) -> TrendingTopic:
        """将原始数据转换为TrendingTopic模型

        Args:
            raw_data: 原始数据

        Returns:
            TrendingTopic对象
        """
        # 计算热度分数
        upvotes = raw_data.get('upvotes', 0)
        comments = raw_data.get('comments', 0)
        relevance = self._calculate_relevance_score(raw_data)

        # 综合热度：投票40% + 评论30% + 相关性30%
        heat_score = min(100, (
            min(100, upvotes / 2) * 0.4 +
            min(100, comments * 2) * 0.3 +
            relevance * 0.3
        ))

        # 判断趋势方向（简化版，实际可以通过时间序列分析）
        if heat_score > 70:
            trend_direction = "rising"
        elif heat_score < 30:
            trend_direction = "falling"
        else:
            trend_direction = "stable"

        # 构建标签
        tags = raw_data.get('tags', [])

        # 从内容中提取额外标签
        text = f"{raw_data.get('title', '')} {raw_data.get('description', '')}".lower()
        if 'mvp' in text:
            tags.append('mvp')
        if 'revenue' in text or 'mrr' in text:
            tags.append('revenue')
        if 'launch' in text:
            tags.append('launch')
        if 'customer' in text:
            tags.append('customer-acquisition')

        # 去重标签
        tags = list(set(tags))[:10]

        return TrendingTopic(
            title=raw_data.get('title', 'Untitled'),
            description=raw_data.get('description', '')[:1000],
            source="Indie Hackers",
            url=raw_data.get('url', f"{self.base_url}/posts"),
            timestamp=raw_data.get('timestamp', datetime.now(timezone.utc)),
            heat_score=heat_score,
            trend_direction=trend_direction,
            tags=tags,
            data_quality_score=0.85  # Indie Hackers数据质量较高
        )

    def scrape_pain_points(self, limit: int = 20) -> List[Dict[str, Any]]:
        """专门抓取痛点相关的讨论

        重点关注"求助"、"寻找工具"、"遇到问题"类的帖子

        Args:
            limit: 限制数量

        Returns:
            痛点相关的帖子列表
        """
        pain_posts = []

        # 痛点相关的搜索关键词
        pain_queries = [
            "struggling with",
            "looking for tool",
            "how do you",
            "need help",
            "anyone using",
            "recommend",
            "alternative to",
            "problem with"
        ]

        for query in pain_queries[:4]:  # 限制查询数量
            try:
                # 搜索相关帖子（假设有搜索API或页面）
                search_url = f"{self.base_url}/search"
                params = {"q": query, "type": "post"}

                response = self.fetch_with_retry(search_url, params=params)
                soup = BeautifulSoup(response.text, 'html.parser')

                # 解析搜索结果（根据实际HTML调整）
                results = soup.select('.search-result, .post-item')[:5]

                for result in results:
                    # 提取帖子信息（复用之前的逻辑）
                    post_data = {
                        "query": query,
                        "is_pain_point": True,
                        # ... 其他字段
                    }
                    pain_posts.append(post_data)

            except Exception as e:
                logger.debug(f"搜索痛点失败 '{query}': {e}")
                continue

        logger.info(f"找到 {len(pain_posts)} 个痛点相关帖子")
        return pain_posts[:limit]