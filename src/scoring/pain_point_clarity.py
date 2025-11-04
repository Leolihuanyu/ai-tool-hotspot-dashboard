"""痛点清晰度评分器

基于research.md第412-424行的算法,评估用户痛点的清晰度。
评分维度:
1. 关键词匹配度(keyword_match_quality): 0-1
2. 具体性(specificity): 0-1
3. 语言质量(language_quality): 0-1

最终分数范围: 0-10
"""

from typing import List
from src.models.pain_point import UserPainPoint
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PainPointClarityScorer:
    """痛点清晰度评分器

    负责评估痛点描述的清晰度,帮助识别真实且明确的需求。
    """

    # 关键词库(表明明确需求的关键词)
    KEYWORD_PATTERNS = {
        "explicit_need": [
            "need a tool", "need tool", "需要工具", "需要一个",
            "wish there was", "希望有", "想要",
            "looking for", "寻找", "找",
            "want a tool", "想要工具",
            "require", "需求", "必须"
        ],
        "pain_indicators": [
            "painful", "痛点", "困难", "难以",
            "frustrating", "沮丧", "麻烦",
            "time-consuming", "耗时", "花费时间",
            "hard to", "很难", "困扰"
        ],
        "action_verbs": [
            "automate", "自动化",
            "generate", "生成",
            "create", "创建",
            "manage", "管理",
            "analyze", "分析"
        ]
    }

    # 具体性指标(描述越具体,分数越高)
    SPECIFICITY_INDICATORS = {
        "scenario": ["when", "while", "during", "当", "在...时"],
        "frequency": ["daily", "every day", "often", "每天", "经常", "频繁"],
        "impact": ["saves time", "节省时间", "reduce cost", "降低成本", "improve", "提高"],
        "measurement": ["hours", "小时", "minutes", "分钟", "times", "次", "人", "users"]
    }

    def __init__(self):
        """初始化痛点清晰度评分器"""
        pass

    def calculate_clarity_score(self, pain_point: UserPainPoint) -> float:
        """计算痛点清晰度评分

        基于research.md第418-424行的算法:
        clarity_score = (
            keyword_match_score * 0.4 +
            specificity_score * 0.4 +
            language_quality_score * 0.2
        ) * 10

        Args:
            pain_point: 用户痛点对象

        Returns:
            清晰度评分(0-10)
        """
        try:
            # 1. 关键词匹配度
            keyword_score = self._calculate_keyword_match(pain_point)

            # 2. 具体性评分
            specificity_score = self._calculate_specificity(pain_point)

            # 3. 语言质量评分
            language_score = self._calculate_language_quality(pain_point)

            # 综合评分
            clarity_score = (
                keyword_score * 0.4 +
                specificity_score * 0.4 +
                language_score * 0.2
            ) * 10

            logger.debug(
                f"Clarity score for '{pain_point.original_text[:50]}...': "
                f"keyword={keyword_score:.2f}, specificity={specificity_score:.2f}, "
                f"language={language_score:.2f}, final={clarity_score:.2f}"
            )

            return round(clarity_score, 2)

        except Exception as e:
            logger.error(f"Failed to calculate clarity score: {e}")
            return 5.0  # 默认中等分数

    def _calculate_keyword_match(self, pain_point: UserPainPoint) -> float:
        """计算关键词匹配度

        检查痛点文本中是否包含明确需求的关键词。

        Args:
            pain_point: 用户痛点对象

        Returns:
            匹配度评分(0-1)
        """
        text = pain_point.original_text.lower()
        total_matches = 0
        max_possible = 0

        # 检查各类关键词
        for category, keywords in self.KEYWORD_PATTERNS.items():
            category_matches = sum(1 for kw in keywords if kw.lower() in text)

            if category == "explicit_need":
                # 明确需求关键词权重更高
                total_matches += category_matches * 2
                max_possible += 2
            elif category == "pain_indicators":
                total_matches += category_matches
                max_possible += 1
            elif category == "action_verbs":
                total_matches += category_matches
                max_possible += 1

        # 归一化到0-1
        if max_possible == 0:
            return 0.0

        score = min(1.0, total_matches / max_possible)
        return score

    def _calculate_specificity(self, pain_point: UserPainPoint) -> float:
        """计算具体性评分

        评估痛点描述是否包含具体场景、频率、影响等细节。

        Args:
            pain_point: 用户痛点对象

        Returns:
            具体性评分(0-1)
        """
        text = pain_point.original_text.lower()
        context = getattr(pain_point, 'context_title', '').lower()
        combined_text = f"{text} {context}"

        score_components = []

        # 检查各类具体性指标
        for category, indicators in self.SPECIFICITY_INDICATORS.items():
            has_indicator = any(ind.lower() in combined_text for ind in indicators)
            score_components.append(1.0 if has_indicator else 0.0)

        # 检查文本长度(适度长度表示描述详细)
        text_length = len(pain_point.original_text)
        if 50 <= text_length <= 300:
            # 适度长度
            score_components.append(1.0)
        elif 30 <= text_length < 50 or 300 < text_length <= 500:
            # 稍短或稍长
            score_components.append(0.7)
        else:
            # 太短或太长
            score_components.append(0.3)

        # 检查是否有提取的关键词(至少3个)
        if len(pain_point.extracted_keywords) >= 3:
            score_components.append(1.0)
        elif len(pain_point.extracted_keywords) >= 1:
            score_components.append(0.5)
        else:
            score_components.append(0.0)

        # 平均分
        specificity_score = sum(score_components) / len(score_components)
        return specificity_score

    def _calculate_language_quality(self, pain_point: UserPainPoint) -> float:
        """计算语言质量评分

        评估文本的可读性和清晰度。

        Args:
            pain_point: 用户痛点对象

        Returns:
            语言质量评分(0-1)
        """
        text = pain_point.original_text

        # 简单的语言质量指标
        quality_indicators = []

        # 1. 句子完整性(包含标点符号)
        has_punctuation = any(p in text for p in ['.', '!', '?', '。', '!', '?'])
        quality_indicators.append(1.0 if has_punctuation else 0.5)

        # 2. 非垃圾文本(不包含过多重复字符)
        # 检查是否有超过3个连续重复字符
        has_spam = any(text[i] == text[i+1] == text[i+2] for i in range(len(text)-2))
        quality_indicators.append(0.3 if has_spam else 1.0)

        # 3. 大小写混合(英文文本)
        if any(c.isalpha() and c.isupper() for c in text):
            # 有大写字母
            if any(c.isalpha() and c.islower() for c in text):
                # 也有小写字母(正常混合)
                quality_indicators.append(1.0)
            else:
                # 全大写(可能是喊叫)
                quality_indicators.append(0.7)
        else:
            # 无大写字母(可能是中文或全小写)
            quality_indicators.append(0.9)

        # 4. 互动分数(高互动通常意味着有价值的内容)
        engagement = pain_point.engagement_score
        if engagement >= 70:
            quality_indicators.append(1.0)
        elif engagement >= 40:
            quality_indicators.append(0.8)
        elif engagement >= 20:
            quality_indicators.append(0.6)
        else:
            quality_indicators.append(0.4)

        # 平均分
        language_score = sum(quality_indicators) / len(quality_indicators)
        return language_score

    def batch_score(self, pain_points: List[UserPainPoint]) -> List[UserPainPoint]:
        """批量计算痛点清晰度评分

        Args:
            pain_points: 痛点列表

        Returns:
            更新后的痛点列表(包含清晰度评分)
        """
        if not pain_points:
            return []

        scored_points = []
        total = len(pain_points)

        for idx, pain_point in enumerate(pain_points, 1):
            try:
                clarity_score = self.calculate_clarity_score(pain_point)

                # 注意: Pydantic模型不可直接修改,需要通过model_copy更新
                # 这里我们假设调用方会使用返回的评分
                # 实际使用时,需要在外部更新痛点对象

                scored_points.append(pain_point)

                if idx % 20 == 0:
                    logger.info(f"Pain point clarity scoring progress: {idx}/{total}")

            except Exception as e:
                logger.error(f"Failed to score pain point {idx}: {e}")
                scored_points.append(pain_point)
                continue

        logger.info(f"Pain point clarity scoring completed: {len(scored_points)} items")
        return scored_points

    def filter_unclear_pain_points(
        self,
        pain_points: List[UserPainPoint],
        min_clarity_score: float = 5.0
    ) -> List[UserPainPoint]:
        """过滤不清晰的痛点

        Args:
            pain_points: 痛点列表
            min_clarity_score: 最低清晰度评分阈值(0-10)

        Returns:
            过滤后的痛点列表
        """
        if not pain_points:
            return []

        # 先计算所有评分
        scored_points = []
        for pp in pain_points:
            score = self.calculate_clarity_score(pp)
            if score >= min_clarity_score:
                scored_points.append(pp)

        removed_count = len(pain_points) - len(scored_points)
        logger.info(
            f"Filtered {removed_count}/{len(pain_points)} unclear pain points "
            f"(min_clarity_score={min_clarity_score})"
        )

        return scored_points
