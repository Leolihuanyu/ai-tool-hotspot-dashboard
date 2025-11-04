# Tasks: AI工具与热点机会发现仪表板

**Branch**: `001-ai-tool-hotspot-dashboard` | **Date**: 2025-11-03
**Input**: Design documents from `/specs/001-ai-tool-hotspot-dashboard/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, quickstart.md ✓

**Tests**: 本项目未明确要求TDD方法,因此测试任务为可选,将在Phase N Polish阶段实现。

**Organization**: 任务按用户故事(User Story)组织,每个故事可独立实现和测试。

## Format: `- [ ] [ID] [P?] [Story?] Description with file path`

- **Checkbox**: 所有任务以 `- [ ]` 开头
- **[ID]**: 任务序号 (T001, T002, T003...)
- **[P]**: 可并行执行(不同文件,无依赖)
- **[Story]**: 用户故事标签 (US1, US2, US3...) - 仅用于User Story阶段
- **Description**: 具体操作 + 精确文件路径

---

## Phase 1: Setup (项目初始化)

**目标**: 建立项目基础结构和开发环境

- [X] T001 Create project structure per plan.md (directories: src/, tests/, data/, docs/, logs/)
- [X] T002 Initialize Python 3.10+ project with virtual environment
- [X] T003 [P] Create requirements.txt with core dependencies (Flask, requests, beautifulsoup4, pydantic, python-dotenv, sendgrid, feedparser, tenacity, ratelimit, pytest)
- [X] T004 [P] Create .env.example with all configuration variables per quickstart.md
- [X] T005 [P] Create .gitignore (exclude: venv/, data/, logs/, .env, __pycache__/, *.pyc, .DS_Store)
- [X] T006 [P] Setup Makefile with common commands (install, scrape, reproduce, run-pipeline)
- [X] T007 [P] Configure linting and formatting (add black, flake8, mypy to requirements.txt)
- [X] T008 Create README.md with project overview and quick start instructions

---

## Phase 2: Foundational (核心基础设施)

**目标**: 建立所有用户故事依赖的核心组件

**⚠️ 关键**: 本阶段必须100%完成后才能开始任何用户故事实现

### 数据模型 (Data Models)

- [X] T009 [P] Implement AITool model in src/models/tool.py with Pydantic validation (schema v1.1)
- [X] T010 [P] Implement TrendingTopic model in src/models/trend.py with Pydantic validation (schema v1.1)
- [X] T011 [P] Implement UserPainPoint model in src/models/pain_point.py with Pydantic validation (schema v1.1)
- [X] T012 [P] Implement Opportunity model in src/models/opportunity.py with Pydantic validation (schema v1.1)
- [X] T013 [P] Implement ScrapingLog model in src/models/scraping_log.py with Pydantic validation
- [X] T014 Create src/models/__init__.py exporting all models

### 核心工具模块 (Core Utilities)

- [X] T015 [P] Implement structured logger in src/utils/logger.py (JSON format,宪法VI)
- [X] T016 [P] Implement config loader in src/utils/config.py using python-dotenv
- [X] T017 [P] Implement atomic storage utilities in src/utils/storage.py (write temp → rename, 宪法I)
- [X] T018 Create src/utils/__init__.py exporting utilities

### 数据库设置 (Database Setup)

- [X] T019 Create SQLite database schema in src/database/schema.sql (tables: ai_tools, trending_topics, pain_points, opportunities, scraping_logs)
- [X] T020 Implement database connection manager in src/database/connection.py
- [X] T021 Implement database initialization in src/database/init.py
- [X] T022 Create src/database/__init__.py

### 爬虫基础设施 (Scraper Infrastructure)

- [X] T023 Implement base scraper class in src/scrapers/base.py with retry logic (tenacity), rate limiting (ratelimit), robots.txt checking, User-Agent setup
- [X] T024 Create src/scrapers/__init__.py
- [X] T025 Create src/scrapers/ai_tools/__init__.py
- [X] T026 Create src/scrapers/trends/__init__.py

### LLM集成基础 (LLM Integration)

- [X] T027 [P] Implement LLM client wrapper in src/llm/client.py (support Claude Haiku 3 + Batch API, 宪法V)
- [X] T028 [P] Define prompt templates in src/llm/prompts.py (summary generation, pain point extraction, MVP suggestions)
- [X] T029 Create src/llm/__init__.py

### CLI框架 (CLI Framework)

- [X] T030 Implement CLI main entry point in src/cli/main.py (commands: init-db, scrape, run-pipeline, send-email)
- [X] T031 Create src/cli/__init__.py

**Checkpoint**: ✅ 基础设施就绪 - 用户故事实现现在可以并行开始

---

## Phase 3: User Story 1 - 查看每日AI工具趋势榜单 (Priority: P1) 🎯 MVP

**目标**: 从多个数据源(Futurepedia, ProductHunt, There's an AI for That)抓取AI工具数据,规范化并在仪表板展示≥30条记录

**独立测试**: 运行 `python -m src.cli.main scrape --test-mode --source ai_tools`,验证至少30条AI工具数据被抓取并保存到data/latest.json,然后访问 `http://127.0.0.1:5000/tools` 验证页面在3秒内加载并显示工具列表

