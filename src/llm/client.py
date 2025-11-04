"""LLM客户端封装

支持Claude Haiku 3 和 OpenAI GPT模型,遵循宪法原则V(多语言输出)。
"""

from typing import Optional
from anthropic import Anthropic
from src.utils.config import config
from src.utils.logger import default_logger

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class LLMClient:
    """LLM客户端

    封装Anthropic Claude API调用。

    Attributes:
        provider: LLM提供商("claude" 或 "openai")
        model: 模型名称
        use_batch_api: 是否使用Batch API
    """

    def __init__(
        self,
        provider: str = None,
        model: str = None,
        api_key: str = None
    ):
        """初始化LLM客户端

        Args:
            provider: LLM提供商(默认从配置读取)
            model: 模型名称(默认从配置读取)
            api_key: API密钥(默认从配置读取)
        """
        self.provider = provider or config.llm_provider
        self.model = model or config.llm_model
        self.use_batch_api = config.llm_use_batch_api

        if self.provider == "claude":
            api_key = api_key or config.anthropic_api_key
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not set in .env")
            self.client = Anthropic(api_key=api_key)
        elif self.provider == "openai":
            if not OPENAI_AVAILABLE:
                raise ImportError("openai库未安装，请运行: pip install openai")
            api_key = api_key or config.openai_api_key
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set in .env")
            self.client = OpenAI(api_key=api_key)
            # OpenAI默认模型
            if not self.model or self.model.startswith("claude"):
                self.model = "gpt-3.5-turbo"
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> Optional[str]:
        """生成文本

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词(可选)
            max_tokens: 最大token数
            temperature: 采样温度(0-1)

        Returns:
            生成的文本,失败返回None
        """
        try:
            if self.provider == "claude":
                # 构建消息
                messages = [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]

                # 调用Claude API
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_prompt if system_prompt else "",
                    messages=messages
                )

                # 提取文本
                if response.content and len(response.content) > 0:
                    return response.content[0].text
                else:
                    default_logger.warning("Empty response from Claude API")
                    return None

            elif self.provider == "openai":
                # 构建消息
                messages = []
                if system_prompt:
                    messages.append({
                        "role": "system",
                        "content": system_prompt
                    })
                messages.append({
                    "role": "user",
                    "content": prompt
                })

                # 调用OpenAI API
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )

                # 提取文本
                if response.choices and len(response.choices) > 0:
                    return response.choices[0].message.content
                else:
                    default_logger.warning("Empty response from OpenAI API")
                    return None

            else:
                raise NotImplementedError(f"Provider {self.provider} not implemented")

        except Exception as e:
            default_logger.error(
                f"LLM generation failed: {e}",
                extra={"extra_fields": {
                    "provider": self.provider,
                    "model": self.model,
                    "error": str(e)
                }}
            )
            return None

    def generate_batch(self, prompts: list[str], **kwargs) -> list[Optional[str]]:
        """批量生成文本

        Args:
            prompts: 提示词列表
            **kwargs: 传递给generate的其他参数

        Returns:
            生成的文本列表
        """
        results = []
        for prompt in prompts:
            result = self.generate(prompt, **kwargs)
            results.append(result)
        return results
