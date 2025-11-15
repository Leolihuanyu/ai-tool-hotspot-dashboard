"""Reddit热点爬虫

从Reddit相关子版块抓取热点话题和用户痛点。
基于research.md推荐,使用PRAW(Python Reddit API Wrapper)或RSS feed。
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone
from uuid import uuid4
import feedparser

from src.scrapers.base import BaseScraper
from src.models.trend import TrendingTopic


class RedditScraper(BaseScraper):
    """Reddit热点爬虫

    支持两种模式:
    1. 使用PRAW(推荐,需要Reddit API认证)
    2. 使用RSS feed(fallback,无需认证)

    目标子版块:r/OpenAI, r/artificial, r/MachineLearning, r/SaaS, r/entrepreneur
    """

    def __init__(self):
        super().__init__(
            source_name="Reddit",
            base_url="https://www.reddit.com"
        )

        # 从配置加载API凭证
        from src.utils.config import config
        self.reddit_client_id = getattr(config, 'reddit_client_id', None)
        self.reddit_client_secret = getattr(config, 'reddit_client_secret', None)
        self.reddit_user_agent = getattr(config, 'reddit_user_agent', 'AI-Opportunity-Matcher/1.0')

        # 目标子版块（热点话题）
        self.subreddits = [
            'OpenAI',
            'artificial',
            'MachineLearning',
            'SaaS',
            'entrepreneur',
            'Futurology',
            'indiehackers',  # 新增：独立开发者社区
            'startups',      # 新增：创业公司
        ]

        # 专门用于痛点提取的高价值子版块
        # 根据2025年调研，这些子版块有最高的付费意愿信号
        self.pain_point_subreddits = [
            'Entrepreneur',      # 企业家讨论
            'SaaS',             # SaaS产品讨论
            'startups',         # 创业公司
            'smallbusiness',    # 小型企业
            'indiehackers',     # 独立开发者（高变现潜力）
            'SideProject',      # 副业项目（MVP验证）
            'microsaas',        # 微型SaaS（低成本创业）
            'Entrepreneur_Ideas',  # 创业想法
            'digitalnomad',     # 数字游民
            'webdev',          # Web开发
            'Design_Critiques', # 设计评审
            'ProductManagement', # 产品管理
            'consulting',       # 咨询服务
            'freelance',        # 自由职业
            'ecommerce'         # 电商
        ]

        # 高信号痛点关键词（按优先级排序）
        # 这些关键词表明强烈的付费意愿和真实痛点
        self.high_value_keywords = [
            # Tier 1: 明确付费意愿
            "would pay for",
            "shut up and take my money",
            "will pay",
            "happy to pay",
            "worth paying",
            "$",  # 提到具体价格

            # Tier 2: 强烈需求
            "desperately need",
            "really need",
            "wish there was",
            "need a tool",
            "looking for a tool",
            "can't find",

            # Tier 3: 痛点描述
            "struggling with",
            "frustrated",
            "no good solution",
            "missing feature",
            "pain point",
            "hard to find",
            "waste of time",

            # Tier 4: MVP验证信号
            "would use",
            "sign me up",
            "interested in",
            "take my email"
        ]

    def _scrape_via_praw(self, limit: int = None) -> List[Dict[str, Any]]:
        """通过PRAW抓取数据

        Args:
            limit: 限制抓取数量

        Returns:
            帖子数据列表
        """
        try:
            import praw
        except ImportError:
            raise ImportError("PRAW not installed. Run: pip install praw")

        if not all([self.reddit_client_id, self.reddit_client_secret]):
            raise ValueError("Reddit API credentials not configured")

        # 初始化PRAW
        reddit = praw.Reddit(
            client_id=self.reddit_client_id,
            client_secret=self.reddit_client_secret,
            user_agent=self.reddit_user_agent
        )

        results = []
        # 确保每个子版块至少抓取1个帖子（测试模式下）
        posts_per_subreddit = max(1, (limit or 30) // len(self.subreddits))

        for subreddit_name in self.subreddits:
            try:
                subreddit = reddit.subreddit(subreddit_name)

                # 获取热门帖子，并进行商业价值过滤
                for submission in subreddit.hot(limit=posts_per_subreddit * 3):  # 多抓取一些用于过滤
                    # 计算商业价值评分（标题+内容）
                    text = f"{submission.title} {submission.selftext}"
                    business_score, matched_kw = self._calculate_payment_willingness_score(text)

                    # 只保留有一定商业价值的帖子（评分>0或高互动）
                    # 高互动帖子即使不含关键词也保留（可能是热点讨论）
                    if business_score >= 10 or submission.score >= 100 or submission.num_comments >= 50:
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
                            'upvote_ratio': submission.upvote_ratio,
                            'business_value_score': business_score,  # 新增：商业价值评分
                            'business_keywords': matched_kw  # 新增：匹配的关键词
                        })
                    else:
                        self.logger.debug(f"过滤低商业价值帖子: {submission.title[:50]}... (评分:{business_score})")

                    if limit and len(results) >= limit:
                        break

            except Exception as e:
                self.logger.warning(f"Failed to fetch from r/{subreddit_name}: {e}")
                continue

            if limit and len(results) >= limit:
                break

        return results

    def _scrape_via_rss(self, limit: int = None) -> List[Dict[str, Any]]:
        """通过RSS feed抓取数据(fallback)

        Reddit为每个子版块提供RSS feed:
        https://www.reddit.com/r/{subreddit}/.rss

        Args:
            limit: 限制抓取数量

        Returns:
            帖子数据列表
        """
        results = []
        # 确保每个子版块至少抓取1个帖子（测试模式下）
        posts_per_subreddit = max(1, (limit or 30) // len(self.subreddits))

        for subreddit_name in self.subreddits:
            try:
                rss_url = f"https://www.reddit.com/r/{subreddit_name}/.rss"
                self.logger.info(f"Fetching RSS from r/{subreddit_name}")

                feed = feedparser.parse(rss_url)

                for entry in feed.entries[:posts_per_subreddit]:
                    # 从entry提取信息
                    results.append({
                        'id': entry.get('id', str(uuid4())),
                        'title': entry.get('title', ''),
                        'selftext': entry.get('summary', ''),
                        'url': entry.get('link', ''),
                        'score': 0,  # RSS不包含score
                        'num_comments': 0,  # RSS不包含评论数
                        'created_utc': None,
                        'author': entry.get('author', 'Unknown'),
                        'subreddit': subreddit_name,
                        'published': entry.get('published_parsed')
                    })

                    if limit and len(results) >= limit:
                        break

            except Exception as e:
                self.logger.warning(f"Failed to fetch RSS from r/{subreddit_name}: {e}")
                continue

            if limit and len(results) >= limit:
                break

        return results

    def scrape(self, limit: int = None) -> List[Dict[str, Any]]:
        """抓取Reddit热点数据

        优先使用PRAW,失败则fallback到RSS。

        Args:
            limit: 限制抓取数量(可选,用于测试)

        Returns:
            原始数据字典列表
        """
        # 优先使用PRAW
        if self.reddit_client_id and self.reddit_client_secret:
            try:
                self.logger.info("Using PRAW mode")
                return self._scrape_via_praw(limit=limit)
            except Exception as e:
                self.logger.warning(f"PRAW failed, falling back to RSS: {e}")

        # Fallback到RSS
        self.logger.info("Using RSS fallback mode")
        return self._scrape_via_rss(limit=limit)

    def normalize(self, raw_data: Dict[str, Any]) -> TrendingTopic:
        """将原始数据转换为TrendingTopic模型

        Args:
            raw_data: 原始数据字典

        Returns:
            TrendingTopic对象
        """
        # 计算热度分数(基于upvotes和评论数)
        score = raw_data.get('score', 0)
        num_comments = raw_data.get('num_comments', 0)

        # 热度计算:score*0.1 + comments*0.5,归一化到0-100
        # 假设500分+100评论 = 100分
        heat_score = min(100.0, (score * 0.1 + num_comments * 0.5) / 1)

        # 解析时间戳
        created_utc = raw_data.get('created_utc')
        if created_utc:
            dt = datetime.fromtimestamp(created_utc, tz=timezone.utc)
        else:
            # 如果是RSS数据,使用published字段
            published = raw_data.get('published')
            if published:
                from time import mktime
                dt = datetime.fromtimestamp(mktime(published), tz=timezone.utc)
            else:
                dt = datetime.now(timezone.utc)

        # 合并标题和selftext作为描述
        title = raw_data['title']
        selftext = raw_data.get('selftext', '')
        description = f"{title}\n\n{selftext}" if selftext else title

        return TrendingTopic(
            id=str(uuid4()),
            title=title[:200],  # 限制长度
            description=description[:1500],  # 限制长度
            source="Reddit",
            url=raw_data['url'],
            timestamp=dt,
            heat_score=heat_score,
            trend_direction="stable",  # 初始值,后续计算
            tags=["Reddit", f"r/{raw_data['subreddit']}", "discussion"],
            summary_cn="",  # 由LLM生成
            summary_ja="",  # 由LLM生成
            data_quality_score=0.8 if self.reddit_client_id else 0.6,  # API数据质量更高
            schema_version="1.1"
        )

    def _calculate_payment_willingness_score(self, text: str) -> Tuple[float, List[str]]:
        """计算文本中的付费意愿分数

        Args:
            text: 评论或帖子文本

        Returns:
            (score, matched_keywords): 0-100的付费意愿分数和匹配到的关键词列表
        """
        text_lower = text.lower()
        matched_keywords = []
        score = 0.0

        # Tier 1: 明确付费意愿 (+40分)
        tier1_keywords = self.high_value_keywords[:6]
        for keyword in tier1_keywords:
            if keyword in text_lower:
                matched_keywords.append(keyword)
                score += 40
                break  # 同一级别只计一次

        # Tier 2: 强烈需求 (+30分)
        tier2_keywords = self.high_value_keywords[6:12]
        for keyword in tier2_keywords:
            if keyword in text_lower:
                matched_keywords.append(keyword)
                score += 30
                break

        # Tier 3: 痛点描述 (+20分)
        tier3_keywords = self.high_value_keywords[12:19]
        for keyword in tier3_keywords:
            if keyword in text_lower:
                matched_keywords.append(keyword)
                score += 20
                break

        # Tier 4: MVP验证信号 (+10分)
        tier4_keywords = self.high_value_keywords[19:]
        for keyword in tier4_keywords:
            if keyword in text_lower:
                matched_keywords.append(keyword)
                score += 10
                break

        return min(100.0, score), matched_keywords

    def scrape_pain_points(self, limit: int = None, filter_by_keywords: bool = True) -> List[Dict[str, Any]]:
        """从Reddit评论中抓取痛点数据

        专门针对r/entrepreneur, r/SaaS等子版块的评论进行痛点抓取

        Args:
            limit: 限制抓取的评论数量
            filter_by_keywords: 是否只保留包含高价值关键词的评论（默认True，提高信号质量）

        Returns:
            评论数据列表,包含text, context_title, source, url, timestamp等字段
        """
        # 必须使用PRAW才能获取评论
        if not all([self.reddit_client_id, self.reddit_client_secret]):
            self.logger.warning("痛点提取需要Reddit API凭证,使用PRAW模式")
            return []

        try:
            import praw
        except ImportError:
            self.logger.error("PRAW未安装,无法提取痛点")
            return []

        # 初始化PRAW
        reddit = praw.Reddit(
            client_id=self.reddit_client_id,
            client_secret=self.reddit_client_secret,
            user_agent=self.reddit_user_agent
        )

        comments_data = []
        filtered_count = 0  # 被过滤掉的评论数
        comments_per_subreddit = (limit or 50) // len(self.pain_point_subreddits)

        for subreddit_name in self.pain_point_subreddits:
            try:
                subreddit = reddit.subreddit(subreddit_name)
                self.logger.info(f"从r/{subreddit_name}提取痛点评论")

                # 从热门帖子中获取评论
                for submission in subreddit.hot(limit=15):  # 增加到15个帖子
                    # 展开评论树(最多获取前N个顶级评论)
                    submission.comments.replace_more(limit=0)

                    for comment in submission.comments[:10]:  # 每个帖子取前10个评论
                        # 只保留足够长的评论(至少30个字符，提高质量)
                        if len(comment.body) < 30:
                            continue

                        # 跳过自动机器人评论
                        if comment.author and str(comment.author).lower().endswith('bot'):
                            continue

                        # 计算付费意愿分数
                        payment_score, matched_kw = self._calculate_payment_willingness_score(
                            comment.body
                        )

                        # 如果启用关键词过滤，只保留有高价值信号的评论
                        if filter_by_keywords and payment_score == 0:
                            filtered_count += 1
                            continue

                        # 计算综合engagement_score（结合upvotes和付费意愿）
                        base_engagement = min(100.0, comment.score / 10.0)
                        # 加权：70% upvotes, 30% 付费意愿
                        final_engagement = base_engagement * 0.7 + payment_score * 0.3

                        comments_data.append({
                            'text': comment.body,
                            'context_title': submission.title,
                            'source': 'Reddit',
                            'url': f"https://reddit.com{comment.permalink}",
                            'timestamp': datetime.fromtimestamp(
                                comment.created_utc,
                                tz=timezone.utc
                            ),
                            'engagement_score': final_engagement,
                            'payment_willingness_score': payment_score,  # 新增字段
                            'matched_keywords': matched_kw,  # 新增字段
                            'author_metadata': {
                                'username': str(comment.author),
                                'karma': comment.author.link_karma + comment.author.comment_karma
                                    if comment.author else 0
                            }
                        })

                        if limit and len(comments_data) >= limit:
                            break

                    if limit and len(comments_data) >= limit:
                        break

            except Exception as e:
                self.logger.warning(f"从r/{subreddit_name}提取评论失败: {e}")
                continue

            if limit and len(comments_data) >= limit:
                break

        self.logger.info(
            f"共从Reddit提取{len(comments_data)}条高质量评论"
            f"（过滤掉{filtered_count}条低信号评论）"
        )

        # 按付费意愿分数排序，优先处理高价值痛点
        comments_data.sort(key=lambda x: x['payment_willingness_score'], reverse=True)

        return comments_data
