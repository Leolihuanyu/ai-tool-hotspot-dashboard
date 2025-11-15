"""MVP建议生成器（简化版）

基于痛点和热点直接生成MVP产品概要，遵循宪法原则V(多语言输出)。
不再考虑现有AI工具，专注于创新性解决方案。
"""

import json
from typing import Optional, Dict, Any, List
from deep_translator import GoogleTranslator
from src.llm.client import LLMClient
from src.llm.prompts import MVP_SUGGESTION_PROMPT
from src.models.pain_point import UserPainPoint
from src.models.trend import TrendingTopic
from src.utils.logger import default_logger


class MVPSuggester:
    """MVP建议生成器（简化版）

    使用LLM生成中日双语MVP产品概要，包含：
    - 核心功能（3-5点）
    - 目标用户群
    - 变现方式建议

    不包含技术栈、时间线、成本估算。

    Attributes:
        llm_client: LLM客户端实例
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """初始化MVP建议生成器

        Args:
            llm_client: LLM客户端(可选,默认创建新实例)
        """
        self.llm_client = llm_client or LLMClient()
        # 初始化翻译器
        self.translator_to_zh = GoogleTranslator(source='en', target='zh-CN')
        self.translator_to_ja = GoogleTranslator(source='en', target='ja')

    def generate(
        self,
        pain_point: UserPainPoint,
        related_topics: List[TrendingTopic] = None
    ) -> Optional[Dict[str, str]]:
        """生成MVP建议（从痛点和热点直接生成，不考虑现有工具）

        Args:
            pain_point: 用户痛点
            related_topics: 相关热点话题列表（可选）

        Returns:
            包含mvp_suggestion_cn和mvp_suggestion_ja的字典,失败返回None
        """
        try:
            # 构建提示词
            prompt = self._build_prompt(pain_point, related_topics or [])

            # 调用LLM生成（降低max_tokens，因为不需要技术栈等内容）
            response = self.llm_client.generate(
                prompt=prompt,
                max_tokens=800,  # 从1024降到800
                temperature=0.7
            )

            if not response:
                default_logger.warning(
                    "Failed to generate MVP suggestion",
                    extra={"extra_fields": {"pain_point_id": pain_point.id}}
                )
                return None

            # 解析JSON响应
            try:
                # 移除可能存在的markdown代码块包裹
                response_clean = response.strip()
                if response_clean.startswith('```json'):
                    response_clean = response_clean[7:]  # 移除 ```json
                elif response_clean.startswith('```'):
                    response_clean = response_clean[3:]  # 移除 ```
                if response_clean.endswith('```'):
                    response_clean = response_clean[:-3]  # 移除结尾的 ```
                response_clean = response_clean.strip()

                result = json.loads(response_clean)

                # 验证必需字段（现在需要英文版本）
                if "mvp_suggestion_en" not in result:
                    # 兼容旧格式：如果只有中文版本，则使用中文版本作为英文（临时方案）
                    if "mvp_suggestion_cn" in result:
                        mvp_en = result["mvp_suggestion_cn"]  # 临时使用中文
                        mvp_cn = result["mvp_suggestion_cn"]
                        mvp_ja = result.get("mvp_suggestion_ja", result["mvp_suggestion_cn"])
                    else:
                        default_logger.warning(
                            "MVP suggestion missing required fields",
                            extra={"extra_fields": {"response": response}}
                        )
                        return None
                else:
                    # 新格式：英文优先，然后翻译
                    mvp_en = result["mvp_suggestion_en"]

                    # 翻译成中文和日文
                    try:
                        mvp_cn = self.translator_to_zh.translate(mvp_en)
                        mvp_ja = self.translator_to_ja.translate(mvp_en)
                    except Exception as e:
                        default_logger.warning(f"Translation failed: {e}, using English version")
                        mvp_cn = mvp_en  # 翻译失败时使用英文版本
                        mvp_ja = mvp_en

                # 返回所有字段（包括新增的英文建议）
                return {
                    "mvp_suggestion_en": mvp_en,  # 新增英文字段
                    "mvp_suggestion_cn": mvp_cn,
                    "mvp_suggestion_ja": mvp_ja,
                    "competitive_analysis": result.get("competitive_analysis", ""),
                    "differentiation": result.get("differentiation", ""),
                    "launch_difficulty": result.get("launch_difficulty", "medium"),
                    "estimated_time": result.get("estimated_time", "1month")
                }

            except json.JSONDecodeError as e:
                default_logger.error(
                    f"Failed to parse MVP suggestion JSON: {e}",
                    extra={"extra_fields": {"response": response}}
                )
                return None

        except Exception as e:
            default_logger.error(
                f"Error generating MVP suggestion: {e}",
                extra={"extra_fields": {"pain_point_id": pain_point.id}}
            )
            return None

    def generate_batch(
        self,
        opportunities: List[Dict[str, Any]]
    ) -> List[Optional[Dict[str, str]]]:
        """批量生成MVP建议

        Args:
            opportunities: 机会列表,每个包含pain_point和related_topics

        Returns:
            MVP建议列表
        """
        results = []
        for opp in opportunities:
            result = self.generate(
                pain_point=opp["pain_point"],
                related_topics=opp.get("related_topics", [])
            )
            results.append(result)

        return results

    def _build_prompt(
        self,
        pain_point: UserPainPoint,
        related_topics: List[TrendingTopic]
    ) -> str:
        """构建提示词（不再使用related_tools）

        Args:
            pain_point: 用户痛点
            related_topics: 相关热点话题列表

        Returns:
            完整的提示词字符串
        """
        # 格式化痛点信息
        pain_point_text = f"""
原始文本: {pain_point.original_text}
上下文标题: {pain_point.context_title}
关键词: {', '.join(pain_point.extracted_keywords)}
中文摘要: {pain_point.summary_cn}
"""

        # 格式化相关热点
        if related_topics:
            topics_text = "\n".join([
                f"- {topic.title} (来源: {topic.source}, 热度: {topic.heat_score:.0f}/100)"
                for topic in related_topics[:3]  # 最多3个热点
            ])
        else:
            topics_text = "（当前无明显市场热点）"

        # 填充模板（不再包含related_tools）
        prompt = MVP_SUGGESTION_PROMPT.format(
            pain_point=pain_point_text,
            related_topics=topics_text
        )

        return prompt


# 全局实例
default_mvp_suggester = MVPSuggester()
