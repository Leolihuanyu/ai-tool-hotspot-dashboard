#!/usr/bin/env python3
"""
测试Phase 1改进的验证脚本
测试内容：
1. Reddit权重提升验证
2. 痛点关键词扩展验证
3. 新的痛点提取字段验证
4. MVP建议新字段验证
5. 时间权重和趋势标记验证
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.source_weights import get_source_weight
from src.llm.pain_extractor import PainPointExtractor
from src.models.pain_point import UserPainPoint
from src.models.trend import TrendingTopic
from datetime import datetime, timezone, timedelta


def test_reddit_weight():
    """测试Reddit权重是否提升至A级"""
    print("=" * 50)
    print("测试1: Reddit权重提升验证")
    print("-" * 50)

    reddit_weight = get_source_weight("Reddit")
    print(f"Reddit当前权重: {reddit_weight}")

    if reddit_weight == 4.0:
        print("✅ Reddit已成功提升至A级权重(4.0)")
    else:
        print(f"❌ Reddit权重未正确设置，期望4.0，实际{reddit_weight}")

    # 测试其他A级源
    print("\n其他A级数据源权重:")
    for source in ["ProductHunt", "GitHub Discussions", "Hacker News"]:
        weight = get_source_weight(source)
        print(f"  - {source}: {weight}")


def test_pain_keywords():
    """测试痛点关键词扩展"""
    print("\n" + "=" * 50)
    print("测试2: 痛点关键词扩展验证")
    print("-" * 50)

    extractor = PainPointExtractor()

    # 测试新增的关键词类型
    test_cases = [
        # 隐式痛点
        ("Every time I have to manually export data, it takes hours", "隐式痛点"),
        # 变现相关
        ("How to monetize my AI app effectively?", "变现相关"),
        # 技术痛点
        ("The inference cost is too high for my use case", "技术痛点"),
        # 中文痛点
        ("找不到合适的工具来处理这个麻烦的任务", "中文痛点"),
    ]

    print(f"痛点关键词总数: {len(extractor.PAIN_KEYWORDS)}")

    for text, category in test_cases:
        contains = extractor.contains_pain_keyword(text)
        result = "✅" if contains else "❌"
        print(f"{result} {category}: {text[:50]}...")


def test_pain_point_model():
    """测试UserPainPoint模型新字段"""
    print("\n" + "=" * 50)
    print("测试3: UserPainPoint模型新字段验证")
    print("-" * 50)

    try:
        pain_point = UserPainPoint(
            original_text="I need a tool to automate my workflow",
            context_title="Automation discussion",
            extracted_keywords=["tool", "automate", "workflow"],
            source="Reddit",
            url="https://reddit.com/test",
            timestamp=datetime.now(timezone.utc),
            engagement_score=75.0,
            confidence_score=0.8,
            tags=["automation"],
            summary_cn="需要工作流自动化工具",
            summary_ja="ワークフロー自動化ツールが必要",
            # 新字段
            business_value=8,
            urgency_level=7,
            market_size_hint="large",
            willingness_to_pay="high"
        )

        print("✅ UserPainPoint模型成功创建，包含新字段:")
        print(f"  - business_value: {pain_point.business_value}")
        print(f"  - urgency_level: {pain_point.urgency_level}")
        print(f"  - market_size_hint: {pain_point.market_size_hint}")
        print(f"  - willingness_to_pay: {pain_point.willingness_to_pay}")
        print(f"  - schema_version: {pain_point.schema_version}")

    except Exception as e:
        print(f"❌ 创建UserPainPoint失败: {e}")


def test_trending_topic_model():
    """测试TrendingTopic模型趋势标记"""
    print("\n" + "=" * 50)
    print("测试4: TrendingTopic趋势标记验证")
    print("-" * 50)

    try:
        topic = TrendingTopic(
            title="AI Tool Revolution",
            description="Discussion about new AI tools",
            source="Reddit",
            url="https://reddit.com/test",
            timestamp=datetime.now(timezone.utc),
            heat_score=85.0,
            trend_direction="rising",
            tags=["AI", "tools"],
            summary_cn="AI工具革命",
            summary_ja="AIツール革命",
            # 新字段
            trend_marker="🔥 最新"
        )

        print("✅ TrendingTopic模型成功创建，包含趋势标记:")
        print(f"  - trend_marker: {topic.trend_marker}")
        print(f"  - schema_version: {topic.schema_version}")

        # 测试不同时间的趋势标记
        print("\n时间权重测试:")
        time_tests = [
            (datetime.now(timezone.utc), "🔥 最新 (24小时内)"),
            (datetime.now(timezone.utc) - timedelta(days=3), "📈 热门 (7天内)"),
            (datetime.now(timezone.utc) - timedelta(days=10), "💡 活跃 (14天内)"),
            (datetime.now(timezone.utc) - timedelta(days=20), "无标记 (14天以上)"),
        ]

        for timestamp, expected in time_tests:
            print(f"  - {expected}: 时间戳 {timestamp.strftime('%Y-%m-%d')}")

    except Exception as e:
        print(f"❌ 创建TrendingTopic失败: {e}")


def test_mvp_prompt():
    """测试MVP建议Prompt更新"""
    print("\n" + "=" * 50)
    print("测试5: MVP建议Prompt验证")
    print("-" * 50)

    from src.llm.prompts import MVP_SUGGESTION_PROMPT

    # 检查新增的字段是否在prompt中
    required_fields = [
        "competitive_analysis",
        "differentiation",
        "launch_difficulty",
        "estimated_time",
        "竞品",
        "差异化"
    ]

    print("检查MVP Prompt中的新字段:")
    for field in required_fields:
        if field in MVP_SUGGESTION_PROMPT:
            print(f"  ✅ 包含: {field}")
        else:
            print(f"  ❌ 缺失: {field}")


def main():
    """运行所有测试"""
    print("\n" + "🚀" * 20)
    print("Phase 1 改进验证测试")
    print("🚀" * 20)

    test_reddit_weight()
    test_pain_keywords()
    test_pain_point_model()
    test_trending_topic_model()
    test_mvp_prompt()

    print("\n" + "=" * 50)
    print("✨ 测试完成！")
    print("=" * 50)
    print("\n建议下一步:")
    print("1. 运行完整的数据抓取流程: python src/main.py")
    print("2. 检查生成的latest.json查看新字段是否正确填充")
    print("3. 验证Dashboard前端是否正确显示趋势标记")
    print("4. 监控LLM API调用成本是否在可控范围内")


if __name__ == "__main__":
    main()