"""AITool数据模型

代表从AI工具数据源抓取的工具信息。
遵循Schema v1.1规范。
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Literal
from datetime import datetime
from uuid import uuid4


class AITool(BaseModel):
    """AI工具实体模型

    Attributes:
        id: 唯一标识符(UUID v4)
        name: 工具名称
        description: 工具描述
        source: 数据来源
        url: 原始链接
        timestamp: 抓取/发布时间(ISO 8601)
        tags: 标签列表
        features: 功能列表(v1.1新增)
        pricing_model: 定价模式(v1.1新增)
        summary_en: 英文摘要(≤200字符)
        summary_cn: 中文摘要(≤200字符)
        summary_ja: 日文摘要(≤200字符)
        data_quality_score: 数据质量评分(0-1, v1.1新增)
        schema_version: 数据模型版本
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    source: Literal["Futurepedia", "ProductHunt", "There's an AI for That"]
    url: HttpUrl
    timestamp: datetime
    tags: List[str]
    features: List[str]  # v1.1
    pricing_model: Literal["free", "freemium", "paid", "subscription"]  # v1.1
    summary_en: str = Field(max_length=200, default="")  # 英文摘要
    summary_cn: str = Field(max_length=200, default="")  # 中文摘要
    summary_ja: str = Field(max_length=200, default="")  # 日文摘要
    data_quality_score: float = Field(ge=0.0, le=1.0, default=0.7)  # v1.1
    schema_version: str = "1.1"

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Midjourney",
                "description": "AI-powered image generation from text prompts",
                "source": "ProductHunt",
                "url": "https://www.midjourney.com",
                "timestamp": "2025-11-03T10:30:00Z",
                "tags": ["image-generation", "creativity", "design"],
                "features": ["text-to-image", "style-transfer", "batch-processing"],
                "pricing_model": "subscription",
                "summary_en": "AI-powered text-to-image tool supporting various art styles",
                "summary_cn": "基于AI的文本生成图像工具，支持多种艺术风格",
                "summary_ja": "テキストから画像を生成するAIツール、複数のアートスタイルをサポート",
                "data_quality_score": 0.95,
                "schema_version": "1.1"
            }
        }
