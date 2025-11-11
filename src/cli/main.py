"""命令行接口主入口

提供所有CLI命令:init-db, scrape, run-pipeline, send-email等。
"""

import sys
import argparse
from src.database import init_database
from src.utils.config import config
from src.utils.logger import default_logger


def cmd_init_db(args):
    """初始化数据库命令"""
    print(f"🔧 Initializing database at {config.database_path}...")

    success = init_database()

    if success:
        print("✅ Database initialized successfully!")
        print(f"   Location: {config.database_path}")
        print("   Tables created: ai_tools, trending_topics, pain_points, opportunities, scraping_logs")
        return 0
    else:
        print("❌ Database initialization failed!")
        print("   Check logs/app.log for details")
        return 1


def cmd_scrape(args):
    """数据抓取命令"""
    print("🔍 Starting data scraping...")
    print(f"   Test mode: {args.test_mode}")
    if args.limit:
        print(f"   Limit: {args.limit} records per source")
    if args.source:
        print(f"   Source filter: {args.source}")
    if args.type:
        print(f"   Type filter: {args.type}")

    try:
        # 导入必要的模块
        from src.scrapers.ai_tools.futurepedia import FuturepediaScraper
        from src.scrapers.ai_tools.theresanai import TheresAnAIForThatScraper
        from src.scrapers.ai_tools.producthunt import ProductHuntScraper
        from src.scrapers.trends.tiktok import TikTokScraper
        from src.scrapers.trends.youtube import YouTubeScraper
        from src.scrapers.trends.x_twitter import XTwitterScraper
        from src.scrapers.trends.reddit import RedditScraper
        from src.scrapers.trends.google_trends import GoogleTrendsScraper
        from src.scrapers.trends.hackernews import HackerNewsScraper
        from src.scrapers.trends.github_discussions import GitHubDiscussionsScraper
        from src.pipeline.normalizer import DataNormalizer
        from src.pipeline.deduplicator import Deduplicator
        from src.llm.summarizer import BilingualSummarizer
        from src.scoring.data_quality import DataQualityScorer
        from src.scoring.trending import TrendingScorer
        from src.pipeline.exporter import DataExporter
        from src.pipeline.archiver import DataArchiver

        # 初始化组件
        normalizer = DataNormalizer()
        deduplicator = Deduplicator()
        summarizer = BilingualSummarizer()
        quality_scorer = DataQualityScorer()
        trending_scorer = TrendingScorer()
        exporter = DataExporter()
        archiver = DataArchiver()

        # 初始化AI工具爬虫
        ai_tool_scrapers = {
            'Futurepedia': FuturepediaScraper(),
            "There's an AI for That": TheresAnAIForThatScraper(),
            'ProductHunt': ProductHuntScraper()
        }

        # 初始化热点爬虫（优先高信号数据源）
        trend_scrapers = {
            'Reddit': RedditScraper(),  # 优化版，15个高价值子版块
            'Hacker News': HackerNewsScraper(),  # Ask HN + Who is Hiring
            'GitHub Discussions': GitHubDiscussionsScraper(),  # Feature Requests
            'TikTok': TikTokScraper(),
            'YouTube': YouTubeScraper(),
            'X': XTwitterScraper(),
            'Google Trends': GoogleTrendsScraper()
        }

        # 注册爬虫到normalizer
        for scraper in list(ai_tool_scrapers.values()) + list(trend_scrapers.values()):
            normalizer.register_scraper(scraper)

        limit = args.limit if args.limit else (5 if args.test_mode else None)
        all_tools = []
        all_topics = []

        # 抓取AI工具数据
        if not args.type or args.type == 'ai_tools':
            print("\n📱 Scraping AI Tools...")
            for source_name, scraper in ai_tool_scrapers.items():
                if args.source and args.source != source_name:
                    continue

                try:
                    print(f"📡 [{source_name}] Scraping...")
                    raw_data = scraper.scrape(limit=limit)
                    normalized_tools = normalizer.normalize_ai_tools(raw_data, source_name)
                    all_tools.extend(normalized_tools)
                    print(f"✅ [{source_name}] Success: {len(normalized_tools)} records")
                except Exception as e:
                    print(f"❌ [{source_name}] Failed: {e}")
                    default_logger.error(f"AI tool scraping failed for {source_name}: {e}", exc_info=True)
                    continue

            # 去重
            if all_tools:
                print(f"🔄 Deduplicating AI tools...")
                unique_tools = deduplicator.deduplicate_ai_tools(all_tools)
                print(f"✅ Deduplicated: {len(unique_tools)} unique tools")

                # 计算质量分数
                print(f"📊 Calculating quality scores for AI tools...")
                scored_tools = quality_scorer.batch_score(unique_tools)

                # 生成摘要
                print(f"🧠 Generating summaries for AI tools...")
                all_tools = summarizer.batch_summarize(scored_tools)

        # 抓取热点数据
        if not args.type or args.type == 'trends':
            print("\n🔥 Scraping Trending Topics...")
            for source_name, scraper in trend_scrapers.items():
                if args.source and args.source != source_name:
                    continue

                try:
                    print(f"📡 [{source_name}] Scraping...")
                    raw_data = scraper.scrape(limit=limit)
                    normalized_topics = normalizer.normalize_trending_topics(raw_data, source_name)
                    all_topics.extend(normalized_topics)
                    print(f"✅ [{source_name}] Success: {len(normalized_topics)} records")
                except Exception as e:
                    print(f"❌ [{source_name}] Failed: {e}")
                    default_logger.error(f"Trending scraping failed for {source_name}: {e}", exc_info=True)
                    continue

            # 去重
            if all_topics:
                print(f"🔄 Deduplicating trending topics...")
                unique_topics = deduplicator.deduplicate_trending_topics(all_topics)
                print(f"✅ Deduplicated: {len(unique_topics)} unique topics")

                # 计算趋势方向和质量分数
                print(f"📊 Calculating trend directions and quality scores...")
                # 为每个话题计算趋势方向（使用空的历史数据列表）
                scored_topics = []
                for topic in unique_topics:
                    topic.trend_direction = trending_scorer.calculate_trend_direction(topic, [])
                    scored_topics.append(topic)
                # 批量计算质量分数
                scored_topics = quality_scorer.batch_score(scored_topics)

                # 生成摘要
                print(f"🧠 Generating summaries for trending topics...")
                all_topics = summarizer.batch_summarize(scored_topics)

        # 导出数据前，先读取现有数据以避免覆盖
        print(f"\n💾 Merging with existing data...")
        existing_tools = []
        existing_topics = []
        try:
            import json
            from pathlib import Path
            latest_path = Path('data/latest.json')
            if latest_path.exists():
                with open(latest_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    # 如果当前没有抓取ai_tools，保留现有的
                    if not all_tools and existing_data.get('ai_tools'):
                        from src.models.tool import AITool
                        existing_tools = [AITool(**t) for t in existing_data['ai_tools']]
                    # 如果当前没有抓取trending_topics，保留现有的
                    if not all_topics and existing_data.get('trending_topics'):
                        from src.models.trend import TrendingTopic
                        existing_topics = [TrendingTopic(**t) for t in existing_data['trending_topics']]
                    print(f"  ✅ Loaded existing data: {len(existing_tools)} tools, {len(existing_topics)} topics")
        except Exception as e:
            print(f"  ⚠️  Could not load existing data: {e}")

        # 合并数据：使用新抓取的数据，如果没有新数据则使用现有数据
        final_tools = all_tools if all_tools else existing_tools
        final_topics = all_topics if all_topics else existing_topics

        # 导出合并后的数据
        print(f"💾 Exporting to JSON...")
        output_file = exporter.export_to_json(
            ai_tools=final_tools,
            trending_topics=final_topics
        )
        print(f"✅ Data exported: {output_file}")

        # 归档
        print(f"📦 Archiving...")
        archive_file = archiver.archive_latest()
        if archive_file:
            print(f"✅ Data archived: {archive_file}")

        print(f"\n📊 Summary:")
        print(f"   - AI Tools: {len(all_tools)}")
        print(f"   - Trending Topics: {len(all_topics)}")
        print(f"\n✅ Scraping completed successfully!")
        return 0

    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        default_logger.error(f"Scraping failed: {e}", exc_info=True)
        return 1


def cmd_run_pipeline(args):
    """运行完整数据处理流程命令"""
    print("🚀 Starting full pipeline...")
    print("   Steps: scrape → normalize → dedupe → extract pain points → match → score → summarize → export")

    try:
        from src.pipeline.orchestrator import default_orchestrator
        from src.scrapers.ai_tools.futurepedia import FuturepediaScraper
        from src.scrapers.ai_tools.theresanai import TheresAnAIForThatScraper
        from src.scrapers.ai_tools.producthunt import ProductHuntScraper
        from src.scrapers.trends.tiktok import TikTokScraper
        from src.scrapers.trends.youtube import YouTubeScraper
        from src.scrapers.trends.x_twitter import XTwitterScraper
        from src.scrapers.trends.reddit import RedditScraper
        from src.scrapers.trends.google_trends import GoogleTrendsScraper
        from src.scrapers.trends.hackernews import HackerNewsScraper
        from src.scrapers.trends.github_discussions import GitHubDiscussionsScraper

        # 准备所有爬虫
        scrapers = {}

        # AI工具爬虫
        print("\n📱 Initializing AI tool scrapers...")
        try:
            scrapers['Futurepedia'] = FuturepediaScraper()
            print("  ✅ Futurepedia")
        except Exception as e:
            print(f"  ⚠️  Futurepedia: {e}")

        try:
            scrapers["There's an AI for That"] = TheresAnAIForThatScraper()
            print("  ✅ There's an AI for That")
        except Exception as e:
            print(f"  ⚠️  There's an AI for That: {e}")

        try:
            scrapers['ProductHunt'] = ProductHuntScraper()
            print("  ✅ ProductHunt")
        except Exception as e:
            print(f"  ⚠️  ProductHunt: {e}")

        # 高信号痛点数据源（2025年优化）
        print("\n💡 Initializing high-signal pain point scrapers...")
        try:
            scrapers['Reddit'] = RedditScraper()
            print("  ✅ Reddit (优化版 - 15个高价值子版块)")
        except Exception as e:
            print(f"  ⚠️  Reddit: {e}")

        try:
            scrapers['Hacker News'] = HackerNewsScraper()
            print("  ✅ Hacker News (Ask HN + Who is Hiring)")
        except Exception as e:
            print(f"  ⚠️  Hacker News: {e}")

        try:
            scrapers['GitHub Discussions'] = GitHubDiscussionsScraper()
            print("  ✅ GitHub Discussions (Feature Requests)")
        except Exception as e:
            print(f"  ⚠️  GitHub Discussions: {e}")

        # 其他热点爬虫（次要优先级）
        print("\n🔥 Initializing additional trending scrapers...")
        try:
            scrapers['TikTok'] = TikTokScraper()
            print("  ✅ TikTok")
        except Exception as e:
            print(f"  ⚠️  TikTok: {e}")

        try:
            scrapers['YouTube'] = YouTubeScraper()
            print("  ✅ YouTube")
        except Exception as e:
            print(f"  ⚠️  YouTube: {e}")

        try:
            scrapers['X'] = XTwitterScraper()
            print("  ✅ X (Twitter)")
        except Exception as e:
            print(f"  ⚠️  X: {e}")

        try:
            scrapers['Google Trends'] = GoogleTrendsScraper()
            print("  ✅ Google Trends")
        except Exception as e:
            print(f"  ⚠️  Google Trends: {e}")

        if not scrapers:
            print("\n❌ No scrapers available. Please check scraper implementations.")
            return 1

        print(f"\n✅ Initialized {len(scrapers)} scrapers")

        # 运行完整流程
        print("\n" + "="*60)
        success = default_orchestrator.run_full_pipeline(scrapers=scrapers)
        print("="*60 + "\n")

        if success:
            print("✅ Pipeline completed successfully!")
            print("\n📊 Next steps:")
            print("  1. Run dashboard: python -m src.dashboard.app")
            print("  2. Visit: http://127.0.0.1:5000/opportunities")
            return 0
        else:
            print("❌ Pipeline failed. Check logs for details.")
            return 1

    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        default_logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        return 1


def cmd_send_email(args):
    """发送邮件命令"""
    print("📧 Sending daily report email...")

    try:
        from src.email import get_email_sender, email_generator
        from src.email.subscriber_manager import get_subscriber_manager
        from src.utils.config import config

        # 获取正确的邮件发送器（根据配置选择SMTP或SendGrid）
        email_sender = get_email_sender()

        # 决定收件人来源：数据库 vs 环境变量
        use_database = getattr(args, 'use_db', False)
        to_emails = []

        if use_database:
            print("📊 Reading subscribers from database...")
            subscriber_manager = get_subscriber_manager()
            to_emails = subscriber_manager.get_subscriber_emails(
                include_beta=True,
                include_paid=True
            )

            if not to_emails:
                print("⚠️  No active subscribers found in database")
                print("💡 Please ensure users table has active subscribers")
                return 1

            print(f"✅ Found {len(to_emails)} active subscribers")
        else:
            print("📧 Reading recipients from EMAIL_TO_LIST...")
            to_emails = config.email_to_list

            if not to_emails:
                print("⚠️  EMAIL_TO_LIST is empty")
                print("\n💡 You can either:")
                print("   1. Set EMAIL_TO_LIST in .env file")
                print("   2. Use --use-db flag to read from database")
                return 1

            print(f"✅ Found {len(to_emails)} recipients from config")

        # 验证邮件配置（发件人和SMTP配置）
        print("\n🔍 Validating email sender configuration...")
        # 临时设置EMAIL_TO_LIST以通过验证
        original_to_list = config.email_to_list
        if not config.email_to_list:
            config.__dict__['_email_to_list_cache'] = to_emails

        is_valid, missing = email_sender.validate_config()

        # 恢复原始配置
        if hasattr(config, '_email_to_list_cache'):
            delattr(config, '_email_to_list_cache')

        if not is_valid:
            print(f"❌ Email sender configuration incomplete:")
            for item in missing:
                if item != "EMAIL_TO_LIST":  # 忽略EMAIL_TO_LIST，因为我们可能从数据库读取
                    print(f"   - Missing: {item}")
            print("\n💡 Please configure the following in .env file:")
            print("   - SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD")
            print("   - Or: SENDGRID_API_KEY")
            print("   - EMAIL_FROM")
            return 1

        print("✅ Email sender configuration valid")

        # 生成邮件内容
        print("\n📝 Generating email content...")
        try:
            # 优先使用环境变量中的配置，命令行参数可以覆盖
            dashboard_url = config.dashboard_url
            if hasattr(args, 'dashboard_url') and args.dashboard_url and args.dashboard_url != "http://127.0.0.1:5000":
                # 只有明确指定了非默认值，才使用命令行参数
                dashboard_url = args.dashboard_url
            subject, html_content, plain_text = email_generator.generate_email_content(
                dashboard_url=dashboard_url
            )
            print(f"✅ Email content generated")
            print(f"   Subject: {subject}")
        except FileNotFoundError as e:
            print(f"❌ Failed to generate email content: {e}")
            print("\n💡 Please run the pipeline first to generate data:")
            print("   python -m src.cli.main run-pipeline")
            return 1
        except Exception as e:
            print(f"❌ Failed to generate email content: {e}")
            default_logger.error(f"Email content generation failed: {e}", exc_info=True)
            return 1

        # 发送邮件
        print(f"\n📤 Sending email to {len(to_emails)} recipient(s)...")
        result = email_sender.send_html_email(
            to_emails=to_emails,
            subject=subject,
            html_content=html_content,
            plain_text_content=plain_text
        )

        if result["success"]:
            print(f"✅ Email sent successfully!")
            print(f"   Recipients: {', '.join(result['recipients'])}")
            print(f"   Status code: {result['status_code']}")
            print(f"   Timestamp: {result['timestamp']}")

            # 记录发送日志
            default_logger.info({
                "event": "email_command_completed",
                "status": "success",
                "recipients_count": len(result['recipients']),
                "timestamp": result['timestamp']
            })

            return 0
        else:
            print(f"❌ Email sending failed:")
            for error in result["errors"]:
                print(f"   - {error}")

            # 如果配置了管理员邮箱,发送失败告警
            admin_email = config.email_from  # 默认发给发件人自己
            if admin_email and not args.no_alert:
                print(f"\n⚠️  Sending failure alert to admin: {admin_email}")
                alert_result = email_sender.send_failure_alert(
                    admin_email=admin_email,
                    failure_details={
                        **result,
                        "subject": subject
                    }
                )
                if alert_result["success"]:
                    print(f"✅ Failure alert sent")
                else:
                    print(f"❌ Failed to send failure alert")

            # 记录失败日志
            default_logger.error({
                "event": "email_command_failed",
                "status": "failed",
                "errors": result["errors"],
                "timestamp": result['timestamp']
            })

            return 1

    except Exception as e:
        print(f"❌ Email command failed: {e}")
        default_logger.error(f"Email command failed: {e}", exc_info=True)
        return 1


def cmd_check_expiry(args):
    """检查并发送过期提醒邮件"""
    print("⏰ 检查即将过期的用户...")

    try:
        from src.email.expiry_reminder import ExpiryReminderService

        service = ExpiryReminderService()

        # 获取时区过滤参数
        use_timezone = getattr(args, 'use_timezone', False)
        target_hour = getattr(args, 'target_hour', 9)

        # 如果指定了天数，只发送特定天数的提醒
        if args.days:
            if args.days not in [1, 7, 14]:
                print(f"❌ 错误: --days 必须是 1, 7 或 14")
                return 1

            timezone_msg = f" (按时区过滤，目标时间: {target_hour}:00)" if use_timezone else ""
            print(f"\n📧 发送 {args.days} 天过期提醒{timezone_msg}...")
            users = service.get_expiring_users(
                args.days,
                filter_by_timezone=use_timezone,
                target_hour=target_hour
            )

            if not users:
                print(f"✅ 没有找到即将在 {args.days} 天后过期的用户{timezone_msg}")
                return 0

            print(f"找到 {len(users)} 个用户")
            sent = 0
            failed = 0

            for user in users:
                language = args.language or None  # None 表示从用户数据中获取
                if service.send_expiry_reminder(user, args.days, language):
                    sent += 1
                else:
                    failed += 1

            print(f"\n✅ 完成: 成功 {sent}, 失败 {failed}")
            return 0 if failed == 0 else 1

        else:
            # 运行完整的每日检查（14天、7天、1天）
            timezone_msg = f" (按时区过滤，目标时间: {target_hour}:00)" if use_timezone else ""
            print(f"\n📧 运行过期提醒检查（14天、7天、1天）{timezone_msg}...")
            result = service.run_daily_check(
                use_timezone_filter=use_timezone,
                target_hour=target_hour
            )

            if result.get("success"):
                print(f"\n✅ 检查完成!")
                print(f"   总共发送: {result['total_sent']} 封邮件")
                print(f"   发送失败: {result['total_failed']} 封邮件")
                print(f"\n详细统计:")
                print(f"   14天提醒: {result['details']['14_days']['sent']} 成功, {result['details']['14_days']['failed']} 失败")
                print(f"   7天提醒: {result['details']['7_days']['sent']} 成功, {result['details']['7_days']['failed']} 失败")
                print(f"   1天提醒: {result['details']['1_day']['sent']} 成功, {result['details']['1_day']['failed']} 失败")
                return 0
            else:
                print("❌ 过期提醒检查失败")
                return 1

    except Exception as e:
        print(f"❌ 过期提醒检查失败: {e}")
        default_logger.error(f"过期提醒检查失败: {e}", exc_info=True)
        return 1


def cmd_reproduce(args):
    """重新处理最新数据命令"""
    print("♻️  Reproducing from latest data...")

    # TODO: 实现数据重处理(Phase N)
    print("⚠️  Reproduce not yet implemented (coming in Phase N)")
    return 0


def cmd_cleanup(args):
    """清理旧数据命令"""
    print(f"🧹 Cleaning up data older than {args.days} days...")

    # TODO: 实现数据清理(Phase N)
    print("⚠️  Cleanup not yet implemented (coming in Phase N)")
    return 0


def cmd_optimize_db(args):
    """优化数据库命令"""
    print("⚡ Optimizing database...")

    # TODO: 实现数据库优化(Phase N)
    print("⚠️  Database optimization not yet implemented (coming in Phase N)")
    return 0


def main():
    """CLI主函数"""
    parser = argparse.ArgumentParser(
        description="AI工具与热点机会发现仪表板 - CLI工具"
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # init-db命令
    parser_init_db = subparsers.add_parser("init-db", help="初始化数据库")
    parser_init_db.set_defaults(func=cmd_init_db)

    # scrape命令
    parser_scrape = subparsers.add_parser("scrape", help="运行数据抓取")
    parser_scrape.add_argument("--test-mode", action="store_true", help="测试模式(仅抓取少量数据)")
    parser_scrape.add_argument("--limit", type=int, help="限制每个数据源的记录数")
    parser_scrape.add_argument("--source", type=str, help="仅抓取指定数据源")
    parser_scrape.add_argument("--type", type=str, choices=['ai_tools', 'trends'], help="数据类型过滤(ai_tools或trends)")
    parser_scrape.set_defaults(func=cmd_scrape)

    # run-pipeline命令
    parser_pipeline = subparsers.add_parser("run-pipeline", help="运行完整数据处理流程")
    parser_pipeline.set_defaults(func=cmd_run_pipeline)

    # send-email命令
    parser_email = subparsers.add_parser("send-email", help="发送每日报告邮件")
    parser_email.add_argument("--dashboard-url", type=str, default=None, help="仪表板URL(用于邮件中的链接，默认从环境变量DASHBOARD_URL读取)")
    parser_email.add_argument("--no-alert", action="store_true", help="发送失败时不发送告警邮件")
    parser_email.add_argument("--use-db", action="store_true", help="从数据库读取活跃订阅者(默认使用EMAIL_TO_LIST)")
    parser_email.set_defaults(func=cmd_send_email)

    # check-expiry命令
    parser_expiry = subparsers.add_parser("check-expiry", help="检查并发送过期提醒邮件")
    parser_expiry.add_argument("--days", type=int, choices=[1, 7, 14], help="仅检查指定天数的过期提醒(1/7/14)")
    parser_expiry.add_argument("--language", type=str, choices=["zh", "en", "ja"], help="邮件语言(默认zh)")
    parser_expiry.add_argument("--use-timezone", action="store_true", help="按用户时区过滤（仅在当地上午9点发送）")
    parser_expiry.add_argument("--target-hour", type=int, default=9, help="目标小时（默认9点，配合--use-timezone使用）")
    parser_expiry.set_defaults(func=cmd_check_expiry)

    # reproduce命令
    parser_reproduce = subparsers.add_parser("reproduce", help="重新处理最新数据")
    parser_reproduce.set_defaults(func=cmd_reproduce)

    # cleanup命令
    parser_cleanup = subparsers.add_parser("cleanup", help="清理旧数据")
    parser_cleanup.add_argument("--days", type=int, default=7, help="保留最近N天的数据(默认7)")
    parser_cleanup.set_defaults(func=cmd_cleanup)

    # optimize-db命令
    parser_optimize = subparsers.add_parser("optimize-db", help="优化数据库")
    parser_optimize.set_defaults(func=cmd_optimize_db)

    # 解析参数
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # 执行命令
    try:
        return args.func(args)
    except Exception as e:
        default_logger.error(f"Command failed: {e}")
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
