# Implementation Plan: AI工具与热点机会发现仪表板

**Branch**: `001-ai-tool-hotspot-dashboard` | **Date**: 2025-11-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-ai-tool-hotspot-dashboard/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

构建一个自动化数据聚合和分析系统，每日从多个AI工具数据源（Futurepedia RSS、There's an AI for That、ProductHunt）和大众热点平台（TikTok、YouTube Shorts、X、Reddit、Google Trends）抓取数据，通过规范化、去重、分类、痛点提取和相关性匹配流程，生成Top 10产品机会榜单。系统提供Flask Web仪表板（AI工具榜、热点榜、机会榜三页）和每日Top 10机会邮件日报（含中日双语摘要与MVP建议），帮助个人或小团队快速发现可落地的AI产品创意。

## Technical Context

**Language/Version**: Python 3.10+（宪法要求Python 3.10+以确保现代类型提示和性能改进）
**Primary Dependencies**:
- Flask（Web仪表板）
- Requests + BeautifulSoup4（核心爬虫，宪法原则III要求）
- Playwright（仅用于JavaScript密集型站点，如TikTok/YouTube Shorts）
- python-dotenv（配置管理，宪法原则III要求）
- Pydantic（数据模型验证，宪法原则II要求）
- NEEDS CLARIFICATION: LLM API选择（OpenAI GPT-4o-mini / Anthropic Claude Haiku / 本地模型）
- NEEDS CLARIFICATION: 邮件服务提供商（Gmail SMTP / SendGrid / AWS SES）

**Storage**:
- SQLite（轻量级关系数据库，存储结构化数据）
- JSON文件（`data/latest.json`，`data/archive/YYYY-MM-DD.json`，宪法原则I要求原子更新）

**Testing**: pytest（单元测试 + 集成测试，宪法原则VI要求）

**Target Platform**: Linux/macOS服务器（支持cron调度），本地开发环境支持Windows/macOS

**Project Type**: Web应用（Flask后端 + 简单HTML/CSS/JS前端）

**Performance Goals**:
- 仪表板首屏加载时间 < 3秒（成功标准SC-003）
- 每日数据抓取完成时间 < 30分钟
- 邮件发送延迟 < 30分钟（成功标准SC-004）

**Constraints**:
- 爬虫速率限制：≤ 1 req/sec per domain（宪法原则I）
- 数据新鲜度：24小时内（成功标准SC-001）
- 错误率 < 5%（成功标准SC-008）
- 单数据源失败不影响整体可用性（成功标准SC-002）

**Scale/Scope**:
- 初期用户数 < 100 DAU（个人或小团队使用）
- 每日抓取数据量：100-500条原始数据，30-100条有效数据（假设2）
- 数据存储：初期 < 10GB（假设6）
- 支持至少6个数据源（功能需求FR-001）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with all constitutional principles:

- [x] **Data Reliability**:
  - ✅ 重试逻辑：所有爬虫将实现指数退避重试（宪法I）
  - ✅ 回退机制：`latest.json`必须始终存在，失败时使用上次数据（FR-016）
  - ✅ 原子写入：写入临时文件后rename（宪法I）
  - ✅ 仅抓取公开数据源，无需认证（宪法I明确要求）
  - ✅ 遵守robots.txt，速率限制1 req/sec（宪法I）

- [x] **Unified Data Model**:
  - ✅ 数据契约将在`src/models/`定义（FR-020）
  - ✅ Schema version 1.1（spec.md定义）
  - ✅ 所有JSON输出包含schema_version字段（FR-020）
  - ✅ 使用Pydantic进行schema验证

- [x] **Minimal Dependencies**:
  - ✅ 核心依赖已最小化：requests + BeautifulSoup4
  - ✅ Playwright仅用于必需的JavaScript密集型站点
  - ✅ 所有secrets（API keys, SMTP）存储在.env（宪法III）
  - ✅ 使用python-dotenv管理配置
  - ✅ Python 3.10+满足宪法要求

- [x] **Value-Driven Scoring**:
  - ✅ 评分包含所有必需维度（宪法IV）：
    - Pain Point Clarity（痛点清晰度）
    - Technical Feasibility/MVP Speed（技术可行性/MVP速度）
    - Monetization Potential（变现潜力）
    - Japan Market Fit（日本市场契合度）
    - US/EU Market Fit（美欧市场契合度）
    - Trending Score（趋势分数）
  - ✅ 痛点提取是核心评分维度（FR-005, FR-006）
  - ✅ 评分公式明确定义（FR-025，spec.md Opportunity实体）

- [x] **Multilingual Output**:
  - ✅ 所有用户界面内容支持中文+日文（FR-008）
  - ✅ LLM生成摘要≤200字符（FR-008）
  - ✅ MVP建议包含中日双语（FR-015）
  - ✅ 使用成本效益LLM（宪法V：GPT-4o-mini/Claude Haiku）

- [x] **Reproducibility**:
  - ✅ 结构化日志（JSON格式，宪法VI）
  - ✅ 历史快照存储（`data/archive/YYYY-MM-DD.json`，宪法VI）
  - ✅ 文档包含设置说明、评分方法、LLM提示（宪法VI）
  - ✅ 每次运行记录时间戳、数据源、记录数、错误、持续时间（FR-017）

**Complexity Justification**: 无违规项，所有宪法原则均已满足。

---

### Phase 1后重新评估（2025-11-03）

经过Phase 1设计（生成data-model.md、contracts/、quickstart.md）后，重新验证宪法合规性：

