"""
数据源分级权重配置

定义不同数据来源的信号强度权重，用于影响最终机会评分。

权重分级：
- A级（权重4）：强信号源，新产品和技术趋势最集中
- B级（权重2）：中等信号源，话题热度高但噪音较多
- C级（权重1）：弱信号源，偶尔能挖掘小众机会
"""

from typing import Dict
import logging

logger = logging.getLogger(__name__)

# A级强信号源（权重4）
A_TIER_SOURCES = {
    "ProductHunt": 4.0,
    "GitHub Discussions": 4.0,
    "Hacker News": 4.0,
    "Reddit": 4.0,  # 提升至A级 - r/entrepreneur, r/SaaS等子版块包含高价值痛点信息
    "Indie Hackers": 4.0,  # 独立开发者核心社区 - revenue分享、MVP验证、获客策略
}

# B级中信号源（权重2）
B_TIER_SOURCES = {
    "YouTube": 2.0,
    "X": 2.0,
}

# C级弱信号源（权重1）
C_TIER_SOURCES = {
    "Google Trends": 1.0,
    "Futurepedia": 1.0,
}

# 合并所有权重
SOURCE_WEIGHTS: Dict[str, float] = {
    **A_TIER_SOURCES,
    **B_TIER_SOURCES,
    **C_TIER_SOURCES,
}

# 数据源别名映射（处理命名不一致问题）
SOURCE_ALIASES = {
    "producthunt": "ProductHunt",
    "product hunt": "ProductHunt",
    "hackernews": "Hacker News",
    "hacker news": "Hacker News",
    "hn": "Hacker News",
    "github": "GitHub Discussions",
    "github discussions": "GitHub Discussions",
    "reddit": "Reddit",
    "indie hackers": "Indie Hackers",
    "indiehackers": "Indie Hackers",
    "indie-hackers": "Indie Hackers",
    "ih": "Indie Hackers",
    "youtube": "YouTube",
    "twitter": "X",
    "x": "X",
    "google trends": "Google Trends",
    "googletrends": "Google Trends",
    "futurepedia": "Futurepedia",
}


def get_source_weight(source: str) -> float:
    """
    获取数据源权重，支持模糊匹配

    Args:
        source: 数据来源名称（不区分大小写）

    Returns:
        float: 数据源权重（1.0-4.0），未知来源返回1.0

    Examples:
        >>> get_source_weight("ProductHunt")
        4.0
        >>> get_source_weight("reddit")
        2.0
        >>> get_source_weight("Unknown Source")
        1.0
    """
    if not source:
        return 1.0

    # 规范化输入：小写 + 去除多余空格
    source_normalized = source.lower().strip()

    # 1. 尝试直接匹配别名
    if source_normalized in SOURCE_ALIASES:
        canonical_name = SOURCE_ALIASES[source_normalized]
        weight = SOURCE_WEIGHTS.get(canonical_name, 1.0)
        logger.debug(f"数据源权重匹配: {source} -> {canonical_name} (权重={weight})")
        return weight

    # 2. 尝试包含匹配（模糊匹配）
    for alias, canonical_name in SOURCE_ALIASES.items():
        if alias in source_normalized or source_normalized in alias:
            weight = SOURCE_WEIGHTS.get(canonical_name, 1.0)
            logger.debug(f"数据源权重模糊匹配: {source} -> {canonical_name} (权重={weight})")
            return weight

    # 3. 未知来源，返回默认权重
    logger.debug(f"未知数据源，使用默认权重: {source} (权重=1.0)")
    return 1.0


def get_all_sources_by_tier() -> Dict[str, Dict[str, float]]:
    """
    获取按层级分组的所有数据源

    Returns:
        Dict[str, Dict[str, float]]: 分层级的数据源字典
    """
    return {
        "A_TIER (强信号)": A_TIER_SOURCES,
        "B_TIER (中信号)": B_TIER_SOURCES,
        "C_TIER (弱信号)": C_TIER_SOURCES,
    }


if __name__ == "__main__":
    # 测试代码
    test_sources = [
        "ProductHunt",
        "product hunt",
        "Reddit",
        "Hacker News",
        "hackernews",
        "GitHub Discussions",
        "YouTube",
        "Unknown Source",
    ]

    print("数据源权重测试:")
    print("=" * 50)
    for src in test_sources:
        weight = get_source_weight(src)
        print(f"{src:30s} -> 权重: {weight}")

    print("\n所有数据源分层:")
    print("=" * 50)
    for tier, sources in get_all_sources_by_tier().items():
        print(f"\n{tier}:")
        for name, weight in sources.items():
            print(f"  - {name}: {weight}")
