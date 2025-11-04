"""Opportunity数据模型

代表基于痛点和热点直接生成的产品机会。
遵循Schema v1.2规范。
"""

from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from uuid import uuid4


class Opportunity(BaseModel):
    """产品机会实体模型

    Attributes:
        id: 唯一标识符(UUID v4)
        pain_point_id: 关联的痛点ID(外键)
        related_topics: 关联的热点话题ID列表
        opportunity_score: 机会评分(0-100，基于痛点质量60%+热点趋势40%)
        mvp_suggestion_cn: 中文MVP建议（产品概要：核心功能+目标用户+变现方式）
        mvp_suggestion_ja: 日文MVP建议（产品概要：核心功能+目标用户+变现方式）
        timestamp: 机会生成时间(ISO 8601)
        tags: 标签列表(聚合自痛点、热点)
        data_quality_score: 数据质量评分(v1.1新增)
        schema_version: 数据模型版本(v1.2: 移除related_tools，简化MVP建议)
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    pain_point_id: str
    related_topics: List[str]
    opportunity_score: float = Field(ge=0.0, le=100.0)
    mvp_suggestion_cn: str
    mvp_suggestion_ja: str
    timestamp: datetime
    tags: List[str]
    data_quality_score: float = Field(ge=0.0, le=1.0, default=0.7)  # v1.1
    schema_version: str = "1.2"  # v1.2: 移除related_tools字段

    class Config:
        json_schema_extra = {
            "example": {
                "id": "880e8400-e29b-41d4-a716-446655440003",
                "pain_point_id": "770e8400-e29b-41d4-a716-446655440002",
                "related_topics": ["660e8400-e29b-41d4-a716-446655440001"],
                "opportunity_score": 78.5,
                "mvp_suggestion_cn": "核心功能：1) AI驱动的YouTube缩略图生成器，支持多种风格模板，2) 一键批量生成和A/B测试功能，3) 数据分析看板展示点击率。目标用户：YouTube内容创作者、视频营销团队、MCN机构。变现方式：免费增值模式，基础版免费（每月10张），专业版$19/月（无限生成+高级模板），企业版$99/月（团队协作+API）。",
                "mvp_suggestion_ja": "コア機能：1) AIによるYouTubeサムネイル生成、複数スタイル対応、2) ワンクリック一括生成とA/Bテスト、3) クリック率分析ダッシュボード。ターゲットユーザー：YouTubeクリエイター、動画マーケティングチーム、MCN。収益化：フリーミアムモデル、基本版無料（月10枚）、プロ版$19/月（無制限+高度テンプレート）、企業版$99/月（チームコラボ+API）。",
                "timestamp": "2025-11-03T16:00:00Z",
                "tags": ["content-creation", "automation", "AI", "video"],
                "data_quality_score": 0.91,
                "schema_version": "1.2"
            }
        }
