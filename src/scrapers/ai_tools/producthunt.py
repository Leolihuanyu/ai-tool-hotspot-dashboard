"""ProductHunt爬虫

从ProductHunt抓取AI工具数据。
优先使用GraphQL API,备选方案:RSS feed
数据源: https://www.producthunt.com/
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import feedparser
from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper
from src.models.tool import AITool


class ProductHuntScraper(BaseScraper):
    """ProductHunt爬虫

    优先使用GraphQL API(需要API key),备选方案使用RSS feed
    RSS feed URL: https://www.producthunt.com/feed
    """

    def __init__(self, api_token: Optional[str] = None):
        """初始化ProductHunt爬虫

        Args:
            api_token: ProductHunt API token(可选)
        """
        super().__init__(
            source_name="ProductHunt",
            base_url="https://www.producthunt.com"
        )
        self.api_token = api_token
        self.rss_url = f"{self.base_url}/feed"
        self.graphql_url = "https://api.producthunt.com/v2/api/graphql"

    def scrape(self, limit: int = None) -> List[Dict[str, Any]]:
        """抓取ProductHunt数据

        优先使用GraphQL API,失败则使用RSS feed

        Args:
            limit: 限制抓取数量(可选,用于测试)

        Returns:
            原始数据字典列表

        Raises:
            Exception: 抓取失败
        """
        # 如果有API token,尝试使用GraphQL API
        if self.api_token:
            try:
                return self._scrape_via_graphql(limit)
            except Exception as e:
                self.logger.warning(f"GraphQL API failed, falling back to RSS: {e}")

        # 使用RSS feed作为备选方案
        return self._scrape_via_rss(limit)

    def _scrape_via_rss(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """通过RSS feed抓取数据

        Args:
            limit: 限制抓取数量

        Returns:
            原始数据字典列表
        """
        try:
            self.logger.info(f"Fetching ProductHunt RSS feed from {self.rss_url}")

            feed = feedparser.parse(self.rss_url)

            if feed.bozo:
                self.logger.warning(f"RSS feed has errors: {feed.bozo_exception}")

            entries = feed.entries

            if limit:
                entries = entries[:limit]

            self.logger.info(f"Parsed {len(entries)} entries from RSS feed")

            raw_data_list = []
            for entry in entries:
                # 检查是否为AI工具相关
                title = entry.get('title', '').lower()
                description = entry.get('summary', '').lower()

                # 过滤只保留AI相关
                ai_keywords = ['ai', 'artificial intelligence', 'machine learning', 'ml', 'gpt', 'llm', 'neural']
                is_ai_related = any(keyword in title or keyword in description for keyword in ai_keywords)

                if not is_ai_related:
                    continue

                raw_data = {
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'description': entry.get('summary', ''),
                    'published': entry.get('published', ''),
                    'published_parsed': entry.get('published_parsed', None),
                    'tags': [tag.term for tag in entry.get('tags', [])],
                    'content': entry.get('content', [{}])[0].get('value', '') if entry.get('content') else ''
                }
                raw_data_list.append(raw_data)

            return raw_data_list

        except Exception as e:
            self.logger.error(f"Failed to scrape RSS feed: {e}")
            raise

    def _scrape_via_graphql(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """通过GraphQL API抓取数据

        Args:
            limit: 限制抓取数量

        Returns:
            原始数据字典列表

        Note:
            需要ProductHunt API token
            API文档: https://api.producthunt.com/v2/docs
        """
        try:
            self.logger.info("Fetching ProductHunt data via GraphQL API")

            # GraphQL查询
            query = """
            query {
              posts(first: %d, order: VOTES) {
                edges {
                  node {
                    id
                    name
                    tagline
                    description
                    url
                    votesCount
                    createdAt
                    topics {
                      edges {
                        node {
                          name
                        }
                      }
                    }
                  }
                }
              }
            }
            """ % (limit if limit else 50)

            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }

            response = self.session.post(
                self.graphql_url,
                json={"query": query},
                headers=headers,
                timeout=self.timeout
            )

            response.raise_for_status()
            data = response.json()

            raw_data_list = []
            posts = data.get('data', {}).get('posts', {}).get('edges', [])

            for edge in posts:
                node = edge['node']

                # 转换topics为tags
                tags = [topic['node']['name'] for topic in node.get('topics', {}).get('edges', [])]

                # 检查是否为AI工具相关
                title_lower = node.get('name', '').lower()
                description_lower = node.get('description', '').lower()

                ai_keywords = ['ai', 'artificial intelligence', 'machine learning', 'ml', 'gpt', 'llm']
                is_ai_related = any(keyword in title_lower or keyword in description_lower or keyword in ' '.join(tags).lower() for keyword in ai_keywords)

                if not is_ai_related:
                    continue

                raw_data = {
                    'title': node.get('name', ''),
                    'link': node.get('url', ''),
                    'description': node.get('description', node.get('tagline', '')),
                    'published': node.get('createdAt', ''),
                    'tags': tags,
                    'votes': node.get('votesCount', 0)
                }

                raw_data_list.append(raw_data)

            self.logger.info(f"Fetched {len(raw_data_list)} AI-related posts via GraphQL API")
            return raw_data_list

        except Exception as e:
            self.logger.error(f"Failed to scrape via GraphQL API: {e}")
            raise

    def normalize(self, raw_data: Dict[str, Any]) -> AITool:
        """将原始数据转换为AITool模型

        Args:
            raw_data: 原始数据字典

        Returns:
            AITool对象

        Raises:
            ValidationError: 数据验证失败
        """
        # 解析时间戳
        if raw_data.get('published_parsed'):
            timestamp = datetime(*raw_data['published_parsed'][:6], tzinfo=timezone.utc)
        else:
            try:
                timestamp = datetime.fromisoformat(raw_data['published'].replace('Z', '+00:00'))
            except:
                timestamp = datetime.now(timezone.utc)

        # 清理描述
        description_html = raw_data.get('content') or raw_data.get('description', '')
        if description_html and '<' in description_html:
            soup = BeautifulSoup(description_html, 'html.parser')
            description = soup.get_text(strip=True)
        else:
            description = description_html

        # 提取features
        features = self._extract_features(description, raw_data.get('tags', []))

        # 推断定价模式
        pricing_model = self._infer_pricing_model(description)

        # 计算数据质量评分
        source_reliability = 1.0  # ProductHunt是高质量数据源
        content_completeness = 1.0 if (raw_data.get('title') and raw_data.get('link') and description) else 0.7
        data_freshness = 1.0 if (datetime.now(timezone.utc) - timestamp).days < 1 else 0.7

        data_quality_score = (
            source_reliability * 0.4 +
            content_completeness * 0.4 +
            data_freshness * 0.2
        )

        # 创建AITool对象
        tool = AITool(
            name=raw_data['title'],
            description=description[:500],
            source="ProductHunt",
            url=raw_data['link'],
            timestamp=timestamp,
            tags=raw_data.get('tags', ['ai-tool']),
            features=features,
            pricing_model=pricing_model,
            summary_cn="",  # 由LLM生成
            summary_ja="",  # 由LLM生成
            data_quality_score=round(data_quality_score, 2)
        )

        return tool

    def _extract_features(self, description: str, tags: List[str]) -> List[str]:
        """从描述和标签中提取功能列表

        Args:
            description: 描述文本
            tags: 标签列表

        Returns:
            功能列表
        """
        features = []

        feature_keywords = {
            'text-to-image': ['text to image', 'image generation', 'generate images', 'ai art'],
            'video-generation': ['video', 'create video', 'video generation', 'video creation'],
            'text-generation': ['text generation', 'write', 'content', 'copywriting', 'writing'],
            'code-generation': ['code', 'programming', 'developer', 'coding', 'github'],
            'translation': ['translate', 'translation', 'language'],
            'summarization': ['summarize', 'summary', 'tldr'],
            'chatbot': ['chat', 'chatbot', 'conversation', 'assistant'],
            'voice-synthesis': ['voice', 'speech', 'tts', 'text to speech'],
            'data-analysis': ['data', 'analytics', 'analysis', 'insights', 'visualization']
        }

        description_lower = description.lower()
        tags_lower = [tag.lower() for tag in tags]

        for feature, keywords in feature_keywords.items():
            if any(kw in description_lower for kw in keywords) or any(kw in ' '.join(tags_lower) for kw in keywords):
                features.append(feature)

        if not features and tags:
            features = tags[:3]

        if not features:
            features = ['ai-tool']

        return features[:5]

    def _infer_pricing_model(self, description: str) -> str:
        """推断定价模式

        Args:
            description: 描述文本

        Returns:
            定价模式: free/freemium/paid/subscription
        """
        description_lower = description.lower()

        if any(word in description_lower for word in ['free', 'open source', 'free tier', '免费']):
            if any(word in description_lower for word in ['premium', 'pro', 'upgrade', 'paid']):
                return 'freemium'
            return 'free'
        elif any(word in description_lower for word in ['subscription', 'monthly', 'yearly', '订阅', 'saas']):
            return 'subscription'
        elif any(word in description_lower for word in ['paid', 'purchase', 'buy', '付费', 'one-time']):
            return 'paid'

        # 默认:freemium
        return 'freemium'

    def scrape_pain_points(self, limit: int = None) -> List[Dict[str, Any]]:
        """从ProductHunt评论和评价中抓取痛点

        通过GraphQL API或爬取产品页面获取用户评论

        Args:
            limit: 限制抓取的评论数量

        Returns:
            评论数据列表,包含text, context_title, source, url, timestamp等字段
        """
        # ProductHunt的痛点主要来自产品评论和讨论
        # 如果有API token,使用GraphQL获取评论
        if self.api_token:
            return self._scrape_pain_points_via_api(limit)
        else:
            # 否则使用RSS feed中的产品描述作为痛点来源
            self.logger.warning("痛点提取建议使用ProductHunt API,当前使用RSS模式")
            return self._scrape_pain_points_via_rss(limit)

    def _scrape_pain_points_via_api(self, limit: int = None) -> List[Dict[str, Any]]:
        """通过API获取评论中的痛点（增强版）

        Args:
            limit: 限制数量

        Returns:
            评论数据列表
        """
        try:
            # 增强版GraphQL查询 - 获取更多产品和更深入的评论
            query = """
            query {
              posts(first: 30, order: VOTES) {
                edges {
                  node {
                    id
                    name
                    tagline
                    description
                    url
                    votesCount
                    commentsCount
                    comments(first: 20) {
                      edges {
                        node {
                          body
                          createdAt
                          votesCount
                          isHunter
                          user {
                            username
                            headline
                            followersCount
                          }
                          replies(first: 5) {
                            edges {
                              node {
                                body
                                votesCount
                                user {
                                  username
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                    reviews {
                      edges {
                        node {
                          rating
                          body
                          createdAt
                          user {
                            username
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
            """

            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }

            response = self.session.post(
                self.graphql_url,
                json={"query": query},
                headers=headers,
                timeout=self.timeout
            )

            response.raise_for_status()
            data = response.json()

            comments_data = []
            posts = data.get('data', {}).get('posts', {}).get('edges', [])

            # 痛点相关关键词（用于优先级排序）
            pain_keywords = [
                'wish', 'need', 'problem', 'issue', 'missing',
                'would be great', 'should have', 'lacking',
                'alternative', 'competitor', 'better than',
                'expensive', 'pricing', 'cheaper',
                'difficult', 'hard to', 'confusing'
            ]

            for post_edge in posts:
                post = post_edge['node']
                product_name = post['name']
                product_tagline = post.get('tagline', '')
                product_url = post['url']
                product_votes = post.get('votesCount', 0)

                # 1. 处理评论
                comments = post.get('comments', {}).get('edges', [])

                for comment_edge in comments:
                    comment = comment_edge['node']
                    comment_body = comment['body']

                    # 只保留足够长的评论
                    if len(comment_body) < 30:
                        continue

                    # 计算痛点相关性分数
                    pain_score = sum(1 for kw in pain_keywords if kw.lower() in comment_body.lower()) * 20

                    # 基础互动分数
                    votes = comment.get('votesCount', 0)
                    user_followers = comment.get('user', {}).get('followersCount', 0)
                    engagement_score = min(100.0, votes * 10.0 + user_followers * 0.1 + pain_score)

                    comments_data.append({
                        'text': comment_body,
                        'context_title': f"{product_name}: {product_tagline}",
                        'source': 'ProductHunt',
                        'url': product_url,
                        'timestamp': datetime.fromisoformat(
                            comment['createdAt'].replace('Z', '+00:00')
                        ),
                        'engagement_score': engagement_score,
                        'author_metadata': {
                            'username': comment.get('user', {}).get('username', 'Unknown'),
                            'headline': comment.get('user', {}).get('headline', ''),
                            'is_hunter': comment.get('isHunter', False)
                        },
                        'product_metadata': {
                            'product_votes': product_votes,
                            'comments_count': post.get('commentsCount', 0)
                        }
                    })

                    # 处理回复（通常包含更深入的讨论）
                    replies = comment.get('replies', {}).get('edges', [])
                    for reply_edge in replies[:3]:  # 限制每条评论最多3个回复
                        reply = reply_edge['node']
                        reply_body = reply.get('body', '')

                        if len(reply_body) < 20:
                            continue

                        comments_data.append({
                            'text': reply_body,
                            'context_title': f"Reply to: {product_name}",
                            'source': 'ProductHunt',
                            'url': product_url,
                            'timestamp': datetime.now(timezone.utc),  # 回复通常没有时间戳
                            'engagement_score': min(100.0, reply.get('votesCount', 0) * 10.0),
                            'author_metadata': {
                                'username': reply.get('user', {}).get('username', 'Unknown'),
                                'is_reply': True
                            }
                        })

                    if limit and len(comments_data) >= limit:
                        break

                # 2. 处理评价（reviews）- 如果存在
                reviews = post.get('reviews', {}).get('edges', [])
                for review_edge in reviews[:5]:  # 每个产品最多5条评价
                    review = review_edge['node']
                    review_body = review.get('body', '')

                    if len(review_body) < 30:
                        continue

                    # 低评分的评价通常包含痛点
                    rating = review.get('rating', 3)
                    pain_bonus = 30 if rating <= 2 else 0

                    comments_data.append({
                        'text': review_body,
                        'context_title': f"Review of {product_name} ({rating}★)",
                        'source': 'ProductHunt',
                        'url': product_url,
                        'timestamp': datetime.fromisoformat(
                            review.get('createdAt', datetime.now(timezone.utc).isoformat()).replace('Z', '+00:00')
                        ),
                        'engagement_score': 60.0 + pain_bonus,  # 评价通常更有价值
                        'author_metadata': {
                            'username': review.get('user', {}).get('username', 'Unknown'),
                            'rating': rating
                        }
                    })

                if limit and len(comments_data) >= limit:
                    break

            self.logger.info(f"共从ProductHunt API提取{len(comments_data)}条评论")
            return comments_data

        except Exception as e:
            self.logger.error(f"从ProductHunt API提取评论失败: {e}")
            return []

    def _scrape_pain_points_via_rss(self, limit: int = None) -> List[Dict[str, Any]]:
        """从RSS feed的产品描述中提取可能的痛点

        Args:
            limit: 限制数量

        Returns:
            评论数据列表(实际是产品描述)
        """
        try:
            feed = feedparser.parse(self.rss_url)
            comments_data = []

            for entry in feed.entries[:limit or 20]:
                # 使用产品描述作为痛点来源
                description = entry.get('summary', '')

                if len(description) < 50:
                    continue

                comments_data.append({
                    'text': description,
                    'context_title': entry.get('title', ''),
                    'source': 'ProductHunt',
                    'url': entry.get('link', ''),
                    'timestamp': datetime(*entry.get('published_parsed', datetime.now().timetuple())[:6], tzinfo=timezone.utc),
                    'engagement_score': 50.0,  # RSS无法获取准确互动数
                    'author_metadata': {
                        'username': entry.get('author', 'Unknown')
                    }
                })

                if limit and len(comments_data) >= limit:
                    break

            self.logger.info(f"共从ProductHunt RSS提取{len(comments_data)}条产品描述")
            return comments_data

        except Exception as e:
            self.logger.error(f"从ProductHunt RSS提取失败: {e}")
            return []
