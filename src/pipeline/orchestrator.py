"""主流程编排器

协调整个数据处理流程:
抓取 → 规范化 → 去重 → 分类 → 提取痛点 → 匹配 → 评分 → 摘要 → 导出

遵循宪法原则I(数据可靠性)和原则VI(可重现性)
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from src.models.tool import AITool
from src.models.trend import TrendingTopic
from src.models.pain_point import UserPainPoint
from src.models.opportunity import Opportunity
from src.models.scraping_log import ScrapingLog
from src.pipeline.normalizer import DataNormalizer
from src.pipeline.deduplicator import Deduplicator
from src.pipeline.matcher import RelevanceMatcher
from src.pipeline.exporter import DataExporter
from src.pipeline.archiver import DataArchiver
from src.llm.summarizer import BilingualSummarizer
from src.llm.pain_extractor import PainPointExtractor
from src.llm.mvp_suggester import MVPSuggester
from src.scoring.aggregator import OpportunityScoreAggregator
from src.utils.logger import get_logger
from src.utils.config import config

logger = get_logger(__name__)


class PipelineOrchestrator:
    """流程编排器

    协调所有数据处理步骤,确保数据可靠性和可重现性。

    Attributes:
        normalizer: 数据规范化器
        deduplicator: 数据去重器
        matcher: 相关性匹配器
        scorer: 机会评分器
        exporter: 数据导出器
        archiver: 数据归档器
    """

    def __init__(self):
        """初始化流程编排器"""
        self.normalizer = DataNormalizer()
        self.deduplicator = Deduplicator()
        self.matcher = RelevanceMatcher()
        self.scorer = OpportunityScoreAggregator()
        self.exporter = DataExporter()
        self.archiver = DataArchiver()

        # LLM组件
        self.summarizer = BilingualSummarizer()
        self.pain_extractor = PainPointExtractor()
        self.mvp_suggester = MVPSuggester()

        self.scraping_logs: List[ScrapingLog] = []
        self.errors: List[str] = []

    def run_full_pipeline(
        self,
        scrapers: Optional[Dict] = None,
        skip_scraping: bool = False
    ) -> bool:
        """运行完整流程

        Args:
            scrapers: 爬虫字典 {source_name: scraper_instance}
            skip_scraping: 是否跳过抓取(使用现有数据)

        Returns:
            成功返回True,失败返回False
        """
        start_time = datetime.now()
        logger.info("开始运行完整数据处理流程")

        try:
            # Phase 0: 注册scrapers到normalizer
            if scrapers:
                self._register_scrapers(scrapers)

            # Phase 1: 数据抓取
            if not skip_scraping and scrapers:
                tools_data, topics_data = self._scrape_data(scrapers)
            else:
                logger.info("跳过数据抓取,使用现有数据")
                tools_data, topics_data = self._load_existing_data()

            if not tools_data and not topics_data:
                logger.error("没有可用数据")
                return False

            # Phase 2: 数据规范化
            tools = self._normalize_tools(tools_data)
            topics = self._normalize_topics(topics_data)

            # Phase 3: 数据去重
            tools = self._deduplicate_tools(tools)
            topics = self._deduplicate_topics(topics)

            # Phase 3.5: 数据筛选（精简到高质量数据）
            tools = self._filter_top_tools(tools)
            topics = self._filter_top_topics(topics)

            # Phase 4: 提取痛点（只从核心源提取）
            pain_points = self._extract_pain_points_from_core_sources(topics)

            # Phase 5: 生成摘要
            tools = self._generate_summaries_tools(tools)
            topics = self._generate_summaries_topics(topics)
            pain_points = self._generate_summaries_pain_points(pain_points)

            # Phase 6: 直接生成MVP机会（不再匹配工具）
            opportunities = self._generate_opportunities_direct(pain_points, topics)

            # Phase 9: 导出数据
            self._export_data(tools, topics, pain_points, opportunities)

            # Phase 10: 归档历史数据
            self._archive_data()

            # 记录成功日志
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"流程完成",
                extra={"extra_fields": {
                    "duration_seconds": duration,
                    "ai_tools_count": len(tools),
                    "trending_topics_count": len(topics),
                    "pain_points_count": len(pain_points),
                    "opportunities_count": len(opportunities),
                    "errors_count": len(self.errors)
                }}
            )

            return True

        except Exception as e:
            logger.error(f"流程失败: {e}")
            self.errors.append(str(e))
            return False

    def _register_scrapers(self, scrapers: Dict):
        """将scrapers注册到normalizer

        Args:
            scrapers: 爬虫字典 {source_name: scraper_instance}
        """
        logger.info(f"注册 {len(scrapers)} 个scrapers到normalizer")
        for source_name, scraper in scrapers.items():
            self.normalizer.register_scraper(scraper)
            logger.debug(f"Registered scraper: {source_name}")

    def _scrape_data(self, scrapers: Dict) -> tuple:
        """抓取数据

        Args:
            scrapers: 爬虫字典

        Returns:
            (tools_data, topics_data) 元组
        """
        logger.info("Phase 1: 开始数据抓取")

        tools_data = []
        topics_data = []

        for source_name, scraper in scrapers.items():
            try:
                start_time = datetime.now()
                data = scraper.scrape()
                duration = (datetime.now() - start_time).total_seconds()

                # 记录日志
                log = ScrapingLog(
                    source=source_name,
                    status="success",
                    records_count=len(data) if data else 0,
                    errors=[],
                    duration_seconds=duration,
                    timestamp=datetime.now()
                )
                self.scraping_logs.append(log)

                # 为每条数据添加source字段
                for item in data:
                    if isinstance(item, dict) and 'source' not in item:
                        item['source'] = source_name

                # 分类数据
                if hasattr(scraper, 'scraper_type'):
                    if scraper.scraper_type == 'ai_tools':
                        tools_data.extend(data)
                    elif scraper.scraper_type == 'trends':
                        topics_data.extend(data)
                else:
                    # 默认按source_name分类
                    # AI工具源: futurepedia, theresanai, producthunt
                    if any(keyword in source_name.lower() for keyword in ['tool', 'product', 'futurepedia', 'theresanai']):
                        tools_data.extend(data)
                    else:
                        topics_data.extend(data)

                logger.info(f"✅ [{source_name}] 抓取成功: {len(data)}条")

            except Exception as e:
                # 单个数据源失败不影响其他数据源 (FR-016)
                error_msg = f"[{source_name}] 抓取失败: {e}"
                logger.warning(error_msg)
                self.errors.append(error_msg)

                log = ScrapingLog(
                    source=source_name,
                    status="failed",
                    records_count=0,
                    errors=[str(e)],
                    duration_seconds=0,
                    timestamp=datetime.now()
                )
                self.scraping_logs.append(log)

        return tools_data, topics_data

    def _load_existing_data(self) -> tuple:
        """加载现有数据"""
        try:
            data_path = Path('data/latest.json')
            if data_path.exists():
                with open(data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data.get('ai_tools', []), data.get('trending_topics', [])
        except Exception as e:
            logger.error(f"加载现有数据失败: {e}")

        return [], []

    def _normalize_tools(self, tools_data: List[Dict]) -> List[AITool]:
        """规范化AI工具数据"""
        logger.info(f"Phase 2: 规范化 {len(tools_data)} 条AI工具数据")
        try:
            # 使用normalizer来处理原始数据
            if tools_data:
                # 按source分组处理
                tools_by_source = {}
                for tool in tools_data:
                    source = tool.get('source', 'Unknown')
                    if source not in tools_by_source:
                        tools_by_source[source] = []
                    tools_by_source[source].append(tool)

                normalized_tools = []
                for source, tools in tools_by_source.items():
                    normalized = self.normalizer.normalize_ai_tools(tools, source)
                    normalized_tools.extend(normalized)

                return normalized_tools
            return []
        except Exception as e:
            logger.error(f"规范化工具数据失败: {e}")
            return []

    def _normalize_topics(self, topics_data: List[Dict]) -> List[TrendingTopic]:
        """规范化热点数据"""
        logger.info(f"Phase 2: 规范化 {len(topics_data)} 条热点数据")
        try:
            # 使用normalizer来处理原始数据
            if topics_data:
                # 按source分组处理
                topics_by_source = {}
                for topic in topics_data:
                    source = topic.get('source', 'Unknown')
                    if source not in topics_by_source:
                        topics_by_source[source] = []
                    topics_by_source[source].append(topic)

                normalized_topics = []
                for source, topics in topics_by_source.items():
                    normalized = self.normalizer.normalize_trending_topics(topics, source)
                    normalized_topics.extend(normalized)

                return normalized_topics
            return []
        except Exception as e:
            logger.error(f"规范化热点数据失败: {e}")
            return []

    def _deduplicate_tools(self, tools: List[AITool]) -> List[AITool]:
        """去重AI工具"""
        logger.info("Phase 3: 去重AI工具")
        return self.deduplicator.deduplicate_ai_tools(tools)

    def _deduplicate_topics(self, topics: List[TrendingTopic]) -> List[TrendingTopic]:
        """去重热点"""
        logger.info("Phase 3: 去重热点")
        return self.deduplicator.deduplicate_trending_topics(topics)

    def _extract_pain_points(self, topics: List[TrendingTopic]) -> List[UserPainPoint]:
        """提取痛点"""
        logger.info("Phase 4: 提取用户痛点")
        pain_points = []

        for topic in topics:
            try:
                # 从描述中提取痛点
                extracted = self.pain_extractor.extract_from_text(
                    text=topic.description,
                    context=topic.title,
                    source=topic.source,
                    url=topic.url
                )
                if extracted:
                    pain_points.append(extracted)
            except Exception as e:
                logger.warning(f"提取痛点失败: {e}")

        logger.info(f"提取到 {len(pain_points)} 个痛点")
        return pain_points

    def _generate_summaries_tools(self, tools: List[AITool]) -> List[AITool]:
        """生成AI工具摘要"""
        logger.info("Phase 5: 生成AI工具摘要")

        for tool in tools:
            try:
                if not tool.summary_cn or not tool.summary_ja:
                    summaries = self.summarizer.generate_summary(tool.description)
                    if summaries:
                        tool.summary_cn = summaries['summary_cn']
                        tool.summary_ja = summaries['summary_ja']
            except Exception as e:
                logger.warning(f"生成工具摘要失败 [{tool.name}]: {e}")

        return tools

    def _generate_summaries_topics(self, topics: List[TrendingTopic]) -> List[TrendingTopic]:
        """生成热点摘要"""
        logger.info("Phase 5: 生成热点摘要")

        for topic in topics:
            try:
                if not topic.summary_cn or not topic.summary_ja:
                    summaries = self.summarizer.generate_summary(topic.description)
                    if summaries:
                        topic.summary_cn = summaries['summary_cn']
                        topic.summary_ja = summaries['summary_ja']
            except Exception as e:
                logger.warning(f"生成热点摘要失败 [{topic.title}]: {e}")

        return topics

    def _generate_summaries_pain_points(self, pain_points: List[UserPainPoint]) -> List[UserPainPoint]:
        """生成痛点摘要"""
        logger.info("Phase 5: 生成痛点摘要")
        # 痛点摘要在提取时已生成
        return pain_points

    def _filter_top_tools(self, tools: List[AITool]) -> List[AITool]:
        """筛选Top 10 AI工具（综合排序：新鲜度30% + 质量70%）

        Args:
            tools: AI工具列表

        Returns:
            Top 10工具列表
        """
        logger.info(f"Phase 3.5: 筛选Top 10 AI工具（当前 {len(tools)} 个）")

        if not tools:
            return []

        # 计算综合评分
        scored_tools = []
        now = datetime.now()

        for tool in tools:
            # 新鲜度评分（0-100）：基于发布时间
            if hasattr(tool, 'published_at') and tool.published_at:
                days_ago = (now - tool.published_at).days
                freshness_score = max(0, 100 - days_ago * 2)  # 每天-2分
            else:
                freshness_score = 50  # 默认中等新鲜度

            # 质量评分（0-100）：基于多个指标
            quality_score = 0

            # 有描述 +20
            if tool.description and len(tool.description) > 50:
                quality_score += 20

            # 有标签 +15
            if tool.tags and len(tool.tags) > 0:
                quality_score += 15

            # 有URL +15
            if tool.url:
                quality_score += 15

            # 有摘要 +20
            if tool.summary_cn or tool.summary_ja:
                quality_score += 20

            # 来自高质量源 +30
            high_quality_sources = ['producthunt', 'futurepedia']
            if any(source in tool.source.lower() for source in high_quality_sources):
                quality_score += 30

            # 综合评分：新鲜度30% + 质量70%
            composite_score = freshness_score * 0.3 + quality_score * 0.7

            scored_tools.append({
                'tool': tool,
                'composite_score': composite_score,
                'freshness_score': freshness_score,
                'quality_score': quality_score
            })

        # 按综合评分排序
        scored_tools.sort(key=lambda x: x['composite_score'], reverse=True)

        # 返回Top 10
        top_tools = [item['tool'] for item in scored_tools[:10]]

        logger.info(
            f"筛选完成: {len(top_tools)} 个工具",
            extra={"extra_fields": {
                "original_count": len(tools),
                "filtered_count": len(top_tools),
                "avg_composite_score": sum(item['composite_score'] for item in scored_tools[:10]) / len(top_tools) if top_tools else 0
            }}
        )

        return top_tools

    def _has_pain_signal(self, text: str) -> bool:
        """检查文本是否包含痛点信号关键词

        Args:
            text: 要检查的文本

        Returns:
            True如果包含痛点信号
        """
        if not text:
            return False

        text_lower = text.lower()
        pain_keywords = [
            'need', 'want', 'looking for', 'wish', 'problem',
            'struggling', 'frustrated', 'pain point', 'issue',
            'challenge', 'difficult', 'hard to', 'how to',
            'would pay', 'willing to pay', 'better way',
            'alternative to', 'missing', 'lack of'
        ]

        return any(keyword in text_lower for keyword in pain_keywords)

    def _calculate_pain_score(self, topic: TrendingTopic) -> float:
        """计算痛点评分

        Args:
            topic: 热点话题

        Returns:
            痛点评分（0-100）
        """
        pain_score = 0

        # 检查标题和描述中的痛点信号
        title_has_pain = self._has_pain_signal(topic.title)
        desc_has_pain = self._has_pain_signal(topic.description)

        if title_has_pain:
            pain_score += 40
        if desc_has_pain:
            pain_score += 30

        # 来自高价值痛点源
        pain_sources = ['reddit', 'github discussions', 'hacker news']
        if any(source in topic.source.lower() for source in pain_sources):
            pain_score += 20

        # 互动量加成
        if hasattr(topic, 'heat_score'):
            pain_score += min(10, topic.heat_score / 10)

        return min(100, pain_score)

    def _filter_top_topics(self, topics: List[TrendingTopic]) -> List[TrendingTopic]:
        """筛选Top 20热点话题（混合策略：12个高热度+8个高痛点）

        Args:
            topics: 热点话题列表

        Returns:
            Top 20话题列表（包含热点和痛点）
        """
        logger.info(f"Phase 3.5: 筛选Top 20热点话题（当前 {len(topics)} 个，混合热点+痛点）")

        if not topics:
            return []

        # 分类和评分
        heat_topics = []  # 高热度话题
        pain_topics = []  # 高痛点话题

        for topic in topics:
            # 基础质量评分（0-100）
            quality_score = 0

            # 有描述且长度合适 +25
            if topic.description and 50 <= len(topic.description) <= 1000:
                quality_score += 25

            # 有标签 +15
            if topic.tags and len(topic.tags) > 0:
                quality_score += 15

            # 有URL +10
            if topic.url:
                quality_score += 10

            # 有摘要 +20
            if topic.summary_cn or topic.summary_ja:
                quality_score += 20

            # 来自高质量源（Tier 1）+30
            tier1_sources = ['hackernews', 'github', 'reddit']
            if any(source in topic.source.lower() for source in tier1_sources):
                quality_score += 30

            # 热度评分（0-100）
            heat_score = min(100, topic.heat_score) if hasattr(topic, 'heat_score') else 50

            # 痛点评分（0-100）
            pain_score = self._calculate_pain_score(topic)

            # 判断类型：痛点评分高于50则归类为痛点话题，否则为热点话题
            if pain_score >= 50:
                pain_topics.append({
                    'topic': topic,
                    'pain_score': pain_score,
                    'quality_score': quality_score,
                    'heat_score': heat_score
                })
            else:
                # 综合评分：质量70% + 热度30%
                composite_score = quality_score * 0.7 + heat_score * 0.3
                heat_topics.append({
                    'topic': topic,
                    'composite_score': composite_score,
                    'quality_score': quality_score,
                    'heat_score': heat_score
                })

        # 分别排序
        heat_topics.sort(key=lambda x: x['composite_score'], reverse=True)
        pain_topics.sort(key=lambda x: x['pain_score'], reverse=True)

        # 质量阈值：综合评分≥55分
        quality_threshold = 55

        # 选择Top 12热点话题
        top_heat = [
            item['topic'] for item in heat_topics[:15]
            if item['composite_score'] >= quality_threshold
        ][:12]

        # 选择Top 8痛点话题
        top_pain = [
            item['topic'] for item in pain_topics[:10]
            if item['pain_score'] >= 50
        ][:8]

        # 合并
        top_topics = top_heat + top_pain

        logger.info(
            f"筛选完成: {len(top_topics)} 个话题（热点:{len(top_heat)}个，痛点:{len(top_pain)}个）",
            extra={"extra_fields": {
                "original_count": len(topics),
                "filtered_count": len(top_topics),
                "heat_topics_count": len(top_heat),
                "pain_topics_count": len(top_pain),
                "quality_threshold": quality_threshold
            }}
        )

        return top_topics

    def _extract_pain_points_from_core_sources(self, topics: List[TrendingTopic]) -> List[UserPainPoint]:
        """只从核心三源（HN+Reddit+GitHub）提取痛点，优先核心源，返回Top 20

        Args:
            topics: 热点话题列表

        Returns:
            Top 20痛点列表
        """
        logger.info("Phase 4: 从核心源提取用户痛点")

        # 核心源定义
        core_sources = ['hackernews', 'reddit', 'github']

        # 先筛选出核心源的话题
        core_topics = [
            topic for topic in topics
            if any(source in topic.source.lower() for source in core_sources)
        ]

        # 如果核心源话题不足，补充其他高质量话题
        if len(core_topics) < 20:
            other_topics = [
                topic for topic in topics
                if not any(source in topic.source.lower() for source in core_sources)
            ]
            # 按热度排序补充
            other_topics.sort(key=lambda x: getattr(x, 'heat_score', 0), reverse=True)
            core_topics.extend(other_topics[:20 - len(core_topics)])

        logger.info(f"筛选到 {len(core_topics)} 个核心源话题用于痛点提取")

        # 优先处理包含痛点信号的话题
        topics_with_pain_signal = []
        topics_without_pain_signal = []

        for topic in core_topics:
            if self._has_pain_signal(topic.title) or self._has_pain_signal(topic.description):
                topics_with_pain_signal.append(topic)
            else:
                topics_without_pain_signal.append(topic)

        # 合并：优先处理痛点信号话题
        sorted_topics = topics_with_pain_signal + topics_without_pain_signal

        logger.info(f"其中包含痛点信号的话题: {len(topics_with_pain_signal)}个")

        # 从话题中提取痛点（扩大处理范围到50个）
        pain_points = []
        for topic in sorted_topics[:50]:  # 从30增加到50
            try:
                extracted = self.pain_extractor.extract_from_text(
                    text=topic.description,
                    context=topic.title,
                    source=topic.source,
                    url=topic.url
                )
                if extracted:
                    pain_points.append(extracted)
            except Exception as e:
                logger.warning(f"提取痛点失败: {e}")

        # 按置信度排序，返回Top 20
        pain_points.sort(key=lambda x: x.confidence_score, reverse=True)
        top_pain_points = pain_points[:20]

        logger.info(
            f"提取到 {len(top_pain_points)} 个痛点",
            extra={"extra_fields": {
                "total_extracted": len(pain_points),
                "top_count": len(top_pain_points),
                "avg_confidence": sum(p.confidence_score for p in top_pain_points) / len(top_pain_points) if top_pain_points else 0
            }}
        )

        return top_pain_points

    def _generate_opportunities_direct(
        self,
        pain_points: List[UserPainPoint],
        topics: List[TrendingTopic]
    ) -> List[Dict]:
        """直接从痛点和热点生成10个MVP机会（不匹配现有工具）

        Args:
            pain_points: 痛点列表
            topics: 热点话题列表

        Returns:
            Top 10 MVP机会列表
        """
        logger.info("Phase 6: 直接生成MVP机会（基于痛点+热点）")

        opportunities = []

        # 为每个痛点生成MVP机会
        for pain_point in pain_points[:15]:  # 多生成一些，然后筛选Top 10
            try:
                # 找到相关热点（基于关键词匹配）
                related_topics = self._find_related_topics(pain_point, topics)

                # 生成MVP建议
                mvp = self.mvp_suggester.generate(
                    pain_point=pain_point,
                    related_topics=related_topics
                )

                if not mvp:
                    continue

                # 计算机会评分（基于痛点质量和热点趋势）
                opportunity_score = self._calculate_opportunity_score(
                    pain_point, related_topics
                )

                # 聚合标签（从痛点和热点）
                tags = list(set(pain_point.tags + [tag for topic in related_topics for tag in topic.tags]))

                # 构建机会对象（符合Opportunity模型）
                opportunity = {
                    'pain_point_id': pain_point.id,
                    'related_topics': [topic.id for topic in related_topics],
                    'mvp_suggestion_cn': mvp['mvp_suggestion_cn'],
                    'mvp_suggestion_ja': mvp['mvp_suggestion_ja'],
                    'opportunity_score': opportunity_score,
                    'timestamp': datetime.now(),
                    'tags': tags,
                    'data_quality_score': pain_point.confidence_score  # 使用痛点置信度作为质量评分
                }

                opportunities.append(opportunity)

            except Exception as e:
                logger.warning(f"生成MVP机会失败: {e}")

        # 按机会评分排序，返回Top 10
        opportunities.sort(key=lambda x: x['opportunity_score'], reverse=True)
        top_opportunities = opportunities[:10]

        logger.info(
            f"生成 {len(top_opportunities)} 个MVP机会",
            extra={"extra_fields": {
                "total_generated": len(opportunities),
                "top_count": len(top_opportunities),
                "avg_score": sum(o['opportunity_score'] for o in top_opportunities) / len(top_opportunities) if top_opportunities else 0
            }}
        )

        return top_opportunities

    def _find_related_topics(
        self,
        pain_point: UserPainPoint,
        topics: List[TrendingTopic],
        max_topics: int = 3
    ) -> List[TrendingTopic]:
        """找到与痛点相关的热点话题

        Args:
            pain_point: 用户痛点
            topics: 热点话题列表
            max_topics: 最多返回话题数

        Returns:
            相关话题列表
        """
        if not topics:
            return []

        # 提取痛点关键词
        pain_keywords = set(pain_point.extracted_keywords)

        # 计算每个话题的相关度
        scored_topics = []
        for topic in topics:
            # 提取话题关键词（从标题和标签）
            topic_keywords = set()
            if topic.title:
                topic_keywords.update(topic.title.lower().split())
            if topic.tags:
                topic_keywords.update([tag.lower() for tag in topic.tags])

            # 计算关键词重叠度
            overlap = len(pain_keywords & topic_keywords)

            # 相关度评分：关键词重叠度 + 热度加权
            relevance_score = overlap * 10 + (topic.heat_score if hasattr(topic, 'heat_score') else 0) * 0.1

            scored_topics.append({
                'topic': topic,
                'relevance_score': relevance_score
            })

        # 按相关度排序
        scored_topics.sort(key=lambda x: x['relevance_score'], reverse=True)

        # 返回最相关的话题
        return [item['topic'] for item in scored_topics[:max_topics]]

    def _calculate_opportunity_score(
        self,
        pain_point: UserPainPoint,
        related_topics: List[TrendingTopic]
    ) -> float:
        """计算机会评分（基于痛点质量和热点趋势）

        Args:
            pain_point: 用户痛点
            related_topics: 相关热点列表

        Returns:
            机会评分（0-100）
        """
        # 痛点质量评分（0-60）：置信度 * 60
        pain_quality_score = pain_point.confidence_score * 60

        # 热点趋势评分（0-40）：相关热点的平均热度 * 0.4
        if related_topics:
            avg_heat = sum(
                getattr(topic, 'heat_score', 0) for topic in related_topics
            ) / len(related_topics)
            trend_score = avg_heat * 0.4
        else:
            trend_score = 0

        # 总评分
        total_score = pain_quality_score + trend_score

        return min(100, total_score)  # 上限100分

    def _export_data(
        self,
        tools: List[AITool],
        topics: List[TrendingTopic],
        pain_points: List[UserPainPoint],
        opportunities: List[Dict]
    ):
        """导出数据"""
        logger.info("Phase 9: 导出数据")

        # 将Opportunity字典转换为Opportunity对象
        opp_objects = []
        for opp_dict in opportunities:
            if isinstance(opp_dict, dict):
                opp_objects.append(Opportunity(**opp_dict))
            else:
                opp_objects.append(opp_dict)

        self.exporter.export_to_json(
            ai_tools=tools,
            trending_topics=topics,
            pain_points=pain_points,
            opportunities=opp_objects
        )

    def _archive_data(self):
        """归档数据"""
        logger.info("Phase 10: 归档历史数据")
        self.archiver.archive_latest()


# 全局实例
default_orchestrator = PipelineOrchestrator()
