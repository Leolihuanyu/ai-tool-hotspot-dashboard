"""市场契合度评分器

基于research.md第450-474行的算法,评估痛点在不同地理市场的契合度。
包含两个评分器:
1. JapanMarketFitScorer: 日本市场契合度(0-10)
2. USEUMarketFitScorer: 美欧市场契合度(0-10)
"""

from typing import List
from src.models.pain_point import UserPainPoint
from src.models.trend import TrendingTopic
from src.utils.logger import get_logger

logger = get_logger(__name__)


class JapanMarketFitScorer:
    """日本市场契合度评分器

    评估维度:
    1. 文化相关性(cultural_relevance): 是否符合日本文化特征
    2. 竞争缺口(competition_gap): 日本本土是否缺少类似解决方案
    3. 市场规模(market_size): 日本市场规模潜力
    """

    # 日本市场相关关键词
    JAPAN_KEYWORDS = {
        "language": ["japanese", "日本語", "日语", "日文", "jp", "japan", "日本"],
        "culture": [
            "anime", "动漫", "manga", "漫画",
            "kanji", "汉字", "hiragana", "平假名", "katakana", "片假名",
            "jpop", "jdrama", "日剧"
        ],
        "business": [
            "rakuten", "楽天", "line", "docomo", "softbank",
            "japan market", "日本市场", "japanese company", "日本企业"
        ],
        "local_needs": [
            "earthquake", "地震", "災害", "灾害",
            "commute", "通勤", "train", "电车",
            "konbini", "便利店", "コンビニ"
        ]
    }

    # 竞争程度指标(日本本土产品饱和度)
    COMPETITION_INDICATORS = {
        "low_competition": [
            # 这些领域日本本土产品较少,海外产品机会大
            "open source", "开源", "developer tools", "开发者工具",
            "saas", "云服务", "ai tools", "ai工具",
            "automation", "自动化"
        ],
        "high_competition": [
            # 这些领域日本本土产品较多
            "game", "游戏", "social media", "社交媒体",
            "payment", "支付", "messaging", "即时通讯"
        ]
    }

    def __init__(self):
        """初始化日本市场契合度评分器"""
        pass

    def calculate_japan_fit_score(
        self,
        pain_point: UserPainPoint,
        related_topics: List[TrendingTopic] = None
    ) -> float:
        """计算日本市场契合度评分

        基于research.md第455-462行的算法:
        japan_fit_score = (
            cultural_relevance * 0.4 +
            competition_gap * 0.4 +
            market_size * 0.2
        ) * 10

        Args:
            pain_point: 用户痛点对象
            related_topics: 相关热点话题列表(可选)

        Returns:
            日本市场契合度评分(0-10)
        """
        try:
            # 1. 文化相关性
            cultural_score = self._calculate_cultural_relevance(pain_point, related_topics)

            # 2. 竞争缺口
            competition_score = self._calculate_competition_gap(pain_point)

            # 3. 市场规模
            market_score = self._estimate_japan_market_size(pain_point)

            # 综合评分
            japan_fit_score = (
                cultural_score * 0.4 +
                competition_score * 0.4 +
                market_score * 0.2
            ) * 10

            logger.debug(
                f"Japan fit score: cultural={cultural_score:.2f}, "
                f"competition={competition_score:.2f}, market={market_score:.2f}, "
                f"final={japan_fit_score:.2f}"
            )

            return round(japan_fit_score, 2)

        except Exception as e:
            logger.error(f"Failed to calculate Japan fit score: {e}")
            return 5.0  # 默认中等分数

    def _calculate_cultural_relevance(
        self,
        pain_point: UserPainPoint,
        related_topics: List[TrendingTopic] = None
    ) -> float:
        """计算文化相关性评分"""
        text = pain_point.original_text.lower()
        keywords = [kw.lower() for kw in pain_point.extracted_keywords]
        combined = f"{text} {' '.join(keywords)}"

        # 检查日本相关关键词
        total_score = 0.0

        # 语言关键词(权重最高)
        language_matches = sum(
            1 for kw in self.JAPAN_KEYWORDS["language"]
            if kw.lower() in combined
        )
        if language_matches > 0:
            total_score += 0.4

        # 文化关键词
        culture_matches = sum(
            1 for kw in self.JAPAN_KEYWORDS["culture"]
            if kw.lower() in combined
        )
        if culture_matches > 0:
            total_score += 0.3

        # 商业关键词
        business_matches = sum(
            1 for kw in self.JAPAN_KEYWORDS["business"]
            if kw.lower() in combined
        )
        if business_matches > 0:
            total_score += 0.2

        # 本地需求关键词
        local_matches = sum(
            1 for kw in self.JAPAN_KEYWORDS["local_needs"]
            if kw.lower() in combined
        )
        if local_matches > 0:
            total_score += 0.1

        # 检查相关热点话题
        if related_topics:
            japan_topics = [
                t for t in related_topics
                if any(kw in t.title.lower() for kw in self.JAPAN_KEYWORDS["language"])
            ]
            if japan_topics:
                total_score += 0.2

        return min(1.0, total_score)

    def _calculate_competition_gap(self, pain_point: UserPainPoint) -> float:
        """计算竞争缺口评分"""
        text = pain_point.original_text.lower()
        keywords = [kw.lower() for kw in pain_point.extracted_keywords]
        combined = f"{text} {' '.join(keywords)}"

        # 检查竞争程度
        low_comp_matches = sum(
            1 for kw in self.COMPETITION_INDICATORS["low_competition"]
            if kw.lower() in combined
        )

        high_comp_matches = sum(
            1 for kw in self.COMPETITION_INDICATORS["high_competition"]
            if kw.lower() in combined
        )

        if low_comp_matches > high_comp_matches:
            # 竞争较低,机会较大
            return 0.8
        elif high_comp_matches > 0:
            # 竞争较高,机会较小
            return 0.3
        else:
            # 无明显信号,默认中等
            return 0.5

    def _estimate_japan_market_size(self, pain_point: UserPainPoint) -> float:
        """估算日本市场规模"""
        # 简化实现:基于互动分数和来源估算
        engagement = pain_point.engagement_score

        # 基础分数
        if engagement >= 70:
            base_score = 0.8
        elif engagement >= 40:
            base_score = 0.6
        else:
            base_score = 0.4

        return base_score