### 数据抓取实现 (Data Scraping)

- [X] T032 [P] [US1] Implement Futurepedia RSS scraper in src/scrapers/ai_tools/futurepedia.py (use feedparser, extend BaseScraper)
- [X] T033 [P] [US1] Implement There's an AI for That scraper in src/scrapers/ai_tools/theresanai.py (BeautifulSoup4, extend BaseScraper)
- [X] T034 [P] [US1] Implement ProductHunt scraper in src/scrapers/ai_tools/producthunt.py (use official API if available, extend BaseScraper)
- [X] T035 [US1] Implement data normalization pipeline in src/pipeline/normalizer.py (convert all sources to AITool model)
- [X] T036 [US1] Implement deduplication logic in src/pipeline/deduplicator.py (hash-based on title+URL, FR-003)

### LLM摘要生成 (LLM Summary Generation)

- [X] T037 [US1] Implement bilingual summarizer in src/llm/summarizer.py (generate summary_cn and summary_ja for AITool, ≤200 chars each, FR-008)
- [X] T038 [US1] Implement data quality scoring in src/scoring/data_quality.py (source reliability + content completeness + freshness, data-model.md line 50-56)

### Web仪表板 (Dashboard)

- [X] T039 [US1] Create Flask app initialization in src/dashboard/app.py
- [X] T040 [US1] Implement routes for AI工具榜 in src/dashboard/routes.py (GET /tools with pagination, source filtering)
- [X] T041 [US1] Create base HTML template in src/dashboard/templates/base.html (navbar with 3 pages: AI工具榜, 热点榜, 机会榜)
- [X] T042 [US1] Create AI工具榜页面 in src/dashboard/templates/tools.html (display ≥30 tools, time-sorted, FR-011)
- [X] T043 [US1] Add CSS styling in src/dashboard/static/css/main.css (ensure <3s load time, SC-003)
- [X] T044 [US1] Add JavaScript for source filtering in src/dashboard/static/js/tools.js

### 数据持久化 (Data Persistence)

- [X] T045 [US1] Implement JSON export in src/pipeline/exporter.py (save to data/latest.json with schema_version, atomic write)
- [X] T046 [US1] Implement historical archiving in src/pipeline/archiver.py (save to data/archive/YYYY-MM-DD.json, 宪法VI)

### CLI集成 (CLI Integration)

