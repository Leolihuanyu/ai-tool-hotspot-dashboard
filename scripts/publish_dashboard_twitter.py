#!/usr/bin/env python3
"""
Dashboard Twitter发布脚本
自动截取Dashboard图片并发布到Twitter
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import tweepy

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.capture_dashboard import DashboardCapture
from scripts.process_dashboard_images import DashboardImageProcessor

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/dashboard_twitter_publisher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DashboardTwitterPublisher:
    """Dashboard Twitter发布器"""

    def __init__(self):
        """初始化发布器"""
        self.twitter_client = None
        self.capture = DashboardCapture()
        self.processor = DashboardImageProcessor()
        self.data_path = "data/latest.json"

    def init_twitter_client(self) -> bool:
        """初始化Twitter客户端"""
        try:
            # Twitter API v2 客户端
            self.twitter_client = tweepy.Client(
                consumer_key=os.getenv('TWITTER_API_KEY'),
                consumer_secret=os.getenv('TWITTER_API_SECRET'),
                access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
                access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
            )

            # API v1.1 用于上传媒体
            auth = tweepy.OAuth1UserHandler(
                os.getenv('TWITTER_API_KEY'),
                os.getenv('TWITTER_API_SECRET'),
                os.getenv('TWITTER_ACCESS_TOKEN'),
                os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
            )
            self.media_api = tweepy.API(auth)

            logger.info("Twitter客户端初始化成功")
            return True

        except Exception as e:
            logger.error(f"Twitter客户端初始化失败: {e}")
            return False

    def load_dashboard_data(self) -> Dict:
        """加载Dashboard数据用于生成文案"""
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 提取关键数据
            summary = {
                'total_tools': len(data.get('tools', [])),
                'total_trends': len(data.get('trends', [])),
                'total_opportunities': len(data.get('opportunities', [])),
                'top_tool': data.get('tools', [{}])[0].get('title', 'N/A') if data.get('tools') else 'N/A',
                'top_trend': data.get('trends', [{}])[0].get('title', 'N/A') if data.get('trends') else 'N/A',
                'top_opportunity': data.get('opportunities', [{}])[0] if data.get('opportunities') else {},
                'date': datetime.now().strftime('%Y-%m-%d')
            }

            logger.info(f"Loaded dashboard data: {summary['total_tools']} tools, "
                       f"{summary['total_trends']} trends, {summary['total_opportunities']} opportunities")
            return summary

        except Exception as e:
            logger.error(f"Failed to load dashboard data: {e}")
            return {}

    def generate_tweet_content(self, data_summary: Dict) -> str:
        """生成推文内容"""
        # 根据数据生成不同风格的推文
        templates = [
            # 数据驱动型
            f"""🚀 Today's AI Hotspot Analysis is live!

📊 Dashboard Highlights:
• {data_summary.get('total_tools', 10)} AI Tools analyzed
• Top trend: {data_summary.get('top_trend', 'AI Agents')[:50]}
• Featured opportunity score: {data_summary.get('top_opportunity', {}).get('score', '9000+')}

