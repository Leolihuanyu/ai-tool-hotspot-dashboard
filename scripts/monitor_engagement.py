#!/usr/bin/env python3
"""
社交媒体互动数据监控脚本
追踪和分析各平台发布内容的表现
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import tweepy
import pandas as pd
import matplotlib.pyplot as plt

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/engagement_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EngagementMonitor:
    """社交媒体互动监控器"""

    def __init__(self):
        """初始化监控器"""
        self.data_dir = Path('data/engagement')
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir = Path('reports/engagement')
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def init_twitter_client(self) -> tweepy.Client:
        """初始化Twitter客户端"""
        try:
            client = tweepy.Client(
                bearer_token=os.getenv('TWITTER_BEARER_TOKEN'),
                consumer_key=os.getenv('TWITTER_API_KEY'),
                consumer_secret=os.getenv('TWITTER_API_SECRET'),
                access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
                access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET'),
                return_type=dict
            )
            logger.info("Twitter client initialized")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize Twitter client: {e}")
            return None

    def fetch_twitter_metrics(self, hours: int = 24) -> Dict:
        """获取Twitter指标"""
        client = self.init_twitter_client()
        if not client:
            return {}

        try:
            # 获取用户信息
            user_response = client.get_me(
                user_fields=['public_metrics']
            )
            user_metrics = user_response['data']['public_metrics']

            # 获取最近的推文
            tweets_response = client.get_users_tweets(
                id=user_response['data']['id'],
                max_results=10,
                tweet_fields=['created_at', 'public_metrics', 'context_annotations'],
                start_time=(datetime.utcnow() - timedelta(hours=hours)).isoformat() + 'Z'
            )

            tweets_data = []
            if tweets_response and 'data' in tweets_response:
                for tweet in tweets_response['data']:
                    tweet_metrics = {
                        'id': tweet['id'],
                        'created_at': tweet['created_at'],
                        'text': tweet['text'][:100],
                        'retweet_count': tweet['public_metrics']['retweet_count'],
                        'reply_count': tweet['public_metrics']['reply_count'],
                        'like_count': tweet['public_metrics']['like_count'],
                        'quote_count': tweet['public_metrics']['quote_count'],
                        'impression_count': tweet['public_metrics'].get('impression_count', 0),
                        'engagement_rate': self._calculate_engagement_rate(tweet['public_metrics'])
                    }
                    tweets_data.append(tweet_metrics)

            metrics = {
                'platform': 'twitter',
                'timestamp': datetime.utcnow().isoformat(),
                'user_metrics': user_metrics,
                'tweets': tweets_data,
                'summary': {
                    'total_tweets': len(tweets_data),
                    'avg_likes': sum(t['like_count'] for t in tweets_data) / len(tweets_data) if tweets_data else 0,
                    'avg_retweets': sum(t['retweet_count'] for t in tweets_data) / len(tweets_data) if tweets_data else 0,
                    'avg_engagement_rate': sum(t['engagement_rate'] for t in tweets_data) / len(tweets_data) if tweets_data else 0
                }
            }

            logger.info(f"Fetched metrics for {len(tweets_data)} tweets")
            return metrics

        except Exception as e:
            logger.error(f"Failed to fetch Twitter metrics: {e}")
            return {}

    def _calculate_engagement_rate(self, metrics: Dict) -> float:
        """计算互动率"""
        engagements = (
            metrics.get('retweet_count', 0) +
            metrics.get('reply_count', 0) +
            metrics.get('like_count', 0) +
            metrics.get('quote_count', 0)
        )
        impressions = metrics.get('impression_count', 0)

        if impressions > 0:
            return (engagements / impressions) * 100
        return 0

    def save_metrics(self, metrics: Dict):
        """保存指标数据"""
        date_str = datetime.now().strftime('%Y%m%d')
        platform = metrics.get('platform', 'unknown')

        filename = self.data_dir / f"{platform}_metrics_{date_str}.json"

        # 如果文件已存在，追加数据
        existing_data = []
        if filename.exists():
            with open(filename, 'r') as f:
                existing_data = json.load(f)

        existing_data.append(metrics)

        with open(filename, 'w') as f:
            json.dump(existing_data, f, indent=2)

        logger.info(f"Saved metrics to {filename}")

    def load_historical_data(self, platform: str, days: int = 7) -> pd.DataFrame:
        """加载历史数据"""
        data = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y%m%d')
            filename = self.data_dir / f"{platform}_metrics_{date_str}.json"

            if filename.exists():
                with open(filename, 'r') as f:
                    daily_data = json.load(f)
                    data.extend(daily_data)

            current_date += timedelta(days=1)

        if data:
            # 展开嵌套的tweets数据
            flattened_data = []
            for entry in data:
                for tweet in entry.get('tweets', []):
                    tweet['fetch_time'] = entry['timestamp']
                    flattened_data.append(tweet)

            return pd.DataFrame(flattened_data)
        else:
            return pd.DataFrame()

    def generate_performance_report(self, platform: str = 'twitter', days: int = 7) -> Dict:
        """生成表现报告"""
        df = self.load_historical_data(platform, days)

        if df.empty:
            logger.warning(f"No data available for {platform}")
            return {}

        # 转换时间列
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['fetch_time'] = pd.to_datetime(df['fetch_time'])

        # 计算统计数据
        report = {
            'platform': platform,
            'period': {
                'start': df['created_at'].min().isoformat(),
                'end': df['created_at'].max().isoformat(),
                'days': days
            },
            'metrics': {
                'total_posts': len(df),
                'total_likes': df['like_count'].sum(),
                'total_retweets': df['retweet_count'].sum(),
                'total_replies': df['reply_count'].sum(),
                'avg_engagement_rate': df['engagement_rate'].mean(),
                'max_engagement_rate': df['engagement_rate'].max(),
                'best_performing_post': df.loc[df['engagement_rate'].idxmax()].to_dict() if not df.empty else {}
            },
            'trends': {
                'daily_average_likes': df.groupby(df['created_at'].dt.date)['like_count'].mean().to_dict(),
                'hourly_distribution': df.groupby(df['created_at'].dt.hour)['engagement_rate'].mean().to_dict()
            },
            'generated_at': datetime.now().isoformat()
        }

        # 保存报告
        report_file = self.report_dir / f"{platform}_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Generated report: {report_file}")
        return report

    def create_visualization(self, platform: str = 'twitter', days: int = 7):
        """创建可视化图表"""
        df = self.load_historical_data(platform, days)

        if df.empty:
            logger.warning("No data for visualization")
            return

        # 转换时间列
        df['created_at'] = pd.to_datetime(df['created_at'])

        # 创建图表
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'{platform.title()} Engagement Analytics - Last {days} Days', fontsize=16)

        # 1. 每日互动趋势
        daily_metrics = df.groupby(df['created_at'].dt.date).agg({
            'like_count': 'sum',
            'retweet_count': 'sum',
            'reply_count': 'sum'
        })

        axes[0, 0].plot(daily_metrics.index, daily_metrics['like_count'], marker='o', label='Likes')
        axes[0, 0].plot(daily_metrics.index, daily_metrics['retweet_count'], marker='s', label='Retweets')
        axes[0, 0].plot(daily_metrics.index, daily_metrics['reply_count'], marker='^', label='Replies')
        axes[0, 0].set_title('Daily Engagement Trends')
        axes[0, 0].set_xlabel('Date')
        axes[0, 0].set_ylabel('Count')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)

        # 2. 互动率分布
        axes[0, 1].hist(df['engagement_rate'], bins=20, edgecolor='black')
        axes[0, 1].set_title('Engagement Rate Distribution')
        axes[0, 1].set_xlabel('Engagement Rate (%)')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].grid(True, alpha=0.3)

        # 3. 按小时的平均互动
        hourly_engagement = df.groupby(df['created_at'].dt.hour)['engagement_rate'].mean()
        axes[1, 0].bar(hourly_engagement.index, hourly_engagement.values)
        axes[1, 0].set_title('Average Engagement by Hour')
        axes[1, 0].set_xlabel('Hour of Day')
        axes[1, 0].set_ylabel('Avg Engagement Rate (%)')
        axes[1, 0].grid(True, alpha=0.3)

        # 4. Top表现内容
        top_posts = df.nlargest(5, 'engagement_rate')[['text', 'engagement_rate']]
        axes[1, 1].axis('tight')
        axes[1, 1].axis('off')

        table_data = []
        for idx, row in top_posts.iterrows():
            text = row['text'][:30] + '...' if len(row['text']) > 30 else row['text']
            table_data.append([text, f"{row['engagement_rate']:.2f}%"])

        table = axes[1, 1].table(
            cellText=table_data,
            colLabels=['Post (truncated)', 'Engagement Rate'],
            cellLoc='left',
            loc='center'
        )
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        axes[1, 1].set_title('Top 5 Posts by Engagement')

        # 调整布局
        plt.tight_layout()

        # 保存图表
        chart_file = self.report_dir / f"{platform}_analytics_{datetime.now().strftime('%Y%m%d')}.png"
        plt.savefig(chart_file, dpi=100, bbox_inches='tight')
        plt.close()

        logger.info(f"Saved visualization: {chart_file}")
        return str(chart_file)

    def compare_periods(self, platform: str = 'twitter') -> Dict:
        """比较不同时期的表现"""
        # 本周数据
        this_week = self.generate_performance_report(platform, days=7)

        # 上周数据
        last_week_df = self.load_historical_data(platform, days=14)
        if not last_week_df.empty:
            last_week_df = last_week_df[
                pd.to_datetime(last_week_df['created_at']) <
                (datetime.now() - timedelta(days=7))
            ]

        comparison = {
            'this_week': this_week.get('metrics', {}),
            'growth': {}
        }

        # 计算增长率
        if this_week and not last_week_df.empty:
            last_week_metrics = {
                'avg_likes': last_week_df['like_count'].mean(),
                'avg_retweets': last_week_df['retweet_count'].mean(),
                'avg_engagement_rate': last_week_df['engagement_rate'].mean()
            }

            for metric in ['avg_engagement_rate']:
                if metric in this_week['metrics'] and metric in last_week_metrics:
                    current = this_week['metrics'][metric]
                    previous = last_week_metrics[metric]
                    if previous > 0:
                        growth = ((current - previous) / previous) * 100
                        comparison['growth'][metric] = growth

        return comparison


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='社交媒体互动监控')
    parser.add_argument(
        '--platform',
        choices=['twitter', 'linkedin', 'all'],
        default='twitter',
        help='监控平台'
    )
    parser.add_argument(
        '--hours',
        type=int,
        default=24,
        help='获取过去N小时的数据'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='分析过去N天的数据'
    )
    parser.add_argument(
        '--mode',
        choices=['fetch', 'analyze', 'visualize', 'compare'],
        default='fetch',
        help='运行模式'
    )

    args = parser.parse_args()

    monitor = EngagementMonitor()

    try:
        if args.mode == 'fetch':
            # 获取最新数据
            if args.platform == 'twitter' or args.platform == 'all':
                metrics = monitor.fetch_twitter_metrics(args.hours)
                if metrics:
                    monitor.save_metrics(metrics)
                    print(f"✅ Fetched Twitter metrics")
                    print(f"   Posts: {metrics['summary']['total_tweets']}")
                    print(f"   Avg Engagement: {metrics['summary']['avg_engagement_rate']:.2f}%")

        elif args.mode == 'analyze':
            # 生成分析报告
            report = monitor.generate_performance_report(args.platform, args.days)
            if report:
                print(f"\n📊 {args.platform.title()} Performance Report")
                print(f"Period: {report['period']['start']} to {report['period']['end']}")
                print(f"Total Posts: {report['metrics']['total_posts']}")
                print(f"Avg Engagement Rate: {report['metrics']['avg_engagement_rate']:.2f}%")
                print(f"Best Performing Post: {report['metrics']['best_performing_post'].get('text', 'N/A')[:50]}...")

        elif args.mode == 'visualize':
            # 创建可视化
            chart_file = monitor.create_visualization(args.platform, args.days)
            if chart_file:
                print(f"✅ Created visualization: {chart_file}")

        elif args.mode == 'compare':
            # 比较不同时期
            comparison = monitor.compare_periods(args.platform)
            print(f"\n📈 Period Comparison")
            print(f"This Week Avg Engagement: {comparison['this_week'].get('avg_engagement_rate', 0):.2f}%")
            for metric, growth in comparison['growth'].items():
                print(f"{metric} Growth: {growth:+.1f}%")

    except Exception as e:
        logger.error(f"Monitor failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()