- [X] T047 [US1] Add `scrape` command for AI tools in src/cli/main.py (support --test-mode, --limit, --source flags)
- [X] T048 [US1] Add error handling and logging for User Story 1 pipeline (FR-016: single source failure doesn't stop others)

**Checkpoint**: ✅ User Story 1完成 - AI工具榜功能完全可用,可独立测试和演示

---

## Phase 4: User Story 2 - 发现大众热点趋势 (Priority: P1)

**目标**: 从社交平台和搜索引擎(TikTok, YouTube Shorts, X, Reddit, Google Trends)抓取热点话题,在仪表板展示≥30条记录

**独立测试**: 运行 `python -m src.cli.main scrape --source trends`,验证至少30条热点数据被抓取,然后访问 `http://127.0.0.1:5000/trends` 验证页面显示热点列表并支持来源筛选

### 热点数据抓取 (Trending Data Scraping)

- [X] T049 [P] [US2] Implement TikTok scraper in src/scrapers/trends/tiktok.py (use Playwright if needed, extend BaseScraper)
- [X] T050 [P] [US2] Implement YouTube Shorts scraper in src/scrapers/trends/youtube.py (use Playwright if needed, extend BaseScraper)
- [X] T051 [P] [US2] Implement X (Twitter) scraper in src/scrapers/trends/x_twitter.py (consider Nitter or RSS Bridge, extend BaseScraper)
- [X] T052 [P] [US2] Implement Reddit scraper in src/scrapers/trends/reddit.py (use PRAW or RSS feed, extend BaseScraper)
- [X] T053 [P] [US2] Implement Google Trends scraper in src/scrapers/trends/google_trends.py (use pytrends library, extend BaseScraper)

### 热点数据处理 (Trending Data Processing)

- [X] T054 [US2] Add TrendingTopic normalization to src/pipeline/normalizer.py
- [X] T055 [US2] Add TrendingTopic deduplication to src/pipeline/deduplicator.py (cross-platform merging, spec.md line 76)
- [X] T056 [US2] Implement trend direction calculator in src/scoring/trending.py (rising/falling/stable based on 24h heat comparison, FR-025)
- [X] T057 [US2] Add bilingual summarization for TrendingTopic in src/llm/summarizer.py

### 热点榜仪表板 (Trending Dashboard)

- [X] T058 [US2] Add routes for 热点榜 in src/dashboard/routes.py (GET /trends with source filtering, heat sorting)
- [X] T059 [US2] Create 热点榜页面 in src/dashboard/templates/trends.html (display ≥30 topics, heat-sorted, FR-012)
- [X] T060 [US2] Add JavaScript for source filtering in src/dashboard/static/js/trends.js

### CLI集成 (CLI Integration)

- [X] T061 [US2] Add trending scraping to `scrape` command in src/cli/main.py
- [X] T062 [US2] Add error handling for User Story 2 pipeline

**Checkpoint**: ✅ User Story 2完成 - 热点榜功能可用,与US1独立运行

---

## Phase 5: User Story 3 - 识别产品机会与痛点 (Priority: P1)

**目标**: 从Reddit/X/ProductHunt评论中提取用户痛点,与AI工具和热点匹配,生成Top 10产品机会并在仪表板展示

**独立测试**: 运行完整pipeline (`python -m src.cli.main run-pipeline`),验证至少50条痛点被提取,Top 10机会生成并包含MVP建议,然后访问 `http://127.0.0.1:5000/opportunities` 验证机会榜显示

### 痛点提取 (Pain Point Extraction)

- [X] T063 [P] [US3] Implement pain point extractor in src/llm/pain_extractor.py (extract from Reddit/X/ProductHunt comments with keywords "need a tool", "wish there was", FR-005)
- [X] T064 [US3] Add pain point scraping to Reddit scraper in src/scrapers/trends/reddit.py (extract comments from r/entrepreneur, r/SaaS, etc.)
- [X] T065 [US3] Add pain point scraping to X scraper in src/scrapers/trends/x_twitter.py
- [X] T066 [US3] Add pain point scraping to ProductHunt scraper in src/scrapers/ai_tools/producthunt.py (extract from product reviews)
- [X] T067 [US3] Implement confidence scoring in src/scoring/pain_point_clarity.py (keyword match + source reliability + engagement, FR-024)

### 相关性匹配 (Relevance Matching)

- [X] T068 [US3] Implement matcher in src/pipeline/matcher.py (match pain points to AI tools and trending topics based on keyword overlap, semantic similarity, time proximity, FR-006)
- [X] T069 [US3] Add feature matching logic for AITool features vs pain point keywords (use features field from data-model.md)

### 机会评分 (Opportunity Scoring)

- [X] T070 [P] [US3] Implement pain point clarity scorer in src/scoring/pain_point_clarity.py (research.md line 412-424)
- [X] T071 [P] [US3] Implement MVP speed scorer in src/scoring/mvp_speed.py (research.md line 426-435)
- [X] T072 [P] [US3] Implement monetization potential scorer in src/scoring/monetization.py (research.md line 437-448)
- [X] T073 [P] [US3] Implement Japan market fit scorer in src/scoring/market_fit.py (research.md line 450-462)
- [X] T074 [P] [US3] Implement US/EU market fit scorer in src/scoring/market_fit.py (research.md line 464-474)
- [X] T075 [P] [US3] Implement trending scorer in src/scoring/trending.py (research.md line 476-488)
- [X] T076 [US3] Implement opportunity score aggregator in src/scoring/aggregator.py (combine 6 dimensions with weights, apply quality modifiers, FR-025)

### MVP建议生成 (MVP Suggestion Generation)

- [X] T077 [US3] Implement MVP suggester in src/llm/mvp_suggester.py (generate mvp_suggestion_cn and mvp_suggestion_ja with tech stack and timeline)

### 机会榜仪表板 (Opportunity Dashboard)

- [X] T078 [US3] Add routes for 机会榜 in src/dashboard/routes.py (GET /opportunities, return Top 10 sorted by opportunity_score)
- [X] T079 [US3] Create 机会榜页面 in src/dashboard/templates/opportunities.html (display Top 10 opportunities with pain points, related tools, related topics, scores, MVP suggestions, FR-013)
- [X] T080 [US3] Add JavaScript for opportunity detail expansion in src/dashboard/static/js/opportunities.js

### Pipeline编排 (Pipeline Orchestration)

- [X] T081 [US3] Implement main pipeline orchestrator in src/pipeline/orchestrator.py (scrape → normalize → dedupe → classify → extract pain points → match → score → summarize → export)
- [X] T082 [US3] Add `run-pipeline` command in src/cli/main.py (run full pipeline end-to-end)

**Checkpoint**: ✅ User Story 3完成 - 机会榜功能可用,核心价值主张实现

---

## Phase 6: User Story 4 - 接收每日机会报告邮件 (Priority: P2)

**目标**: 每天早上8点自动发送包含Top 10机会的邮件报告,包含中日双语摘要和MVP建议

**独立测试**: 手动运行 `python -m src.cli.main send-email`,验证邮件在30分钟内送达,包含Top 10机会,中日双语内容完整,链接可跳转到仪表板详情页

### 邮件服务实现 (Email Service)

- [X] T083 [P] [US4] Implement email sender in src/email/sender.py using SendGrid API (research.md推荐, with retry logic, 宪法I)
- [X] T084 [P] [US4] Create HTML email template in src/email/templates/daily_report.html (include Top 10 opportunities, bilingual summaries, MVP suggestions, clickable links to dashboard)
- [X] T085 [US4] Implement email content generator in src/email/generator.py (load Top 10 from latest.json, render HTML template)
- [X] T086 [US4] Create src/email/__init__.py

### CLI集成和调度 (CLI Integration and Scheduling)

- [X] T087 [US4] Add `send-email` command in src/cli/main.py (send daily report to EMAIL_TO_LIST from .env)
- [X] T088 [US4] Add email delivery logging in src/utils/logger.py (track send status, delivery time, errors, FR-017)
- [X] T089 [US4] Create cron setup documentation in docs/scheduling.md (Linux/macOS cron, Windows Task Scheduler, FR-014)

### 错误处理 (Error Handling)

- [X] T090 [US4] Add email retry logic in src/email/sender.py (max 3 retries, exponential backoff, spec.md line 107)
- [X] T091 [US4] Add fallback error notification in src/email/sender.py (send failure alert to admin email if all retries fail)

**Checkpoint**: ✅ User Story 4完成 - 邮件日报功能可用

---

## Phase 7: User Story 5 - 浏览历史数据和趋势变化 (Priority: P3)

**目标**: 支持查看过去7天或30天的历史数据,显示趋势图表和工具热度变化曲线

**独立测试**: 在仪表板选择"过去7天"时间范围,验证显示历史数据和趋势折线图,点击某个工具查看30天热度变化曲线

### 历史数据查询 (Historical Data Query)

- [ ] T092 [P] [US5] Add time range filtering to routes in src/dashboard/routes.py (support ?days=7 or ?days=30 query parameter)
- [ ] T093 [P] [US5] Implement historical data loader in src/pipeline/history_loader.py (load from data/archive/YYYY-MM-DD.json for specified date range)
- [ ] T094 [US5] Add database queries for historical trends in src/database/queries.py (retrieve heat_score time series for tools/topics)

### 趋势可视化 (Trend Visualization)

- [ ] T095 [US5] Add Chart.js library to base.html for trend visualization
- [ ] T096 [P] [US5] Create trend chart component in src/dashboard/static/js/trend_chart.js (line chart for heat_score over time)
- [ ] T097 [P] [US5] Update tools.html to include "View History" button for each tool
- [ ] T098 [P] [US5] Update trends.html to include "View History" button for each topic
- [ ] T099 [US5] Add comparison view in src/dashboard/templates/compare.html (display two trend lines side by side, spec.md line 124)

### API端点 (API Endpoints)

- [ ] T100 [US5] Add GET /api/v1/tools/{id}/history endpoint in src/dashboard/routes.py (return heat_score time series for specific tool)
- [ ] T101 [US5] Add GET /api/v1/trends/{id}/history endpoint in src/dashboard/routes.py (return heat_score time series for specific topic)

**Checkpoint**: ✅ User Story 5完成 - 历史数据和趋势分析功能可用

---

## Phase N: Polish & Cross-Cutting Concerns (完善与跨功能任务)

**目标**: 宪法合规,代码质量提升,文档完善,生产环境准备

### 宪法原则I: 数据可靠性 (Data Reliability)

- [ ] T102 [P] Verify all scrapers use exponential backoff retry (tenacity library, research.md line 273-280)
- [ ] T103 [P] Verify all data writes use atomic operations (write temp → rename, src/utils/storage.py)
- [ ] T104 [P] Ensure latest.json always exists (fallback to previous run on pipeline failure, FR-016)
- [ ] T105 [P] Add rate limiting verification (≤1 req/sec per domain, research.md line 283-290)
- [ ] T106 Verify robots.txt compliance for all scrapers (research.md line 293-302)

### 宪法原则II: 统一数据模型 (Unified Data Model)

- [ ] T107 [P] Verify all models include schema_version field (data-model.md line 79, 165, 256, 352)
- [ ] T108 [P] Verify all JSON outputs use Pydantic validation
- [ ] T109 Add schema migration script in scripts/migrate_v1.0_to_v1.1.py (data-model.md line 537)
- [ ] T110 Document schema versioning policy in docs/schema-versioning.md

### 宪法原则III: 最小依赖 (Minimal Dependencies)

- [ ] T111 Audit requirements.txt and remove unused dependencies
- [ ] T112 Add dependency rationale comments in requirements.txt
- [ ] T113 Pin all dependency versions in requirements.txt
- [ ] T114 Verify all secrets are in .env (no hardcoded API keys, plan.md line 73)
- [ ] T115 Add .env validation script in scripts/validate_env.py

### 宪法原则IV: 价值驱动评分 (Value-Driven Scoring)

- [ ] T116 Verify all 6 scoring dimensions are implemented (research.md line 411-488)
- [ ] T117 Make scoring weights configurable via .env (quickstart.md line 133-139)
- [ ] T118 Add unit tests for deterministic scoring in tests/unit/test_scoring.py

### 宪法原则V: 多语言输出 (Multilingual Output)

- [ ] T119 Verify all summaries are ≤200 characters (data-model.md line 76-77, FR-008)
- [ ] T120 Add fallback to English if LLM generation fails (quickstart.md line 120)
- [ ] T121 Verify MVP suggestions include tech stack and timeline (data-model.md line 362-363)

### 宪法原则VI: 可重现性 (Reproducibility)

- [ ] T122 [P] Verify structured logging (JSON format) for all operations (src/utils/logger.py)
- [ ] T123 [P] Verify historical archiving (data/archive/YYYY-MM-DD.json, T046)
- [ ] T124 Create docs/scoring.md documenting scoring formulas (research.md section 4)
- [ ] T125 Create docs/data-sources.md documenting all data sources and API usage
- [ ] T126 Document LLM prompts in docs/llm-prompts.md
- [ ] T127 Add `make reproduce` command to reprocess latest data

### 测试 (Testing)

- [ ] T128 [P] Add unit tests for all models in tests/unit/test_models.py (Pydantic validation, data-model.md line 552)
- [ ] T129 [P] Add unit tests for deduplicator in tests/unit/test_deduplicator.py
- [ ] T130 [P] Add unit tests for scoring in tests/unit/test_scoring.py
- [ ] T131 [P] Add integration test for full pipeline in tests/integration/test_pipeline.py
- [ ] T132 [P] Add integration test for dashboard in tests/integration/test_dashboard.py
- [ ] T133 Create mock data for tests in tests/mocks/scrapers/ (avoid hitting real APIs in tests)
- [ ] T134 Add test coverage reporting (pytest-cov)

### 文档 (Documentation)

- [ ] T135 [P] Create docs/setup.md (environment setup and first run, based on quickstart.md)
- [ ] T136 [P] Create docs/deployment.md (Docker, Nginx, HTTPS, monitoring)
- [ ] T137 [P] Create docs/api-reference.md (REST API documentation)
- [ ] T138 Update README.md with badges (build status, coverage, license)

### 安全与性能 (Security & Performance)

- [ ] T139 Add input validation for all user inputs (防止XSS, SQL injection)
- [ ] T140 Add HTTPS redirect in Flask app (production mode)
- [ ] T141 Add database connection pooling in src/database/connection.py
- [ ] T142 Add caching for dashboard queries (Flask-Caching, 减少数据库查询)
- [ ] T143 Optimize latest.json file size (<10MB, quickstart.md line 383)

### 运维工具 (Operations)

- [ ] T144 Add health check endpoint GET /health in src/dashboard/routes.py
- [ ] T145 Add metrics endpoint GET /metrics for monitoring (Prometheus format)
- [ ] T146 Create data cleanup script in scripts/cleanup.py (remove data older than 30 days)
- [ ] T147 Add database optimization script in scripts/optimize_db.py

### Quickstart验证 (Quickstart Validation)

- [ ] T148 Run through quickstart.md on fresh environment and verify all steps work
- [ ] T149 Verify test mode works (`python -m src.cli.main scrape --test-mode --limit 5`)
- [ ] T150 Verify dashboard loads in <3s (SC-003)
- [ ] T151 Verify email delivery in <30 min (SC-004)

---

## Dependencies & Execution Order

### Phase依赖关系

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational) ← 阻塞所有用户故事
    ↓
