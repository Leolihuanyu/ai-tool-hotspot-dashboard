"""趋势评分和方向计算

计算热点话题的趋势方向(rising/falling/stable)和趋势速度。
遵循data-model.md的TR-025功能需求和评分算法。
"""

from typing import List, Dict
from datetime import datetime, timedelta
from src.models.trend import TrendingTopic
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TrendingScorer:
    """趋势评分器

    负责计算:
    1. 趋势方向(trend_direction): rising/falling/stable
    2. 趋势速度(trend_velocity): 热度增长率百分比
    3. 综合趋势分数(trending_score): 0-10分
    """

    def __init__(self):
        """初始化趋势评分器"""
        pass

    def calculate_trend_direction(
        self,
        current_topic: TrendingTopic,
        historical_topics: List[TrendingTopic]
    ) -> str:
        """计算趋势方向

        对比当前热度与24小时前热度,判断趋势方向。
        遵循data-model.md第134-143行的算法。

        Args:
            current_topic: 当前话题
            historical_topics: 历史话题列表(同一话题的历史记录)

        Returns:
            "rising", "falling", 或 "stable"
        """
        if not historical_topics:
            # 无历史数据,默认stable
            return "stable"

        # 查找24小时前的数据
        cutoff_time = current_topic.timestamp - timedelta(hours=24)

        historical_heat = []
        for topic in historical_topics:
            if topic.timestamp >= cutoff_time and topic.timestamp < current_topic.timestamp:
                historical_heat.append(topic.heat_score)

        if not historical_heat:
            # 无24小时内的历史数据,默认stable
            return "stable"

        # 计算历史平均热度
        avg_historical_heat = sum(historical_heat) / len(historical_heat)
        current_heat = current_topic.heat_score

        # 判断趋势方向(阈值:20%)
        if current_heat > avg_historical_heat * 1.2:
            return "rising"
        elif current_heat < avg_historical_heat * 0.8:
            return "falling"
        else:
            return "stable"

    def calculate_trend_velocity(
        self,
        current_topic: TrendingTopic,
        historical_topics: List[TrendingTopic]
    ) -> float:
        """计算趋势速度

        计算热度增长率百分比。

        Args:
            current_topic: 当前话题
            historical_topics: 历史话题列表

        Returns:
            增长率百分比(如35.2表示35.2%增长)
        """
        if not historical_topics:
            return 0.0

        # 查找24小时前的数据
        cutoff_time = current_topic.timestamp - timedelta(hours=24)

        historical_heat = []
        for topic in historical_topics:
            if topic.timestamp >= cutoff_time and topic.timestamp < current_topic.timestamp:
                historical_heat.append(topic.heat_score)

        if not historical_heat:
            return 0.0

        avg_historical_heat = sum(historical_heat) / len(historical_heat)

        if avg_historical_heat == 0:
            # 避免除零
            return 0.0

        # 计算增长率百分比
        velocity = ((current_topic.heat_score - avg_historical_heat) / avg_historical_heat) * 100

        return round(velocity, 2)

    def calculate_trending_score(
        self,
        topic: TrendingTopic,
        cross_platform_count: int = 1
    ) -> float:
        """计算综合趋势分数

        基于research.md第471-483行的评分算法:
        - 社交信号(engagement_score): heat_score * 0.4
        - 时间速度(velocity_score): trend_velocity归一化 * 0.3
        - 跨平台动量(cross_platform_score): 平台数量归一化 * 0.3

        Args:
            topic: 话题对象
            cross_platform_count: 跨平台出现次数(默认1)

        Returns:
            趋势分数(0-10)
        """
        # 1. 社交信号(基于热度)
        # heat_score已经是0-100,归一化到0-10
        engagement_score = (topic.heat_score / 100) * 10

        # 2. 时间速度(基于trend_velocity)
        # 假设50%增长 = 满分10
        velocity = getattr(topic, 'trend_velocity', 0.0)
        velocity_score = min(10.0, abs(velocity) / 50 * 10)

        # 3. 跨平台动量
        # 假设3个平台 = 满分10
        cross_platform_score = min(10.0, cross_platform_count / 3 * 10)

        # 综合分数
        trending_score = (
            engagement_score * 0.4 +
            velocity_score * 0.3 +
            cross_platform_score * 0.3
        )

        return round(trending_score, 2)

    def update_trending_topics(
        self,
        current_topics: List[TrendingTopic],
        historical_data: Dict[str, List[TrendingTopic]]
    ) -> List[TrendingTopic]:
        """批量更新话题的趋势信息

        Args:
            current_topics: 当前话题列表
            historical_data: 历史数据字典,key为话题标题,value为历史记录列表

        Returns:
            更新后的话题列表
        """
        updated_topics = []

        for topic in current_topics:
            # 获取历史数据
            historical = historical_data.get(topic.title, [])

            # 计算趋势方向
            trend_direction = self.calculate_trend_direction(topic, historical)

            # 计算趋势速度
            trend_velocity = self.calculate_trend_velocity(topic, historical)

            # 检查是否跨平台出现
            cross_platform_count = 1
            if historical:
                # 统计不同来源的数量
                sources = set([h.source for h in historical] + [topic.source])
                cross_platform_count = len(sources)

            # 计算趋势分数
            trending_score = self.calculate_trending_score(topic, cross_platform_count)

            # 更新话题对象
            # 由于Pydantic模型是不可变的,需要创建新对象
            updated_topic = topic.model_copy(update={
                'trend_direction': trend_direction,
                'trend_velocity': trend_velocity,
                'platforms': list({topic.source} | {h.source for h in historical}) if historical else None
            })

            updated_topics.append(updated_topic)

            logger.debug(
                f"Updated topic '{topic.title}': direction={trend_direction}, "
                f"velocity={trend_velocity}, score={trending_score}"
            )

        logger.info(f"Updated trending info for {len(updated_topics)} topics")
        return updated_topics

    def merge_cross_platform_topics(
        self,
        topics: List[TrendingTopic],
        similarity_threshold: float = 0.7
    ) -> List[TrendingTopic]:
        """合并跨平台出现的相同话题

        基于标题相似度合并来自不同平台的相同话题。
        遵循spec.md第76行的跨平台合并需求。

        Args:
            topics: 话题列表
            similarity_threshold: 相似度阈值(0-1)

        Returns:
            合并后的话题列表
        """
        if not topics:
            return []

        # 简单实现:基于标题关键词重叠度判断相似性
        merged_topics = []
        processed = set()

        for i, topic in enumerate(topics):
            if i in processed:
                continue

            # 查找相似话题
            similar_indices = [i]
            topic_keywords = set(topic.title.lower().split())

            for j in range(i + 1, len(topics)):
                if j in processed:
                    continue

                other_topic = topics[j]
                other_keywords = set(other_topic.title.lower().split())

                # 计算Jaccard相似度
                intersection = topic_keywords & other_keywords
                union = topic_keywords | other_keywords

                if union:
                    similarity = len(intersection) / len(union)

                    if similarity >= similarity_threshold:
                        similar_indices.append(j)
                        processed.add(j)

            processed.add(i)

            # 合并相似话题
            if len(similar_indices) > 1:
                similar_topics = [topics[idx] for idx in similar_indices]

                # 选择heat_score最高的作为主话题
                main_topic = max(similar_topics, key=lambda t: t.heat_score)

                # 收集所有平台
                all_platforms = set()
                total_heat = 0
                for t in similar_topics:
                    all_platforms.add(t.source)
                    total_heat += t.heat_score

                # 平均热度
                avg_heat = total_heat / len(similar_topics)

                # 创建合并后的话题
                merged_topic = main_topic.model_copy(update={
                    'heat_score': avg_heat,
                    'platforms': list(all_platforms)
                })

                merged_topics.append(merged_topic)

                logger.info(
                    f"Merged {len(similar_topics)} cross-platform topics: '{main_topic.title}' "
                    f"from platforms: {all_platforms}"
                )
            else:
                merged_topics.append(topic)

        logger.info(f"Merged {len(topics)} topics into {len(merged_topics)} unique topics")
        return merged_topics
