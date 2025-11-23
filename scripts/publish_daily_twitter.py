#!/usr/bin/env python3
"""
Twitter日报自动发布脚本
每天自动发布Top 3-5个AI工具机会到Twitter
"""

import os
import json
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import tweepy
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/twitter_publisher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TwitterDailyPublisher:
    """Twitter日报发布器"""

    def __init__(self):
        """初始化Twitter客户端"""
        self.client = self._init_twitter_client()
        self.data_path = "data/latest.json"
        self.template = self._load_template()

    def _init_twitter_client(self) -> tweepy.Client:
        """初始化Twitter API客户端"""
        try:
            # 使用OAuth 2.0 Bearer Token (用于只读操作)
            # 如果需要发布，使用OAuth 1.0a
            client = tweepy.Client(
                consumer_key=os.getenv('TWITTER_API_KEY'),
                consumer_secret=os.getenv('TWITTER_API_SECRET'),
                access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
                access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
            )
            logger.info("Twitter客户端初始化成功")
            return client
        except Exception as e:
            logger.error(f"Twitter客户端初始化失败: {e}")
            raise

    def _load_template(self) -> Dict:
        """加载推文模板"""
        return {
            'daily_report': {
                'title': '🚀 AI工具机会日报',
                'emoji_numbers': ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣'],
                'hashtags': '#AITools #人工智能 #独立开发者 #SaaS #创业',
                'max_length': 280
            }
        }

    def load_latest_data(self) -> Dict:
        """加载最新数据"""
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"成功加载数据，共{len(data.get('opportunities', []))}个机会")
                return data
        except FileNotFoundError:
            logger.error(f"数据文件不存在: {self.data_path}")
            return {'opportunities': [], 'tools': [], 'trends': []}
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
            return {'opportunities': [], 'tools': [], 'trends': []}

    def select_top_opportunities(self, data: Dict, count: int = 3) -> List[Dict]:
        """选择Top N个机会"""
        opportunities = data.get('opportunities', [])

        # 按评分排序（假设有score字段）
        # 如果没有score，可以基于其他指标排序
        sorted_opportunities = sorted(
            opportunities,
            key=lambda x: x.get('score', 0),
            reverse=True
        )

        return sorted_opportunities[:count]

    def format_opportunity(self, opportunity: Dict, index: int) -> str:
        """格式化单个机会"""
        emoji = self.template['daily_report']['emoji_numbers'][index]
        
        # 尝试从mvp_suggestion_en提取标题和摘要
        mvp_text = opportunity.get('mvp_suggestion_en', '')
        if mvp_text:
            # 尝试提取 "Introducing 'Title'"
            import re
            match = re.search(r"Introducing '([^']+)'", mvp_text)
            if match:
                title = match.group(1)
            else:
                # 简单的截取作为标题
                title = mvp_text.split(':')[0][:30]
            
            # 使用前100个字符作为摘要
            summary = mvp_text[:80].replace('\n', ' ') + "..."
        else:
            title = opportunity.get('title', '未知标题')[:30]
            summary = opportunity.get('summary', '暂无描述')[:40]

        # 如果有付费信号，添加💰emoji
        payment_signal = '💰' if opportunity.get('has_payment_signal', False) else ''

        return f"{emoji} {title}\n💡 {summary}{payment_signal}"

    def create_tweet_content(self, opportunities: List[Dict]) -> str:
        """创建推文内容"""
        template = self.template['daily_report']

        # 构建推文
        lines = [f"{template['title']} #{datetime.now().strftime('%m%d')}"]
        lines.append("")  # 空行

        # 添加Top机会
        for i, opp in enumerate(opportunities[:3]):  # 最多3个，保证不超过字符限制
            lines.append(self.format_opportunity(opp, i))
            lines.append("")  # 机会之间空行

        # 添加链接和hashtags
        dashboard_url = "https://your-domain.vercel.app"
        lines.append(f"🔗 完整榜单: {dashboard_url}")
        lines.append("")
        lines.append(template['hashtags'])

        tweet = "\n".join(lines)

        # 检查长度
        if len(tweet) > template['max_length']:
            logger.warning(f"推文过长({len(tweet)}字符)，需要截断")
            # 简化内容
            tweet = self._truncate_tweet(opportunities)

        return tweet

    def _truncate_tweet(self, opportunities: List[Dict]) -> str:
        """截断过长的推文"""
        template = self.template['daily_report']
        lines = [f"{template['title']}"]

        for i, opp in enumerate(opportunities[:3]):
            # 尝试从mvp_suggestion_en提取标题
            mvp_text = opp.get('mvp_suggestion_en', '')
            if mvp_text:
                import re
                match = re.search(r"Introducing '([^']+)'", mvp_text)
                if match:
                    title = match.group(1)
                else:
                    title = mvp_text.split(':')[0][:20]
            else:
                title = opp.get('title', '')[:20]
                
            lines.append(f"{i+1}. {title}")

        lines.append(f"\n详情 👉 https://your-domain.vercel.app")
        lines.append(template['hashtags'])

        return "\n".join(lines)

    def publish_tweet(self, content: str, dry_run: bool = False) -> Optional[Dict]:
        """发布推文"""
        if dry_run:
            logger.info("【演练模式】将发布以下内容:")
            logger.info(f"\n{content}")
            logger.info(f"字符数: {len(content)}")
            return {'dry_run': True, 'content': content}

        try:
            # 发布推文
            response = self.client.create_tweet(text=content)

            if response.data:
                tweet_id = response.data['id']
                tweet_url = f"https://twitter.com/user/status/{tweet_id}"
                logger.info(f"推文发布成功: {tweet_url}")

                return {
                    'success': True,
                    'tweet_id': tweet_id,
                    'url': tweet_url,
                    'content': content,
                    'published_at': datetime.utcnow().isoformat()
                }
            else:
                logger.error("发布失败，没有返回数据")
                return None

        except Exception as e:
            logger.error(f"发布推文失败: {e}")
            return None

    def save_publish_log(self, result: Dict):
        """保存发布日志"""
        log_dir = Path("logs/publish")
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"twitter_{datetime.now().strftime('%Y%m%d')}.json"

        # 读取现有日志
        existing_logs = []
        if log_file.exists():
            with open(log_file, 'r') as f:
                existing_logs = json.load(f)

        # 添加新日志
        existing_logs.append(result)

        # 保存
        with open(log_file, 'w') as f:
            json.dump(existing_logs, f, ensure_ascii=False, indent=2)

        logger.info(f"发布日志已保存: {log_file}")

    def check_rate_limit(self) -> bool:
        """检查API限制"""
        try:
            # 获取限制状态
            # Twitter API v2的限制检查方式
            # 这里简化处理，实际应该记录请求次数
            return True
        except Exception as e:
            logger.error(f"检查限制失败: {e}")
            return False

    def run(self, dry_run: bool = False):
        """执行发布流程"""
        logger.info("="*50)
        logger.info("开始执行Twitter日报发布")
        logger.info(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"模式: {'演练' if dry_run else '正式发布'}")

        # 1. 加载数据
        data = self.load_latest_data()
        if not data['opportunities']:
            logger.error("没有可发布的机会数据")
            return

        # 2. 选择Top机会
        top_opportunities = self.select_top_opportunities(data, count=3)
        logger.info(f"选择了{len(top_opportunities)}个机会")

        # 3. 创建推文内容
        tweet_content = self.create_tweet_content(top_opportunities)

        # 4. 发布推文
        result = self.publish_tweet(tweet_content, dry_run=dry_run)

        # 5. 保存日志
        if result:
            self.save_publish_log(result)
            logger.info("发布流程完成")
        else:
            logger.error("发布失败")
            sys.exit(1)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Twitter日报自动发布')
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='演练模式，不实际发布'
    )

    args = parser.parse_args()

    # 检查环境变量
    required_env_vars = [
        'TWITTER_API_KEY',
        'TWITTER_API_SECRET',
        'TWITTER_ACCESS_TOKEN',
        'TWITTER_ACCESS_TOKEN_SECRET'
    ]

    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars and not args.dry_run:
        logger.error(f"缺少必要的环境变量: {', '.join(missing_vars)}")
        logger.info("请设置环境变量或使用 --dry-run 进行演练")
        sys.exit(1)

    # 执行发布
    try:
        publisher = TwitterDailyPublisher()
        publisher.run(dry_run=args.dry_run)
    except Exception as e:
        logger.error(f"发布过程出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()