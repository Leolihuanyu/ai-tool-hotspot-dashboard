#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/ri/Projects/ai-tool-hotspot-dashboard')

from dotenv import load_dotenv
load_dotenv()

import praw
import logging

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Reddit配置
reddit_client_id = 'uCh9uvRgI68kRagmhNMeLA'
reddit_client_secret = '6BgDGuMIf5NMuIChvbH9xlUrITweog'
reddit_user_agent = 'AI-Opportunity-Matcher/1.0'

# 目标子版块（与爬虫相同）
subreddits = [
    'OpenAI',
    'artificial',
    'MachineLearning',
    'SaaS',
    'entrepreneur'
]

logger.info(f"初始化PRAW...")
reddit = praw.Reddit(
    client_id=reddit_client_id,
    client_secret=reddit_client_secret,
    user_agent=reddit_user_agent
)

results = []
limit = 5
posts_per_subreddit = limit // len(subreddits)

logger.info(f"目标: 从{len(subreddits)}个子版块各抓取{posts_per_subreddit}个帖子")

for subreddit_name in subreddits:
    try:
        logger.info(f"\n处理 r/{subreddit_name}...")
        subreddit = reddit.subreddit(subreddit_name)

        # 获取热门帖子
        count = 0
        for submission in subreddit.hot(limit=posts_per_subreddit):
            count += 1
            logger.debug(f"  帖子 {count}: {submission.title[:50]}...")

            results.append({
                'id': submission.id,
                'title': submission.title,
                'selftext': submission.selftext,
                'url': f"https://reddit.com{submission.permalink}",
                'score': submission.score,
                'num_comments': submission.num_comments,
                'created_utc': submission.created_utc,
                'author': str(submission.author),
                'subreddit': subreddit_name,
                'upvote_ratio': submission.upvote_ratio
            })

            if limit and len(results) >= limit:
                logger.info(f"  已达到总限制 {limit}")
                break

        logger.info(f"  从 r/{subreddit_name} 获取了 {count} 个帖子")

    except Exception as e:
        logger.error(f"  失败: {e}")
        continue

    if limit and len(results) >= limit:
        break

logger.info(f"\n最终结果: 共获取 {len(results)} 个帖子")
for i, post in enumerate(results[:3], 1):
    logger.info(f"{i}. {post['title'][:60]}... (r/{post['subreddit']}, 分数: {post['score']})")