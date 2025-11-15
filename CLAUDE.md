# Claude Code 项目配置

## 语言偏好
请使用中文与我对话和交流。所有解释、说明和沟通都应该用中文进行。

## 代码注释
代码中的注释也请使用中文。

## 项目概述
AI工具热点分析Dashboard - 全栈Flask + React应用，用于分析AI工具市场痛点和热点趋势。

## Active Technologies

### 后端 (Python 3.10+)
- **Web框架**: Flask 3.0+ (支持CORS的REST API)
- **数据库**: PostgreSQL + psycopg2-binary (Supabase云数据库) / SQLite (本地开发)
- **数据验证**: Pydantic 2.5+ (类型安全的数据模型)
- **测试框架**: pytest + pytest-cov + pytest-asyncio
- **代码质量**: black (格式化) + flake8 (检查) + mypy (类型检查)
- **WSGI服务器**: gunicorn (生产环境)

### 前端 (Node.js + React)
- **UI框架**: React 19 + React DOM 19
- **路由**: React Router v7
- **构建工具**: Vite 7.1+
- **样式**: TailwindCSS 3.4 + PostCSS
- **国际化**: i18next + react-i18next
- **图表**: Recharts 3.3
- **工具库**: lucide-react (图标), clsx + tailwind-merge (样式工具)

### 集成服务
- **LLM分析**: Anthropic Claude (anthropic >=0.40.0) / OpenAI (openai >=1.0.0)
- **支付**: Stripe 7.0+ (订阅管理)
- **邮件**: SendGrid 6.12+ / SMTP (邮件推送)
- **访问控制**: JWT (JSON Web Tokens)
- **数据抓取**: requests, beautifulsoup4, feedparser, praw (Reddit), pytrends (Google Trends)

### 部署架构
- **后端部署**: Render (Docker容器) / 本地 gunicorn
- **前端部署**: Vercel (自动CI/CD)
- **数据库**: Supabase PostgreSQL (生产) / SQLite (开发)
- **容器化**: Docker + Dockerfile

## 项目结构
```
/
├── src/                    # Python后端源码
│   ├── dashboard/          # Flask应用 (app.py + routes)
│   ├── pipeline/           # 数据处理管道 (爬虫、去重、归档)
│   ├── llm/                # LLM集成 (Claude/OpenAI客户端)
│   ├── database/           # 数据库操作层
│   ├── email/              # 邮件服务 (SendGrid/SMTP)
│   ├── auth/               # JWT认证管理
│   └── utils/              # 工具函数 (config, logger)
├── frontend/               # React前端
│   ├── src/
│   │   ├── components/     # React组件
│   │   ├── hooks/          # 自定义Hooks
│   │   ├── locales/        # i18n翻译文件
│   │   └── lib/            # 工具库
│   ├── package.json
│   └── vite.config.js
├── tests/                  # 测试文件
├── scripts/                # 工具脚本 (数据库初始化、邮件测试等)
├── data/                   # 数据存储 (SQLite数据库、JSON导出)
├── docs/                   # 项目文档
├── requirements.txt        # Python依赖
├── Dockerfile              # Docker镜像构建
├── render.yaml             # Render部署配置
└── .env.example            # 环境变量模板
```

## 开发规范

### Python代码规范
- 所有Python文件必须通过 **black** (格式化) + **flake8** (检查) + **mypy** (类型检查)
- 使用中文注释说明复杂逻辑
- API路由遵循RESTful规范 (`/api/资源名`)
- 使用 Pydantic 模型验证所有输入数据
- 日志使用结构化JSON格式 (src/utils/logger.py)

### React代码规范
- 使用函数式组件 + Hooks (不使用Class组件)
- 组件文件使用 .jsx 扩展名
- 样式使用 TailwindCSS utility classes
- 使用 i18next 实现多语言支持 (中文/英文/日文)

### API设计规范
- 所有API路径以 `/api/` 开头
- 使用标准HTTP状态码 (200成功, 201创建, 400错误请求, 401未授权, 404未找到, 500服务器错误)
- 返回JSON格式数据
- 需要认证的接口使用JWT token (通过 `@require_token` 装饰器)

### 数据库规范
- 开发环境使用 SQLite (`data/dashboard.db`)
- 生产环境使用 PostgreSQL (Supabase)
- 数据库操作使用参数化查询防止SQL注入
- 所有迁移脚本放在 `scripts/` 目录

## 环境变量
关键环境变量 (详见 .env.example):
- `DATABASE_URL` - PostgreSQL连接字符串
- `JWT_SECRET_KEY` - JWT密钥
- `SENDGRID_API_KEY` / `SMTP_*` - 邮件配置
- `STRIPE_SECRET_KEY` - Stripe支付密钥
- `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` - LLM API密钥

## Recent Changes
- 2025-11: 完善 Claude Code 配置，添加完整技术栈描述
- 001-ai-tool-hotspot-dashboard: 初始化Python 3.10+项目结构
