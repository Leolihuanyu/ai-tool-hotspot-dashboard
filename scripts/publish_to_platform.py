#!/usr/bin/env python3
"""
多平台统一发布脚本
支持发布日报/周报到各个社交媒体平台
"""

import os
import json
import sys
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from abc import ABC, abstractmethod
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/multi_platform_publisher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PlatformPublisher(ABC):
    """平台发布器基类"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.client = None

    @abstractmethod
    def init_client(self) -> bool:
        """初始化平台客户端"""
        pass

    @abstractmethod
    def validate_content(self, content: str) -> bool:
        """验证内容是否符合平台要求"""
        pass

    @abstractmethod
    def publish(self, content: str, metadata: Dict = None) -> Dict:
        """发布内容到平台"""
        pass

    def format_content(self, raw_content: Dict, content_type: str) -> str:
        """格式化内容以适应平台"""
        return raw_content.get('content', '')


from src.utils.image_gen import generate_social_image

class TwitterPublisher(PlatformPublisher):
    """Twitter发布器"""

    def init_client(self) -> bool:
        try:
            import tweepy
            # API v2 Client (用于发推)
            self.client = tweepy.Client(
                consumer_key=os.getenv('TWITTER_API_KEY'),
                consumer_secret=os.getenv('TWITTER_API_SECRET'),
                access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
                access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
            )
            
            # API v1.1 (用于上传媒体)
            auth = tweepy.OAuth1UserHandler(
                os.getenv('TWITTER_API_KEY'),
                os.getenv('TWITTER_API_SECRET'),
                os.getenv('TWITTER_ACCESS_TOKEN'),
                os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
            )
            self.api = tweepy.API(auth)
            
            logger.info("Twitter客户端初始化成功")
            return True
        except Exception as e:
            logger.error(f"Twitter客户端初始化失败: {e}")
            return False

    def validate_content(self, content: str) -> bool:
        """验证推文长度"""
        return len(content) <= 320 # 稍微放宽

    def format_content(self, raw_content: Dict, content_type: str) -> str:
        """格式化Twitter内容"""
        if content_type == 'daily':
            return self._format_daily_tweet(raw_content)
        elif content_type == 'weekly':
            return self._format_weekly_tweet(raw_content)
        return raw_content.get('content', '')

    def _format_daily_tweet(self, data: Dict) -> str:
        """格式化日报推文"""
        # 尝试使用LLM生成更有吸引力的推文
        try:
            from src.llm.client import LLMClient
            llm = LLMClient()
            
            # 简化的数据摘要供LLM使用
            summary = {
                "trends": [t.get('title') for t in data.get('trends', [])[:3]],
                "tools": [t.get('name') for t in data.get('tools', [])[:3]],
                "opportunities": [o.get('mvp_suggestion_en', '')[:100] for o in data.get('opportunities', [])[:1]]
            }
            
            prompt = f"""
Role: You are a top-tier tech influencer on Twitter/X.
Task: Write a daily AI digest tweet based on the data below.

Data:
{json.dumps(summary)}

Structure & Requirements:
1. **🛠️ Tool**: Pick the best tool. Write a VERY short, punchy summary (max 10 words).
2. **📈 Trend**: Pick the hottest trend. Write a VERY short insight (max 10 words).
3. **💡 MVP Idea**: Just the NAME of the idea.
4. **Outro**: "Follow for daily AI alpha 🚀"

