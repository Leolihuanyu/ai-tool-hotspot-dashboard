"""pn»Í;

úhash»Í,2båwÝ«Í
°U
&FR-003: »Í;(útitle+URLhash)
"""

import hashlib
from typing import List, Dict, Any, Union, Set
from src.models.tool import AITool
from src.models.trend import TrendingTopic
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Deduplicator:
    """pn»Íh

    (hash-based¹Õ»Í,útitle+URLÄ
    """

    def __init__(self):
        """Ë»Íh"""
        self.seen_hashes: Set[str] = set()

    def _generate_hash(self, title: str, url: str) -> str:
        """生成hash值

        Args:
            title: 标题
            url: URL

        Returns:
            SHA256 hash字符串
        """
        # 规范化
        normalized_title = str(title).lower().strip()
        normalized_url = str(url).lower().strip()

        # ûdURLåâÂpfragment
        if '?' in normalized_url:
            normalized_url = normalized_url.split('?')[0]
        if '#' in normalized_url:
            normalized_url = normalized_url.split('#')[0]

        # hash
        content = f"{normalized_title}||{normalized_url}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def deduplicate_ai_tools(self, tools: List[AITool]) -> List[AITool]:
        """»ÍAIåwh

        Args:
            tools: AIToolùah

        Returns:
            »ÍAIToolh
        """
        if not tools:
            return []

        unique_tools = []
        duplicates_count = 0

        for tool in tools:
            try:
                tool_hash = self._generate_hash(tool.name, tool.url)

                if tool_hash not in self.seen_hashes:
                    self.seen_hashes.add(tool_hash)
                    unique_tools.append(tool)
                else:
                    duplicates_count += 1
                    logger.debug(f"Duplicate tool found: {tool.name} ({tool.url})")

            except Exception as e:
                logger.error(f"Failed to process tool for deduplication: {e}")
                continue

        logger.info(f"Deduplicated AI tools: {len(unique_tools)} unique, {duplicates_count} duplicates removed")
        return unique_tools

    def deduplicate_trending_topics(self, topics: List[TrendingTopic]) -> List[TrendingTopic]:
        """»Íí¹Ýh

        ùí¹Ý,Ý(*sðú°,v

        Args:
            topics: TrendingTopicùah

        Returns:
            »ÍTrendingTopich
        """
        if not topics:
            return []

        # ,e:úhash»Í
        unique_topics = []
        duplicates_count = 0
        topic_groups: Dict[str, List[TrendingTopic]] = {}  # hash -> [topics]

        for topic in topics:
            try:
                topic_hash = self._generate_hash(topic.title, topic.url)

                if topic_hash not in topic_groups:
                    topic_groups[topic_hash] = [topic]
                else:
                    topic_groups[topic_hash].append(topic)
                    duplicates_count += 1

            except Exception as e:
                logger.error(f"Failed to process topic for deduplication: {e}")
                continue

        # ,e:vèsðøÝ
        for topic_hash, topics_list in topic_groups.items():
            if len(topics_list) == 1:
                # /Ý,ô¥û
                unique_topics.append(topics_list[0])
            else:
                # *sðøÝ,v
                merged_topic = self._merge_topics(topics_list)
                unique_topics.append(merged_topic)

        logger.info(f"Deduplicated trending topics: {len(unique_topics)} unique, {duplicates_count} duplicates merged")
        return unique_topics

    def _merge_topics(self, topics: List[TrendingTopic]) -> TrendingTopic:
        """v*sðøÝ

        Args:
            topics: øÝh

        Returns:
            vTrendingTopicùa
        """
        # 	éheat_scoreØ\:úÆ
        base_topic = max(topics, key=lambda t: t.heat_score)

        # 6Æ@	sð
        all_platforms = set()
        for topic in topics:
            all_platforms.add(topic.source)
            if topic.platforms:
                all_platforms.update(topic.platforms)

        # vtags
        all_tags = set()
        for topic in topics:
            all_tags.update(topic.tags)

        # ¡sGí¦
        avg_heat = sum(t.heat_score for t in topics) / len(topics)

        # úvtopic
        merged = TrendingTopic(
            id=base_topic.id,
            title=base_topic.title,
            description=base_topic.description,
            source=base_topic.source,
            url=base_topic.url,
            timestamp=base_topic.timestamp,
            heat_score=round(avg_heat, 2),
            trend_direction=base_topic.trend_direction,
            tags=sorted(list(all_tags)),
            summary_cn=base_topic.summary_cn,
            summary_ja=base_topic.summary_ja,
            data_quality_score=base_topic.data_quality_score,
            platforms=sorted(list(all_platforms)),
            trend_velocity=base_topic.trend_velocity
        )

        logger.debug(f"Merged topic from {len(topics)} platforms: {merged.title}")
        return merged

    def reset(self):
        """Ín»Íh¶

        zòÁhashÆ,(°»ÍÝ
        """
        self.seen_hashes.clear()
        logger.debug("Deduplicator reset")

    def get_stats(self) -> Dict[str, Any]:
        """·Ö»Íß¡áo

        Returns:
            ß¡áoWx
        """
        return {
            "total_unique_hashes": len(self.seen_hashes)
        }
