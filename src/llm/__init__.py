"""LLM集成模块

导出LLM客户端和提示词模板。
"""

from src.llm.client import LLMClient
from src.llm import prompts

__all__ = [
    "LLMClient",
    "prompts",
]
