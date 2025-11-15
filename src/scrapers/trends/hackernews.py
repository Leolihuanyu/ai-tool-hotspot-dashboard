"""Hacker News热点爬虫

从Hacker News抓取高质量的痛点和商业机会，重点关注：
1. Ask HN帖子（用户直接提问痛点和需求）
2. Who is Hiring月度帖子（企业招聘需求 → 业务痛点）
3. Show HN帖子（新产品发布，观察市场反应）

HN官方API文档：https://github.com/HackerNews/API
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone
from uuid import uuid4
import time

from src.scrapers.base import BaseScraper
from src.models.trend import TrendingTopic


class HackerNewsScraper(BaseScraper):
    """Hacker News热点爬虫

    使用HN官方API抓取高价值内容：
    - Ask HN: pain point, idea, MVP等关键词
    - Who is Hiring: 月度招聘帖
    - Show HN: 新产品发布

    数据质量评分：0.95（HN社区质量极高，信噪比优秀）
    """

    def __init__(self):
        super().__init__(
            source_name="Hacker News",
            base_url="https://hacker-news.firebaseio.com/v0"
        )

        # HN API端点
        self.api_base = "https://hacker-news.firebaseio.com/v0"

        # Ask HN关键词（痛点发现）
        self.ask_hn_keywords = [
            "pain point",
            "idea",
            "MVP",
            "startup",
            "looking for",
            "need advice",
            "frustrated",
            "better way",
            "alternative to",
            "problem",
            "solution",
            "build",
            "create",
            "automate"
        ]

        # Who is Hiring关键词（业务痛点）
        self.hiring_keywords = [
            "Who is hiring",
            "Who wants to be hired",
            "Freelancer? Seeking freelancer?"
        ]

        # 付费意愿信号
        self.monetization_signals = [
            "willing to pay",
            "would pay",
            "subscription",
            "pricing",
            "customers",
            "revenue",
            "B2B",
            "SaaS",
            "enterprise"
        ]

    def _fetch_item(self, item_id: int) -> Dict[str, Any]:
        """获取单个HN item（story/comment）

        Args:
            item_id: HN item ID

        Returns:
            Item数据字典
        """
        url = f"{self.api_base}/item/{item_id}.json"
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def _fetch_top_stories(self, story_type: str = "topstories", limit: int = 100) -> List[int]:
        """获取热门story ID列表

        Args:
            story_type: 类型（topstories, newstories, beststories）
            limit: 限制数量

        Returns:
            Story ID列表
        """
        url = f"{self.api_base}/{story_type}.json"
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()

        story_ids = response.json()
        return story_ids[:limit] if limit else story_ids

    def _extract_pain_points_from_hiring_post(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从Who is Hiring帖子中提取业务痛点

        招聘需求 → 反映公司正在解决的问题 → 业务痛点

        Args:
            item: Who is Hiring帖子数据

        Returns:
            提取的痛点列表
        """
        pain_points = []

        # 获取所有评论（每个评论是一个招聘信息）
        kids = item.get('kids', [])

        # 限制处理前50个评论（避免API过载）
        for kid_id in kids[:50]:
            try:
                comment = self._fetch_item(kid_id)

                if not comment or comment.get('deleted') or comment.get('dead'):
                    continue

                text = comment.get('text', '')
                if len(text) < 50:  # 太短的评论跳过
                    continue

                # 提取公司正在解决的问题（招聘岗位描述往往暗示业务方向）
                pain_points.append({
                    'text': text,
                    'context_title': item.get('title', ''),
                    'source': 'Hacker News',
                    'url': f"https://news.ycombinator.com/item?id={kid_id}",
                    'timestamp': datetime.fromtimestamp(
                        comment.get('time', time.time()),
                        tz=timezone.utc
                    ),
                    'engagement_score': 60.0,  # 招聘帖基础评分
                    'type': 'hiring_need'  # 标记为招聘需求
                })

                # API速率限制：延迟100ms
                time.sleep(0.1)

            except Exception as e:
                self.logger.warning(f"提取评论{kid_id}失败: {e}")
                continue

        return pain_points

    def _matches_keywords(self, text: str, keywords: List[str]) -> Tuple[bool, List[str]]:
        """检查文本是否匹配关键词列表

        Args:
            text: 文本内容
            keywords: 关键词列表

        Returns:
            (是否匹配, 匹配到的关键词列表)
        """
        text_lower = text.lower()
        matched = []

        for keyword in keywords:
            if keyword.lower() in text_lower:
                matched.append(keyword)

        return len(matched) > 0, matched

    def scrape(self, limit: int = None) -> List[Dict[str, Any]]:
        """抓取Hacker News热点数据

        Args:
            limit: 限制抓取数量（None=30）

        Returns:
            原始数据字典列表
        """
        limit = limit or 30
        results = []

        self.logger.info("开始抓取Hacker News数据")

        # 1. 获取Top Stories
        top_story_ids = self._fetch_top_stories(story_type="topstories", limit=200)

        # 2. 过滤出Ask HN和Who is Hiring帖子
        for story_id in top_story_ids:
            try:
                item = self._fetch_item(story_id)

                if not item or item.get('deleted') or item.get('dead'):
                    continue

                title = item.get('title', '')
                item_type = item.get('type', '')

                # 只处理story类型
                if item_type != 'story':
                    continue

                # 检查类型和关键词
                title_lower = title.lower()
                is_ask_hn = title_lower.startswith('ask hn')
                is_show_hn = title_lower.startswith('show hn')
                has_keywords, matched_kw = self._matches_keywords(title, self.ask_hn_keywords)
                is_hiring, _ = self._matches_keywords(title, self.hiring_keywords)

                # 获取互动指标
                score = item.get('score', 0)
                num_comments = item.get('descendants', 0)
                high_engagement = (score >= 50 or num_comments >= 20)

                # 放宽过滤条件：
                # 1) Ask HN帖子（不要求关键词，高互动即可）
                # 2) Show HN帖子（新产品发布）
                # 3) 高热度帖子且包含关键词
                # 4) Who is Hiring
                should_include = False
                post_type = 'story'

                if is_ask_hn:
                    # Ask HN帖子：只要有合理互动就收录
                    if num_comments >= 10:  # 至少10条评论
                        should_include = True
                        post_type = 'ask_hn'
                elif is_show_hn:
                    # Show HN帖子：新产品发布
                    should_include = True
                    post_type = 'show_hn'
                elif is_hiring:
                    # Who is Hiring
                    should_include = True
                    post_type = 'who_is_hiring'
                elif high_engagement and has_keywords:
                    # 高热度+关键词匹配
                    should_include = True
                    post_type = 'trending'

                if should_include:
                    results.append({
                        'id': str(story_id),
                        'title': title,
                        'text': item.get('text', '') if post_type != 'who_is_hiring'
                                else f"Monthly hiring thread with {num_comments} job postings",
                        'url': item.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                        'score': score,
                        'num_comments': num_comments,
                        'created_time': item.get('time'),
                        'author': item.get('by', 'Unknown'),
                        'matched_keywords': matched_kw if matched_kw else (['hiring'] if is_hiring else []),
                        'type': post_type,
                        'hn_id': story_id
                    })

                # API速率限制
                time.sleep(0.05)

                if len(results) >= limit:
                    break

            except Exception as e:
                self.logger.warning(f"处理story {story_id}失败: {e}")
                continue

        self.logger.info(f"共从Hacker News抓取{len(results)}条数据")
        return results

    def scrape_pain_points(self, limit: int = None) -> List[Dict[str, Any]]:
        """从HN抓取痛点数据（包括Ask HN评论和Who is Hiring）

        Args:
            limit: 限制抓取数量

        Returns:
            痛点数据列表
        """
        limit = limit or 50
        pain_points = []

        self.logger.info("从Hacker News抓取痛点数据")

        # 1. 获取Ask HN帖子的评论
        stories = self.scrape(limit=20)

        for story in stories:
            if story['type'] == 'ask_hn':
                # 获取Ask HN帖子的评论
                try:
                    item = self._fetch_item(story['hn_id'])
                    kids = item.get('kids', [])

                    # 前10个评论
                    for kid_id in kids[:10]:
                        try:
                            comment = self._fetch_item(kid_id)

                            if not comment or comment.get('deleted') or comment.get('dead'):
                                continue

                            text = comment.get('text', '')
                            if len(text) < 30:
                                continue

                            # 检查付费意愿
                            has_monetization, mon_kw = self._matches_keywords(
                                text, self.monetization_signals
                            )

                            pain_points.append({
                                'text': text,
                                'context_title': story['title'],
                                'source': 'Hacker News',
                                'url': f"https://news.ycombinator.com/item?id={kid_id}",
                                'timestamp': datetime.fromtimestamp(
                                    comment.get('time', time.time()),
                                    tz=timezone.utc
                                ),
                                'engagement_score': min(100.0, comment.get('score', 0) * 5.0),
                                'payment_willingness_score': 50.0 if has_monetization else 20.0,
                                'matched_keywords': mon_kw,
                                'type': 'ask_hn_comment'
                            })

                            time.sleep(0.1)

                            if len(pain_points) >= limit:
                                break

                        except Exception as e:
                            self.logger.warning(f"处理评论{kid_id}失败: {e}")
                            continue

                    if len(pain_points) >= limit:
                        break

                except Exception as e:
                    self.logger.warning(f"处理story {story['hn_id']}评论失败: {e}")
                    continue

            elif story['type'] == 'who_is_hiring':
                # 从Who is Hiring中提取业务痛点
                item = self._fetch_item(story['hn_id'])
                hiring_pain_points = self._extract_pain_points_from_hiring_post(item)
                pain_points.extend(hiring_pain_points)

                if len(pain_points) >= limit:
                    break

        self.logger.info(f"共从Hacker News提取{len(pain_points)}条痛点")

        # 按engagement分数排序
        pain_points.sort(key=lambda x: x['engagement_score'], reverse=True)

        return pain_points[:limit]

    def normalize(self, raw_data: Dict[str, Any]) -> TrendingTopic:
        """将原始数据转换为TrendingTopic模型

        Args:
            raw_data: 原始数据字典

        Returns:
            TrendingTopic对象
        """
        # 计算热度分数（HN的分数权重更高）
        score = raw_data.get('score', 0)
        num_comments = raw_data.get('num_comments', 0)

        # HN热度计算：score*0.5 + comments*2，归一化到0-100
        # 假设200分+50评论 = 100分
        heat_score = min(100.0, (score * 0.5 + num_comments * 2) / 3)

        # 解析时间戳
        created_time = raw_data.get('created_time')
        if created_time:
            dt = datetime.fromtimestamp(created_time, tz=timezone.utc)
        else:
            dt = datetime.now(timezone.utc)

        # 标题和描述
        title = raw_data['title']
        text = raw_data.get('text', '')
        description = f"{title}\n\n{text}" if text else title

        # 标签
        tags = ["Hacker News", raw_data.get('type', 'story')]
        if raw_data.get('matched_keywords'):
            tags.extend(raw_data['matched_keywords'][:3])  # 添加最多3个关键词

        return TrendingTopic(
            id=str(uuid4()),
            title=title[:200],
            description=description[:1500],
            source="Hacker News",
            url=raw_data['url'],
            timestamp=dt,
            heat_score=heat_score,
            trend_direction="stable",
            tags=tags,
            summary_cn="",  # 由LLM生成
            summary_ja="",  # 由LLM生成
            data_quality_score=0.95,  # HN数据质量极高
            schema_version="1.1"
        )
