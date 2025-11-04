"""相关性匹配模块

将用户痛点与AI工具和热点话题进行匹配,基于:
1. 关键词重叠
2. 语义相似度
3. 时间接近度
"""

from typing import List, Dict, Tuple
from datetime import datetime, timedelta
import logging

from src.models.pain_point import UserPainPoint
from src.models.tool import AITool
from src.models.trend import TrendingTopic
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RelevanceMatcher:
    """相关性匹配器

    根据多个维度(关键词、语义、时间)为每个痛点找到相关的AI工具和热点话题
    """

    def __init__(
        self,
        keyword_weight: float = 0.5,
        time_weight: float = 0.3,
        engagement_weight: float = 0.2
    ):
        """初始化匹配器

        Args:
            keyword_weight: 关键词匹配权重
            time_weight: 时间接近度权重
            engagement_weight: 互动热度权重
        """
        self.keyword_weight = keyword_weight
        self.time_weight = time_weight
        self.engagement_weight = engagement_weight

    def match_pain_points(
        self,
        pain_points: List[UserPainPoint],
        tools: List[AITool],
        topics: List[TrendingTopic],
        max_related_tools: int = 5,
        max_related_topics: int = 3,
        min_relevance_score: float = 0.3
    ) -> List[Dict]:
        """为每个痛点匹配相关的工具和话题

        Args:
            pain_points: 痛点列表
            tools: AI工具列表
            topics: 热点话题列表
            max_related_tools: 每个痛点最多关联的工具数
            max_related_topics: 每个痛点最多关联的话题数
            min_relevance_score: 最小相关性分数阈值

        Returns:
            匹配结果列表,每个元素包含:
                - pain_point: 痛点对象
                - related_tools: 相关工具ID列表
                - related_topics: 相关话题ID列表
                - relevance_scores: 相关性分数字典
        """
        matches = []

        for pain_point in pain_points:
            # 匹配工具
            tool_matches = self._match_tools(pain_point, tools)
            # 过滤并排序
            relevant_tools = [
                (tool_id, score)
                for tool_id, score in tool_matches
                if score >= min_relevance_score
            ]
            relevant_tools.sort(key=lambda x: x[1], reverse=True)
            relevant_tools = relevant_tools[:max_related_tools]

            # 匹配话题
            topic_matches = self._match_topics(pain_point, topics)
            # 过滤并排序
            relevant_topics = [
                (topic_id, score)
                for topic_id, score in topic_matches
                if score >= min_relevance_score
            ]
            relevant_topics.sort(key=lambda x: x[1], reverse=True)
            relevant_topics = relevant_topics[:max_related_topics]

            if relevant_tools or relevant_topics:
                matches.append({
                    'pain_point': pain_point,
                    'related_tools': [tool_id for tool_id, _ in relevant_tools],
                    'related_topics': [topic_id for topic_id, _ in relevant_topics],
                    'relevance_scores': {
                        'tools': {tool_id: score for tool_id, score in relevant_tools},
                        'topics': {topic_id: score for topic_id, score in relevant_topics}
                    }
                })

        logger.info(
            f"匹配完成: {len(pain_points)}个痛点, "
            f"{len([m for m in matches if m['related_tools']])}个有相关工具, "
            f"{len([m for m in matches if m['related_topics']])}个有相关话题"
        )

        return matches

    def _match_tools(
        self,
        pain_point: UserPainPoint,
        tools: List[AITool]
    ) -> List[Tuple[str, float]]:
        """为痛点匹配相关工具

        Args:
            pain_point: 痛点对象
            tools: 工具列表

        Returns:
            (工具ID, 相关性分数)元组列表
        """
        matches = []

        for tool in tools:
            # 计算多维度相关性分数
            keyword_score = self._calculate_keyword_similarity(
                pain_point.extracted_keywords,
                tool.tags + tool.features
            )

            time_score = self._calculate_time_proximity(
                pain_point.timestamp,
                tool.timestamp
            )

            # 对于工具,还考虑功能匹配度
            feature_match_score = self._calculate_feature_match(
                pain_point.extracted_keywords,
                tool.features
            )

            # 综合分数
            relevance_score = (
                keyword_score * self.keyword_weight +
                time_score * self.time_weight +
                feature_match_score * 0.2  # 功能匹配额外加权
            )

            matches.append((tool.id, relevance_score))

        return matches

    def _match_topics(
        self,
        pain_point: UserPainPoint,
        topics: List[TrendingTopic]
    ) -> List[Tuple[str, float]]:
        """为痛点匹配相关话题

        Args:
            pain_point: 痛点对象
            topics: 话题列表

        Returns:
            (话题ID, 相关性分数)元组列表
        """
        matches = []

        for topic in topics:
            # 计算多维度相关性分数
            keyword_score = self._calculate_keyword_similarity(
                pain_point.extracted_keywords,
                topic.tags
            )

            time_score = self._calculate_time_proximity(
                pain_point.timestamp,
                topic.timestamp
            )

            # 考虑话题热度(热度越高,权重越大)
            heat_bonus = min(1.0, topic.heat_score / 100.0) * self.engagement_weight

            # 综合分数
            relevance_score = (
                keyword_score * self.keyword_weight +
                time_score * self.time_weight +
                heat_bonus
            )

            matches.append((topic.id, relevance_score))

        return matches

    def _calculate_keyword_similarity(
        self,
        keywords1: List[str],
        keywords2: List[str]
    ) -> float:
        """计算两个关键词列表的相似度

        使用Jaccard相似系数: |A∩B| / |A∪B|

        Args:
            keywords1: 第一个关键词列表
            keywords2: 第二个关键词列表

        Returns:
            相似度分数 (0-1)
        """
        if not keywords1 or not keywords2:
            return 0.0

        # 转换为小写集合
        set1 = set(kw.lower() for kw in keywords1)
        set2 = set(kw.lower() for kw in keywords2)

        # Jaccard相似度
        intersection = len(set1 & set2)
        union = len(set1 | set2)

        if union == 0:
            return 0.0

        jaccard_score = intersection / union

        # 检查部分匹配(子串匹配)
        partial_matches = sum(
            1 for kw1 in set1
            for kw2 in set2
            if kw1 in kw2 or kw2 in kw1
        )

        # 部分匹配加分(最多0.2)
        partial_bonus = min(0.2, partial_matches * 0.05)

        return min(1.0, jaccard_score + partial_bonus)

    def _calculate_feature_match(
        self,
        pain_keywords: List[str],
        tool_features: List[str]
    ) -> float:
        """计算痛点关键词与工具功能的匹配度

        特别关注功能性关键词(如"generate", "automate", "analyze"等)

        Args:
            pain_keywords: 痛点关键词
            tool_features: 工具功能列表

        Returns:
            匹配分数 (0-1)
        """
        if not pain_keywords or not tool_features:
            return 0.0

        # 功能性动词
        action_verbs = {
            'generate', 'create', 'make', 'build', 'design',
            'automate', 'analyze', 'process', 'convert', 'transform',
            'summarize', 'extract', 'detect', 'recognize', 'classify'
        }

        # 从痛点关键词中提取动作词
        pain_actions = set(
            kw.lower() for kw in pain_keywords
            if any(verb in kw.lower() for verb in action_verbs)
        )

        # 从工具功能中提取动作词
        tool_actions = set(
            feature.lower() for feature in tool_features
            if any(verb in feature.lower() for verb in action_verbs)
        )

        if not pain_actions and not tool_actions:
            # 如果都没有动作词,使用普通关键词匹配
            return self._calculate_keyword_similarity(pain_keywords, tool_features)

        # 计算动作词匹配度
        if pain_actions and tool_actions:
            action_match = len(pain_actions & tool_actions) / max(len(pain_actions), len(tool_actions))
        else:
            action_match = 0.0

        # 整体关键词匹配
        general_match = self._calculate_keyword_similarity(pain_keywords, tool_features)

        # 加权合并(动作匹配更重要)
        return action_match * 0.7 + general_match * 0.3

    def _calculate_time_proximity(
        self,
        timestamp1: datetime,
        timestamp2: datetime,
        max_days: int = 30
    ) -> float:
        """计算时间接近度

        时间越接近,分数越高。超过max_days的分数为0。

        Args:
            timestamp1: 第一个时间戳
            timestamp2: 第二个时间戳
            max_days: 最大相关天数

        Returns:
            时间接近度分数 (0-1)
        """
        time_diff = abs((timestamp1 - timestamp2).total_seconds())
        days_diff = time_diff / (24 * 3600)

        if days_diff > max_days:
            return 0.0

        # 线性衰减: 0天=1.0, max_days=0.0
        return 1.0 - (days_diff / max_days)

    def create_opportunity_candidates(
        self,
        matches: List[Dict]
    ) -> List[Dict]:
        """从匹配结果创建机会候选

        过滤出有足够相关性的匹配,作为Opportunity实体的候选

        Args:
            matches: 匹配结果列表

        Returns:
            机会候选列表,每个元素包含创建Opportunity所需的所有字段
        """
        candidates = []

        for match in matches:
            # 至少要有一个相关工具或话题才算有效机会
            if not match['related_tools'] and not match['related_topics']:
                continue

            # 计算平均相关性分数
            tool_scores = list(match['relevance_scores']['tools'].values())
            topic_scores = list(match['relevance_scores']['topics'].values())

            avg_relevance = (
                (sum(tool_scores) / len(tool_scores) if tool_scores else 0) * 0.6 +
                (sum(topic_scores) / len(topic_scores) if topic_scores else 0) * 0.4
            )

            candidates.append({
                'pain_point_id': match['pain_point'].id,
                'pain_point': match['pain_point'],
                'related_tools': match['related_tools'],
                'related_topics': match['related_topics'],
                'avg_relevance_score': avg_relevance,
                'tags': self._merge_tags(match)
            })

        # 按相关性排序
        candidates.sort(key=lambda x: x['avg_relevance_score'], reverse=True)

        logger.info(f"创建了{len(candidates)}个机会候选")
        return candidates

    def _merge_tags(self, match: Dict) -> List[str]:
        """合并痛点、工具和话题的标签

        Args:
            match: 匹配结果

        Returns:
            合并后的标签列表
        """
        tags = set(match['pain_point'].tags)

        # 这里需要从tools和topics对象中获取tags
        # 因为match只包含ID,实际实现时需要查询对应对象
        # 这里先返回痛点的tags

        return list(tags)
