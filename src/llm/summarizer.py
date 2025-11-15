"""三语摘要生成器

使用LLM生成英文摘要，然后通过Google翻译生成中文和日文版本。
这种方式可以：
1. 节省LLM调用成本（减少50%）
2. 保证三语内容的一致性
3. 提高翻译质量（英文作为源语言）
"""

from typing import Dict, Union
from deep_translator import GoogleTranslator
from src.llm.client import LLMClient
from src.llm.prompts import SUMMARY_PROMPT_EN
from src.models.tool import AITool
from src.models.trend import TrendingTopic
from src.models.pain_point import UserPainPoint
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TrilingualSummarizer:
    """三语摘要生成器

    生成英文摘要，然后翻译成中文和日文，用于AI工具、热点话题和用户痛点。
    """

    def __init__(self, llm_client: LLMClient = None):
        """初始化三语摘要生成器

        Args:
            llm_client: LLM客户端(可选，默认创建新实例)
        """
        self.llm_client = llm_client or LLMClient()

    def generate_summary(self, description: str) -> Dict[str, str]:
        """生成三语摘要

        Args:
            description: 原始描述文本

        Returns:
            包含summary_en、summary_cn和summary_ja的字典
        """
        try:
            # 步骤1：生成英文摘要（使用LLM）
            summary_en = self._generate_english_summary(description)

            # 步骤2：翻译成中文和日文（使用Google翻译）
            summary_cn = self._translate_to_chinese(summary_en)
            summary_ja = self._translate_to_japanese(summary_en)

            return {
                'summary_en': summary_en,
                'summary_cn': summary_cn,
                'summary_ja': summary_ja
            }

        except Exception as e:
            logger.error(f"Failed to generate trilingual summary: {e}")
            # 失败时返回截断的原始描述
            return {
                'summary_en': description[:200] if description else '',
                'summary_cn': '',
                'summary_ja': ''
            }

    def _generate_english_summary(self, description: str) -> str:
        """生成英文摘要（使用LLM）

        Args:
            description: 原始描述

        Returns:
            英文摘要(≤200字符)
        """
        try:
            prompt = SUMMARY_PROMPT_EN.format(description=description)
            summary = self.llm_client.generate(prompt, max_tokens=300)

            # 确保摘要长度≤200字符
            if len(summary) > 200:
                summary = summary[:197] + '...'

            return summary

        except Exception as e:
            logger.error(f"Failed to generate English summary: {e}")
            # 降级：返回原始描述
            return description[:200] if description else ''

    def _translate_to_chinese(self, text: str) -> str:
        """翻译成中文（使用Google翻译）

        Args:
            text: 英文文本

        Returns:
            中文翻译(≤200字符)
        """
        try:
            if not text:
                return ''

            translator = GoogleTranslator(source='en', target='zh-CN')
            translated = translator.translate(text)

            # 确保长度≤200字符
            if len(translated) > 200:
                translated = translated[:197] + '...'

            return translated

        except Exception as e:
            logger.error(f"Failed to translate to Chinese: {e}")
            # 失败时返回英文
            return text

    def _translate_to_japanese(self, text: str) -> str:
        """翻译成日文（使用Google翻译）

        Args:
            text: 英文文本

        Returns:
            日文翻译(≤200字符)
        """
        try:
            if not text:
                return ''

            translator = GoogleTranslator(source='en', target='ja')
            translated = translator.translate(text)

            # 确保长度≤200字符
            if len(translated) > 200:
                translated = translated[:197] + '...'

            return translated

        except Exception as e:
            logger.error(f"Failed to translate to Japanese: {e}")
            # 失败时返回英文
            return text

    def summarize_ai_tool(self, tool: AITool) -> AITool:
        """为AI工具生成三语摘要

        Args:
            tool: AITool对象

        Returns:
            更新后的AITool对象
        """
        # 检查是否已有所有三语摘要
        if hasattr(tool, 'summary_en') and tool.summary_en and tool.summary_cn and tool.summary_ja:
            logger.debug(f"Tool {tool.name} already has all summaries, skipping")
            return tool

        try:
            summaries = self.generate_summary(tool.description)

            # 更新tool对象的摘要
            if hasattr(tool, 'summary_en'):
                tool.summary_en = summaries['summary_en']
            tool.summary_cn = summaries['summary_cn']
            tool.summary_ja = summaries['summary_ja']

            logger.info(f"Generated summaries for tool: {tool.name}")
            return tool

        except Exception as e:
            logger.error(f"Failed to summarize tool {tool.name}: {e}")
            return tool

    def summarize_trending_topic(self, topic: TrendingTopic) -> TrendingTopic:
        """为热点话题生成三语摘要

        Args:
            topic: TrendingTopic对象

        Returns:
            更新后的TrendingTopic对象
        """
        # 检查是否已有所有三语摘要
        if hasattr(topic, 'summary_en') and topic.summary_en and topic.summary_cn and topic.summary_ja:
            logger.debug(f"Topic {topic.title} already has all summaries, skipping")
            return topic

        try:
            summaries = self.generate_summary(topic.description)

            # 更新topic对象的摘要
            if hasattr(topic, 'summary_en'):
                topic.summary_en = summaries['summary_en']
            topic.summary_cn = summaries['summary_cn']
            topic.summary_ja = summaries['summary_ja']

            logger.info(f"Generated summaries for topic: {topic.title}")
            return topic

        except Exception as e:
            logger.error(f"Failed to summarize topic {topic.title}: {e}")
            return topic

    def summarize_pain_point(self, pain_point: UserPainPoint) -> UserPainPoint:
        """为用户痛点生成三语摘要

        Args:
            pain_point: UserPainPoint对象

        Returns:
            更新后的UserPainPoint对象
        """
        # 检查是否已有所有三语摘要
        if hasattr(pain_point, 'summary_en') and pain_point.summary_en and pain_point.summary_cn and pain_point.summary_ja:
            logger.debug(f"Pain point already has all summaries, skipping")
            return pain_point

        try:
            summaries = self.generate_summary(pain_point.original_text)

            # 更新pain_point对象的摘要
            if hasattr(pain_point, 'summary_en'):
                pain_point.summary_en = summaries['summary_en']
            pain_point.summary_cn = summaries['summary_cn']
            pain_point.summary_ja = summaries['summary_ja']

            logger.info(f"Generated summaries for pain point")
            return pain_point

        except Exception as e:
            logger.error(f"Failed to summarize pain point: {e}")
            return pain_point

    def batch_summarize(self, items: list) -> list:
        """批量生成摘要

        Args:
            items: AITool、TrendingTopic或UserPainPoint对象列表

        Returns:
            更新后的对象列表
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


# 保留向后兼容性
BilingualSummarizer = TrilingualSummarizer