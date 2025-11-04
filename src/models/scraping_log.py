"""ScrapingLog数据模型

用于记录每次数据抓取的结果,符合宪法原则VI(可重现性)。
"""

from pydantic import BaseModel, Field
from typing import List, Literal
from datetime import datetime
from uuid import uuid4


class ScrapingLog(BaseModel):
    """爬取日志实体模型

    Attributes:
        id: 唯一标识符(UUID v4)
        source: 数据源名称
        status: 执行状态
        records_count: 成功抓取的记录数
        errors: 错误消息列表
        duration_seconds: 执行耗时(秒)
        timestamp: 执行时间(ISO 8601)
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    source: str
    status: Literal["success", "failed", "partial"]
    records_count: int = Field(ge=0)
    errors: List[str] = []
    duration_seconds: float = Field(ge=0.0)
    timestamp: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "990e8400-e29b-41d4-a716-446655440004",
                "source": "Futurepedia",
                "status": "success",
                "records_count": 45,
                "errors": [],
                "duration_seconds": 12.5,
                "timestamp": "2025-11-03T08:00:00Z"
            }
        }
