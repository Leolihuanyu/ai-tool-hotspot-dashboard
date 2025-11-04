"""Xh

(LLM-X
&FR-008: @	Xd200W&
"""

from typing import Dict, Union
from src.llm.client import LLMClient
from src.llm.prompts import SUMMARY_PROMPT_CN, SUMMARY_PROMPT_JA
from src.models.tool import AITool
from src.models.trend import TrendingTopic
from src.models.pain_point import UserPainPoint
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BilingualSummarizer:
    """Xh

    :AIw(7-X
    """

    def __init__(self, llm_client: LLMClient = None):
        """Xh

        Args:
            llm_client: LLM7(	,)
        """
        self.llm_client = llm_client or LLMClient()

    def generate_summary(self, description: str) -> Dict[str, str]:
        """-X

        Args:
            description: ,

        Returns:
            +summary_cnsummary_jaWx
        """
        try:
            # -X
            summary_cn = self._generate_chinese_summary(description)

            # X
            summary_ja = self._generate_japanese_summary(description)

            return {
                'summary_cn': summary_cn,
                'summary_ja': summary_ja
            }

        except Exception as e:
            logger.error(f"Failed to generate bilingual summary: {e}")
            # zX\:M
            return {
                'summary_cn': description[:200] if description else '',
                'summary_ja': ''
            }

    def _generate_chinese_summary(self, description: str) -> str:
        """-X

        Args:
            description: 

        Returns:
            -X(d200W&)
        """
        try:
            prompt = SUMMARY_PROMPT_CN.format(description=description)
            summary = self.llm_client.generate(prompt, max_tokens=300)

            # 确保摘要长度200字符 (FR-008)
            if len(summary) > 200:
                summary = summary[:197] + '...'

            return summary

        except Exception as e:
            logger.error(f"Failed to generate Chinese summary: {e}")
            # M:*
            return description[:200] if description else ''

    def _generate_japanese_summary(self, description: str) -> str:
        """X

        Args:
            description: 

        Returns:
            X(d200W&)
        """
        try:
            prompt = SUMMARY_PROMPT_JA.format(description=description)
            summary = self.llm_client.generate(prompt, max_tokens=300)

            # 确保摘要长度≤200字符
            if len(summary) > 200:
                summary = summary[:197] + '...'

            return summary

        except Exception as e:
            logger.error(f"Failed to generate Japanese summary: {e}")
            # M:zW&2
            logger.info("Using English description as fallback for Japanese summary")
            return ''

    def summarize_ai_tool(self, tool: AITool) -> AITool:
        """:AIwX

        Args:
            tool: AITool

        Returns:
            XAITool
        """
        if tool.summary_cn and tool.summary_ja:
            # XX(,
            logger.debug(f"Tool {tool.name} already has summaries, skipping")
            return tool

        try:
            summaries = self.generate_summary(tool.description)

            # toola
            tool.summary_cn = summaries['summary_cn']
            tool.summary_ja = summaries['summary_ja']

            logger.info(f"Generated summaries for tool: {tool.name}")
            return tool

        except Exception as e:
            logger.error(f"Failed to summarize tool {tool.name}: {e}")
            return tool

    def summarize_trending_topic(self, topic: TrendingTopic) -> TrendingTopic:
        """:X

        Args:
            topic: TrendingTopic

        Returns:
            XTrendingTopic
        """
        if topic.summary_cn and topic.summary_ja:
            # XX(,
            logger.debug(f"Topic {topic.title} already has summaries, skipping")
            return topic

        try:
            summaries = self.generate_summary(topic.description)

            # topica
            topic.summary_cn = summaries['summary_cn']
            topic.summary_ja = summaries['summary_ja']

            logger.info(f"Generated summaries for topic: {topic.title}")
            return topic

        except Exception as e:
            logger.error(f"Failed to summarize topic {topic.title}: {e}")
            return topic

    def summarize_pain_point(self, pain_point: UserPainPoint) -> UserPainPoint:
        """:(7X

        Args:
            pain_point: UserPainPoint

        Returns:
            XUserPainPoint
        """
        if pain_point.summary_cn and pain_point.summary_ja:
            # XX(,
            logger.debug(f"Pain point already has summaries, skipping")
            return pain_point

        try:
            summaries = self.generate_summary(pain_point.original_text)

            # pain_pointa
            pain_point.summary_cn = summaries['summary_cn']
            pain_point.summary_ja = summaries['summary_ja']

            logger.info(f"Generated summaries for pain point")
            return pain_point

        except Exception as e:
            logger.error(f"Failed to summarize pain point: {e}")
            return pain_point

    def batch_summarize(self, items: list) -> list:
        """yX

        Args:
            items: AIToolTrendingTopicUserPainPointh

        Returns:
            Xh
        """
        if not items:
            return []

        summarized_items = []
        total = len(items)

        for idx, item in enumerate(items, 1):
            try:
                if isinstance(item, AITool):
                    summarized = self.summarize_ai_tool(item)
                elif isinstance(item, TrendingTopic):
                    summarized = self.summarize_trending_topic(item)
                elif isinstance(item, UserPainPoint):
                    summarized = self.summarize_pain_point(item)
                else:
                    logger.warning(f"Unknown item type: {type(item)}")
                    summarized = item

                summarized_items.append(summarized)

                if idx % 10 == 0:
                    logger.info(f"Batch summarization progress: {idx}/{total}")

            except Exception as e:
                logger.error(f"Failed to summarize item {idx}: {e}")
                summarized_items.append(item)
                continue

        logger.info(f"Batch summarization completed: {len(summarized_items)}/{total} items")
        return summarized_items
