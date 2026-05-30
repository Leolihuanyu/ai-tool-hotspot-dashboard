# Quickstart Guide: AI工具与热点机会发现仪表板

**Branch**: `001-ai-tool-hotspot-dashboard` | **Date**: 2025-11-03

本文档提供快速上手指南，帮助开发者在15分钟内完成环境搭建和首次运行。

---

## 目录

1. [前置要求](#前置要求)
2. [环境设置](#环境设置)
3. [配置文件](#配置文件)
4. [首次运行](#首次运行)
5. [访问仪表板](#访问仪表板)
6. [故障排除](#故障排除)
7. [下一步](#下一步)

---

## 前置要求

确保您的系统已安装以下软件：

| 软件 | 最低版本 | 验证命令 | 安装指南 |
|------|----------|----------|----------|
| **Python** | 3.10+ | `python --version` | [python.org](https://www.python.org/downloads/) |
| **Git** | 2.0+ | `git --version` | [git-scm.com](https://git-scm.com/) |
| **pip** | 20.0+ | `pip --version` | 通常随Python安装 |

**可选依赖**（用于JavaScript密集型站点爬取）：
- **Playwright**: 将通过pip自动安装，首次运行需下载浏览器二进制文件

---

## 环境设置

### 1. 克隆仓库

```bash
git clone <your-repository-url>
cd ai-tool-hotspot-dashboard
git checkout 001-ai-tool-hotspot-dashboard
```

### 2. 创建虚拟环境

**Linux/macOS**:
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows**:
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. 安装依赖

```bash
# 安装核心依赖
pip install -r requirements.txt

# （可选）如果需要爬取TikTok/YouTube Shorts，安装Playwright浏览器
playwright install chromium
```

**预期安装的核心依赖**（基于research.md和宪法原则III）:
- `Flask>=3.0.0` - Web仪表板框架
- `requests>=2.31.0` - HTTP请求
- `beautifulsoup4>=4.12.0` - HTML解析
- `pydantic>=2.5.0` - 数据模型验证
- `python-dotenv>=1.0.0` - 环境变量管理
- `sendgrid>=6.12.0` - 邮件发送（research.md推荐）
- `feedparser>=6.0.0` - RSS解析
- `tenacity>=8.2.0` - 重试逻辑
- `ratelimit>=2.2.0` - 速率限制
- `playwright>=1.40.0` - JavaScript密集型站点爬取（可选）
- `pytest>=7.4.0` - 测试框架

### 4. 创建必要的目录

```bash
mkdir -p data/archive
mkdir -p docs
mkdir -p logs
```

---

## 配置文件

### 1. 复制环境变量模板

```bash
cp .env.example .env
```

### 2. 编辑 `.env` 文件

使用您喜欢的编辑器打开 `.env`，填写以下必需配置：

```bash
# === LLM API配置（research.md推荐：Claude Haiku 3）===
ANTHROPIC_API_KEY=<ANTHROPIC_API_KEY>
# 或使用OpenAI（备选方案）
# OPENAI_API_KEY=sk-xxxxxxxxxxxxx

# LLM提供商选择（claude 或 openai）
LLM_PROVIDER=claude
LLM_MODEL=claude-haiku-3-20240307
LLM_USE_BATCH_API=true  # 开启Batch API以节省50%成本

# === 邮件服务配置（research.md推荐：SendGrid）===
SENDGRID_API_KEY=SG.xxxxxxxxxxxxx
EMAIL_FROM=your-verified-email@domain.com
EMAIL_TO_LIST=recipient1@example.com,recipient2@example.com

# 邮件发送时间（cron格式，默认每天早上8点）
EMAIL_SCHEDULE_CRON="0 8 * * *"

# === 数据库配置 ===
DATABASE_PATH=data/db.sqlite

# === 数据抓取配置 ===
# 速率限制（遵守宪法I：≤1 req/sec per domain）
SCRAPER_RATE_LIMIT=1.0  # 秒/请求
SCRAPER_MAX_RETRIES=3
SCRAPER_TIMEOUT=10  # 秒

# === 评分权重配置（research.md评分算法）===
SCORE_WEIGHT_PAIN_CLARITY=0.4
SCORE_WEIGHT_MVP_SPEED=0.3
SCORE_WEIGHT_MONETIZATION=0.3
SCORE_WEIGHT_JAPAN_MARKET=0.2
SCORE_WEIGHT_US_EU_MARKET=0.2
SCORE_WEIGHT_TRENDING=0.3

# === Flask配置 ===
FLASK_ENV=development
FLASK_DEBUG=true
FLASK_PORT=5000
```

**最小化配置**（仅用于快速测试，不发送邮件）：
```bash
ANTHROPIC_API_KEY=<ANTHROPIC_API_KEY>
LLM_PROVIDER=claude
LLM_MODEL=claude-haiku-3-20240307
DATABASE_PATH=data/db.sqlite
```

### 3. 获取API密钥

#### Claude Haiku 3（推荐）
1. 访问 [console.anthropic.com](https://console.anthropic.com/)
2. 注册账号（$5免费额度，无需信用卡）
3. 在"API Keys"页面创建新密钥
4. 复制密钥到 `.env` 的 `ANTHROPIC_API_KEY`

#### SendGrid（邮件服务）
1. 访问 [signup.sendgrid.com](https://signup.sendgrid.com/)
2. 注册免费账号（100封/天额度）
3. 在"Settings > API Keys"创建密钥（权限：Mail Send）
4. 在"Settings > Sender Authentication"验证发件人邮箱
5. 复制API Key到 `.env` 的 `SENDGRID_API_KEY`

---

## 首次运行

### 1. 初始化数据库

```bash
python -m src.cli.main init-db
```

**预期输出**:
```
✅ Database initialized at data/db.sqlite
✅ Created tables: ai_tools, trending_topics, pain_points, opportunities, scraping_logs
```

### 2. 运行数据抓取（测试模式）

首次运行建议使用测试模式，仅抓取少量数据验证配置：

```bash
python -m src.cli.main scrape --test-mode --limit 5
```

**预期输出**:
```
🔍 Starting data scraping (test mode: 5 records per source)...

📡 [Futurepedia RSS] Scraping...
✅ [Futurepedia RSS] Success: 5 records in 3.2s

📡 [ProductHunt] Scraping...
✅ [ProductHunt] Success: 5 records in 4.1s

📡 [Reddit r/OpenAI] Scraping...
✅ [Reddit r/OpenAI] Success: 3 pain points in 2.8s

🧠 Generating summaries (Claude Haiku 3)...
✅ Summaries generated: 13 records

💾 Saving to data/latest.json...
✅ Data saved (schema version: 1.1)

📊 Summary:
   - AI Tools: 10
   - Trending Topics: 0 (skipped in test mode)
   - Pain Points: 3
   - Opportunities: 0 (requires full run)

⏱️  Total time: 15.3s
```

### 3. 启动Web仪表板

```bash
python -m src.dashboard.app
```

**预期输出**:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on

✅ Dashboard ready! Open http://127.0.0.1:5000 in your browser
```

---

## 访问仪表板

打开浏览器访问 `http://127.0.0.1:5000`

### 可用页面

| 页面 | 路径 | 说明 | 对应User Story |
|------|------|------|----------------|
| **首页** | `/` | 系统概览和快速导航 | - |
| **AI工具榜** | `/tools` | 显示≥30条最新AI工具（FR-011） | User Story 1 (P1) |
| **热点榜** | `/trends` | 显示≥30条热点话题（FR-012） | User Story 2 (P1) |
| **机会榜** | `/opportunities` | 显示Top 10产品机会（FR-013） | User Story 3 (P1) |
| **API文档** | `/api/docs` | Swagger UI（基于contracts/api_spec.yaml） | - |

### 功能测试清单

- [ ] AI工具榜页面在3秒内加载（SC-003）
- [ ] 可以按来源筛选（Futurepedia/ProductHunt）
- [ ] 显示中日双语摘要
- [ ] 点击工具卡片查看详情
- [ ] 热点榜按热度排序
- [ ] 机会榜显示MVP建议

---

## 完整数据流程运行

测试成功后，运行完整的数据处理流程：

```bash
# 1. 数据抓取（所有数据源）
python -m src.cli.main scrape

# 2. 数据去重和规范化
python -m src.cli.main normalize

# 3. 痛点提取
python -m src.cli.main extract-pain-points

# 4. 相关性匹配
python -m src.cli.main match

# 5. 评分和排序
python -m src.cli.main score

# 6. 生成中日双语摘要
python -m src.cli.main summarize

# 7. 生成latest.json
python -m src.cli.main export

# 或使用一键命令运行所有步骤
make run-pipeline
```

**预期完整运行时间**: 10-20分钟（取决于API响应速度）

---

## 设置定时任务（可选）

### Linux/macOS（cron）

```bash
# 编辑crontab
crontab -e

# 添加以下行（每天早上7:30运行数据抓取，8:00发送邮件）
30 7 * * * cd /path/to/ai-tool-hotspot-dashboard && /path/to/venv/bin/python -m src.cli.main run-pipeline >> logs/cron.log 2>&1
0 8 * * * cd /path/to/ai-tool-hotspot-dashboard && /path/to/venv/bin/python -m src.cli.main send-email >> logs/email.log 2>&1
```

### Windows（Task Scheduler）

1. 打开"任务计划程序"（Task Scheduler）
2. 创建基本任务 > 命名"AI Dashboard Daily Scrape"
3. 触发器：每天7:30 AM
4. 操作：启动程序
   - 程序/脚本：`C:\path\to\venv\Scripts\python.exe`
   - 参数：`-m src.cli.main run-pipeline`
   - 起始于：`C:\path\to\ai-tool-hotspot-dashboard`

---

## 故障排除

### 问题1: `ModuleNotFoundError: No module named 'src'`

**原因**: 未激活虚拟环境或未安装依赖

**解决**:
```bash
# 确保虚拟环境已激活
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 重新安装依赖
pip install -r requirements.txt
```

---

### 问题2: API请求失败 `AuthenticationError`

**原因**: API密钥无效或未配置

**解决**:
1. 检查 `.env` 文件是否存在并包含正确的API密钥
2. 验证API密钥格式：
   - Claude: `<ANTHROPIC_API_KEY>`
   - OpenAI: `sk-xxxxxxxxxxxxx`
3. 确认API密钥有效（访问API提供商控制台）

---

### 问题3: 邮件发送失败 `SendGridException`

**原因**: SendGrid API密钥无效或未验证发件人邮箱

**解决**:
1. 登录SendGrid控制台
2. 在"Settings > Sender Authentication"验证发件人邮箱
3. 确认API Key权限包含"Mail Send"
4. 检查 `.env` 中 `EMAIL_FROM` 与SendGrid验证的邮箱一致

---

### 问题4: 爬虫失败 `RateLimitExceeded`

**原因**: 超过数据源的速率限制

**解决**:
1. 检查 `.env` 中 `SCRAPER_RATE_LIMIT` 设置（默认1.0秒/请求）
2. 增加延迟：`SCRAPER_RATE_LIMIT=2.0`
3. 查看 `logs/scraper.log` 了解具体错误
4. 部分数据源可能需要更高的延迟（如Google Trends建议3-5秒）

---

### 问题5: 仪表板加载慢（>3秒）

**原因**: 数据量大或数据库查询未优化

**解决**:
1. 检查 `data/latest.json` 文件大小（应<10MB）
2. 运行数据库优化：`python -m src.cli.main optimize-db`
3. 启用分页（前端默认每页30条）
4. 清理7天前的历史数据：`python -m src.cli.main cleanup --days 7`

---

### 问题6: Playwright浏览器下载失败

**原因**: 网络问题或权限不足

**解决**:
```bash
# 手动安装Playwright浏览器（仅需Chromium）
playwright install chromium

# 如果在中国大陆，使用国内镜像
PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/ playwright install chromium
```

---

## 下一步

恭喜！您已成功运行AI工具与热点机会发现仪表板。以下是进阶操作建议：

### 1. 自定义评分权重

根据您的业务需求调整评分权重（`.env`）：
```bash
# 如果您更关注变现潜力，增加Monetization权重
SCORE_WEIGHT_MONETIZATION=0.5
SCORE_WEIGHT_PAIN_CLARITY=0.3
```

### 2. 添加自定义数据源

参考 `src/scrapers/base.py` 创建新的爬虫模块：
```bash
# 创建新爬虫
cp src/scrapers/ai_tools/futurepedia.py src/scrapers/ai_tools/your_source.py

# 编辑并实现 scrape() 和 normalize() 方法

# 在 src/pipeline/orchestrator.py 注册新数据源
```

### 3. 优化LLM提示词

编辑 `src/llm/summarizer.py` 中的prompt模板以优化摘要质量：
```python
SUMMARY_PROMPT_CN = """
请用简洁的中文（≤200字符）总结以下内容：
{description}

要求：
- 突出核心功能和价值主张
- 使用通俗易懂的语言
- 避免营销术语
"""
```

### 4. 部署到生产环境

参考 `docs/deployment.md`（Phase 2将生成），了解：
- Docker容器化部署
- Nginx反向代理配置
- HTTPS证书设置
- 生产环境监控（Prometheus + Grafana）

### 5. 探索API

访问 `http://127.0.0.1:5000/api/docs` 查看完整API文档，集成到您的工具链：
```bash
# 示例：通过API获取Top 10机会
curl http://127.0.0.1:5000/api/v1/opportunities?per_page=10&sort_by=opportunity_score
```

---

## 相关文档

- **[Data Model](./data-model.md)**: 了解所有实体的详细定义
- **[API Specification](./contracts/api_spec.yaml)**: REST API完整规范
- **[Research Report](./research.md)**: 技术选型决策依据
- **[Implementation Plan](./plan.md)**: 系统架构和项目结构

---

## 获取帮助

遇到问题？以下资源可能有帮助：

1. **查看日志**: `logs/scraper.log`, `logs/app.log`, `logs/email.log`
2. **运行测试**: `pytest tests/ -v` 验证系统完整性
3. **提交Issue**: [GitHub Issues](https://github.com/yourproject/issues)
4. **宪法原则**: `.specify/memory/constitution.md` 了解设计理念

---

**祝您使用愉快！🚀**

如果这个quickstart帮到了您，请给项目一个⭐️ Star！
