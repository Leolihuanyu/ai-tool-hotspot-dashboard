# 架构说明文档

本文档详细说明AI Tool Hotspot Dashboard的部署架构、数据流和技术选型。

## 📐 整体架构

### 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        免费云端部署架构                           │
└─────────────────────────────────────────────────────────────────┘

用户请求流程：
┌─────────────┐
│   用户浏览器  │
│  (全球访问)  │
└──────┬──────┘
       │ HTTPS
       ▼
┌──────────────────────────────────────┐
│    Render.com (Web Service)          │
│  ┌────────────────────────────────┐  │
│  │  Docker Container (~150MB)     │  │
│  │  ┌──────────────────────────┐  │  │
│  │  │  Gunicorn + Flask App    │  │  │
│  │  │  - 路由: /, /tools,      │  │  │
│  │  │         /trends, /api    │  │  │
│  │  │  - 读取: data/latest.json│  │  │
│  │  │  - 模板渲染 (Jinja2)     │  │  │
│  │  └──────────────────────────┘  │  │
│  └────────────────────────────────┘  │
│  - 自动HTTPS (Let's Encrypt)        │
│  - CDN加速                          │
│  - 健康检查: /health                │
│  - 15分钟无活动后休眠 (免费计划)     │
└──────────┬───────────────────────────┘
           │ 读取数据
           ▼
┌──────────────────────────────────────┐
│    GitHub Repository                 │
│  ┌────────────────────────────────┐  │
│  │  data/latest.json              │  │
│  │  data/archive/YYYY-MM-DD.json  │  │
│  │  data/db.sqlite (可选)         │  │
│  └────────────────────────────────┘  │
│  - 版本控制 (Git history)           │
│  - 免费1GB存储                      │
│  - 全球CDN (jsDelivr, raw.github)  │
└──────────┬───────────────────────────┘
           │ 每日更新
           ▼
┌──────────────────────────────────────┐
│  GitHub Actions (定时任务)           │
│  ┌────────────────────────────────┐  │
│  │  Workflow: daily-scrape.yml    │  │
│  │  触发: Cron (0 0 * * *)        │  │
│  │  ┌──────────────────────────┐  │  │
│  │  │ 1. 数据抓取              │  │  │
│  │  │    - AI工具 (3个源)      │  │  │
│  │  │    - 热点趋势 (7个源)    │  │  │
│  │  │                          │  │  │
│  │  │ 2. LLM分析               │  │  │
│  │  │    - 痛点提取            │  │  │
│  │  │    - 机会匹配            │  │  │
│  │  │                          │  │  │
│  │  │ 3. 数据处理              │  │  │
│  │  │    - 去重                │  │  │
│  │  │    - 评分排序            │  │  │
│  │  │    - JSON导出            │  │  │
│  │  │                          │  │  │
│  │  │ 4. 提交到GitHub          │  │  │
│  │  │    - git add/commit/push │  │  │
│  │  └──────────────────────────┘  │  │
│  └────────────────────────────────┘  │
│  - 免费2000分钟/月                  │
│  - Ubuntu runners                   │
│  - Python 3.10环境                  │
└──────────┬───────────────────────────┘
           │
           ├─→ 调用 OpenAI API (gpt-3.5-turbo)
           ├─→ 或 Anthropic API (claude-haiku)
           │
           └─→ (可选) 发送邮件报告
               └─→ Gmail SMTP / SendGrid

数据源（公开API/RSS，无需认证）：
┌────────────────────────────────────────────────┐
│ AI工具源:                                       │
│  - Futurepedia RSS                             │
│  - ProductHunt GraphQL API / RSS               │
│  - There's an AI (可选，默认禁用)               │
│                                                │
│ 热点趋势源:                                     │
│  - Reddit PRAW API                             │
│  - Hacker News Firebase API                    │
│  - GitHub Discussions GraphQL API              │
│  - TikTok RapidAPI / RSS                       │
│  - YouTube Data API v3                         │
│  - X/Twitter (Nitter RSS)                      │
│  - Google Trends (pytrends)                    │
└────────────────────────────────────────────────┘
```

---

## 🔄 数据流详解

### 1. 数据采集阶段（GitHub Actions）

```
开始 (UTC 00:00, 北京时间08:00)
  │
  ├─→ [步骤1] 环境准备
  │    - checkout代码
  │    - 安装Python 3.10
  │    - 安装依赖（requirements.txt）
  │    - 加载环境变量（Secrets）
  │
  ├─→ [步骤2] 数据抓取（并行执行，10-15分钟）
  │    │
  │    ├─→ AI工具爬虫
  │    │    - Futurepedia: RSS feed → JSON
  │    │    - ProductHunt: GraphQL → JSON
  │    │    - (可选) There's an AI
  │    │
  │    └─→ 热点趋势爬虫
  │         - Reddit: PRAW → 15个子版块 → JSON
  │         - Hacker News: Firebase API → Top Stories
  │         - GitHub: GraphQL → Discussions
  │         - TikTok: RapidAPI/RSS → 热门视频
  │         - YouTube: Official API → 趋势视频
  │         - X/Twitter: Nitter RSS → 话题
  │         - Google Trends: pytrends → 搜索趋势
  │
  ├─→ [步骤3] 数据规范化
  │    - 统一数据格式（Pydantic模型）
  │    - 时间标准化（ISO 8601）
  │    - 文本清理（去除HTML、特殊字符）
  │    - 去重（基于URL/标题/内容hash）
  │
  ├─→ [步骤4] LLM分析（5-10分钟，成本$0.30-0.50）
  │    │
  │    ├─→ 痛点提取
  │    │    - 输入：热点话题文本（标题+描述）
  │    │    - Prompt：提取用户痛点和需求
  │    │    - 输出：结构化痛点列表
  │    │    - 评估：痛点清晰度评分（0-10）
  │    │
  │    └─→ 机会匹配
  │         - 痛点 × AI工具 → 产品机会
  │         - MVP可行性评估
  │         - 市场潜力评分
  │         - 中日双语建议生成
  │
  ├─→ [步骤5] 评分排序
  │    - 综合评分算法（research.md定义）
  │    - Top 10 AI工具
  │    - Top 20 热点话题
  │    - Top 10 产品机会
  │
  ├─→ [步骤6] 数据导出
  │    - 生成 data/latest.json
  │    - 归档到 data/archive/YYYY-MM-DD.json
  │    - 更新 SQLite数据库（可选）
  │
  ├─→ [步骤7] Git提交
  │    - git add data/
  │    - git commit -m "🤖 自动更新数据"
  │    - git push
  │
  └─→ [步骤8] 邮件报告（可选）
       - 生成HTML报告
       - 通过SMTP发送
       - 收件人：EMAIL_TO_LIST
结束
```

### 2. Dashboard展示阶段（Render.com）

```
用户访问 https://your-app.onrender.com
  │
  ├─→ [冷启动检测]
  │    - 如果容器休眠（15分钟无活动）
  │    - 启动容器（10-30秒）
  │    - 加载Flask应用
  │
  ├─→ [路由处理]
  │    │
  │    ├─→ GET /
  │    │    - 读取 data/latest.json
  │    │    - 渲染 index.html
  │    │    - 显示统计概览
  │    │
  │    ├─→ GET /tools
  │    │    - 读取 ai_tools 数组
  │    │    - 渲染 tools.html
  │    │    - 显示Top 10 AI工具
  │    │
  │    ├─→ GET /trends
  │    │    - 读取 trending_topics 数组
  │    │    - 渲染 trends.html
  │    │    - 显示Top 20 热点话题
  │    │
  │    ├─→ GET /opportunities
  │    │    - 读取 opportunities 数组
  │    │    - 渲染 opportunities.html
  │    │    - 显示Top 10 产品机会
  │    │
  │    ├─→ GET /api/v1/tools
  │    │    - 返回JSON格式数据
  │    │    - 支持分页和过滤
  │    │
  │    └─→ GET /health
  │         - 返回 {"status": "ok"}
  │         - 用于健康检查
  │
  └─→ [响应返回]
       - HTML渲染（Jinja2）
       - 或JSON响应（API）
       - GZIP压缩
       - HTTPS加密
```

### 3. 健康检查阶段（可选）

```
GitHub Actions: health-check.yml
触发: 每14分钟 (*/14 * * * *)

执行:
  │
  ├─→ curl https://your-app.onrender.com/health
  │    - 超时: 30秒
  │    - 预期: 200 OK
  │
  ├─→ [结果处理]
  │    ├─→ 200 OK: Dashboard正常运行
  │    ├─→ 超时: 可能正在冷启动（正常）
  │    └─→ 其他错误: 记录日志（不失败）
  │
  └─→ 作用：防止容器休眠，保持快速响应
```

---

## 🏗️ 技术选型

### 后端技术栈

| 技术 | 版本 | 用途 | 选择理由 |
|------|------|------|----------|
| **Python** | 3.10+ | 核心语言 | 丰富的数据处理和LLM库 |
| **Flask** | 3.0+ | Web框架 | 轻量级，适合小型Dashboard |
| **Gunicorn** | 21.2+ | WSGI服务器 | 生产环境标准，多进程 |
| **Pydantic** | 2.5+ | 数据验证 | 类型安全，自动验证 |
| **SQLite** | 3.x | 数据库 | 无需额外服务，适合单机 |
| **Jinja2** | 3.x | 模板引擎 | Flask内置，功能强大 |

### 数据采集技术

| 技术 | 用途 | 优势 |
|------|------|------|
| **requests** | HTTP请求 | 简单易用，支持所有REST API |
| **BeautifulSoup4** | HTML解析 | 灵活的DOM解析 |
| **feedparser** | RSS解析 | 标准化RSS/Atom feed处理 |
| **PRAW** | Reddit API | 官方封装，稳定可靠 |
| **pytrends** | Google Trends | 非官方但成熟稳定 |

**为什么移除Playwright？**
- 10个爬虫中9个使用API/RSS，无需浏览器
- 减少Docker镜像500-1000MB（77-87%）
- 简化依赖，加快构建速度
- 降低资源消耗

### LLM集成

| 提供商 | 模型 | 成本/1K tokens | 用途 |
|--------|------|----------------|------|
| **OpenAI** | gpt-3.5-turbo | $0.0015 | 痛点提取、机会匹配 |
| **OpenAI** | gpt-4o-mini | $0.00015 | 更便宜的替代 |
| **Anthropic** | claude-haiku | $0.00025 | Claude替代方案 |

**Batch API优化：**
- Claude Batch API节省50%成本
- 适合非实时场景（每日运行）
- 配置: `LLM_USE_BATCH_API=true`

### 部署技术

| 平台 | 用途 | 免费额度 | 限制 |
|------|------|----------|------|
| **Render.com** | Web托管 | 750小时/月 | 15分钟无活动休眠 |
| **GitHub Actions** | 定时任务 | 2000分钟/月 | 单任务最长6小时 |
| **GitHub** | 数据存储 | 1GB | 文件<100MB |
| **Docker** | 容器化 | - | 轻量级镜像~150MB |

---

## 📊 数据模型

### JSON Schema (data/latest.json)

```json
{
  "generated_at": "2024-01-15T08:00:00Z",
  "ai_tools": [
    {
      "name": "工具名称",
      "url": "https://example.com",
      "description": "工具描述",
      "category": "类别",
      "pricing": "免费/付费",
      "score": 8.5,
      "source": "Futurepedia",
      "scraped_at": "2024-01-15T08:00:00Z"
    }
  ],
  "trending_topics": [
    {
      "title": "话题标题",
      "url": "https://example.com",
      "content": "话题内容",
      "source": "Reddit",
      "subreddit": "r/MachineLearning",
      "upvotes": 1500,
      "comments": 200,
      "pain_points": ["痛点1", "痛点2"],
      "score": 9.2,
      "scraped_at": "2024-01-15T08:00:00Z"
    }
  ],
  "opportunities": [
    {
      "pain_point": "用户痛点描述",
      "solution": "解决方案",
      "mvp_suggestion_zh": "中文MVP建议",
      "mvp_suggestion_ja": "日文MVP建議",
      "related_tools": ["工具1", "工具2"],
      "market_potential": "high",
      "complexity": "medium",
      "score": 8.8
    }
  ]
}
```

### SQLite Schema

参考 `src/database/schema.sql`:

```sql
-- AI工具表
CREATE TABLE ai_tools (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  url TEXT UNIQUE,
  description TEXT,
  score REAL,
  scraped_at TIMESTAMP
);

-- 热点话题表
CREATE TABLE trending_topics (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  url TEXT UNIQUE,
  content TEXT,
  source TEXT,
  score REAL,
  scraped_at TIMESTAMP
);

-- 产品机会表
CREATE TABLE opportunities (
  id INTEGER PRIMARY KEY,
  pain_point TEXT,
  solution TEXT,
  mvp_suggestion_zh TEXT,
  mvp_suggestion_ja TEXT,
  score REAL,
  created_at TIMESTAMP
);
```

---

## 🔐 安全考虑

### 敏感信息管理

1. **API Keys存储**
   - GitHub Secrets（CI/CD）
   - Render Environment Variables（Web）
   - **绝不**提交到代码仓库

2. **数据隐私**
   - 只抓取公开数据
   - 不存储个人隐私信息
   - 遵守各平台API使用条款

3. **HTTPS加密**
   - Render自动提供SSL证书
   - Let's Encrypt免费证书
   - 强制HTTPS重定向

### 访问控制

- Dashboard是公开的（无需登录）
- API暂无认证（可后续添加）
- GitHub仓库可设为私有

---

## 📈 性能优化

### 1. Docker镜像优化

```dockerfile
# ❌ 优化前: ~1GB
FROM python:3.10
RUN apt-get install -y chromium  # 不需要

# ✅ 优化后: ~150MB
FROM python:3.10-slim
RUN apt-get install -y --no-install-recommends gcc
```

### 2. 数据缓存策略

- **GitHub存储**: 数据文件自带Git缓存
- **Render读取**: 直接读取JSON，无需数据库查询
- **浏览器缓存**: 静态资源设置Cache-Control

### 3. 爬虫优化

- **速率限制**: 1请求/秒（遵守宪法原则）
- **并发控制**: 最多5个并发爬虫
- **重试机制**: 最多3次，指数退避
- **超时设置**: 10秒请求超时

### 4. LLM成本优化

- **批量处理**: 合并相似请求
- **Prompt优化**: 减少token消耗
- **使用Batch API**: Claude节省50%
- **缓存结果**: 避免重复分析

---

## 🚀 扩展性

### 水平扩展

当前架构可轻松扩展：

1. **增加爬虫**
   - 在 `src/scrapers/` 添加新爬虫
   - 实现 `BaseScraper` 接口
   - 配置环境变量开关

2. **多语言支持**
   - 扩展LLM prompt支持更多语言
   - 添加i18n模板

3. **数据库升级**
   - SQLite → PostgreSQL（Render Pro）
   - 支持更大数据量和并发

4. **API增强**
   - 添加认证（JWT）
   - 实现更多端点
   - 支持GraphQL

### 性能扩展

- **Render Starter**: $7/月，永不休眠，更高性能
- **CDN加速**: Cloudflare免费CDN
- **数据库优化**: Redis缓存热数据

---

## 📝 监控和日志

### GitHub Actions日志

- 每次workflow运行的完整日志
- 失败时自动通知
- 30天日志保留

### Render日志

- 实时应用日志
- 访问日志
- 错误追踪

### 推荐工具

- **Sentry**: 错误追踪（免费5000 events/月）
- **LogTail**: 日志聚合（免费1GB/月）
- **UptimeRobot**: 健康监控（免费50个监控）

---

## 🔄 CI/CD流程

```
开发者推送代码到GitHub
  │
  ├─→ [Git Push]
  │    └─→ branch: main
  │
  ├─→ [Render自动部署]
  │    1. 检测到新commit
  │    2. 拉取最新代码
  │    3. 构建Docker镜像
  │    4. 运行健康检查
  │    5. 切换到新容器
  │    6. 关闭旧容器
  │    时间: 3-5分钟
  │
  └─→ [GitHub Actions触发]
       ├─→ 代码检查（可选）
       ├─→ 单元测试（可选）
       └─→ 每日数据抓取（定时）

自动化程度：100%
无需手动操作
```

---

## 📚 相关文档

- [DEPLOYMENT.md](./DEPLOYMENT.md) - 详细部署步骤
- [README.md](../README.md) - 项目概览
- [constitution.md](../specs/constitution.md) - 项目原则
- [research.md](../specs/research.md) - 技术调研

---

**架构设计完成！** 🎉

这个架构：
- ✅ 完全免费（除LLM API）
- ✅ 高度自动化
- ✅ 可扩展
- ✅ 易维护
- ✅ 遵守宪法原则
