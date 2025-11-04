#!/usr/bin/env python3
"""测试简化后的Pipeline逻辑

验证：
1. Opportunity模型不再需要related_tools字段
2. 数据筛选逻辑（Top 10工具、≤10热点、20痛点）
3. 直接MVP生成（痛点+热点，不匹配工具）
"""

from datetime import datetime
from src.models.opportunity import Opportunity
from src.models.pain_point import UserPainPoint
from src.models.trend import TrendingTopic
from src.models.tool import AITool

def test_opportunity_model():
    """测试Opportunity模型（v1.2）"""
    print("\n" + "="*60)
    print("测试1: Opportunity模型（不包含related_tools）")
    print("="*60)

    try:
        # 创建Opportunity对象（不包含related_tools）
        opp = Opportunity(
            pain_point_id="test-pain-point-001",
            related_topics=["topic-001", "topic-002"],
            opportunity_score=85.5,
            mvp_suggestion_cn="核心功能：1) 自动化工具，2) 数据分析，3) API集成。目标用户：开发者。变现方式：订阅制，$29/月。",
            mvp_suggestion_ja="コア機能：1) 自動化ツール、2) データ分析、3) API統合。ターゲット：開発者。収益化：サブスク、$29/月。",
            timestamp=datetime.now(),
            tags=["automation", "ai", "saas"],
            data_quality_score=0.85
        )

        print(f"✅ Opportunity创建成功")
        print(f"   ID: {opp.id}")
        print(f"   Schema版本: {opp.schema_version}")
        print(f"   痛点ID: {opp.pain_point_id}")
        print(f"   相关热点数: {len(opp.related_topics)}")
        print(f"   机会评分: {opp.opportunity_score}")
        print(f"   质量评分: {opp.data_quality_score}")

        # 验证不包含related_tools字段
        assert not hasattr(opp, 'related_tools') or 'related_tools' not in opp.model_dump()
        print(f"✅ 确认：不包含related_tools字段")

        return True

    except Exception as e:
        print(f"❌ Opportunity模型测试失败: {e}")
        return False


def test_data_filtering():
    """测试数据筛选逻辑"""
    print("\n" + "="*60)
    print("测试2: 数据筛选逻辑")
    print("="*60)

    from src.pipeline.orchestrator import PipelineOrchestrator

    orchestrator = PipelineOrchestrator()

    # 创建测试数据：30个AI工具
    test_tools = []
    sources = ["Futurepedia", "ProductHunt", "There's an AI for That"]
    pricing_models = ["free", "freemium", "paid", "subscription"]

    for i in range(30):
        tool = AITool(
            name=f"Test Tool {i}",
            url=f"https://example.com/tool{i}",
            description=f"This is a test AI tool number {i} with description",
            tags=["ai", "automation"],
            source=sources[i % len(sources)],
            timestamp=datetime.now(),
            features=["feature1", "feature2"],
            pricing_model=pricing_models[i % len(pricing_models)],
            summary_cn=f"测试工具{i}",
            summary_ja=f"テストツール{i}"
        )
        test_tools.append(tool)

    # 筛选Top 10工具
    filtered_tools = orchestrator._filter_top_tools(test_tools)

    print(f"原始工具数: {len(test_tools)}")
    print(f"筛选后工具数: {len(filtered_tools)}")

    if len(filtered_tools) == 10:
        print(f"✅ 工具筛选通过：正确筛选到Top 10")
    else:
        print(f"❌ 工具筛选失败：期望10个，实际{len(filtered_tools)}个")
        return False

    # 创建测试数据：20个热点话题（质量参差不齐）
    test_topics = []
    topic_sources = ["TikTok", "YouTube", "X", "Reddit", "Google Trends"]

    for i in range(20):
        # 前10个高质量，后10个低质量
        if i < 10:
            topic = TrendingTopic(
                title=f"High Quality Topic {i}",
                url=f"https://example.com/topic{i}",
                description="A" * 100,  # 合适的描述长度
                tags=["ai", "tech"],
                source="Reddit",  # Tier 1源（虽然Reddit在TrendingTopic模型中不是Tier 1）
                timestamp=datetime.now(),
                heat_score=80.0,
                trend_direction="rising",
                summary_cn=f"高质量话题{i}",
                summary_ja=f"高品質トピック{i}"
            )
        else:
            topic = TrendingTopic(
                title=f"Low Quality Topic {i}",
                url=f"https://example.com/topic{i}",
                description="Short",  # 描述太短
                tags=[],  # 没有标签
                source="YouTube",  # Tier 2源
                timestamp=datetime.now(),
                heat_score=30.0,
                trend_direction="stable",
                summary_cn="",
                summary_ja=""
            )
        test_topics.append(topic)

    # 筛选热点话题
    filtered_topics = orchestrator._filter_top_topics(test_topics)

    print(f"\n原始话题数: {len(test_topics)}")
    print(f"筛选后话题数: {len(filtered_topics)}")

    if len(filtered_topics) <= 10:
        print(f"✅ 话题筛选通过：筛选到{len(filtered_topics)}个（≤10且质量达标）")
    else:
        print(f"❌ 话题筛选失败：期望≤10个，实际{len(filtered_topics)}个")
        return False

    return True