Constraints:
- **TOTAL LENGTH MUST BE UNDER 260 CHARACTERS**.
- No fluff. No filler words. Be direct.
- Use the emojis provided above (🛠️, 📈, 💡).
- Tone: Professional, insightful, concise.
"""
            tweet = llm.generate(prompt)
            # Twitter字符计算复杂，稍微放宽一点限制，让Twitter API自己去拒或者截断
            if tweet and len(tweet) <= 320:
                logger.info("Successfully generated tweet using LLM")
                return tweet
            else:
                logger.warning("LLM generated tweet too long or empty, falling back to template")
                
        except Exception as e:
            logger.error(f"LLM tweet generation failed: {e}, falling back to template")

        # === 降级方案：使用固定模板 ===
        return "Today's AI Indie Hacker Intel 🚀"

    def publish(self, content: str, metadata: Dict = None) -> Dict:
        """发布推文"""
        try:
            media_ids = []
            
            # 1. 检查是否需要生成配图
            tool_data = metadata.get('tool_data')
            if tool_data:
                logger.info(f"正在为 {tool_data.get('name', 'AI Tool')} 生成配图...")
                image_path = "temp_social_image.png"
                if generate_social_image(tool_data, image_path):
                    # 上传图片
                    logger.info("正在上传图片...")
                    try:
                        media = self.api.media_upload(filename=image_path)
                        media_ids.append(media.media_id)
                        logger.info(f"图片上传成功, media_id: {media.media_id}")
                    except Exception as e:
                        logger.error(f"图片上传失败: {e}")
                    
                    # 清理
                    if os.path.exists(image_path):
                        os.remove(image_path)
                else:
                    logger.warning("配图生成失败，将只发布文字")

            # 2. 验证内容
            if not self.validate_content(content):
                content = content[:277] + "..."

            # 3. 发布
            if media_ids:
                response = self.client.create_tweet(text=content, media_ids=media_ids)
            else:
                response = self.client.create_tweet(text=content)

            if response.data:
                return {
                    'success': True,
                    'platform': 'twitter',
                    'post_id': response.data['id'],
                    'url': f"https://twitter.com/user/status/{response.data['id']}"
                }
        except Exception as e:
            logger.error(f"Twitter发布失败: {e}")
            return {'success': False, 'platform': 'twitter', 'error': str(e)}


class LinkedInPublisher(PlatformPublisher):
    """LinkedIn发布器"""

    def init_client(self) -> bool:
        try:
            # LinkedIn使用REST API，不需要特殊客户端
            self.access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
            if not self.access_token:
                raise ValueError("LinkedIn Access Token未设置")
            logger.info("LinkedIn配置成功")
            return True
        except Exception as e:
            logger.error(f"LinkedIn配置失败: {e}")
            return False

    def validate_content(self, content: str) -> bool:
        """LinkedIn内容长度限制"""
        return len(content) <= 3000

    def format_content(self, raw_content: Dict, content_type: str) -> str:
        """格式化LinkedIn内容"""
        if content_type == 'daily':
            return self._format_daily_post(raw_content)
        elif content_type == 'weekly':
            return self._format_weekly_post(raw_content)
        return raw_content.get('content', '')

    def _format_daily_post(self, data: Dict) -> str:
        """格式化LinkedIn日报"""
        opportunities = data.get('opportunities', [])[:5]

        lines = [
            "🚀 今日AI工具机会洞察",
            "",
            "发现了几个值得关注的产品机会，特别适合独立开发者和创业者：",
            ""
        ]

        for i, opp in enumerate(opportunities, 1):
            lines.append(f"{i}. {opp.get('title', '')}")
            lines.append(f"   💡 {opp.get('description', '')[:100]}")
            lines.append(f"   📊 来源: {opp.get('source', '')}")
            lines.append("")

        lines.extend([
            "这些机会都经过LLM智能筛选，识别出真实的用户痛点和付费意愿。",
            "",
            "想要获取完整的数据分析？访问 https://your-domain.vercel.app",
            "",
            "#AI #创业 #产品开发 #独立开发者 #SaaS"
        ])

        return "\n".join(lines)

    def _format_weekly_post(self, data: Dict) -> str:
        """格式化LinkedIn周报"""
        return f"""📊 AI工具机会周报 - {data.get('week_number', '')}

本周数据亮点：
• 分析了 {data.get('total_sources', 10)}+ 个数据源
• 发现 {data.get('opportunity_count', 50)}+ 个产品机会
• 识别出 {data.get('unique_opportunities', 10)} 个高价值机会

