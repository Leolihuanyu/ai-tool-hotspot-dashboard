"""TrendingTopic数据模型

代表从社交平台和搜索引擎抓取的热点话题。
遵循Schema v1.1规范。
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Literal, Optional
from datetime import datetime
from uuid import uuid4


class TrendingTopic(BaseModel):
    """热点话题实体模型

    Attributes:
        id: 唯一标识符(UUID v4)
        title: 话题标题
        description: 话题描述
        source: 来源平台
        url: 原始链接
        timestamp: 抓取/发布时间(ISO 8601)
        heat_score: 热度分数(0-100)
        trend_direction: 趋势方向(v1.1新增)
        tags: 标签列表
        summary_cn: 中文摘要(≤200字符)
        summary_ja: 日文摘要(≤200字符)
        data_quality_score: 数据质量评分(0-1, v1.1新增)
        schema_version: 数据模型版本
        platforms: 跨平台列表(可选)
        trend_velocity: 趋势速度(可选, v1.1新增)
        trend_marker: 趋势标记(可选, v1.2新增)
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: str
    source: Literal["TikTok", "YouTube", "X", "Reddit", "Google Trends", "Hacker News", "GitHub Discussions"]
    url: HttpUrl
    timestamp: datetime
    heat_score: float = Field(ge=0.0, le=100.0)
    trend_direction: Literal["rising", "falling", "stable"]  # v1.1
    tags: List[str]
    summary_cn: str = Field(max_length=200, default="")
    summary_ja: str = Field(max_length=200, default="")
    data_quality_score: float = Field(ge=0.0, le=1.0, default=0.7)  # v1.1
    schema_version: str = "1.2"

    # 可选字段
    platforms: Optional[List[str]] = None
    trend_velocity: Optional[float] = None  # v1.1
    trend_marker: Optional[str] = None  # v1.2 趋势标记（🔥最新/📈热门/💡活跃）

    class Config:
        json_schema_extra = {
            "example": {
                "id": "660e8400-e29b-41d4-a716-446655440001",
                "title": "How to use ChatGPT for coding",
                "description": "Tutorial on using ChatGPT to write Python code",
                "source": "TikTok",
                "url": "https://www.tiktok.com/@user/video/123456",
                "timestamp": "2025-11-03T12:00:00Z",
                "heat_score": 85.5,
                "trend_direction": "rising",
                "tags": ["AI", "coding", "tutorial"],
                "summary_cn": "教你如何使用ChatGPT编写Python代码的教程",
                "summary_ja": "ChatGPTを使ってPythonコードを書く方法のチュートリアル",
                "data_quality_score": 0.88,
                "schema_version": "1.1",
                "platforms": ["TikTok", "YouTube"],
                "trend_velocity": 35.2
            }
        }
