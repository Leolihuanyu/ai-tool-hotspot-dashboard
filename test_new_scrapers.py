#!/usr/bin/env python3
"""测试新的高信号数据源爬虫

测试以下爬虫：
1. Reddit（优化版） - 15个高价值子版块
2. Hacker News - Ask HN + Who is Hiring
3. GitHub Discussions - Feature Requests

使用方法：
    python test_new_scrapers.py
"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.logger import get_logger

logger = get_logger(__name__)


def test_reddit_scraper():
    """测试Reddit爬虫"""
    print("\n" + "="*60)
    print("测试 Reddit 爬虫（优化版）")
    print("="*60)

    try:
        from src.scrapers.trends.reddit import RedditScraper

        scraper = RedditScraper()

        # 显示配置
        print(f"\n📊 子版块数量: {len(scraper.pain_point_subreddits)}")
        print(f"📊 高价值关键词数量: {len(scraper.high_value_keywords)}")
        print(f"\n子版块列表:")
        for sub in scraper.pain_point_subreddits[:5]:
            print(f"  - r/{sub}")
        print(f"  ... 共{len(scraper.pain_point_subreddits)}个")

        # 测试抓取热点
        print(f"\n🔍 测试抓取热点数据（限制5条）...")
        topics = scraper.scrape(limit=5)
        print(f"✅ 成功抓取 {len(topics)} 条热点")

        if topics:
            print(f"\n示例数据:")
            topic = topics[0]
            print(f"  标题: {topic.get('title', '')[:60]}...")
            print(f"  来源: r/{topic.get('subreddit', '')}")
            print(f"  评分: {topic.get('score', 0)}")
            print(f"  评论数: {topic.get('num_comments', 0)}")

        # 测试痛点提取
        print(f"\n🔍 测试痛点提取（限制5条）...")
        pain_points = scraper.scrape_pain_points(limit=5, filter_by_keywords=True)
        print(f"✅ 成功提取 {len(pain_points)} 条高质量痛点")

        if pain_points:
            print(f"\n高价值痛点示例:")
            pp = pain_points[0]
            print(f"  文本: {pp['text'][:80]}...")
            print(f"  付费意愿分数: {pp.get('payment_willingness_score', 0)}")
            print(f"  匹配关键词: {pp.get('matched_keywords', [])}")
            print(f"  Engagement分数: {pp.get('engagement_score', 0):.1f}")

        print(f"\n✅ Reddit爬虫测试通过！")
        return True

    except Exception as e:
        print(f"\n❌ Reddit爬虫测试失败: {e}")
        logger.error(f"Reddit scraper test failed: {e}", exc_info=True)
        return False


def test_hackernews_scraper():
    """测试Hacker News爬虫"""
    print("\n" + "="*60)
    print("测试 Hacker News 爬虫")
    print("="*60)

    try:
        from src.scrapers.trends.hackernews import HackerNewsScraper

        scraper = HackerNewsScraper()

        # 显示配置
        print(f"\n📊 Ask HN关键词: {len(scraper.ask_hn_keywords)}个")
        print(f"📊 付费意愿信号: {len(scraper.monetization_signals)}个")

        # 测试抓取
        print(f"\n🔍 测试抓取数据（限制5条）...")
        stories = scraper.scrape(limit=5)
        print(f"✅ 成功抓取 {len(stories)} 条Story")

        if stories:
            print(f"\n示例数据:")
            story = stories[0]
            print(f"  标题: {story.get('title', '')[:60]}...")
            print(f"  类型: {story.get('type', '')}")
            print(f"  评分: {story.get('score', 0)}")
            print(f"  评论数: {story.get('num_comments', 0)}")
            print(f"  匹配关键词: {story.get('matched_keywords', [])}")

        # 测试痛点提取
        print(f"\n🔍 测试痛点提取（限制3条）...")
        pain_points = scraper.scrape_pain_points(limit=3)
        print(f"✅ 成功提取 {len(pain_points)} 条痛点")

        if pain_points:
            print(f"\n痛点示例:")
            pp = pain_points[0]
            print(f"  上下文: {pp['context_title'][:60]}...")
            print(f"  类型: {pp.get('type', '')}")
            print(f"  Engagement分数: {pp.get('engagement_score', 0):.1f}")

        print(f"\n✅ Hacker News爬虫测试通过！")
        return True

    except Exception as e:
        print(f"\n❌ Hacker News爬虫测试失败: {e}")
        logger.error(f"HackerNews scraper test failed: {e}", exc_info=True)
        return False


def test_github_scraper():
    """测试GitHub Discussions爬虫"""
    print("\n" + "="*60)
    print("测试 GitHub Discussions 爬虫")
    print("="*60)

    try:
        from src.scrapers.trends.github_discussions import GitHubDiscussionsScraper

        scraper = GitHubDiscussionsScraper()

        # 显示配置
        print(f"\n📊 目标仓库数量: {len(scraper.target_repos)}")
        print(f"\n目标仓库示例:")
        for repo in scraper.target_repos[:5]:
            print(f"  - {repo}")
        print(f"  ... 共{len(scraper.target_repos)}个")

        # 检查GitHub Token
        if not scraper.github_token:
            print(f"\n⚠️  警告: 未配置GITHUB_TOKEN，请在.env中配置")
            print(f"   跳过GitHub Discussions测试")
            return True

        # 测试抓取
        print(f"\n🔍 测试抓取Discussions（限制3条）...")
        discussions = scraper.scrape(limit=3)
        print(f"✅ 成功抓取 {len(discussions)} 条Discussion")

        if discussions:
            print(f"\n示例数据:")
            disc = discussions[0]
            print(f"  标题: {disc.get('title', '')[:60]}...")
            print(f"  仓库: {disc.get('repo', '')}")
            print(f"  👍数: {disc.get('upvote_count', 0)}")
            print(f"  评论数: {disc.get('comment_count', 0)}")
            print(f"  匹配关键词: {disc.get('matched_keywords', [])}")

        # 测试痛点提取
        print(f"\n🔍 测试痛点提取（限制3条）...")
        pain_points = scraper.scrape_pain_points(limit=3)
        print(f"✅ 成功提取 {len(pain_points)} 条痛点")

        if pain_points:
            print(f"\n痛点示例:")
            pp = pain_points[0]
            print(f"  上下文: {pp['context_title'][:60]}...")
            print(f"  Engagement分数: {pp.get('engagement_score', 0):.1f}")
            print(f"  付费意愿分数: {pp.get('payment_willingness_score', 0):.1f}")

        print(f"\n✅ GitHub Discussions爬虫测试通过！")
        return True

    except Exception as e:
        print(f"\n❌ GitHub Discussions爬虫测试失败: {e}")
        logger.error(f"GitHub scraper test failed: {e}", exc_info=True)
        return False


def main():
    """主测试函数"""
    print("\n🚀 开始测试新的高信号数据源爬虫\n")

    results = {
        'Reddit': test_reddit_scraper(),
        'Hacker News': test_hackernews_scraper(),
        'GitHub Discussions': test_github_scraper(),
    }

    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)

    passed = sum(results.values())
    total = len(results)

    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！新的数据源已准备就绪。")
        print("\n下一步:")
        print("  1. 配置API密钥（.env文件）:")
        print("     - REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET")
        print("     - GITHUB_TOKEN")
        print("  2. 运行完整流程: make run-pipeline")
        print("  3. 查看仪表板: make run-dashboard")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查错误信息")
        return 1


if __name__ == "__main__":
    sys.exit(main())