See full dashboard & get daily insights 👇
https://ai-hotspot.com?utm_source=twitter&utm_campaign=daily_{data_summary.get('date')}""",

            # 机会聚焦型
            f"""💡 New AI opportunity discovered!

{data_summary.get('top_opportunity', {}).get('title', 'Revolutionary AI Tool')}
Score: {data_summary.get('top_opportunity', {}).get('score', '9000+')}

Plus {data_summary.get('total_opportunities', 10)-1} more opportunities in today's dashboard.

Explore now 👇
https://ai-hotspot.com?utm_source=twitter&utm_campaign=daily_{data_summary.get('date')}""",

            # 趋势洞察型
            f"""📈 AI Market Pulse - {datetime.now().strftime('%B %d')}

🔥 Trending: {data_summary.get('top_trend', 'AI Innovation')[:60]}
🛠️ {data_summary.get('total_tools', 10)} new tools discovered
💎 {data_summary.get('total_opportunities', 10)} business opportunities

Visual dashboard below 👇 Full analysis at:
https://ai-hotspot.com?utm_source=twitter&utm_campaign=daily_{data_summary.get('date')}"""
        ]

        # 选择模板（可以基于A/B测试或轮换）
        import random
        selected_template = random.choice(templates)

        # 确保不超过280字符
        if len(selected_template) > 280:
            # 截断并添加省略号
            selected_template = selected_template[:277] + "..."

        return selected_template

    def upload_media(self, image_paths: List[str]) -> List[str]:
        """上传图片到Twitter"""
        media_ids = []

        for image_path in image_paths:
            try:
                # 上传媒体文件
                media = self.media_api.media_upload(image_path)
                media_ids.append(media.media_id_string)
                logger.info(f"Uploaded media: {image_path} -> {media.media_id_string}")

            except Exception as e:
                logger.error(f"Failed to upload media {image_path}: {e}")

        return media_ids

    def publish_tweet_with_images(self, content: str, image_paths: List[str]) -> Dict:
        """发布带图片的推文"""
        try:
            # 上传图片
            media_ids = self.upload_media(image_paths)

            if not media_ids:
                logger.warning("No media uploaded, posting text-only tweet")

            # 发布推文
            response = self.twitter_client.create_tweet(
                text=content,
                media_ids=media_ids if media_ids else None
            )

            if response.data:
                tweet_id = response.data['id']
                tweet_url = f"https://twitter.com/_/status/{tweet_id}"

                logger.info(f"Tweet published successfully: {tweet_url}")

                return {
                    'success': True,
                    'tweet_id': tweet_id,
                    'url': tweet_url,
                    'media_count': len(media_ids),
                    'content': content,
                    'published_at': datetime.utcnow().isoformat()
                }

            else:
                return {'success': False, 'error': 'No response data'}

        except Exception as e:
            logger.error(f"Failed to publish tweet: {e}")
            return {'success': False, 'error': str(e)}

    def capture_and_process_dashboard(self) -> List[str]:
        """截取并处理Dashboard图片"""
        logger.info("Starting dashboard capture and processing")

        # 1. 截取Dashboard
        captured_images = self.capture.capture_for_twitter()

        if not captured_images:
            logger.error("No images captured")
            return []

        logger.info(f"Captured {len(captured_images)} images")

        # 2. 处理图片（优化和添加品牌）
        processed_images = self.processor.create_twitter_carousel(captured_images)

        logger.info(f"Processed {len(processed_images)} images for Twitter")

        return processed_images

    def run_full_pipeline(self, dry_run: bool = False) -> Dict:
        """运行完整的发布流程"""
        logger.info("="*50)
        logger.info("Starting Dashboard Twitter Publishing Pipeline")
        logger.info(f"Mode: {'DRY RUN' if dry_run else 'PRODUCTION'}")

        result = {
            'success': False,
            'steps': {}
        }

        try:
            # 1. 初始化Twitter客户端
            if not dry_run:
                if not self.init_twitter_client():
                    raise Exception("Failed to initialize Twitter client")
                result['steps']['twitter_init'] = 'success'

            # 2. 截取并处理Dashboard图片
            logger.info("Capturing dashboard screenshots...")
            processed_images = self.capture_and_process_dashboard()

            if not processed_images:
                raise Exception("No images to publish")

            result['steps']['capture'] = f"{len(processed_images)} images"

            # 3. 加载数据并生成文案
            logger.info("Generating tweet content...")
            data_summary = self.load_dashboard_data()
            tweet_content = self.generate_tweet_content(data_summary)
            result['steps']['content'] = 'generated'

            if dry_run:
                # 演练模式
                result['dry_run'] = True
                result['content'] = tweet_content
                result['images'] = processed_images
                result['success'] = True

                print("\n" + "="*50)
                print("DRY RUN RESULTS:")
                print("="*50)
                print("\nTweet Content:")
                print(tweet_content)
                print(f"\nCharacter count: {len(tweet_content)}/280")
                print(f"\nImages to publish: {len(processed_images)}")
                for img in processed_images:
                    print(f"  - {img}")

            else:
                # 4. 发布到Twitter
                logger.info("Publishing to Twitter...")
                publish_result = self.publish_tweet_with_images(tweet_content, processed_images)

                result.update(publish_result)
                result['steps']['publish'] = 'success' if publish_result['success'] else 'failed'

                if publish_result['success']:
                    print(f"\n✅ Successfully published to Twitter!")
                    print(f"🔗 Tweet URL: {publish_result['url']}")
                    print(f"📷 Images: {publish_result['media_count']}")

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            result['error'] = str(e)
            result['success'] = False

        # 5. 保存发布日志
        self.save_publish_log(result)

        return result

    def save_publish_log(self, result: Dict):
        """保存发布日志"""
        log_dir = Path('logs/publish')
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"dashboard_twitter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(log_file, 'w') as f:
            json.dump(result, f, indent=2)

        logger.info(f"Saved publish log to {log_file}")

    def run_analysis_mode(self) -> Dict:
        """分析模式 - 只生成报告不发布"""
        logger.info("Running in analysis mode")

        # 加载数据
        data_summary = self.load_dashboard_data()

        # 生成多个版本的推文
        tweet_variants = []
        for i in range(3):
            content = self.generate_tweet_content(data_summary)
            tweet_variants.append({
                'variant': i+1,
                'content': content,
                'length': len(content),
                'fits_limit': len(content) <= 280
            })

        # 分析报告
        analysis = {
            'data_summary': data_summary,
            'tweet_variants': tweet_variants,
            'best_posting_times': [
                '08:00 EST',
                '12:00 EST',
                '17:00 EST'
            ],
            'recommended_hashtags': [
                '#AITools',
                '#AINews',
                '#TechTrends',
                '#MachineLearning',
                '#Startup'
            ],
            'generated_at': datetime.now().isoformat()
        }

        # 保存分析报告
        report_path = Path('reports/twitter_analysis.json')
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, 'w') as f:
            json.dump(analysis, f, indent=2)

        print("\n📊 Analysis Report Generated")
        print(f"📁 Saved to: {report_path}")
        print("\nData Summary:")
        print(f"  - Tools: {data_summary.get('total_tools')}")
        print(f"  - Trends: {data_summary.get('total_trends')}")
        print(f"  - Opportunities: {data_summary.get('total_opportunities')}")

        return analysis


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Dashboard Twitter Publisher')

    parser.add_argument(
        '--mode',
        choices=['publish', 'dry-run', 'analyze', 'capture-only'],
        default='dry-run',
        help='运行模式'
    )

    parser.add_argument(
        '--dashboard-url',
        default=None,
        help='Dashboard URL (可选，默认使用环境变量)'
    )

    parser.add_argument(
        '--skip-capture',
        action='store_true',
        help='跳过截图，使用已有图片'
    )

    args = parser.parse_args()

    # 设置Dashboard URL
    if args.dashboard_url:
        os.environ['DASHBOARD_URL'] = args.dashboard_url

    # 创建发布器
    publisher = DashboardTwitterPublisher()

    try:
        if args.mode == 'analyze':
            # 分析模式
            publisher.run_analysis_mode()

        elif args.mode == 'capture-only':
            # 仅截图
            images = publisher.capture_and_process_dashboard()
            print(f"✅ Captured and processed {len(images)} images:")
            for img in images:
                print(f"  - {img}")

        elif args.mode == 'dry-run':
            # 演练模式
            publisher.run_full_pipeline(dry_run=True)

        else:
            # 正式发布
            result = publisher.run_full_pipeline(dry_run=False)

            if not result['success']:
                logger.error(f"Publishing failed: {result.get('error')}")
                sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()