"""变现潜力评分器

基于research.md第437-448行的算法,评估痛点的商业变现潜力。
评分维度:
1. 付费意愿(payment_willingness)
2. 商业模式清晰度(business_model_clarity)
3. 市场规模估算(market_size_estimate)

最终分数范围: 0-10
"""

from typing import List
from src.models.pain_point import UserPainPoint
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MonetizationScorer:
    """变现潜力评分器

    评估解决痛点后的商业变现可能性。
    分数越高,表示变现潜力越大。
    """

    # 付费意愿关键词
    PAYMENT_WILLINGNESS_KEYWORDS = {
        "explicit": [
            "willing to pay", "愿意付费", "会付钱",
            "would pay", "pay for", "为...付费",
            "subscription", "订阅", "月费",
            "pricing", "定价", "how much", "多少钱",
            "worth paying", "值得付费"
        ],
        "implicit": [
            "save time", "节省时间", "效率",
            "save money", "省钱", "降低成本",
            "business", "商业", "enterprise", "企业",
            "team", "团队", "organization", "组织",
            "professional", "专业", "commercial", "商用"
        ],
        "negative": [
            "free", "免费", "open source", "开源",
            "no budget", "没有预算", "can't afford", "买不起"
        ]
    }

    # 商业模式类型(优先级从高到低)
    BUSINESS_MODELS = {
        "saas": {
            "keywords": ["saas", "subscription", "订阅", "monthly", "每月", "recurring", "定期"],
            "score": 1.0,  # SaaS模式最优
            "description": "SaaS订阅"
        },
        "api": {
            "keywords": ["api", "integration", "集成", "webhook", "plugin", "插件"],
            "score": 0.9,
            "description": "API/插件"
        },
        "marketplace": {
            "keywords": ["template", "模板", "marketplace", "市场", "asset", "资源"],
            "score": 0.8,
            "description": "模板市场"
        },
        "one_time": {
            "keywords": ["purchase", "购买", "buy", "买", "license", "许可证"],
            "score": 0.6,
            "description": "一次性购买"
        },
        "freemium": {
            "keywords": ["freemium", "免费增值", "free trial", "免费试用", "upgrade", "升级"],
            "score": 0.7,
            "description": "Freemium"
        }
    }

    # 市场规模指标
    MARKET_SIZE_INDICATORS = {
        "b2b": [
            "business", "商业", "enterprise", "企业", "company", "公司",
            "team", "团队", "organization", "组织", "corporate", "企业级"
        ],
        "b2c": [
            "personal", "个人", "consumer", "消费者", "individual", "个体",
            "hobby", "爱好", "student", "学生"
        ],
        "creator_economy": [
            "creator", "创作者", "content creator", "内容创作",
            "youtuber", "blogger", "博主", "influencer", "网红"
        ],
        "developer": [
            "developer", "开发者", "programmer", "程序员",
            "coder", "编程", "software engineer", "软件工程师"
        ]
    }

    def __init__(self):
        """初始化变现潜力评分器"""
        pass

    def calculate_monetization_score(self, pain_point: UserPainPoint) -> float:
        """计算变现潜力评分

        基于research.md第442-448行的算法:
        monetization_score = (
            payment_willingness_score * 0.5 +
            business_model_clarity * 0.3 +
            market_size_estimate * 0.2
        ) * 10

        Args:
            pain_point: 用户痛点对象

        Returns:
            变现潜力评分(0-10)
        """
        try:
            # 1. 付费意愿评分
            payment_score = self._calculate_payment_willingness(pain_point)

            # 2. 商业模式清晰度
            model_clarity = self._calculate_business_model_clarity(pain_point)

            # 3. 市场规模估算
            market_size = self._estimate_market_size(pain_point)

            # 综合评分
            monetization_score = (
                payment_score * 0.5 +
                model_clarity * 0.3 +
                market_size * 0.2
            ) * 10

            logger.debug(
                f"Monetization score: payment={payment_score:.2f}, "
                f"model_clarity={model_clarity:.2f}, market_size={market_size:.2f}, "
                f"final={monetization_score:.2f}"
            )

            return round(monetization_score, 2)

        except Exception as e:
            logger.error(f"Failed to calculate monetization score: {e}")
            return 5.0  # 默认中等分数

    def _calculate_payment_willingness(self, pain_point: UserPainPoint) -> float:
        """计算付费意愿评分

        Args:
            pain_point: 用户痛点对象

        Returns:
            付费意愿评分(0-1)
        """
        text = pain_point.original_text.lower()
        context = getattr(pain_point, 'context_title', '').lower()
        combined = f"{text} {context}"

        # 检查明确付费意愿
        explicit_matches = sum(
            1 for kw in self.PAYMENT_WILLINGNESS_KEYWORDS["explicit"]
            if kw.lower() in combined
        )

        # 检查隐含付费意愿
        implicit_matches = sum(
            1 for kw in self.PAYMENT_WILLINGNESS_KEYWORDS["implicit"]
            if kw.lower() in combined
        )

        # 检查负面信号
        negative_matches = sum(
            1 for kw in self.PAYMENT_WILLINGNESS_KEYWORDS["negative"]
            if kw.lower() in combined
        )

        # 计算评分
        if explicit_matches > 0:
            # 明确表示愿意付费
            base_score = 1.0
        elif implicit_matches > 0:
            # 隐含商业价值
            base_score = 0.7
        else:
            # 无明显付费意愿信号
            base_score = 0.4

        # 负面信号扣分
        penalty = min(0.3, negative_matches * 0.15)
        final_score = max(0.0, base_score - penalty)

        # 互动分数加成(高互动可能表示需求强烈)
        engagement_boost = 0.0
        if pain_point.engagement_score >= 80:
            engagement_boost = 0.2
        elif pain_point.engagement_score >= 50:
            engagement_boost = 0.1

        return min(1.0, final_score + engagement_boost)

    def _calculate_business_model_clarity(self, pain_point: UserPainPoint) -> float:
        """计算商业模式清晰度

        检查痛点描述中是否暗示了明确的商业模式。

        Args:
            pain_point: 用户痛点对象

        Returns:
            商业模式清晰度评分(0-1)
        """
        text = pain_point.original_text.lower()
        keywords = [kw.lower() for kw in pain_point.extracted_keywords]
        combined = f"{text} {' '.join(keywords)}"

        # 检查各种商业模式
        matched_models = []
        for model_name, model_info in self.BUSINESS_MODELS.items():
            has_match = any(kw in combined for kw in model_info["keywords"])
            if has_match:
                matched_models.append(model_info["score"])

        if matched_models:
            # 取最高分的商业模式
            clarity_score = max(matched_models)
        else:
            # 无明确商业模式,默认较低分数
            clarity_score = 0.3

        return clarity_score

    def _estimate_market_size(self, pain_point: UserPainPoint) -> float:
        """估算市场规模

        基于痛点涉及的目标用户群体估算市场规模。

        Args:
            pain_point: 用户痛点对象

        Returns:
            市场规模评分(0-1)
        """
        text = pain_point.original_text.lower()
        context = getattr(pain_point, 'context_title', '').lower()
        combined = f"{text} {context}"

        # 统计各类市场指标
        b2b_matches = sum(
            1 for kw in self.MARKET_SIZE_INDICATORS["b2b"]
            if kw.lower() in combined
        )

        b2c_matches = sum(
            1 for kw in self.MARKET_SIZE_INDICATORS["b2c"]
            if kw.lower() in combined
        )

        creator_matches = sum(
            1 for kw in self.MARKET_SIZE_INDICATORS["creator_economy"]
            if kw.lower() in combined
        )

        developer_matches = sum(
            1 for kw in self.MARKET_SIZE_INDICATORS["developer"]
            if kw.lower() in combined
        )

        # 市场规模评分逻辑
        if b2b_matches > 0:
            # B2B市场规模大,付费能力强
            market_score = 0.9
        elif creator_matches > 0 or developer_matches > 0:
            # 创作者经济和开发者工具市场规模中等
            market_score = 0.7
        elif b2c_matches > 0:
            # B2C市场规模大但付费意愿较低
            market_score = 0.5
        else:
            # 无明显市场指标
            market_score = 0.4

        # 基于来源调整(某些平台用户群体更商业化)
        source_boost = 0.0
        if pain_point.source == "Reddit":
            # Reddit r/entrepreneur等社区商业化程度较高
            if "entrepreneur" in combined or "business" in combined or "saas" in combined:
                source_boost = 0.1
        elif pain_point.source == "ProductHunt":
            # ProductHunt用户通常是早期采用者和创业者
            source_boost = 0.15

        return min(1.0, market_score + source_boost)

    def identify_business_model(self, pain_point: UserPainPoint) -> str:
        """识别最适合的商业模式

        Args:
            pain_point: 用户痛点对象

        Returns:
            商业模式名称(如"SaaS订阅", "API/插件"等)
        """
        text = pain_point.original_text.lower()
        keywords = [kw.lower() for kw in pain_point.extracted_keywords]
        combined = f"{text} {' '.join(keywords)}"

        # 检查各种商业模式
        matched_models = []
        for model_name, model_info in self.BUSINESS_MODELS.items():
            has_match = any(kw in combined for kw in model_info["keywords"])
            if has_match:
                matched_models.append((model_info["description"], model_info["score"]))

        if matched_models:
            # 返回得分最高的商业模式
            best_model = max(matched_models, key=lambda x: x[1])
            return best_model[0]
        else:
            return "待定"

    def batch_score(self, pain_points: List[UserPainPoint]) -> dict:
        """批量计算变现潜力评分

        Args:
            pain_points: 痛点列表

        Returns:
            痛点ID到变现潜力评分的映射
        """
        if not pain_points:
            return {}

        scores = {}
        total = len(pain_points)

        for idx, pain_point in enumerate(pain_points, 1):
            try:
                score = self.calculate_monetization_score(pain_point)
                scores[pain_point.id] = score

                if idx % 20 == 0:
                    logger.info(f"Monetization scoring progress: {idx}/{total}")

            except Exception as e:
                logger.error(f"Failed to score pain point {pain_point.id}: {e}")
                scores[pain_point.id] = 5.0  # 默认分数
                continue

        logger.info(f"Monetization scoring completed: {len(scores)} items")
        return scores

    def rank_by_monetization(
        self,
        pain_points: List[UserPainPoint]
    ) -> List[tuple]:
        """按变现潜力排序痛点

        Args:
            pain_points: 痛点列表

        Returns:
            (pain_point, score, business_model)元组列表,按分数降序排列
        """
        results = []

        for pp in pain_points:
            score = self.calculate_monetization_score(pp)
            model = self.identify_business_model(pp)
            results.append((pp, score, model))

        # 按分数降序排序
        ranked = sorted(results, key=lambda x: x[1], reverse=True)

        logger.info(
            f"Ranked {len(ranked)} pain points by monetization potential. "
            f"Top score: {ranked[0][1]:.2f}, Bottom score: {ranked[-1][1]:.2f}"
        )

        return ranked
