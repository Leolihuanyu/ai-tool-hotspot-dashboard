"""MVP速度/技术可行性评分器

基于research.md第426-435行的算法,评估痛点对应的MVP开发速度。
评分维度:
1. 相关AI工具可用性
2. 技术复杂度
3. 预估开发时间

最终分数范围: 0-10
"""

from typing import List
from src.models.pain_point import UserPainPoint
from src.models.tool import AITool
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MVPSpeedScorer:
    """MVP速度评分器

    评估解决痛点的技术可行性和开发速度。
    分数越高,表示MVP越容易快速实现。
    """

    # 技术复杂度关键词
    COMPLEXITY_KEYWORDS = {
        "low": [
            # 前端工具和简单自动化
            "website", "网站", "landing page", "着陆页",
            "dashboard", "仪表板", "chart", "图表",
            "form", "表单", "template", "模板",
            "export", "导出", "download", "下载"
        ],
        "medium": [
            # 全栈应用
            "api", "backend", "后端", "database", "数据库",
            "authentication", "认证", "payment", "支付",
            "notification", "通知", "email", "邮件",
            "search", "搜索", "filter", "筛选"
        ],
        "high": [
            # 复杂ML/AI任务
            "train model", "训练模型", "machine learning", "机器学习",
            "neural network", "神经网络", "deep learning", "深度学习",
            "computer vision", "计算机视觉", "nlp", "自然语言处理",
            "real-time", "实时", "streaming", "流式处理"
        ]
    }

    # AI工具类别与开发加速度
    TOOL_CATEGORY_BOOST = {
        "text-generation": 1.5,  # 文本生成工具可大幅加速开发
        "image-generation": 1.3,
        "code-generation": 2.0,   # 代码生成工具加速最大
        "automation": 1.8,
        "no-code": 2.0,           # no-code工具加速显著
        "api": 1.5,
        "template": 1.4
    }

    def __init__(self):
        """初始化MVP速度评分器"""
        pass

    def calculate_mvp_speed_score(
        self,
        pain_point: UserPainPoint,
        related_tools: List[AITool] = None
    ) -> float:
        """计算MVP速度评分

        基于research.md第431-435行的算法:
        mvp_speed_score = min(10, related_tools_count * 2 + base_feasibility)

        Args:
            pain_point: 用户痛点对象
            related_tools: 相关AI工具列表(可选)

        Returns:
            MVP速度评分(0-10)
        """
        try:
            # 1. 基础可行性评分(基于技术复杂度)
            base_feasibility = self._calculate_base_feasibility(pain_point)

            # 2. 工具可用性加成
            tool_boost = 0.0
            if related_tools:
                tool_boost = self._calculate_tool_boost(related_tools, pain_point)

            # 3. 综合评分
            # related_tools_count * 2: 每个相关工具贡献2分
            tools_count_score = len(related_tools) * 2 if related_tools else 0

            mvp_speed_score = min(
                10.0,
                base_feasibility + tools_count_score + tool_boost
            )

            logger.debug(
                f"MVP speed score: base={base_feasibility:.2f}, "
                f"tools_count={tools_count_score:.2f}, boost={tool_boost:.2f}, "
                f"final={mvp_speed_score:.2f}"
            )

            return round(mvp_speed_score, 2)

        except Exception as e:
            logger.error(f"Failed to calculate MVP speed score: {e}")
            return 5.0  # 默认中等分数

    def _calculate_base_feasibility(self, pain_point: UserPainPoint) -> float:
        """计算基础可行性评分

        基于痛点描述中的技术复杂度关键词判断。

        Args:
            pain_point: 用户痛点对象

        Returns:
            基础可行性评分(0-10)
        """
        text = pain_point.original_text.lower()
        keywords = pain_point.extracted_keywords

        # 合并文本和关键词
        combined = f"{text} {' '.join(keywords)}".lower()

        # 检查复杂度关键词
        low_matches = sum(1 for kw in self.COMPLEXITY_KEYWORDS["low"] if kw.lower() in combined)
        medium_matches = sum(1 for kw in self.COMPLEXITY_KEYWORDS["medium"] if kw.lower() in combined)
        high_matches = sum(1 for kw in self.COMPLEXITY_KEYWORDS["high"] if kw.lower() in combined)

        # 根据匹配情况判断复杂度
        if high_matches > 0:
            # 高复杂度: 需要ML训练,开发慢
            base_score = 3.0
        elif medium_matches > low_matches:
            # 中等复杂度: 全栈应用
            base_score = 5.0
        elif low_matches > 0:
            # 低复杂度: 前端工具或简单自动化
            base_score = 7.0
        else:
            # 无明显复杂度指标,默认中等
            base_score = 5.0

        return base_score

    def _calculate_tool_boost(
        self,
        related_tools: List[AITool],
        pain_point: UserPainPoint
    ) -> float:
        """计算工具可用性加成

        如果相关工具的功能与痛点高度匹配,提供额外加成。

        Args:
            related_tools: 相关AI工具列表
            pain_point: 用户痛点对象

        Returns:
            工具加成分数(0-3)
        """
        if not related_tools:
            return 0.0

        total_boost = 0.0

        # 提取痛点关键词
        pain_keywords = set(kw.lower() for kw in pain_point.extracted_keywords)

        for tool in related_tools:
            # 检查工具功能匹配度
            tool_features = getattr(tool, 'features', [])
            tool_tags = getattr(tool, 'tags', [])

            # 合并工具的特征和标签
            tool_keywords = set(
                [f.lower() for f in tool_features] +
                [t.lower() for t in tool_tags]
            )

            # 计算关键词交集
            intersection = pain_keywords & tool_keywords

            if intersection:
                # 有匹配的关键词,提供加成
                match_ratio = len(intersection) / len(pain_keywords) if pain_keywords else 0
                boost = match_ratio * 1.0  # 最多1分加成per工具

                # 检查工具类别加成
                for tag in tool.tags:
                    for category, multiplier in self.TOOL_CATEGORY_BOOST.items():
                        if category in tag.lower():
                            boost *= multiplier
                            break

                total_boost += boost

        # 限制最大加成为3分
        return min(3.0, total_boost)

    def estimate_development_time(
        self,
        pain_point: UserPainPoint,
        related_tools: List[AITool] = None
    ) -> str:
        """估算开发时间

        基于MVP速度评分,估算大致开发时间。

        Args:
            pain_point: 用户痛点对象
            related_tools: 相关AI工具列表

        Returns:
            开发时间估算字符串(如"<1周", "<2周", ">2周")
        """
        score = self.calculate_mvp_speed_score(pain_point, related_tools)

        if score >= 8.0:
            return "<1周"  # 非常快
        elif score >= 6.0:
            return "1-2周"  # 较快
        elif score >= 4.0:
            return "2-4周"  # 中等
        else:
            return ">1个月"  # 较慢

    def batch_score(
        self,
        pain_points: List[UserPainPoint],
        tools_by_pain_point: dict = None
    ) -> dict:
        """批量计算MVP速度评分

        Args:
            pain_points: 痛点列表
            tools_by_pain_point: 痛点ID到相关工具列表的映射(可选)

        Returns:
            痛点ID到MVP速度评分的映射
        """
        if not pain_points:
            return {}

        scores = {}
        total = len(pain_points)

        for idx, pain_point in enumerate(pain_points, 1):
            try:
                # 获取相关工具
                related_tools = None
                if tools_by_pain_point:
                    related_tools = tools_by_pain_point.get(pain_point.id, [])

                # 计算评分
                score = self.calculate_mvp_speed_score(pain_point, related_tools)
                scores[pain_point.id] = score

                if idx % 20 == 0:
                    logger.info(f"MVP speed scoring progress: {idx}/{total}")

            except Exception as e:
                logger.error(f"Failed to score pain point {pain_point.id}: {e}")
                scores[pain_point.id] = 5.0  # 默认分数
                continue

        logger.info(f"MVP speed scoring completed: {len(scores)} items")
        return scores

    def rank_by_speed(
        self,
        pain_points: List[UserPainPoint],
        tools_by_pain_point: dict = None
    ) -> List[tuple]:
        """按MVP速度排序痛点

        Args:
            pain_points: 痛点列表
            tools_by_pain_point: 痛点ID到相关工具列表的映射

        Returns:
            (pain_point, score)元组列表,按分数降序排列
        """
        scores = self.batch_score(pain_points, tools_by_pain_point)

        # 排序
        ranked = sorted(
            [(pp, scores.get(pp.id, 0.0)) for pp in pain_points],
            key=lambda x: x[1],
            reverse=True
        )

        logger.info(
            f"Ranked {len(ranked)} pain points by MVP speed. "
            f"Top score: {ranked[0][1]:.2f}, Bottom score: {ranked[-1][1]:.2f}"
        )

        return ranked
