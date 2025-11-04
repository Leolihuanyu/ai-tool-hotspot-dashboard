# AI工具与热点机会发现仪表板

自动化数据聚合和分析系统,每日从多个AI工具数据源和大众热点平台抓取数据,通过智能分析生成Top 10产品机会榜单。

## 🆕 2025年重大升级

**从泛化热点 → 高信号痛点！**

我们对数据源进行了重大升级，现在能够获取**真正能反映痛点、有变现机会、可形成MVP灵感的高信号热点**：

✅ **Reddit深度挖掘** - 15个高价值子版块（r/entrepreneur, r/SaaS, r/indiehackers等）
✅ **Hacker News集成** - Ask HN痛点 + Who is Hiring企业需求
✅ **GitHub Discussions** - Top 10开源项目的Feature Requests
✅ **付费意愿识别** - 自动识别"would pay for"等高价值信号
✅ **数据质量提升** - 从每日30条 → 100+条高质量痛点

**预期效果：**
- 信号质量：⭐⭐⭐⭐⭐（HN评分0.95）
- 痛点识别速度：7天 → 24小时内
- 变现路径：自动生成MVP建议 + 竞品分析

👉 **详细说明：** [docs/UPGRADE_2025.md](docs/UPGRADE_2025.md)
👉 **快速测试：** `python test_new_scrapers.py`

---

## 🎯 核心功能

- **AI工具榜**: 每日聚合≥30条最新AI工具信息
- **热点榜**: 追踪TikTok、YouTube、X、Reddit、Google Trends热点话题
- **机会榜**: 智能匹配用户痛点与AI工具,生成Top 10产品机会
- **邮件日报**: 每日自动发送机会报告(含中日双语摘要和MVP建议)
- **历史分析**: 支持查看过去7天/30天的趋势变化

## 🚀 快速开始

### 前置要求

- Python 3.10+
- pip 20.0+
- Git 2.0+

### 安装步骤

```bash
# 1. 克隆仓库
git clone <your-repository-url>
cd ai-tool-hotspot-dashboard
git checkout 001-ai-tool-hotspot-dashboard

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 3. 安装依赖
make install
# 或
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 填写必需的API密钥
```

### 首次运行

```bash
# 初始化数据库
make init-db

# 运行测试模式数据抓取(仅5条记录)
make scrape-test

# 启动Web仪表板
make run-dashboard
# 访问 http://127.0.0.1:5000
```

详细安装和配置指南请参考: [specs/001-ai-tool-hotspot-dashboard/quickstart.md](specs/001-ai-tool-hotspot-dashboard/quickstart.md)

## 📊 技术栈

- **后端**: Python 3.10+, Flask, Gunicorn
- **数据抓取**: Requests, BeautifulSoup4, Feedparser, PRAW (Reddit), pytrends
- **数据验证**: Pydantic
- **LLM**: OpenAI GPT-3.5 / Anthropic Claude Haiku (Batch API)
- **邮件**: SMTP (Gmail) / SendGrid
- **数据库**: SQLite
- **测试**: pytest
- **部署**: Docker, Render.com, GitHub Actions

## 🏗️ 项目结构

```
├── src/
│   ├── models/          # Pydantic数据模型
│   ├── scrapers/        # 数据源爬虫
│   ├── scoring/         # 评分逻辑
│   ├── llm/             # LLM集成
│   ├── dashboard/       # Flask Web仪表板
│   ├── email/           # 邮件报告
│   ├── pipeline/        # 数据处理流程
│   ├── utils/           # 工具函数
│   └── cli/             # 命令行接口
├── tests/               # 测试
├── data/                # 数据存储
├── docs/                # 文档
├── specs/               # 设计规范
└── logs/                # 日志
```

## 🔧 常用命令

```bash
make help              # 显示所有可用命令
make scrape            # 运行数据抓取
make run-pipeline      # 运行完整数据处理流程
make send-email        # 发送每日报告邮件
make test              # 运行测试
make lint              # 运行代码检查
make format            # 格式化代码
```

## 📝 文档