Phase 3-7 (User Stories) ← 可并行执行
    ├── Phase 3: User Story 1 (P1) 🎯 MVP
    ├── Phase 4: User Story 2 (P1)
    ├── Phase 5: User Story 3 (P1)
    ├── Phase 6: User Story 4 (P2)
    └── Phase 7: User Story 5 (P3)
    ↓
Phase N (Polish)
```

### User Story依赖关系

- **User Story 1 (P1)**: 无依赖 - 可在Foundational完成后立即开始
- **User Story 2 (P1)**: 无依赖 - 可与US1并行
- **User Story 3 (P1)**: 需要US1和US2的数据 - 但仍可独立测试(使用mock数据)
- **User Story 4 (P2)**: 需要US3生成机会数据 - 轻依赖
- **User Story 5 (P3)**: 需要历史数据 - 依赖US1-US3运行至少7天

### 任务内部依赖 (以User Story 1为例)

```
T032-T034 (爬虫实现) → 可并行
    ↓
T035 (数据规范化) → 依赖爬虫完成
    ↓
T036 (去重) → 依赖规范化完成
    ↓
T037-T038 (LLM摘要+质量评分) → 可并行,依赖去重完成
    ↓
T039-T044 (仪表板) → 可并行,依赖数据处理完成
    ↓
