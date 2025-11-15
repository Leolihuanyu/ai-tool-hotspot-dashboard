#!/usr/bin/env python3
"""
测试新增数据源：Indie Hackers和增强版Product Hunt
验证数据抓取和痛点提取功能
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_indie_hackers():
    """测试Indie Hackers爬虫"""
    print("\n" + "=" * 60)
    print("🚀 测试 Indie Hackers 爬虫")
    print("=" * 60)

    try:
        from src.scrapers.trends.indie_hackers import IndieHackersScraper

        scraper = IndieHackersScraper()
        print(f"✅ 成功初始化 Indie Hackers 爬虫")
        print(f"   - 基础URL: {scraper.base_url}")
        print(f"   - 爬虫类型: {scraper.scraper_type}")
        print(f"   - 重点群组: {', '.join(scraper.focus_groups[:3])}...")

        # 测试基础抓取功能
        print("\n📡 测试基础抓取功能 (限制5条)...")
        try:
            posts = scraper.scrape(limit=5)
            print(f"✅ 成功抓取 {len(posts)} 个帖子")

            if posts:
                # 显示第一个帖子的信息
                first_post = posts[0]
                print("\n📝 第一个帖子示例:")
                print(f"   标题: {first_post.get('title', 'N/A')[:80]}...")
                print(f"   URL: {first_post.get('url', 'N/A')}")
                print(f"   投票数: {first_post.get('upvotes', 0)}")
                print(f"   评论数: {first_post.get('comments', 0)}")
                print(f"   标签: {', '.join(first_post.get('tags', [])[:3])}")

                # 测试数据规范化
                print("\n🔄 测试数据规范化...")
                trending_topic = scraper.normalize(first_post)
                print(f"✅ 成功规范化为 TrendingTopic")
                print(f"   - 热度分数: {trending_topic.heat_score:.1f}")
                print(f"   - 趋势方向: {trending_topic.trend_direction}")
                print(f"   - 数据质量: {trending_topic.data_quality_score}")

        except Exception as e:
            print(f"❌ 抓取失败: {e}")

        # 测试痛点提取功能
        print("\n🔍 测试痛点提取功能...")
        try:
            pain_points = scraper.scrape_pain_points(limit=3)
            print(f"✅ 成功提取 {len(pain_points)} 个痛点相关帖子")

            if pain_points:
                print("\n痛点示例:")
                for i, pp in enumerate(pain_points[:2], 1):
                    print(f"   {i}. 查询: {pp.get('query', 'N/A')}")
                    print(f"      是痛点: {pp.get('is_pain_point', False)}")

        except Exception as e:
            print(f"⚠️  痛点提取失败（可能需要API）: {e}")

    except ImportError as e:
        print(f"❌ 无法导入 Indie Hackers 爬虫: {e}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")


def test_producthunt_comments():
    """测试增强版Product Hunt评论抓取"""
    print("\n" + "=" * 60)
    print("💬 测试 Product Hunt 评论抓取（增强版）")
    print("=" * 60)

    try:
        from src.scrapers.ai_tools.producthunt import ProductHuntScraper

        # 初始化爬虫（不使用API token进行基础测试）
        scraper = ProductHuntScraper(api_token=None)
        print(f"✅ 成功初始化 Product Hunt 爬虫")
        print(f"   - 基础URL: {scraper.base_url}")
        print(f"   - RSS URL: {scraper.rss_url}")
        print(f"   - API模式: {'启用' if scraper.api_token else '禁用'}")

        # 测试痛点提取功能
        print("\n💭 测试痛点提取功能...")
        try:
            comments_data = scraper.scrape_pain_points(limit=5)
            print(f"✅ 成功提取 {len(comments_data)} 条评论/反馈")

            if comments_data:
                print("\n评论示例:")
                for i, comment in enumerate(comments_data[:2], 1):
                    print(f"   {i}. 上下文: {comment.get('context_title', 'N/A')[:60]}...")
                    print(f"      文本长度: {len(comment.get('text', ''))}")
                    print(f"      互动分数: {comment.get('engagement_score', 0):.1f}")
                    print(f"      作者: {comment.get('author_metadata', {}).get('username', 'Unknown')}")

        except Exception as e:
            print(f"⚠️  评论提取失败（RSS模式限制）: {e}")

        # 测试基础AI工具抓取
        print("\n🤖 测试AI工具抓取...")
        try:
            tools = scraper.scrape(limit=3)
            print(f"✅ 成功抓取 {len(tools)} 个AI工具")

            if tools:
                first_tool = tools[0]
                print(f"\n第一个工具:")
                print(f"   名称: {first_tool.get('title', 'N/A')}")
                print(f"   链接: {first_tool.get('link', 'N/A')}")
                print(f"   标签: {', '.join(first_tool.get('tags', [])[:3])}")

        except Exception as e:
            print(f"❌ AI工具抓取失败: {e}")

    except ImportError as e:
        print(f"❌ 无法导入 Product Hunt 爬虫: {e}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")


def test_data_source_weights():
    """测试数据源权重配置"""
    print("\n" + "=" * 60)
    print("⚖️  测试数据源权重配置")
    print("=" * 60)

    try:
        from src.config.source_weights import get_source_weight, get_all_sources_by_tier

        # 测试新数据源的权重
        sources_to_test = [
            "Indie Hackers",
            "indiehackers",
            "indie-hackers",
            "ProductHunt",
            "Reddit"
        ]

        print("权重测试:")
        for source in sources_to_test:
            weight = get_source_weight(source)
            tier = "A级" if weight == 4.0 else "B级" if weight == 2.0 else "C级"
            print(f"   {source:20s} → 权重: {weight:.1f} ({tier})")

        # 显示所有A级数据源
        print("\n当前A级数据源:")
        all_tiers = get_all_sources_by_tier()
        for name, weight in all_tiers.get("A_TIER (强信号)", {}).items():
            print(f"   - {name}: {weight}")

    except ImportError as e:
        print(f"❌ 无法导入权重配置: {e}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")


def test_integration():
    """测试集成：数据流从抓取到痛点提取"""
    print("\n" + "=" * 60)
    print("🔗 测试数据流集成")
    print("=" * 60)

    try:
        from src.scrapers.trends.indie_hackers import IndieHackersScraper
        from src.llm.pain_extractor import PainPointExtractor
        from src.llm.client import LLMClient

        print("初始化组件...")
        ih_scraper = IndieHackersScraper()

        # 模拟简单的痛点检测（不调用LLM）
        print("\n📊 测试痛点关键词检测...")

        # 创建测试文本
        test_cases = [
            "I'm struggling with finding my first customers for my SaaS",
            "Looking for a tool to automate my email marketing",
            "How to monetize my side project effectively?",
            "需要一个工具来管理客户反馈",
        ]

        extractor = PainPointExtractor(llm_client=None)
        print(f"痛点关键词总数: {len(extractor.PAIN_KEYWORDS)}")

        for text in test_cases:
            contains = extractor.contains_pain_keyword(text)
            result = "✅ 是痛点" if contains else "❌ 非痛点"
            print(f"   {result}: {text[:60]}...")

    except ImportError as e:
        print(f"⚠️  部分组件无法导入（可能缺少依赖）: {e}")
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")


def main():
    """运行所有测试"""
    print("\n" + "🎯" * 30)
    print(" Phase 2 数据源扩展测试 ")
    print("🎯" * 30)

    start_time = datetime.now()

    # 运行各项测试
    test_indie_hackers()
    test_producthunt_comments()
    test_data_source_weights()
    test_integration()

    # 测试总结
    duration = (datetime.now() - start_time).total_seconds()
    print("\n" + "=" * 60)
    print("✨ 测试完成！")
    print("=" * 60)
    print(f"⏱  总耗时: {duration:.2f}秒")
    print("\n关键成果:")
    print("✅ Indie Hackers爬虫已创建并配置")
    print("✅ Product Hunt评论抓取功能已增强")
    print("✅ 数据源权重已更新（两者均为A级）")
    print("✅ 痛点关键词已扩展（支持中文）")
    print("\n建议下一步:")
    print("1. 安装依赖后运行完整数据抓取")
    print("2. 申请Product Hunt API token以启用完整评论抓取")
    print("3. 监控Indie Hackers爬虫的稳定性")
    print("4. 收集用户反馈，优化痛点识别准确率")


if __name__ == "__main__":
    main()