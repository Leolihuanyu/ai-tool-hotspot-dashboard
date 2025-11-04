"""机会评分聚合器

整合所有评分维度,生成最终的机会评分(Opportunity Score)。
基于research.md第485-503行和data-model.md第311-321行的算法。

评分维度(来自宪法原则IV):
1. Pain Point Clarity (痛点清晰度): 0-10
2. MVP Speed (MVP速度): 0-10
3. Monetization Potential (变现潜力): 0-10
4. Japan Market Fit (日本市场契合度): 0-10
5. US/EU Market Fit (美欧市场契合度): 0-10
6. Trending Score (趋势分数): 0-10

最终评分范围: 0-100
"""

from typing import List, Dict
import os
from src.models.pain_point import UserPainPoint
from src.models.tool import AITool
from src.models.trend import TrendingTopic
from src.models.opportunity import Opportunity
from src.scoring.pain_point_clarity import PainPointClarityScorer
from src.scoring.mvp_speed import MVPSpeedScorer
from src.scoring.monetization import MonetizationScorer
from src.scoring.market_fit import MarketFitScorer
from src.scoring.trending import TrendingScorer
from src.utils.logger import get_logger

logger = get_logger(__name__)


class OpportunityScoreAggregator:
    """机会评分聚合器

    整合6个评分维度,计算最终的机会评分。
    """

    def __init__(self):
        """初始化评分聚合器"""
        # 初始化各维度评分器
        self.clarity_scorer = PainPointClarityScorer()
        self.mvp_scorer = MVPSpeedScorer()
        self.monetization_scorer = MonetizationScorer()
        self.market_scorer = MarketFitScorer()
        self.trending_scorer = TrendingScorer()

        # 从环境变量读取权重配置(宪法原则IV要求可配置)
        self.weights = {
            "pain_clarity": float(os.getenv("SCORE_WEIGHT_PAIN_CLARITY", "0.4")),
            "mvp_speed": float(os.getenv("SCORE_WEIGHT_MVP_SPEED", "0.3")),
            "monetization": float(os.getenv("SCORE_WEIGHT_MONETIZATION", "0.3")),
            "japan_market": float(os.getenv("SCORE_WEIGHT_JAPAN_MARKET", "0.2")),
            "us_eu_market": float(os.getenv("SCORE_WEIGHT_US_EU_MARKET", "0.2")),
            "trending": float(os.getenv("SCORE_WEIGHT_TRENDING", "0.3"))
        }

        logger.info(f"Initialized OpportunityScoreAggregator with weights: {self.weights}")

    def calculate_opportunity_score(
        self,
        pain_point: UserPainPoint,
        related_tools: List[AITool] = None,
        related_topics: List[TrendingTopic] = None
    ) -> Dict[str, float]:
        """计算机会评分

        基于research.md第487-503行和data-model.md第311-321行的公式:

        opportunity_score = [
            (pain_point_clarity * 0.4) +
            (mvp_speed * 0.3) +
            (monetization_potential * 0.3) +
            (japan_market_fit * 0.2) +
            (us_eu_market_fit * 0.2) +
            (trending_score * 0.3)
        ] / 1.7  # 归一化到0-10范围

        # 应用质量权重
        final_score = (
            opportunity_score *
            pain_point.confidence_score *
            average_data_quality_score
        ) * 10  # 转换为0-100范围

        Args:
            pain_point: 用户痛点对象
            related_tools: 相关AI工具列表(可选)
            related_topics: 相关热点话题列表(可选)

        Returns:
            包含各维度评分和最终评分的字典
        """
        try:
            # 1. 计算各维度评分(0-10)
            pain_clarity = self.clarity_scorer.calculate_clarity_score(pain_point)
            mvp_speed = self.mvp_scorer.calculate_mvp_speed_score(pain_point, related_tools)
            monetization = self.monetization_scorer.calculate_monetization_score(pain_point)

            # 市场契合度(分别计算日本和美欧)
            market_scores = self.market_scorer.calculate_all_market_scores(
                pain_point, related_topics
            )
            japan_fit = market_scores["japan"]
            us_eu_fit = market_scores["us_eu"]

            # 趋势分数(取相关话题的平均值)
            trending_score = 0.0
            if related_topics:
                cross_platform_counts = {}
                for topic in related_topics:
                    # 统计跨平台出现次数
                    platforms = getattr(topic, 'platforms', None)
                    count = len(platforms) if platforms else 1
                    cross_platform_counts[topic.id] = count

                # 计算趋势分数
                trending_scores = [
                    self.trending_scorer.calculate_trending_score(
                        topic,
                        cross_platform_counts.get(topic.id, 1)
                    )
                    for topic in related_topics
                ]
                trending_score = sum(trending_scores) / len(trending_scores)
            else:
                # 无相关热点,使用默认分数
                trending_score = 5.0

            # 2. 计算加权综合评分(使用配置的权重)
            weighted_score = (
                pain_clarity * self.weights["pain_clarity"] +
                mvp_speed * self.weights["mvp_speed"] +
                monetization * self.weights["monetization"] +
                japan_fit * self.weights["japan_market"] +
                us_eu_fit * self.weights["us_eu_market"] +
                trending_score * self.weights["trending"]
            )

            # 计算权重总和用于归一化
            total_weight = sum(self.weights.values())

            # 归一化到0-10范围
            base_score = weighted_score / total_weight * 10

            # 3. 应用质量权重(FR-025)
            confidence_score = getattr(pain_point, 'confidence_score', 0.7)

            # 计算平均数据质量分数
            quality_scores = [getattr(pain_point, 'data_quality_score', 0.7)]
            if related_tools:
                quality_scores.extend([
                    getattr(tool, 'data_quality_score', 0.7)
                    for tool in related_tools
                ])
            if related_topics:
                quality_scores.extend([
                    getattr(topic, 'data_quality_score', 0.7)
                    for topic in related_topics
                ])

            avg_quality = sum(quality_scores) / len(quality_scores)

            # 最终评分(0-100范围)
            final_score = base_score * confidence_score * avg_quality * 10
            final_score = min(100.0, max(0.0, final_score))  # 限制范围

            # 返回详细评分
            result = {
                "final_score": round(final_score, 2),
                "base_score": round(base_score, 2),
                "dimension_scores": {
                    "pain_clarity": round(pain_clarity, 2),
                    "mvp_speed": round(mvp_speed, 2),
                    "monetization": round(monetization, 2),
                    "japan_fit": round(japan_fit, 2),
                    "us_eu_fit": round(us_eu_fit, 2),
                    "trending": round(trending_score, 2)
                },
                "quality_modifiers": {
                    "confidence_score": round(confidence_score, 2),
                    "avg_data_quality": round(avg_quality, 2)
                }
            }

            logger.debug(
                f"Opportunity score calculated: final={result['final_score']:.2f}, "
                f"dimensions={result['dimension_scores']}"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to calculate opportunity score: {e}")
            # 返回默认中等分数
            return {
                "final_score": 50.0,
                "base_score": 5.0,
                "dimension_scores": {
                    "pain_clarity": 5.0,
                    "mvp_speed": 5.0,
                    "monetization": 5.0,
                    "japan_fit": 5.0,
                    "us_eu_fit": 5.0,
                    "trending": 5.0
                },
                "quality_modifiers": {
                    "confidence_score": 0.7,
                    "avg_data_quality": 0.7
                }
            }

    def batch_score_opportunities(
        self,
        pain_points: List[UserPainPoint],
        tools_by_pain_point: Dict[str, List[AITool]] = None,
        topics_by_pain_point: Dict[str, List[TrendingTopic]] = None
    ) -> Dict[str, Dict[str, float]]:
        """批量计算机会评分

        Args:
            pain_points: 痛点列表
            tools_by_pain_point: 痛点ID到相关工具列表的映射(可选)
            topics_by_pain_point: 痛点ID到相关热点列表的映射(可选)

        Returns:
            痛点ID到评分详情的映射
        """
        if not pain_points:
            return {}

        scores = {}
        total = len(pain_points)

        for idx, pain_point in enumerate(pain_points, 1):
            try:
                # 获取相关工具和热点
                related_tools = None
                related_topics = None

                if tools_by_pain_point:
                    related_tools = tools_by_pain_point.get(pain_point.id, [])

                if topics_by_pain_point:
                    related_topics = topics_by_pain_point.get(pain_point.id, [])

                # 计算评分
                score_detail = self.calculate_opportunity_score(
                    pain_point,
                    related_tools,
                    related_topics
                )
                scores[pain_point.id] = score_detail

                if idx % 10 == 0:
                    logger.info(f"Opportunity scoring progress: {idx}/{total}")

            except Exception as e:
                logger.error(f"Failed to score pain point {pain_point.id}: {e}")
                # 使用默认分数
                scores[pain_point.id] = {
                    "final_score": 50.0,
                    "base_score": 5.0,
                    "dimension_scores": {},
                    "quality_modifiers": {}
                }
                continue

        logger.info(
            f"Opportunity scoring completed: {len(scores)} items. "
            f"Score range: {min(s['final_score'] for s in scores.values()):.2f} - "
            f"{max(s['final_score'] for s in scores.values()):.2f}"
        )

        return scores

    def rank_opportunities(
        self,
        pain_points: List[UserPainPoint],
        tools_by_pain_point: Dict[str, List[AITool]] = None,
        topics_by_pain_point: Dict[str, List[TrendingTopic]] = None,
        top_k: int = 10
    ) -> List[tuple]:
        """对机会进行排名

        Args:
            pain_points: 痛点列表
            tools_by_pain_point: 痛点ID到相关工具列表的映射
            topics_by_pain_point: 痛点ID到相关热点列表的映射
            top_k: 返回Top K机会(默认10)

        Returns:
            (pain_point, score_detail)元组列表,按最终评分降序排列
        """
        # 批量评分
        scores = self.batch_score_opportunities(
            pain_points,
            tools_by_pain_point,
            topics_by_pain_point
        )

        # 按最终评分排序
        ranked = sorted(
            [(pp, scores.get(pp.id, {"final_score": 0.0})) for pp in pain_points],
            key=lambda x: x[1]["final_score"],
            reverse=True
        )

        # 返回Top K
        top_opportunities = ranked[:top_k]

        logger.info(
            f"Ranked top {len(top_opportunities)} opportunities. "
            f"Top score: {top_opportunities[0][1]['final_score']:.2f}"
        )

        return top_opportunities

    def create_opportunity_objects(
        self,
        pain_points: List[UserPainPoint],
        tools_by_pain_point: Dict[str, List[AITool]] = None,
        topics_by_pain_point: Dict[str, List[TrendingTopic]] = None,
        top_k: int = 10
    ) -> List[Opportunity]:
        """创建Opportunity对象

        注意: MVP建议(mvp_suggestion_cn/ja)需要通过LLM生成,
        这里暂时留空,由mvp_suggester.py模块负责填充。

        Args:
            pain_points: 痛点列表
            tools_by_pain_point: 痛点ID到相关工具列表的映射
            topics_by_pain_point: 痛点ID到相关热点列表的映射
            top_k: 创建Top K机会对象(默认10)

        Returns:
            Opportunity对象列表
        """
        from datetime import datetime
        from uuid import uuid4

        # 排名
        ranked = self.rank_opportunities(
            pain_points,
            tools_by_pain_point,
            topics_by_pain_point,
            top_k
        )

        opportunities = []

        for pain_point, score_detail in ranked:
            try:
                # 获取相关工具和热点ID
                related_tool_ids = []
                related_topic_ids = []

                if tools_by_pain_point and pain_point.id in tools_by_pain_point:
                    related_tool_ids = [t.id for t in tools_by_pain_point[pain_point.id]]

                if topics_by_pain_point and pain_point.id in topics_by_pain_point:
                    related_topic_ids = [t.id for t in topics_by_pain_point[pain_point.id]]

                # 聚合标签
                tags = list(pain_point.tags)
                if tools_by_pain_point and pain_point.id in tools_by_pain_point:
                    for tool in tools_by_pain_point[pain_point.id]:
                        tags.extend(tool.tags)
                if topics_by_pain_point and pain_point.id in topics_by_pain_point:
                    for topic in topics_by_pain_point[pain_point.id]:
                        tags.extend(topic.tags)

                # 去重
                tags = list(set(tags))

                # 计算平均数据质量分数
                quality_scores = [getattr(pain_point, 'data_quality_score', 0.7)]
                if tools_by_pain_point and pain_point.id in tools_by_pain_point:
                    quality_scores.extend([
                        getattr(t, 'data_quality_score', 0.7)
                        for t in tools_by_pain_point[pain_point.id]
                    ])
                if topics_by_pain_point and pain_point.id in topics_by_pain_point:
                    quality_scores.extend([
                        getattr(t, 'data_quality_score', 0.7)
                        for t in topics_by_pain_point[pain_point.id]
                    ])

                avg_quality = sum(quality_scores) / len(quality_scores)

                # 创建Opportunity对象
                opportunity = Opportunity(
                    id=str(uuid4()),
                    pain_point_id=pain_point.id,
                    related_tools=related_tool_ids,
                    related_topics=related_topic_ids,
                    opportunity_score=score_detail["final_score"],
                    mvp_suggestion_cn="",  # 待LLM生成
                    mvp_suggestion_ja="",  # 待LLM生成
                    timestamp=datetime.now(),
                    tags=tags,
                    data_quality_score=round(avg_quality, 2),
                    schema_version="1.1"
                )

                opportunities.append(opportunity)

            except Exception as e:
                logger.error(f"Failed to create Opportunity object for pain point {pain_point.id}: {e}")
                continue

        logger.info(f"Created {len(opportunities)} Opportunity objects")
        return opportunities
