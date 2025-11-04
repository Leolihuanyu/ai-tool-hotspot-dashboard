"""
痛点提取模块
从Reddit/X/ProductHunt评论中使用LLM提取用户痛点
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import logging

from src.llm.client import LLMClient
from src.models.pain_point import UserPainPoint
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PainPointExtractor:
    """痛点提取器 - 使用LLM从评论文本中提取用户痛点"""

    # 痛点识别关键词
    PAIN_KEYWORDS = [
        "need a tool",
        "wish there was",
        "looking for",
        "can't find",
        "struggling with",
        "frustrating",
        "difficult to",
        "hard to find",
        "missing feature",
        "would pay for",
        "no good solution",
        "pain point",
        "problem with",
        "hate that",
        "annoying",
    ]

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        初始化痛点提取器

        Args:
            llm_client: LLM客户端实例,如果为None则创建新实例
        """
        self.llm_client = llm_client or LLMClient()

    def contains_pain_keyword(self, text: str) -> bool:
        """
        检查文本是否包含痛点关键词

        Args:
            text: 要检查的文本

        Returns:
            True如果包含痛点关键词,否则False
        """
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.PAIN_KEYWORDS)

    def extract_from_comment(
        self,
        comment_text: str,
        context_title: str,
        source: str,
        url: str,
        timestamp: datetime,
        engagement_score: float = 0.0,
        author_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[UserPainPoint]:
        """
        从单条评论中提取痛点

        Args:
            comment_text: 评论原文
            context_title: 帖子/讨论标题
            source: 来源平台 (Reddit/X/ProductHunt)
            url: 评论链接
            timestamp: 评论时间
            engagement_score: 互动分数 (0-100)
            author_metadata: 作者元信息(可选)

        Returns:
            UserPainPoint对象,如果未提取到痛点则返回None
        """
        # 快速检查:如果不包含痛点关键词,跳过LLM调用
        if not self.contains_pain_keyword(comment_text):
            logger.debug(f"评论不包含痛点关键词,跳过: {comment_text[:50]}...")
            return None

        # 使用LLM提取结构化痛点信息
        prompt = self._build_extraction_prompt(comment_text, context_title)

        try:
            response = self.llm_client.generate(
                prompt=prompt,
                max_tokens=500,
                temperature=0.3  # 低温度以获得更确定性的提取
            )

            # 解析LLM响应
            extracted_data = self._parse_llm_response(response)

            if not extracted_data or not extracted_data.get("is_pain_point"):
                logger.debug(f"LLM判断不是痛点: {comment_text[:50]}...")
                return None

            # 构建UserPainPoint对象
            pain_point = UserPainPoint(
                original_text=comment_text,
                context_title=context_title,
                extracted_keywords=extracted_data.get("keywords", []),
                source=source,
                url=url,
                timestamp=timestamp,
                engagement_score=engagement_score,
                confidence_score=extracted_data.get("confidence_score", 0.5),
                tags=extracted_data.get("tags", []),
                summary_cn=extracted_data.get("summary_cn", ""),
                summary_ja=extracted_data.get("summary_ja", ""),
                data_quality_score=self._calculate_data_quality(
                    comment_text, source, engagement_score
                ),
                author_metadata=author_metadata
            )

            logger.info(f"成功提取痛点: {pain_point.summary_cn[:50]}...")
            return pain_point

        except Exception as e:
            logger.error(f"痛点提取失败: {str(e)}")
            return None

    def extract_from_text(
        self,
        text: str,
        context: str,
        source: str,
        url: str
    ) -> Optional[UserPainPoint]:
        """
        从任意文本中提取痛点（简化版，用于trending topics描述等场景）

        Args:
            text: 文本内容
            context: 上下文（如标题）
            source: 来源平台
            url: 链接

        Returns:
            UserPainPoint对象，如果未提取到痛点则返回None
        """
        # 调用现有的extract_from_comment方法，提供默认参数
        return self.extract_from_comment(
            comment_text=text,
            context_title=context,
            source=source,
            url=url,
            timestamp=datetime.now(timezone.utc),  # 使用当前时间
            engagement_score=50.0,  # 默认中等热度
            author_metadata=None
        )

    def extract_batch(
        self,
        comments: List[Dict[str, Any]],
        max_results: Optional[int] = None
    ) -> List[UserPainPoint]:
        """
        批量提取痛点

        Args:
            comments: 评论列表,每个评论是包含以下字段的字典:
                - text: 评论文本
                - context_title: 帖子标题
                - source: 来源
                - url: 链接
                - timestamp: 时间戳
                - engagement_score: 互动分数(可选)
                - author_metadata: 作者元信息(可选)
            max_results: 最大返回结果数(可选)

        Returns:
            UserPainPoint对象列表
        """
        pain_points = []

        for comment in comments:
            if max_results and len(pain_points) >= max_results:
                break

            pain_point = self.extract_from_comment(
                comment_text=comment["text"],
                context_title=comment["context_title"],
                source=comment["source"],
                url=comment["url"],
                timestamp=comment["timestamp"],
                engagement_score=comment.get("engagement_score", 0.0),
                author_metadata=comment.get("author_metadata")
            )

            if pain_point:
                pain_points.append(pain_point)

        logger.info(f"批量提取完成: 从{len(comments)}条评论中提取到{len(pain_points)}个痛点")
        return pain_points

    def _build_extraction_prompt(self, comment_text: str, context_title: str) -> str:
        """构建痛点提取的LLM提示词"""
        return f"""你是一个专业的用户痛点分析师。请分析以下评论,判断是否表达了用户痛点,并提取相关信息。

**帖子标题**: {context_title}

**评论内容**: {comment_text}

请以JSON格式返回分析结果,包含以下字段:

1. **is_pain_point** (boolean): 是否表达了真实的用户痛点(不仅仅是抱怨或吐槽)
2. **confidence_score** (float 0-1): 痛点的置信度评分
3. **keywords** (list[str]): 提取的关键词(5-10个)
4. **tags** (list[str]): 分类标签(如 "automation", "data-analysis" 等)
5. **summary_cn** (str): 中文摘要(≤200字符)
6. **summary_ja** (str): 日文摘要(≤200字符)

评估标准:
- **是痛点**: 明确表达需要解决的问题、缺失的功能、工作流程障碍
- **不是痛点**: 一般性抱怨、情绪发泄、无具体需求

返回JSON:"""

    def _parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        解析LLM返回的JSON响应

        Args:
            response: LLM响应文本

        Returns:
            解析后的字典,失败则返回None
        """
        try:
            # 尝试提取JSON部分(处理可能的markdown代码块)
            response = response.strip()
            # 移除可能存在的markdown代码块包裹
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            elif response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

            data = json.loads(response)

            # 验证必需字段
            if "is_pain_point" not in data:
                logger.warning("LLM响应缺少is_pain_point字段")
                return None

            return data

        except json.JSONDecodeError as e:
            logger.error(f"无法解析LLM响应为JSON: {e}\n响应内容: {response[:200]}")
            return None

    def _calculate_data_quality(
        self,
        comment_text: str,
        source: str,
        engagement_score: float
    ) -> float:
        """
        计算数据质量评分

        Args:
            comment_text: 评论文本
            source: 来源平台
            engagement_score: 互动分数

        Returns:
            数据质量评分 (0-1)
        """
        # 来源可靠性
        source_reliability = {
            "Reddit": 0.8,
            "X": 0.7,
            "ProductHunt": 0.9
        }.get(source, 0.6)

        # 内容完整性(基于文本长度)
        text_length = len(comment_text)
        if text_length >= 100:
            content_completeness = 1.0
        elif text_length >= 50:
            content_completeness = 0.8
        elif text_length >= 20:
            content_completeness = 0.6
        else:
            content_completeness = 0.4

        # 互动质量(归一化)
        engagement_quality = min(1.0, engagement_score / 100.0)

        # 综合评分
        data_quality_score = (
            source_reliability * 0.4 +
            content_completeness * 0.3 +
            engagement_quality * 0.3
        )

        return round(data_quality_score, 2)
