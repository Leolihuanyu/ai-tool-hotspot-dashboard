"""Stack Overflow痛点爬虫

从Stack Overflow抓取高票未解决问题，识别开发者真实技术痛点。
使用StackExchange API（免费，每日10000次请求）。
"""

import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from src.scrapers.base import BaseScraper
from src.utils.logger import get_logger

logger = get_logger(__name__)


class StackOverflowPainScraper(BaseScraper):
    """Stack Overflow痛点爬虫

    抓取高票未解决的技术问题，识别开发者工具需求。
    重点关注：
    - 自动化需求（automation, workflow）
    - API集成痛点（api, integration）
    - 开发工具需求（tooling, devtools）
    - 数据处理痛点（data-analysis, parsing）
    """

    def __init__(self):
        """初始化Stack Overflow爬虫"""
        super().__init__(
            source_name="Stack Overflow",
            base_url="https://api.stackexchange.com/2.3"
        )

        # 爬虫类型
        self.scraper_type = "pain_points"

        # 目标标签（与AI工具开发相关）
        self.target_tags = [
            # AI/ML相关
            'python',
            'api',
            'automation',
            'web-scraping',
            'data-analysis',
            'machine-learning',
            'nlp',
            'chatgpt',

            # 开发工具相关
            'workflow',
            'ci-cd',
            'testing',
            'deployment',

            # 数据处理
            'pandas',
            'data-processing',
            'csv',
            'json'
        ]

        # 痛点关键词（标题中包含这些词的问题更可能是真实痛点）
        self.pain_keywords = [
            'automate', 'automatically',
            'easier way', 'better way',
            'reduce', 'simplify',
            'without manually',
            'time-consuming', 'tedious',
            'alternative to',
            'tool for', 'library for',
            'how to efficiently'
        ]

    def scrape(self) -> List[Dict[str, Any]]:
        """抓取Stack Overflow高价值痛点问题

        Returns:
            问题列表
        """
        logger.info("开始从Stack Overflow抓取技术痛点")

        all_questions = []

        # 从每个标签抓取top问题
        for tag in self.target_tags[:5]:  # 先从前5个标签开始
            questions = self._fetch_questions_by_tag(tag, pagesize=10)
            all_questions.extend(questions)

            if len(all_questions) >= 30:  # 限制总数
                break

        logger.info(f"Stack Overflow抓取完成: {len(all_questions)}条技术痛点")
        return all_questions

    def _fetch_questions_by_tag(
        self,
        tag: str,
        pagesize: int = 10
    ) -> List[Dict[str, Any]]:
        """按标签获取问题

        Args:
            tag: 标签名
            pagesize: 每页数量

        Returns:
            问题列表
        """
        # StackExchange API endpoint
        url = f"{self.base_url}/questions"

        # 计算30天前的时间戳
        from_date = int((datetime.now(timezone.utc) - timedelta(days=30)).timestamp())

        params = {
            'order': 'desc',
            'sort': 'votes',  # 按投票数排序
            'tagged': tag,
            'site': 'stackoverflow',
            'pagesize': pagesize,
            'filter': 'withbody',  # 包含问题正文
            'fromdate': from_date,  # 只抓取最近30天
            'accepted': False,  # 未解决的问题（更可能是痛点）
            'key': 'U4DMV*8nvpm3EOpvf69Rxw(('  # 公开key（提高配额）
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            questions = []
            for item in data.get('items', []):
                # 计算痛点相关性
                pain_relevance = self._calculate_pain_relevance(
                    item.get('title', ''),
                    item.get('body', '')
                )

                # 只保留痛点相关性>20分的问题
                if pain_relevance >= 20:
                    questions.append({
                        'id': str(item.get('question_id')),
                        'title': item.get('title', ''),
                        'body': item.get('body', '')[:1500],  # 限制长度
                        'url': item.get('link', ''),
                        'score': item.get('score', 0),
                        'view_count': item.get('view_count', 0),
                        'answer_count': item.get('answer_count', 0),
                        'creation_date': item.get('creation_date'),
                        'tags': item.get('tags', []),
                        'pain_relevance': pain_relevance  # 痛点相关性评分
                    })
                else:
                    logger.debug(f"过滤低痛点相关性问题: {item.get('title', '')[:50]}...")

            logger.info(f"标签 [{tag}]: 抓取到 {len(questions)} 个高痛点相关性问题")
            return questions

        except Exception as e:
            logger.error(f"Stack Overflow API调用失败 (标签:{tag}): {e}")
            return []

    def _calculate_pain_relevance(self, title: str, body: str) -> float:
        """计算痛点相关性评分

        Args:
            title: 问题标题
            body: 问题正文

        Returns:
            痛点相关性评分 (0-100)
        """
        text = f"{title} {body}".lower()
        score = 0.0

        # 检查痛点关键词
        for keyword in self.pain_keywords:
            if keyword in text:
                score += 20
                break  # 找到一个即可

        # 额外加分：标题包含"how to"且是问题（不是教程）
        if 'how to' in title.lower() or 'how can' in title.lower():
            score += 15

        # 额外加分：提到工具/库需求
        if 'tool' in text or 'library' in text or 'package' in text:
            score += 10

        # 额外加分：提到效率/性能优化
        if 'efficiently' in text or 'faster' in text or 'optimize' in text:
            score += 10

        return min(100.0, score)


# 全局实例
default_stackoverflow_scraper = StackOverflowPainScraper()
