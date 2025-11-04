# Data Model: AI工具与热点机会发现仪表板

**Branch**: `001-ai-tool-hotspot-dashboard` | **Date**: 2025-11-03
**Schema Version**: 1.1

本文档定义了系统中所有核心实体的数据模型，遵循宪法原则II（统一数据模型）。所有实体将在`src/models/`中使用Pydantic实现。

---

## Schema Versioning

**当前版本**: 1.1

**版本规则**（遵循宪法II）:
- **MAJOR**: 破坏性变更（字段删除、类型不兼容修改）
- **MINOR**: 向后兼容的新增（新增字段、新增可选属性）
- **PATCH**: 文档修正、注释更新

**版本历史**:
- v1.0 → v1.1: 新增字段以支持更精确的LLM分析和数据质量控制（详见spec.md第189-195行）

---

## 核心实体

### 1. AITool（AI工具）

代表从AI工具数据源抓取的工具信息。

**源文件**: `src/models/tool.py`

**必需属性**:

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `id` | `str` | 唯一标识符（UUID v4） | `"550e8400-e29b-41d4-a716-446655440000"` |
| `name` | `str` | 工具名称 | `"Midjourney"` |
| `description` | `str` | 工具描述 | `"AI-powered image generation from text prompts"` |
| `source` | `str` | 数据来源（枚举值） | `"Futurepedia"`, `"ProductHunt"`, `"There's an AI for That"` |
| `url` | `str` | 原始链接 | `"https://www.midjourney.com"` |
| `timestamp` | `datetime` | 抓取/发布时间（ISO 8601） | `"2025-11-03T10:30:00Z"` |
| `tags` | `List[str]` | 标签列表 | `["image-generation", "creativity", "design"]` |
| `features` | `List[str]` | 功能列表（v1.1新增，用于与痛点进行功能匹配） | `["text-to-image", "style-transfer", "batch-processing"]` |
| `pricing_model` | `str` | 定价模式（枚举值，v1.1新增） | `"free"`, `"freemium"`, `"paid"`, `"subscription"` |
| `summary_cn` | `str` | 中文摘要（≤200字符） | `"基于AI的文本生成图像工具，支持多种艺术风格"` |
| `summary_ja` | `str` | 日文摘要（≤200字符） | `"テキストから画像を生成するAIツール、複数のアートスタイルをサポート"` |
| `data_quality_score` | `float` | 数据质量评分（0-1，v1.1新增） | `0.95` |
| `schema_version` | `str` | 数据模型版本 | `"1.1"` |

**数据质量评分计算**（`data_quality_score`）:
```python
data_quality_score = (
    source_reliability * 0.4 +      # 来源可靠性（ProductHunt=1.0, RSS=0.9, 爬虫=0.7）
    content_completeness * 0.4 +    # 内容完整性（所有必需字段非空=1.0）
    data_freshness * 0.2            # 数据新鲜度（<24h=1.0, <7d=0.7, >7d=0.3）
)
```

**Pydantic示例**:
```python
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Literal
from datetime import datetime
from uuid import uuid4

class AITool(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    source: Literal["Futurepedia", "ProductHunt", "There's an AI for That"]
    url: HttpUrl
    timestamp: datetime
    tags: List[str]
    features: List[str]  # v1.1
    pricing_model: Literal["free", "freemium", "paid", "subscription"]  # v1.1
    summary_cn: str = Field(max_length=200)
    summary_ja: str = Field(max_length=200)
    data_quality_score: float = Field(ge=0.0, le=1.0)  # v1.1
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
                "summary_cn": "基于AI的文本生成图像工具，支持多种艺术风格",
                "summary_ja": "テキストから画像を生成するAIツール、複数のアートスタイルをサポート",
                "data_quality_score": 0.95,
                "schema_version": "1.1"
            }
        }
```

---

### 2. TrendingTopic（热点话题）

代表从社交平台和搜索引擎抓取的热点话题。

**源文件**: `src/models/trend.py`