- [x] **Data Reliability** - ✅ 通过
  - data-model.md定义了ScrapingLog实体用于审计（宪法VI）
  - quickstart.md包含完整的错误处理指南
  - research.md详细说明了重试逻辑、速率限制、robots.txt遵守

- [x] **Unified Data Model** - ✅ 通过
  - data-model.md完整定义了所有实体（AITool, TrendingTopic, UserPainPoint, Opportunity, ScrapingLog）
  - 所有实体包含schema_version字段（v1.1）
  - 提供了Pydantic示例和验证规则
  - 包含v1.0→v1.1迁移指南

- [x] **Minimal Dependencies** - ✅ 通过
  - quickstart.md列出的依赖与宪法III要求一致（Flask, requests, BeautifulSoup4, Pydantic, python-dotenv）
  - .env.example展示了所有配置通过环境变量管理
  - Playwright标记为可选依赖

- [x] **Value-Driven Scoring** - ✅ 通过
  - research.md第4节详细设计了6维度评分算法
  - data-model.md的Opportunity实体包含完整评分计算公式
  - quickstart.md的.env配置允许调整评分权重

- [x] **Multilingual Output** - ✅ 通过
  - data-model.md所有实体包含summary_cn和summary_ja字段（≤200字符）
  - Opportunity实体包含mvp_suggestion_cn和mvp_suggestion_ja
  - contracts/api_spec.yaml的响应schema包含双语字段

- [x] **Reproducibility** - ✅ 通过
  - data-model.md定义了ScrapingLog实体用于审计
  - quickstart.md提供完整的环境设置、首次运行、故障排除指南
  - research.md记录了所有技术选型决策和替代方案分析

**结论**: 所有宪法原则在Phase 1设计后仍保持完全合规。无需复杂性证明。

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── models/              # Pydantic数据模型（宪法II）
│   ├── __init__.py
│   ├── tool.py         # AITool实体
│   ├── trend.py        # TrendingTopic实体
│   ├── pain_point.py   # UserPainPoint实体
│   └── opportunity.py  # Opportunity实体
├── scrapers/           # 数据源爬虫（宪法I）
│   ├── __init__.py
│   ├── base.py         # 基础爬虫类（重试逻辑、速率限制）
│   ├── ai_tools/
│   │   ├── futurepedia.py
│   │   ├── theresanai.py
│   │   └── producthunt.py
│   └── trends/
│       ├── tiktok.py
│       ├── youtube.py
│       ├── x_twitter.py
│       ├── reddit.py
│       └── google_trends.py
├── scoring/            # 评分逻辑（宪法IV）
│   ├── __init__.py
│   ├── pain_point_clarity.py
│   ├── mvp_speed.py
│   ├── monetization.py
│   ├── market_fit.py
│   ├── trending.py
│   └── aggregator.py   # 总评分聚合
├── llm/                # LLM集成（宪法V）
│   ├── __init__.py
│   ├── summarizer.py   # 中日双语摘要生成
│   ├── pain_extractor.py # 痛点提取
│   └── mvp_suggester.py  # MVP建议生成
├── dashboard/          # Flask Web仪表板
│   ├── __init__.py
│   ├── app.py          # Flask应用主入口
│   ├── routes.py       # 路由定义
│   ├── templates/
│   │   ├── base.html
│   │   ├── tools.html  # AI工具榜页面
│   │   ├── trends.html # 热点榜页面
│   │   └── opportunities.html # 机会榜页面
│   └── static/
│       ├── css/
│       └── js/
├── email/              # 邮件报告
│   ├── __init__.py
│   ├── sender.py       # SMTP发送
│   └── templates/
│       └── daily_report.html
├── pipeline/           # 数据处理流程编排
│   ├── __init__.py
│   ├── orchestrator.py # 主流程：抓取→规范化→去重→分类→匹配→评分→摘要
│   ├── deduplicator.py # 去重逻辑
│   └── matcher.py      # 相关性匹配
├── utils/              # 工具函数
│   ├── __init__.py
│   ├── logger.py       # 结构化日志（宪法VI）
│   ├── config.py       # 配置加载（python-dotenv）
│   └── storage.py      # 原子写入JSON/SQLite
└── cli/                # 命令行接口
    ├── __init__.py
    └── main.py         # 手动触发数据抓取（FR-018）

tests/
├── unit/               # 单元测试
│   ├── test_models.py
│   ├── test_scoring.py
│   └── test_deduplicator.py
├── integration/        # 集成测试
│   ├── test_pipeline.py
│   └── test_dashboard.py
└── mocks/              # Mock数据和API响应
    └── scrapers/

data/                   # 数据存储（.gitignore）
├── latest.json         # 当前最新数据
├── archive/            # 历史快照
│   └── YYYY-MM-DD.json
└── db.sqlite           # SQLite数据库

docs/                   # 文档（宪法VI）
├── setup.md            # 环境设置和首次运行
├── scoring.md          # 评分方法详解
├── data-model.md       # 数据模型文档
└── api-sources.md      # 数据源API文档

.env.example            # 环境变量模板
requirements.txt        # Python依赖（带注释）
Makefile                # 常用命令（make scrape, make reproduce）
```

**Structure Decision**: 选择Web应用结构（Flask后端 + 简单前端），因为：
1. 功能规格明确要求Flask Web仪表板（FR-010）
2. 前端仅为数据展示，不涉及复杂交互，使用Flask模板引擎足够
3. 不需要独立的frontend/backend分离，降低部署复杂度
4. 符合宪法原则III（最小依赖）和初期规模假设（<100 DAU）

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

无违规项，无需复杂性证明。所有设计决策符合宪法原则。
