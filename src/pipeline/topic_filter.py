"""
话题过滤器 - 过滤低商业价值的话题

专注于寻找可产品化和变现的AI机会，过滤掉：
- 社区管理事务
- 学术流程通知
- 纯技术细节讨论
- 元讨论和公告
"""

import re
from typing import Optional, Tuple
from src.models.trend import TrendingTopic
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TopicFilter:
    """话题过滤器 - 基于商业价值和相关性过滤话题"""

    # 黑名单关键词（这些话题没有产品化价值）
    BLACKLIST = {
        # 社区管理（招募、管理员、志愿者）
        'community_management': [
            'mods', 'moderator', 'recruit', 'volunteer',
            'apply', 'hiring', 'wanted', 'job posting',
            'resume', 'application', 'who is hiring',
            'who wants to be hired', 'looking for work'
        ],

        # 学术流程（会议、论文、评审）
        'academic_process': [
            'cvpr', 'icml', 'neurips', 'iclr',
            'conference submission', 'openreview',
            'paper submission', 'desk reject',
            'peer review', 'journal', 'publication',
            'author registration', 'reviewer assignment'
        ],

        # 元讨论（社区规则、公告、指南）
        'meta_discussion': [
            'announcement', 'guideline', 'rule',
            'policy', 'how to post', 'subreddit',
            'community rules', 'please read',
            'read before posting', 'faq'
        ],

        # 低价值技术讨论（编程语言内部细节，无产品化价值）
        'low_value_tech': [
            'encoding/json', 'math/rand', 'net/http',
            'standard library', 'stdlib', 'v2 api',
            'codereview', 'gerrit', 'pr workflow',
            'error handling boilerplate', 'syntax proposal',
            'memory regions', 'internal design',
            'http/2 migration', 'library implementation'
        ],

        # 完全无关的话题
        'irrelevant': [
            'artificial womb', 'gamified war',
            'drone pilots', 'ukraine war',
            'cryptocurrency', 'blockchain',
            'philosophy', 'uncomfortable truth'
        ]
    }

    # 黑名单模式（正则表达式）
    BLACKLIST_PATTERNS = [
        r'^\[D\]',           # [D] 开头的讨论帖
        r'^\[Meta\]',        # [Meta] 元讨论
        r'^\[Discussion\]',  # [Discussion] 讨论
        r'^\[P\]',           # [P] 项目展示
        r'encoding/',        # 编码库
        r'math/',            # 数学库
        r'net/',             # 网络库
        r'/v2\b',            # v2 API
        r'CVPR|ICML|NeurIPS|ICLR',  # 学术会议
        r'OpenReview',       # 学术平台
    ]

    def __init__(self):
        """初始化过滤器"""
        # 将所有黑名单关键词展平为单一列表
        self.all_blacklist_keywords = []
        for category, keywords in self.BLACKLIST.items():
            self.all_blacklist_keywords.extend(keywords)

        # 编译正则表达式模式
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.BLACKLIST_PATTERNS
        ]

    def should_filter(self, topic: TrendingTopic) -> Tuple[bool, Optional[str]]:
        """
        判断话题是否应该被过滤

        Args:
            topic: 待检查的话题

        Returns:
            (是否过滤, 过滤原因)
        """
        # 1. 检查标题中的黑名单关键词
        title_lower = topic.title.lower()
        for keyword in self.all_blacklist_keywords:
            if keyword in title_lower:
                return True, f"黑名单关键词: {keyword}"

        # 2. 检查描述中的黑名单关键词（前100字符）
        desc_lower = topic.description[:100].lower()
        for keyword in self.all_blacklist_keywords:
            if keyword in desc_lower:
                return True, f"黑名单关键词: {keyword} (描述)"

        # 3. 检查黑名单模式
        for pattern in self.compiled_patterns:
            if pattern.search(topic.title):
                return True, f"黑名单模式: {pattern.pattern}"

        # 4. 检查商业价值（热度过低且没有明确痛点信号）
        if topic.heat_score < 30 and not self._has_business_value_signal(topic):
            return True, "商业价值过低"

        # 5. 检查话题完整性（标题或描述过短）
        if len(topic.title) < 20:
            return True, "标题过短"

        if len(topic.description) < 30:
            return True, "描述过短"

        return False, None

    def _has_business_value_signal(self, topic: TrendingTopic) -> bool:
        """
        检查话题是否包含商业价值信号

        商业价值信号：
        - 表达付费意愿
        - 描述具体痛点
        - 提到工作流程/效率问题
        """
        business_value_keywords = [
            'would pay', 'will pay', 'need a tool',
            'struggling with', 'waste time', 'waste my time',
            'so frustrating', 'can\'t find', 'looking for',
            'no good solution', 'missing feature',
            'improve productivity', 'save time',
            'automate', 'efficiency', 'workflow'
        ]

        text = (topic.title + ' ' + topic.description).lower()
        return any(keyword in text for keyword in business_value_keywords)

    def filter_topics(self, topics: list[TrendingTopic]) -> Tuple[list[TrendingTopic], dict]:
        """
        批量过滤话题

        Args:
            topics: 话题列表

        Returns:
            (过滤后的话题列表, 统计信息)
        """
        filtered_topics = []
        filter_stats = {
            'total': len(topics),
            'filtered': 0,
            'kept': 0,
            'filter_reasons': {}
        }

        for topic in topics:
            should_filter, reason = self.should_filter(topic)

            if should_filter:
                filter_stats['filtered'] += 1
                filter_stats['filter_reasons'][reason] = \
                    filter_stats['filter_reasons'].get(reason, 0) + 1
                logger.debug(f"过滤话题: {topic.title[:50]}... (原因: {reason})")
            else:
                filtered_topics.append(topic)
                filter_stats['kept'] += 1

        logger.info(
            f"话题过滤完成: 保留 {filter_stats['kept']}/{filter_stats['total']} 个话题"
        )
        logger.info(f"过滤原因统计: {filter_stats['filter_reasons']}")

        return filtered_topics, filter_stats