**必需属性**:

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `id` | `str` | 唯一标识符（UUID v4） | `"660e8400-e29b-41d4-a716-446655440001"` |
| `title` | `str` | 话题标题 | `"How to use ChatGPT for coding"` |
| `description` | `str` | 话题描述 | `"Tutorial on using ChatGPT to write Python code"` |
| `source` | `str` | 来源平台（枚举值） | `"TikTok"`, `"YouTube"`, `"X"`, `"Reddit"`, `"Google Trends"` |
| `url` | `str` | 原始链接 | `"https://www.tiktok.com/@user/video/123456"` |
| `timestamp` | `datetime` | 抓取/发布时间（ISO 8601） | `"2025-11-03T12:00:00Z"` |
| `heat_score` | `float` | 热度分数（0-100，基于互动量归一化） | `85.5` |
| `trend_direction` | `str` | 趋势方向（枚举值，v1.1新增） | `"rising"`, `"falling"`, `"stable"` |
| `tags` | `List[str]` | 标签列表 | `["AI", "coding", "tutorial"]` |
| `summary_cn` | `str` | 中文摘要（≤200字符） | `"教你如何使用ChatGPT编写Python代码的教程"` |
| `summary_ja` | `str` | 日文摘要（≤200字符） | `"ChatGPTを使ってPythonコードを書く方法のチュートリアル"` |
| `data_quality_score` | `float` | 数据质量评分（0-1，v1.1新增） | `0.88` |
| `schema_version` | `str` | 数据模型版本 | `"1.1"` |

**可选属性**:

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `platforms` | `List[str]` | 如果同一热点在多个平台出现，记录所有平台列表 | `["TikTok", "YouTube", "Reddit"]` |
| `trend_velocity` | `float` | 趋势速度，热度增长率百分比（v1.1新增） | `35.2`（表示35.2%增长） |

**趋势方向计算**（`trend_direction`，FR-025）:
```python
# 对比当前热度与24小时前热度
if current_heat > historical_heat * 1.2:
    trend_direction = "rising"
elif current_heat < historical_heat * 0.8:
    trend_direction = "falling"
else:
    trend_direction = "stable"
```

**Pydantic示例**:
```python
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Literal, Optional
from datetime import datetime
from uuid import uuid4

class TrendingTopic(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: str
    source: Literal["TikTok", "YouTube", "X", "Reddit", "Google Trends"]
    url: HttpUrl
    timestamp: datetime
    heat_score: float = Field(ge=0.0, le=100.0)
    trend_direction: Literal["rising", "falling", "stable"]  # v1.1
    tags: List[str]
    summary_cn: str = Field(max_length=200)
    summary_ja: str = Field(max_length=200)
    data_quality_score: float = Field(ge=0.0, le=1.0)  # v1.1
    schema_version: str = "1.1"

    # 可选字段
    platforms: Optional[List[str]] = None
    trend_velocity: Optional[float] = None  # v1.1

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
```

---

### 3. UserPainPoint（用户痛点）

代表从评论中提取的用户痛点。

**源文件**: `src/models/pain_point.py`

**必需属性**:

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `id` | `str` | 唯一标识符（UUID v4） | `"770e8400-e29b-41d4-a716-446655440002"` |
| `original_text` | `str` | 原始评论文本 | `"I need a tool to automatically generate thumbnails for my YouTube videos"` |
| `context_title` | `str` | 帖子/讨论标题，提供完整背景（v1.1新增） | `"Best AI tools for content creators in 2025"` |
| `extracted_keywords` | `List[str]` | 提取的关键词列表 | `["tool", "automatically", "generate", "thumbnails", "YouTube"]` |
| `source` | `str` | 来源（枚举值） | `"Reddit"`, `"X"`, `"ProductHunt"` |
| `url` | `str` | 评论链接 | `"https://reddit.com/r/youtubers/comments/abc123"` |
| `timestamp` | `datetime` | 评论时间（ISO 8601） | `"2025-11-03T14:30:00Z"` |
| `engagement_score` | `float` | 互动分数（基于点赞/评论数，0-100） | `72.0` |
| `confidence_score` | `float` | 痛点置信度（0-1，v1.1新增） | `0.85` |
| `tags` | `List[str]` | 标签列表 | `["content-creation", "automation", "video"]` |
| `summary_cn` | `str` | 中文摘要（≤200字符） | `"需要一个自动生成YouTube视频缩略图的工具"` |
| `summary_ja` | `str` | 日文摘要（≤200字符） | `"YouTube動画のサムネイルを自動生成するツールが必要"` |
| `data_quality_score` | `float` | 数据质量评分（0-1，v1.1新增） | `0.90` |
| `schema_version` | `str` | 数据模型版本 | `"1.1"` |