- [实现计划](specs/001-ai-tool-hotspot-dashboard/plan.md) - 系统架构和技术上下文
- [数据模型](specs/001-ai-tool-hotspot-dashboard/data-model.md) - 实体定义和Schema
- [API规范](specs/001-ai-tool-hotspot-dashboard/contracts/api_spec.yaml) - REST API文档
- [研究报告](specs/001-ai-tool-hotspot-dashboard/research.md) - 技术选型决策
- [快速开始](specs/001-ai-tool-hotspot-dashboard/quickstart.md) - 详细安装指南

## 🛡️ 设计原则

本项目遵循6条宪法原则:

1. **数据可靠性**: 指数退避重试、速率限制、原子写入
2. **统一数据模型**: Pydantic验证、Schema版本控制
3. **最小依赖**: .env配置管理、核心依赖最小化
4. **价值驱动评分**: 6维度评分模型(痛点清晰度、MVP速度、变现潜力、市场契合度、趋势分数)
5. **多语言输出**: 中日双语摘要和MVP建议
6. **可重现性**: 结构化日志、历史快照、完整文档

详见: [.specify/memory/constitution.md](.specify/memory/constitution.md)

## 🧪 测试

```bash
# 运行所有测试
make test

# 运行测试并生成覆盖率报告
make test-cov

# 运行特定测试
pytest tests/unit/test_models.py -v
```

## 📦 部署

### 🌐 免费云端部署（推荐）

本项目已配置完整的免费部署方案，无需服务器，无需信用卡！

**部署架构：**
- ☁️ **Render.com** - 托管Flask Dashboard (免费750小时/月)
- 🤖 **GitHub Actions** - 每日自动数据抓取 (免费2000分钟/月)
- 📦 **GitHub** - 数据存储和版本控制
- 📧 **Gmail SMTP** - 邮件报告发送 (免费)

**成本：**
- 平台服务: $0/月
- LLM API: ~$9-15/月 (OpenAI gpt-3.5-turbo 或 Claude Haiku)

**部署步骤：**

1. **配置GitHub Secrets** - 添加API Keys等环境变量
2. **部署到Render.com** - 一键部署，3-5分钟完成
3. **验证部署** - 访问您的Dashboard URL
4. **配置自定义域名** - 可选，支持免费HTTPS

**详细文档：**
- 📖 [完整部署指南](docs/DEPLOYMENT.md) - 含截图步骤和常见问题
- 🏗️ [架构说明](docs/ARCHITECTURE.md) - 技术选型和数据流
- 🚀 [快速开始](docs/DEPLOYMENT.md#步骤2部署到rendercom) - 10分钟上线

**快速链接：**
```bash
# 查看部署文件
├── Dockerfile           # 轻量级镜像 (~150MB)
├── render.yaml          # Render.com配置
├── start.sh             # 启动脚本
├── .github/workflows/   # GitHub Actions
│   ├── daily-scrape.yml     # 每日数据抓取
│   └── health-check.yml     # 保持Dashboard活跃
```

### 🖥️ 本地部署

如果您想在本地服务器部署：

**Docker部署：**
```bash
# 构建镜像
docker build -t ai-tool-dashboard .

# 运行容器
docker run -p 5000:5000 \
  -e OPENAI_API_KEY=your_key \
  -e EMAIL_FROM=your@email.com \
  ai-tool-dashboard
```

**传统部署：**
```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env

# 启动Dashboard
python -m src.dashboard.app
```

**定时任务：**
```bash
# macOS (launchd)
cp scripts/com.ai-dashboard.daily.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.ai-dashboard.daily.plist

# Linux (cron)
crontab -e
# 添加: 0 8 * * * cd /path/to/project && make run-pipeline
```

## 🤝 贡献

欢迎提交Issue和Pull Request!

## 📄 许可证

MIT License

## 🔗 相关链接

- [Claude API文档](https://docs.anthropic.com/)
- [SendGrid文档](https://docs.sendgrid.com/)
- [Flask文档](https://flask.palletsprojects.com/)