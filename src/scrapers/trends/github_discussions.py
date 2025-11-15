"""GitHub Discussions爬虫

从GitHub热门项目的Discussions中抓取feature requests和用户需求。
开发者社区的功能请求往往代表真实的产品痛点和技术需求。

使用GitHub GraphQL API v4
文档：https://docs.github.com/en/graphql
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from uuid import uuid4
import json

from src.scrapers.base import BaseScraper
from src.models.trend import TrendingTopic


class GitHubDiscussionsScraper(BaseScraper):
    """GitHub Discussions爬虫

    抓取热门开源项目的功能请求和讨论：
    - VS Code, React, Next.js等高星项目
    - 过滤feature request, enhancement标签
    - 按👍反应数排序

    数据质量评分：0.9（技术社区，需求明确）
    """

    def __init__(self):
        super().__init__(
            source_name="GitHub Discussions",
            base_url="https://api.github.com"
        )

        # GraphQL API端点
        self.graphql_url = "https://api.github.com/graphql"

        # 从配置加载GitHub Token
        from src.utils.config import config
        self.github_token = getattr(config, 'github_token', None)

        # 目标仓库（owner/name格式）
        # 选择高星、活跃的项目，它们的discussions质量高
        self.target_repos = [
            "microsoft/vscode",       # VS Code - 开发工具
            "vercel/next.js",        # Next.js - Web框架
            "facebook/react",        # React - UI库
            "python/cpython",        # Python - 编程语言
            "rust-lang/rust",        # Rust - 编程语言
            "golang/go",             # Go - 编程语言
            "nodejs/node",           # Node.js - 运行时
            "tensorflow/tensorflow", # TensorFlow - AI框架
            "anthropics/anthropic-sdk-python",  # Anthropic SDK
            "openai/openai-python",  # OpenAI SDK
        ]

        # Feature request关键词
        self.feature_keywords = [
            "feature request",
            "enhancement",
            "proposal",
            "idea",
            "suggestion",
            "would be nice",
            "can we have",
            "please add",
            "support for",
            "implement"
        ]

    def _make_graphql_request(self, query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        """发送GraphQL请求

        Args:
            query: GraphQL查询语句
            variables: 查询变量

        Returns:
            响应数据
        """
        if not self.github_token:
            raise ValueError("GitHub token未配置，请设置GITHUB_TOKEN环境变量")

        headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "query": query,
            "variables": variables or {}
        }

        response = self.session.post(
            self.graphql_url,
            headers=headers,
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()

        data = response.json()

        if 'errors' in data:
            raise Exception(f"GraphQL错误: {data['errors']}")

        return data['data']

    def _fetch_discussions(self, owner: str, repo: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取某个仓库的Discussions

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            limit: 限制数量

        Returns:
            Discussion列表
        """
        # GraphQL查询：获取Discussions，按👍反应数排序
        query = """
        query($owner: String!, $repo: String!, $limit: Int!) {
          repository(owner: $owner, name: $repo) {
            discussions(first: $limit, orderBy: {field: CREATED_AT, direction: DESC}) {
              nodes {
                id
                title
                body
                url
                createdAt
                updatedAt
                author {
                  login
                }
                category {
                  name
                }
                upvoteCount
                comments {
                  totalCount
                }
                labels(first: 5) {
                  nodes {
                    name
                  }
                }
                reactions(first: 1) {
                  totalCount
                }
              }
            }
          }
        }
        """

        variables = {
            "owner": owner,
            "repo": repo,
            "limit": limit
        }

        try:
            data = self._make_graphql_request(query, variables)
            discussions = data.get('repository', {}).get('discussions', {}).get('nodes', [])
            return discussions
        except Exception as e:
            self.logger.warning(f"获取{owner}/{repo} discussions失败: {e}")
            return []

    def _is_feature_request(self, discussion: Dict[str, Any]) -> tuple[bool, List[str]]:
        """判断是否是功能请求

        Args:
            discussion: Discussion数据

        Returns:
            (是否是feature request, 匹配的关键词)
        """
        # 检查category
        category = discussion.get('category', {})
        if category:
            category_name = category.get('name', '').lower()
            if any(keyword in category_name for keyword in ['feature', 'idea', 'enhancement']):
                return True, [f"category:{category_name}"]

        # 检查labels
        labels = discussion.get('labels', {}).get('nodes', [])
        for label in labels:
            label_name = label.get('name', '').lower()
            if any(keyword in label_name for keyword in ['feature', 'enhancement', 'proposal']):
                return True, [f"label:{label_name}"]

        # 检查标题和内容
        title = discussion.get('title', '').lower()
        body = discussion.get('body', '').lower()
        text = f"{title} {body}"

        matched_keywords = []
        for keyword in self.feature_keywords:
            if keyword in text:
                matched_keywords.append(keyword)

        return len(matched_keywords) > 0, matched_keywords

    def scrape(self, limit: int = None) -> List[Dict[str, Any]]:
        """抓取GitHub Discussions数据

        Args:
            limit: 限制抓取数量（None=30）

        Returns:
            原始数据字典列表
        """
        limit = limit or 30
        results = []
        discussions_per_repo = max(5, limit // len(self.target_repos))

        self.logger.info(f"开始抓取GitHub Discussions（目标{limit}条）")

        for repo_full_name in self.target_repos:
            owner, repo = repo_full_name.split('/')

            self.logger.info(f"抓取{repo_full_name}的discussions")

            discussions = self._fetch_discussions(owner, repo, limit=discussions_per_repo * 2)

            for discussion in discussions:
                # 过滤出feature requests
                is_feature, matched_kw = self._is_feature_request(discussion)

                if not is_feature:
                    continue

                # 提取数据
                results.append({
                    'id': discussion.get('id'),
                    'title': discussion.get('title', ''),
                    'body': discussion.get('body', ''),
                    'url': discussion.get('url', ''),
                    'author': discussion.get('author', {}).get('login', 'Unknown'),
                    'category': discussion.get('category', {}).get('name', ''),
                    'upvote_count': discussion.get('upvoteCount', 0),
                    'comment_count': discussion.get('comments', {}).get('totalCount', 0),
                    'reaction_count': discussion.get('reactions', {}).get('totalCount', 0),
                    'created_at': discussion.get('createdAt'),
                    'updated_at': discussion.get('updatedAt'),
                    'labels': [l.get('name') for l in discussion.get('labels', {}).get('nodes', [])],
                    'repo': repo_full_name,
                    'matched_keywords': matched_kw
                })

                if len(results) >= limit:
                    break

            if len(results) >= limit:
                break

        self.logger.info(f"共从GitHub Discussions抓取{len(results)}条数据")

        # 按upvote数排序
        results.sort(key=lambda x: x['upvote_count'], reverse=True)

        return results[:limit]

    def scrape_pain_points(self, limit: int = None) -> List[Dict[str, Any]]:
        """从GitHub Discussions抓取痛点数据

        Args:
            limit: 限制抓取数量

        Returns:
            痛点数据列表
        """
        limit = limit or 50

        # GitHub的feature requests本身就是痛点
        discussions = self.scrape(limit=limit)

        pain_points = []

        for disc in discussions:
            # 计算engagement分数（基于upvotes和评论数）
            upvotes = disc.get('upvote_count', 0)
            comments = disc.get('comment_count', 0)

            # GitHub的upvote权重很高（开发者投票很有价值）
            engagement_score = min(100.0, upvotes * 2 + comments * 0.5)

            pain_points.append({
                'text': f"{disc['title']}\n\n{disc.get('body', '')[:500]}",
                'context_title': f"[{disc['repo']}] {disc['title']}",
                'source': 'GitHub Discussions',
                'url': disc['url'],
                'timestamp': datetime.fromisoformat(
                    disc['created_at'].replace('Z', '+00:00')
                ),
                'engagement_score': engagement_score,
                'payment_willingness_score': 40.0,  # 开发者需求，中等变现潜力
                'matched_keywords': disc.get('matched_keywords', []),
                'author_metadata': {
                    'username': disc['author'],
                    'repo': disc['repo']
                },
                'type': 'github_feature_request'
            })

        self.logger.info(f"共从GitHub Discussions提取{len(pain_points)}条痛点")

        # 按engagement分数排序
        pain_points.sort(key=lambda x: x['engagement_score'], reverse=True)

        return pain_points

    def normalize(self, raw_data: Dict[str, Any]) -> TrendingTopic:
        """将原始数据转换为TrendingTopic模型

        Args:
            raw_data: 原始数据字典

        Returns:
            TrendingTopic对象
        """
        # 计算热度分数
        upvotes = raw_data.get('upvote_count', 0)
        comments = raw_data.get('comment_count', 0)

        # GitHub热度：upvote*3 + comment*1，归一化到0-100
        # 假设30 upvotes + 20 comments = 100分
        heat_score = min(100.0, (upvotes * 3 + comments * 1) / 1.1)

        # 解析时间
        created_at = raw_data.get('created_at')
        if created_at:
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        else:
            dt = datetime.now(timezone.utc)

        # 标题和描述
        title = f"[{raw_data['repo']}] {raw_data['title']}"
        body = raw_data.get('body', '')
        description = f"{raw_data['title']}\n\n{body[:400]}"  # 限制长度

        # 标签
        tags = ["GitHub", raw_data['repo'], "feature-request"]
        tags.extend(raw_data.get('labels', [])[:3])

        return TrendingTopic(
            id=str(uuid4()),
            title=title[:200],
            description=description[:1500],
            source="GitHub Discussions",
            url=raw_data['url'],
            timestamp=dt,
            heat_score=heat_score,
            trend_direction="stable",
            tags=tags,
            summary_cn="",  # 由LLM生成
            summary_ja="",  # 由LLM生成
            data_quality_score=0.9,  # GitHub discussions质量很高
            schema_version="1.1"
        )