class USEUMarketFitScorer:
    """美欧市场契合度评分器

    评估维度:
    1. 可扩展性(scalability): 产品是否易于全球化
    2. 合规性(compliance): GDPR等法规合规性
    3. 市场潜力(market_potential): 美欧市场规模
    """

    # 美欧市场相关关键词
    USEU_KEYWORDS = {
        "language": ["english", "英语", "英文", "us", "usa", "europe", "欧洲", "eu"],
        "global": [
            "international", "国际", "global", "全球",
            "worldwide", "世界范围", "multi-language", "多语言"
        ],
        "gdpr": [
            "gdpr", "privacy", "隐私", "data protection", "数据保护",
            "consent", "同意", "cookie"
        ],
        "scalability": [
            "cloud", "云", "aws", "azure", "gcp",
            "scalable", "可扩展", "distributed", "分布式",
            "api", "webhook", "integration", "集成"
        ]
    }

    def __init__(self):
        """初始化美欧市场契合度评分器"""
        pass

    def calculate_useu_fit_score(
        self,
        pain_point: UserPainPoint,
        related_topics: List[TrendingTopic] = None
    ) -> float:
        """计算美欧市场契合度评分

        基于research.md第467-474行的算法:
        us_eu_fit_score = (
            scalability * 0.4 +
            compliance * 0.3 +
            market_potential * 0.3
        ) * 10

        Args:
            pain_point: 用户痛点对象
            related_topics: 相关热点话题列表(可选)

        Returns:
            美欧市场契合度评分(0-10)
        """
        try:
            # 1. 可扩展性
            scalability_score = self._calculate_scalability(pain_point)

            # 2. 合规性
            compliance_score = self._calculate_compliance(pain_point)

            # 3. 市场潜力
            market_score = self._estimate_useu_market_potential(pain_point, related_topics)

            # 综合评分
            useu_fit_score = (
                scalability_score * 0.4 +
                compliance_score * 0.3 +
                market_score * 0.3
            ) * 10

            logger.debug(
                f"US/EU fit score: scalability={scalability_score:.2f}, "
                f"compliance={compliance_score:.2f}, market={market_score:.2f}, "
                f"final={useu_fit_score:.2f}"
            )

            return round(useu_fit_score, 2)

        except Exception as e:
            logger.error(f"Failed to calculate US/EU fit score: {e}")
            return 5.0  # 默认中等分数

    def _calculate_scalability(self, pain_point: UserPainPoint) -> float:
        """计算可扩展性评分"""
        text = pain_point.original_text.lower()
        keywords = [kw.lower() for kw in pain_point.extracted_keywords]
        combined = f"{text} {' '.join(keywords)}"

        # 检查可扩展性关键词
        scalability_matches = sum(
            1 for kw in self.USEU_KEYWORDS["scalability"]
            if kw.lower() in combined
        )

        global_matches = sum(
            1 for kw in self.USEU_KEYWORDS["global"]
            if kw.lower() in combined
        )

        total_matches = scalability_matches + global_matches

        if total_matches >= 3:
            return 1.0
        elif total_matches >= 1:
            return 0.7
        else:
            # 默认中等(大多数SaaS产品都具有一定可扩展性)
            return 0.5

    def _calculate_compliance(self, pain_point: UserPainPoint) -> float:
        """计算合规性评分"""
        text = pain_point.original_text.lower()
        keywords = [kw.lower() for kw in pain_point.extracted_keywords]
        combined = f"{text} {' '.join(keywords)}"

        # 检查是否涉及敏感数据
        gdpr_matches = sum(
            1 for kw in self.USEU_KEYWORDS["gdpr"]
            if kw.lower() in combined
        )

        if gdpr_matches > 0:
            # 涉及隐私/数据保护,需要额外合规工作
            return 0.6
        else:
            # 不涉及敏感数据,合规较简单
            return 0.9

    def _estimate_useu_market_potential(
        self,
        pain_point: UserPainPoint,
        related_topics: List[TrendingTopic] = None
    ) -> float:
        """估算美欧市场潜力"""
        text = pain_point.original_text.lower()
        keywords = [kw.lower() for kw in pain_point.extracted_keywords]
        combined = f"{text} {' '.join(keywords)}"

        # 检查美欧市场关键词
        language_matches = sum(
            1 for kw in self.USEU_KEYWORDS["language"]
            if kw.lower() in combined
        )

        # 基础分数(美欧市场普遍规模较大)
        base_score = 0.7

        # 语言匹配加成
        if language_matches > 0:
            base_score += 0.2

        # 检查相关热点话题
        if related_topics:
            global_topics = [
                t for t in related_topics
                if any(kw in t.title.lower() for kw in self.USEU_KEYWORDS["global"])
            ]
            if global_topics:
                base_score += 0.1

        return min(1.0, base_score)