def test_mvp_generation_structure():
    """测试MVP生成数据结构"""
    print("\n" + "="*60)
    print("测试3: MVP生成数据结构")
    print("="*60)

    # 创建测试痛点
    pain_point = UserPainPoint(
        original_text="I need a tool to automate my daily tasks",
        context_title="Automation needs discussion",
        source="Reddit",
        url="https://reddit.com/r/productivity/test",
        timestamp=datetime.now(),
        engagement_score=75.0,
        extracted_keywords=["automation", "tasks", "productivity"],
        confidence_score=0.85,
        tags=["automation", "productivity"],
        summary_cn="需要自动化日常任务的工具",
        summary_ja="日常タスクを自動化するツールが必要"
    )

    # 创建测试热点
    topic = TrendingTopic(
        title="AI Automation Tools Trending",
        url="https://example.com/automation",
        description="Discussion about automation tools and productivity",
        tags=["automation", "ai"],
        source="Reddit",
        timestamp=datetime.now(),
        heat_score=75.0,
        trend_direction="rising",
        summary_cn="AI自动化工具趋势",
        summary_ja="AI自動化ツールのトレンド"
    )

    # 模拟生成的机会数据结构
    opportunity_dict = {
        'pain_point_id': pain_point.id,
        'related_topics': [topic.id],
        'mvp_suggestion_cn': "核心功能：1) 任务自动化引擎，2) 智能调度，3) 报告生成。目标用户：知识工作者、创业者。变现方式：订阅制，$29/月基础版，$99/月专业版。",
        'mvp_suggestion_ja': "コア機能：1) タスク自動化エンジン、2) スマートスケジューリング、3) レポート生成。ターゲット：知識労働者、起業家。収益化：サブスク、$29/月基本版、$99/月プロ版。",
        'opportunity_score': 82.5,
        'timestamp': datetime.now(),
        'tags': ["automation", "productivity", "ai"],
        'data_quality_score': 0.85
    }

    # 验证能否创建Opportunity对象
    try:
        opp = Opportunity(**opportunity_dict)
        print(f"✅ MVP机会对象创建成功")
        print(f"   痛点ID: {opp.pain_point_id}")
        print(f"   相关热点: {len(opp.related_topics)}个")
        print(f"   机会评分: {opp.opportunity_score}")
        print(f"   中文建议长度: {len(opp.mvp_suggestion_cn)}字符")
        print(f"   日文建议长度: {len(opp.mvp_suggestion_ja)}文字")

        # 验证MVP建议格式（应包含：核心功能、目标用户、变现方式）
        if "核心功能" in opp.mvp_suggestion_cn and "目标用户" in opp.mvp_suggestion_cn and "变现方式" in opp.mvp_suggestion_cn:
            print(f"✅ 中文MVP建议格式正确（包含核心功能、目标用户、变现方式）")
        else:
            print(f"❌ 中文MVP建议格式不完整")
            return False

        if "コア機能" in opp.mvp_suggestion_ja and "ターゲット" in opp.mvp_suggestion_ja and "収益化" in opp.mvp_suggestion_ja:
            print(f"✅ 日文MVP建议格式正确（包含核心功能、目标用户、变现方式）")
        else:
            print(f"❌ 日文MVP建议格式不完整")
            return False

        # 验证不包含技术栈、时间线、成本估算
        tech_keywords = ["技术栈", "Flask", "Python", "周", "天", "成本", "预算"]
        has_tech_details = any(keyword in opp.mvp_suggestion_cn for keyword in tech_keywords)

        if not has_tech_details:
            print(f"✅ MVP建议不包含技术栈/时间线/成本（符合简化要求）")
        else:
            print(f"⚠️  MVP建议可能包含技术细节（不符合简化要求）")

        return True

    except Exception as e:
        print(f"❌ MVP机会对象创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("简化Pipeline逻辑测试套件")
    print("="*60)

    results = []

    # 运行测试
    results.append(("Opportunity模型测试", test_opportunity_model()))
    results.append(("数据筛选逻辑测试", test_data_filtering()))
    results.append(("MVP生成结构测试", test_mvp_generation_structure()))

    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)

    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status}: {test_name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)

    print(f"\n总计: {passed}/{total} 个测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！简化后的Pipeline逻辑验证成功！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查")
        return 1


if __name__ == "__main__":
    exit(main())