T045-T046 (数据持久化) → 依赖所有处理完成
    ↓
T047-T048 (CLI集成) → 依赖全部完成
```

### 并行机会 (Parallel Opportunities)

#### Phase 2 (Foundational)

```bash
# 并行执行所有模型定义
T009 (AITool model) || T010 (TrendingTopic model) || T011 (UserPainPoint model) || T012 (Opportunity model) || T013 (ScrapingLog model)

# 并行执行所有工具模块
T015 (logger) || T016 (config) || T017 (storage)

# 并行执行LLM基础
T027 (LLM client) || T028 (prompts)
```

#### User Story 1 (爬虫阶段)

```bash
# 并行执行3个AI工具爬虫
T032 (Futurepedia) || T033 (There's an AI for That) || T034 (ProductHunt)

# 并行执行LLM任务
T037 (summarizer) || T038 (data quality)
```

#### User Story 2 (热点爬虫阶段)

```bash
# 并行执行5个热点爬虫
T049 (TikTok) || T050 (YouTube) || T051 (X) || T052 (Reddit) || T053 (Google Trends)
```

#### User Story 3 (评分阶段)

```bash
# 并行执行6个评分维度
T070 (pain clarity) || T071 (MVP speed) || T072 (monetization) || T073 (Japan fit) || T074 (US/EU fit) || T075 (trending)
```

#### Phase N (Polish - 测试阶段)

```bash
# 并行执行所有单元测试
T128 (models) || T129 (deduplicator) || T130 (scoring) || T131 (pipeline) || T132 (dashboard)

# 并行执行所有文档
T135 (setup.md) || T136 (deployment.md) || T137 (api-reference.md)
```

---

## Implementation Strategy

### MVP First (仅User Story 1)

**最小可行产品**: 抓取AI工具数据并在仪表板展示

1. ✅ Complete Phase 1: Setup (T001-T008)
2. ✅ Complete Phase 2: Foundational (T009-T031) - **关键阻塞点**
3. ✅ Complete Phase 3: User Story 1 (T032-T048)
4. 🎯 **STOP and VALIDATE**:
   - 运行 `python -m src.cli.main scrape --test-mode`
   - 访问 `http://127.0.0.1:5000/tools`
   - 验证至少30条AI工具显示,页面<3s加载
5. 📦 Deploy/Demo MVP

**MVP任务总数**: 48个任务
**预计时间**: 2-3周 (单人开发)

### Incremental Delivery (渐进交付)

1. **Week 1-2**: Setup + Foundational → 基础设施就绪
2. **Week 3**: User Story 1 → AI工具榜可用 → 📦 Deploy MVP
3. **Week 4**: User Story 2 → 热点榜可用 → 📦 Deploy v1.1
4. **Week 5**: User Story 3 → 机会榜可用 → 📦 Deploy v1.2 (核心功能完成)
5. **Week 6**: User Story 4 → 邮件日报可用 → 📦 Deploy v1.3
6. **Week 7**: User Story 5 → 历史数据可用 → 📦 Deploy v1.4
7. **Week 8**: Polish → 生产环境优化 → 📦 Deploy v2.0

### Parallel Team Strategy

如果有3个开发者:

1. **Week 1-2**: 全员完成 Setup + Foundational
2. **Week 3+** (Foundational完成后):
   - Developer A: User Story 1 (AI工具榜)
   - Developer B: User Story 2 (热点榜)
   - Developer C: User Story 3的基础部分(痛点提取)
3. **Week 4**:
   - Developer A: User Story 4 (邮件)
   - Developer B: User Story 3集成(匹配+评分)
   - Developer C: User Story 5 (历史数据)
4. **Week 5**: 全员 Polish 和测试

**团队开发预计时间**: 4-5周

---

## Task Summary

### 按阶段统计

| Phase | Task Range | Task Count | 预计时间(单人) |
|-------|-----------|-----------|---------------|
| Phase 1: Setup | T001-T008 | 8 | 1天 |
| Phase 2: Foundational | T009-T031 | 23 | 1周 |
| Phase 3: User Story 1 (P1) | T032-T048 | 17 | 1周 |
| Phase 4: User Story 2 (P1) | T049-T062 | 14 | 1周 |
| Phase 5: User Story 3 (P1) | T063-T082 | 20 | 1.5周 |
| Phase 6: User Story 4 (P2) | T083-T091 | 9 | 3天 |
| Phase 7: User Story 5 (P3) | T092-T101 | 10 | 4天 |
| Phase N: Polish | T102-T151 | 50 | 1.5周 |
| **总计** | T001-T151 | **151** | **8周** |

### 按用户故事统计

| User Story | Priority | Task Count | 独立可演示 | MVP候选 |
|-----------|----------|-----------|-----------|---------|
| US1: AI工具榜 | P1 | 17 | ✅ | 🎯 推荐 |
| US2: 热点榜 | P1 | 14 | ✅ | ⭐ 可选 |
| US3: 机会榜 | P1 | 20 | ✅ | ⭐ 核心价值 |
| US4: 邮件日报 | P2 | 9 | ✅ | - |
| US5: 历史数据 | P3 | 10 | ✅ | - |

### 并行任务统计

- **可并行任务数**: 47个任务标记[P]
- **最大并行度**:
  - Phase 2 Foundational: 6个任务可同时进行
  - User Story 1: 3个爬虫可同时进行
  - User Story 2: 5个爬虫可同时进行
  - User Story 3: 6个评分器可同时进行

### 建议的MVP范围

**推荐MVP**: Setup + Foundational + User Story 1 (48任务,2-3周)

**原因**:
- ✅ 最小化开发时间
- ✅ 展示核心数据抓取能力
- ✅ 提供完整的用户界面
- ✅ 独立可演示和测试
- ✅ 为后续User Story奠定基础

**扩展MVP**: 如果希望展示核心差异化功能,建议包含User Story 3 (机会榜),总计68任务,4-5周。

---

## Notes

- **[P]标记**: 表示该任务与其他[P]任务操作不同文件,可真正并行执行
- **[Story]标记**: 将任务映射到具体用户故事,便于追溯和独立测试
- **检查点(Checkpoint)**: 每个用户故事完成时都有明确的验证标准
- **宪法合规**: Phase N包含所有6条宪法原则的验证任务
- **独立性**: 每个用户故事设计为可独立实现、测试、演示
- **灵活性**: 可以在任何检查点停止,已完成的功能仍然可用
- **建议**: 严格按Phase顺序执行,确保Foundational 100%完成后再开始User Story

---

## 下一步 (Next Steps)

1. ✅ **Review this tasks.md**: 与团队review任务分解是否合理
2. ✅ **Estimate effort**: 根据团队规模调整时间预估
3. ✅ **Choose MVP scope**: 决定是否采用推荐MVP (US1) 或扩展MVP (US1+US3)
4. 🚀 **Start Phase 1**: 创建项目结构,初始化开发环境
5. 📋 **Track progress**: 使用GitHub Issues或项目管理工具跟踪每个任务状态

**祝开发顺利!** 如有任何疑问,参考 `quickstart.md` 或提交Issue。