**可选属性**:

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `author_metadata` | `Dict[str, Any]` | 作者元信息（v1.1新增，用于判断痛点权威性） | `{"account_type": "verified", "followers": 5000, "karma": 12000}` |

**置信度评分计算**（`confidence_score`，FR-024）:
```python
confidence_score = (
    keyword_match_quality * 0.4 +    # 关键词匹配度（完全匹配=1.0, 部分匹配=0.6）
    source_reliability * 0.3 +       # 来源可靠性（Reddit r/entrepreneur=0.9, 随机评论=0.5）
    engagement_quality * 0.3         # 互动质量（高赞评论=1.0, 无互动=0.3）
)
```

**Pydantic示例**:
```python
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Literal, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4

class UserPainPoint(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    original_text: str
    context_title: str  # v1.1
    extracted_keywords: List[str]
    source: Literal["Reddit", "X", "ProductHunt"]
    url: HttpUrl
    timestamp: datetime
    engagement_score: float = Field(ge=0.0, le=100.0)
    confidence_score: float = Field(ge=0.0, le=1.0)  # v1.1
    tags: List[str]
    summary_cn: str = Field(max_length=200)
    summary_ja: str = Field(max_length=200)
    data_quality_score: float = Field(ge=0.0, le=1.0)  # v1.1
    schema_version: str = "1.1"

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
```

---

### 4. Opportunity（产品机会）

代表匹配后的产品机会。

**源文件**: `src/models/opportunity.py`

**必需属性**:

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `id` | `str` | 唯一标识符（UUID v4） | `"880e8400-e29b-41d4-a716-446655440003"` |
| `pain_point_id` | `str` | 关联的痛点ID（外键） | `"770e8400-e29b-41d4-a716-446655440002"` |
| `related_tools` | `List[str]` | 关联的AI工具ID列表 | `["550e8400-...", "550e8401-..."]` |
| `related_topics` | `List[str]` | 关联的热点话题ID列表 | `["660e8400-...", "660e8401-..."]` |
| `opportunity_score` | `float` | 机会评分（0-100） | `78.5` |
| `mvp_suggestion_cn` | `str` | 中文MVP建议 | `"开发一个基于AI的YouTube缩略图生成器，支持一键生成多种风格"` |
| `mvp_suggestion_ja` | `str` | 日文MVP建议 | `"AIベースのYouTubeサムネイル生成ツールを開発し、ワンクリックで複数のスタイルをサポート"` |
| `timestamp` | `datetime` | 机会生成时间（ISO 8601） | `"2025-11-03T16:00:00Z"` |
| `tags` | `List[str]` | 标签列表（聚合自痛点、工具、热点） | `["content-creation", "automation", "AI", "video"]` |
| `data_quality_score` | `float` | 数据质量评分（v1.1新增，取平均值） | `0.91` |
| `schema_version` | `str` | 数据模型版本 | `"1.1"` |

**评分计算**（FR-025，spec.md第185行）:
```python
opportunity_score = [
    (pain_point.engagement_score * 0.4) +
    (related_tools.count * 10 * 0.3) +     # 每个相关工具贡献10分
    (related_topics.heat_score * 0.3)
] * pain_point.confidence_score * average_data_quality_score

# 归一化到0-100范围
opportunity_score = min(100, opportunity_score)
```

**详细评分维度**（基于research.md评分算法设计）:

| 维度 | 权重 | 计算方法 | 范围 |
|------|------|----------|------|
| Pain Point Clarity | 0.4 | 基于关键词匹配度、具体性、语言质量 | 0-10 |
| MVP Speed | 0.3 | 基于相关工具数量和技术复杂度 | 0-10 |
| Monetization Potential | 0.3 | 基于付费意愿、商业模式、市场规模 | 0-10 |
| Japan Market Fit | 0.2 | 基于文化相关性、竞争分析、市场规模 | 0-10 |
| US/EU Market Fit | 0.2 | 基于可扩展性、GDPR合规、市场潜力 | 0-10 |
| Trending Score | 0.3 | 基于社交信号、速度、跨平台动量 | 0-10 |

**Pydantic示例**:
```python
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from uuid import uuid4

class Opportunity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    pain_point_id: str
    related_tools: List[str]
    related_topics: List[str]
    opportunity_score: float = Field(ge=0.0, le=100.0)
    mvp_suggestion_cn: str
    mvp_suggestion_ja: str
    timestamp: datetime
    tags: List[str]
    data_quality_score: float = Field(ge=0.0, le=1.0)  # v1.1
    schema_version: str = "1.1"

    class Config:
        json_schema_extra = {
            "example": {
                "id": "880e8400-e29b-41d4-a716-446655440003",
                "pain_point_id": "770e8400-e29b-41d4-a716-446655440002",
                "related_tools": ["550e8400-e29b-41d4-a716-446655440000"],
                "related_topics": ["660e8400-e29b-41d4-a716-446655440001"],
                "opportunity_score": 78.5,
                "mvp_suggestion_cn": "开发一个基于AI的YouTube缩略图生成器，支持一键生成多种风格。技术栈：Flask + Stable Diffusion API，预计2周MVP",
                "mvp_suggestion_ja": "AIベースのYouTubeサムネイル生成ツールを開発し、ワンクリックで複数のスタイルをサポート。技術スタック：Flask + Stable Diffusion API、2週間でMVP",
                "timestamp": "2025-11-03T16:00:00Z",
                "tags": ["content-creation", "automation", "AI", "video"],
                "data_quality_score": 0.91,
                "schema_version": "1.1"
            }
        }
```

---

## 辅助模型

### 5. ScrapingLog（爬取日志）

用于记录每次数据抓取的结果，符合宪法原则VI（可重现性）。

**源文件**: `src/models/scraping_log.py`

**必需属性**:

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `id` | `str` | 唯一标识符（UUID v4） | `"990e8400-e29b-41d4-a716-446655440004"` |
| `source` | `str` | 数据源名称 | `"Futurepedia"`, `"Reddit"` |
| `status` | `str` | 执行状态（枚举值） | `"success"`, `"failed"`, `"partial"` |
| `records_count` | `int` | 成功抓取的记录数 | `45` |
| `errors` | `List[str]` | 错误消息列表 | `["Timeout after 3 retries", "Rate limit exceeded"]` |
| `duration_seconds` | `float` | 执行耗时（秒） | `12.5` |
| `timestamp` | `datetime` | 执行时间（ISO 8601） | `"2025-11-03T08:00:00Z"` |

**Pydantic示例**:
```python
from pydantic import BaseModel, Field
from typing import List, Literal
from datetime import datetime
from uuid import uuid4

class ScrapingLog(BaseModel):
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
```

---

## 数据关系图

```text
┌─────────────────┐
│   AITool        │
│  (AI工具数据)    │
└────────┬────────┘
         │
         │ related_tools (FK)
         │
         ▼
┌─────────────────┐       pain_point_id (FK)      ┌──────────────────┐
│  Opportunity    │◄──────────────────────────────│  UserPainPoint   │
│  (产品机会)      │                                │  (用户痛点)       │
└────────┬────────┘                                └──────────────────┘
         │
         │ related_topics (FK)
         │
         ▼
┌─────────────────┐
│ TrendingTopic   │
│  (热点话题)      │
└─────────────────┘

┌─────────────────┐
│  ScrapingLog    │  (独立，用于监控和调试)
│  (爬取日志)      │
└─────────────────┘
```

