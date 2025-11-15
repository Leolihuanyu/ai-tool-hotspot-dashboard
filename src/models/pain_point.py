"""UserPainPoint数据模型

代表从评论中提取的用户痛点。
遵循Schema v1.1规范。
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Literal, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4


class UserPainPoint(BaseModel):
    """用户痛点实体模型

    Attributes:
        id: 唯一标识符(UUID v4)
        original_text: 原始评论文本
        context_title: 帖子/讨论标题(v1.1新增)
        extracted_keywords: 提取的关键词列表
        source: 来源
        url: 评论链接
        timestamp: 评论时间(ISO 8601)
        engagement_score: 互动分数(0-100)
        confidence_score: 痛点置信度(0-1, v1.1新增)
        tags: 标签列表
        summary_en: 英文摘要(≤200字符)
        summary_cn: 中文摘要(≤200字符)
        summary_ja: 日文摘要(≤200字符)
        data_quality_score: 数据质量评分(0-1, v1.1新增)
        business_value: 商业价值评分(1-10, v1.2新增)
        urgency_level: 紧迫性评分(1-10, v1.2新增)
        market_size_hint: 潜在市场规模(v1.2新增)
        willingness_to_pay: 付费意愿(v1.2新增)
        schema_version: 数据模型版本
        author_metadata: 作者元信息(可选, v1.1新增)
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    original_text: str
    context_title: str  # v1.1
    extracted_keywords: List[str]
    source: Literal["Reddit", "X", "ProductHunt", "Hacker News", "GitHub Discussions"]
    url: HttpUrl
    timestamp: datetime
    engagement_score: float = Field(ge=0.0, le=100.0)
    confidence_score: float = Field(ge=0.0, le=1.0)  # v1.1
    tags: List[str]
    summary_en: str = Field(max_length=200, default="")  # 英文摘要
    summary_cn: str = Field(max_length=200, default="")  # 中文摘要
    summary_ja: str = Field(max_length=200, default="")  # 日文摘要
    data_quality_score: float = Field(ge=0.0, le=1.0, default=0.7)  # v1.1

    # v1.2 新增字段
    business_value: int = Field(ge=1, le=10, default=5)  # 商业价值评分
    urgency_level: int = Field(ge=1, le=10, default=5)  # 紧迫性评分
    market_size_hint: Literal["niche", "moderate", "large"] = Field(default="moderate")  # 市场规模
    willingness_to_pay: Literal["low", "medium", "high", "very_high"] = Field(default="medium")  # 付费意愿

    schema_version: str = "1.2"

    # 可选字段
    author_metadata: Optional[Dict[str, Any]] = None  # v1.1

    class Config:
        json_schema_extra = {
            "example": {
                "id": "770e8400-e29b-41d4-a716-446655440002",
                "original_text": "I need a tool to automatically generate thumbnails for my YouTube videos",
                "context_title": "Best AI tools for content creators in 2025",
                "extracted_keywords": ["tool", "automatically", "generate", "thumbnails", "YouTube"],
                "source": "Reddit",
                "url": "https://reddit.com/r/youtubers/comments/abc123",
                "timestamp": "2025-11-03T14:30:00Z",
                "engagement_score": 72.0,
                "confidence_score": 0.85,
                "tags": ["content-creation", "automation", "video"],
                "summary_en": "Need a tool to automatically generate YouTube video thumbnails",
                "summary_cn": "需要一个自动生成YouTube视频缩略图的工具",
                "summary_ja": "YouTube動画のサムネイルを自動生成するツールが必要",
                "data_quality_score": 0.90,
                "schema_version": "1.1",
                "author_metadata": {
                    "account_type": "verified",
                    "followers": 5000,
                    "karma": 12000
                }
            }
        }