热门趋势：
{self._format_trends(data.get('trends', []))}

Top 3 机会：
{self._format_top_opportunities(data.get('opportunities', [])[:3])}

这些数据来自ProductHunt、Reddit、Hacker News等平台，经过AI智能过滤，帮助您快速发现真实的市场需求。

查看完整周报: https://your-domain.vercel.app/weekly

#数据分析 #市场洞察 #AI工具 #产品管理 #创业
"""

    def _format_trends(self, trends: List) -> str:
        """格式化趋势列表"""
        return "\n".join([f"• {trend}" for trend in trends[:3]])

    def _format_top_opportunities(self, opportunities: List) -> str:
        """格式化Top机会"""
        result = []
        for i, opp in enumerate(opportunities, 1):
            result.append(f"{i}. {opp.get('title', '')}")
        return "\n".join(result)

    def publish(self, content: str, metadata: Dict = None) -> Dict:
        """发布到LinkedIn"""
        try:
            import requests

            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }

            # 获取用户ID
            user_response = requests.get(
                "https://api.linkedin.com/v2/me",
                headers=headers
            )
            user_id = user_response.json()['id']

            # 构建发布数据
            post_data = {
                "author": f"urn:li:person:{user_id}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": content},
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
            }

            response = requests.post(
                "https://api.linkedin.com/v2/ugcPosts",
                json=post_data,
                headers=headers
            )

            if response.status_code == 201:
                return {
                    'success': True,
                    'platform': 'linkedin',
                    'post_id': response.headers.get('X-RestLi-Id'),
                    'response': response.text
                }
            else:
                return {'success': False, 'platform': 'linkedin', 'error': response.text}

        except Exception as e:
            logger.error(f"LinkedIn发布失败: {e}")
            return {'success': False, 'platform': 'linkedin', 'error': str(e)}


class RedditPublisher(PlatformPublisher):
    """Reddit发布器"""

    def init_client(self) -> bool:
        try:
            import praw
            self.client = praw.Reddit(
                client_id=os.getenv('REDDIT_CLIENT_ID'),
                client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
                username=os.getenv('REDDIT_USERNAME'),
                password=os.getenv('REDDIT_PASSWORD'),
                user_agent='AI-Tool-Hotspot-Bot/1.0'
            )
            logger.info("Reddit客户端初始化成功")
            return True
        except Exception as e:
            logger.error(f"Reddit客户端初始化失败: {e}")
            return False

    def validate_content(self, content: str) -> bool:
        """Reddit标题长度限制"""
        return len(content.split('\n')[0]) <= 300

    def publish(self, content: str, metadata: Dict = None) -> Dict:
        """发布到Reddit"""
        try:
            subreddit_name = metadata.get('subreddit', 'SideProject')
            subreddit = self.client.subreddit(subreddit_name)

            # 分离标题和正文
            lines = content.split('\n', 1)
            title = lines[0]
            body = lines[1] if len(lines) > 1 else ''

            submission = subreddit.submit(title=title, selftext=body)

            return {
                'success': True,
                'platform': 'reddit',
                'post_id': submission.id,
                'url': f"https://reddit.com{submission.permalink}"
            }
        except Exception as e:
            logger.error(f"Reddit发布失败: {e}")
            return {'success': False, 'platform': 'reddit', 'error': str(e)}


class MultiPlatformManager:
    """多平台发布管理器"""

    def __init__(self):
        self.publishers = {
            'twitter': TwitterPublisher(),
            'linkedin': LinkedInPublisher(),
            'reddit': RedditPublisher(),
        }
        self.results = []

    def load_content(self, content_type: str) -> Dict:
        """加载要发布的内容"""
        if content_type == 'daily':
            # 加载日报数据
            with open('data/latest.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    'type': 'daily',
                    'opportunities': data.get('opportunities', []),
                    # JSON文件中是 'ai_tools'，但代码里用 'tools'
                    'tools': data.get('ai_tools', []), 
                    # JSON文件中是 'trending_topics'，但代码里用 'trends'
                    'trends': data.get('trending_topics', [])
                }
        elif content_type == 'weekly':
            # 加载周报数据
            report_dir = Path('reports/weekly')
            latest_report = max(report_dir.glob('*.json'), key=os.path.getctime)
            with open(latest_report, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            raise ValueError(f"未知的内容类型: {content_type}")

    def publish_to_platforms(
        self,
        platforms: List[str],
        content_type: str,
        dry_run: bool = False,
        metadata: Dict = None
    ) -> List[Dict]:
        """发布到多个平台"""
        # 加载内容
        raw_content = self.load_content(content_type)
        results = []

        for platform_name in platforms:
            if platform_name not in self.publishers:
                logger.warning(f"不支持的平台: {platform_name}")
                continue

            publisher = self.publishers[platform_name]

            # 初始化客户端
            if not publisher.init_client():
                results.append({
                    'platform': platform_name,
                    'success': False,
                    'error': '客户端初始化失败'
                })
                continue

            # 格式化内容
            formatted_content = publisher.format_content(raw_content, content_type)

            # 提取工具数据 (如果有)
            tool_data = None
            if content_type == 'daily' and raw_content.get('tools'):
                tool_data = raw_content['tools'][0]  # 传递完整的工具数据
            
            if dry_run:
                logger.info(f"【演练模式】{platform_name}:")
                logger.info(formatted_content)
                if tool_data:
                    logger.info(f"【演练模式】配图工具: {tool_data.get('name')}")
                results.append({
                    'platform': platform_name,
                    'success': True,
                    'dry_run': True,
                    'content': formatted_content
                })
            else:
                # 发布
                publish_metadata = {**(metadata or {}), 'content_type': content_type}
                if tool_data:
                    publish_metadata['tool_data'] = tool_data
                    
                result = publisher.publish(
                    formatted_content,
                    metadata=publish_metadata
                )
                results.append(result)

                if result['success']:
                    logger.info(f"✅ {platform_name} 发布成功: {result.get('url', '')}")
                else:
                    logger.error(f"❌ {platform_name} 发布失败: {result.get('error', '')}")

        return results

    def save_results(self, results: List[Dict]):
        """保存发布结果"""
        log_dir = Path('logs/publish')
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"publish_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'results': results
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"发布结果已保存: {log_file}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='多平台内容发布')
    parser.add_argument(
        '--platform',
        required=True,
        choices=['twitter', 'linkedin', 'reddit', 'all'],
        help='目标平台'
    )
    parser.add_argument(
        '--type',
        required=True,
        choices=['daily', 'weekly'],
        help='内容类型'
    )
    parser.add_argument(
        '--subreddit',
        default='SideProject',
        help='Reddit子版块（仅Reddit需要）'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='演练模式，不实际发布'
    )

    args = parser.parse_args()

    # 确定要发布的平台
    if args.platform == 'all':
        platforms = ['twitter', 'linkedin', 'reddit']
    else:
        platforms = [args.platform]

    # 设置metadata
    metadata = {}
    if 'reddit' in platforms:
        metadata['subreddit'] = args.subreddit

    # 执行发布
    manager = MultiPlatformManager()
    results = manager.publish_to_platforms(
        platforms=platforms,
        content_type=args.type,
        dry_run=args.dry_run,
        metadata=metadata
    )

    # 保存结果
    if not args.dry_run:
        manager.save_results(results)

    # 检查是否有失败
    failed = [r for r in results if not r['success']]
    if failed:
        logger.error(f"有 {len(failed)} 个平台发布失败")
        sys.exit(1)
    else:
        logger.info(f"所有平台发布成功！共 {len(results)} 个")


if __name__ == "__main__":
    main()