class MarketFitScorer:
    """市场契合度评分器(组合器)

    组合日本和美欧市场评分器,提供统一接口。
    """

    def __init__(self):
        """初始化市场契合度评分器"""
        self.japan_scorer = JapanMarketFitScorer()
        self.useu_scorer = USEUMarketFitScorer()

    def calculate_all_market_scores(
        self,
        pain_point: UserPainPoint,
        related_topics: List[TrendingTopic] = None
    ) -> dict:
        """计算所有市场的契合度评分

        Args:
            pain_point: 用户痛点对象
            related_topics: 相关热点话题列表

        Returns:
            包含各市场评分的字典
        """
        return {
            "japan": self.japan_scorer.calculate_japan_fit_score(
                pain_point, related_topics
            ),
            "us_eu": self.useu_scorer.calculate_useu_fit_score(
                pain_point, related_topics
            )
        }

    def batch_score(
        self,
        pain_points: List[UserPainPoint],
        topics_by_pain_point: dict = None
    ) -> dict:
        """批量计算市场契合度评分

        Args:
            pain_points: 痛点列表
            topics_by_pain_point: 痛点ID到相关热点列表的映射(可选)

        Returns:
            痛点ID到市场评分字典的映射
        """
        if not pain_points:
            return {}

        scores = {}
        total = len(pain_points)

        for idx, pain_point in enumerate(pain_points, 1):
            try:
                # 获取相关热点
                related_topics = None
                if topics_by_pain_point:
                    related_topics = topics_by_pain_point.get(pain_point.id, [])

                # 计算所有市场评分
                market_scores = self.calculate_all_market_scores(
                    pain_point, related_topics
                )
                scores[pain_point.id] = market_scores

                if idx % 20 == 0:
                    logger.info(f"Market fit scoring progress: {idx}/{total}")

            except Exception as e:
                logger.error(f"Failed to score pain point {pain_point.id}: {e}")
                scores[pain_point.id] = {"japan": 5.0, "us_eu": 5.0}
                continue

        logger.info(f"Market fit scoring completed: {len(scores)} items")
        return scores