**关系说明**:
- **Opportunity** 是中心实体，聚合了 **UserPainPoint**、**AITool**、**TrendingTopic**
- **FK（外键）**: 通过UUID建立关联
- **ScrapingLog**: 独立实体，用于审计和监控

---

## JSON序列化示例

### latest.json 结构

```json
{
  "schema_version": "1.1",
  "generated_at": "2025-11-03T16:00:00Z",
  "ai_tools": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Midjourney",
      "description": "AI-powered image generation from text prompts",
      "source": "ProductHunt",
      "url": "https://www.midjourney.com",
      "timestamp": "2025-11-03T10:30:00Z",
      "tags": ["image-generation", "creativity", "design"],
      "features": ["text-to-image", "style-transfer", "batch-processing"],
      "pricing_model": "subscription",
      "summary_cn": "基于AI的文本生成图像工具，支持多种艺术风格",
      "summary_ja": "テキストから画像を生成するAIツール、複数のアートスタイルをサポート",
      "data_quality_score": 0.95,
      "schema_version": "1.1"
    }
  ],
  "trending_topics": [...],
  "pain_points": [...],
  "opportunities": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "pain_point_id": "770e8400-e29b-41d4-a716-446655440002",
      "related_tools": ["550e8400-e29b-41d4-a716-446655440000"],
      "related_topics": ["660e8400-e29b-41d4-a716-446655440001"],
      "opportunity_score": 78.5,
      "mvp_suggestion_cn": "开发一个基于AI的YouTube缩略图生成器...",
      "mvp_suggestion_ja": "AIベースのYouTubeサムネイル生成ツール...",
      "timestamp": "2025-11-03T16:00:00Z",
      "tags": ["content-creation", "automation", "AI", "video"],
      "data_quality_score": 0.91,
      "schema_version": "1.1"
    }
  ],
  "scraping_logs": [...]
}
```

---

## 迁移指南

### 从v1.0升级到v1.1

如果存在v1.0的历史数据，按以下步骤迁移：

1. **AITool**:
   - 新增 `features` 字段（默认值：`[]`）
   - 新增 `pricing_model` 字段（默认值：`"unknown"`，需手动标注）
   - 新增 `data_quality_score` 字段（默认值：`0.7`）

2. **TrendingTopic**:
   - 新增 `trend_direction` 字段（默认值：`"stable"`）
   - 新增 `trend_velocity` 字段（可选，默认值：`null`）
   - 新增 `data_quality_score` 字段（默认值：`0.7`）

3. **UserPainPoint**:
   - 新增 `context_title` 字段（默认值：`""`，需回填）
   - 新增 `confidence_score` 字段（默认值：`0.5`，需重新计算）
   - 新增 `author_metadata` 字段（可选，默认值：`null`）
   - 新增 `data_quality_score` 字段（默认值：`0.7`）

4. **Opportunity**:
   - 新增 `data_quality_score` 字段（默认值：取相关实体平均值）
   - 更新 `opportunity_score` 计算公式（需重新计算）

**迁移脚本位置**: `scripts/migrate_v1.0_to_v1.1.py`（将在Phase 2实现）

---

## 验证规则

所有Pydantic模型将包含以下验证：

1. **URL验证**: 使用 `HttpUrl` 类型确保URL格式正确
2. **日期验证**: 使用 `datetime` 类型，ISO 8601格式
3. **范围验证**: 使用 `Field(ge=, le=)` 确保分数在有效范围内
4. **枚举验证**: 使用 `Literal` 类型确保字段值符合预定义选项
5. **长度验证**: 使用 `Field(max_length=)` 限制摘要长度
6. **非空验证**: 必需字段不允许空值

**测试覆盖**: `tests/unit/test_models.py` 将包含所有验证规则的测试用例。

---

## 参考资料

- **Pydantic文档**: https://docs.pydantic.dev/latest/
- **UUID v4规范**: https://datatracker.ietf.org/doc/html/rfc4122
- **ISO 8601日期格式**: https://en.wikipedia.org/wiki/ISO_8601
- **宪法原则II（统一数据模型）**: `.specify/memory/constitution.md` 第43-55行
