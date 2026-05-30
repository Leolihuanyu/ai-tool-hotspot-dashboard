# Render.com 后端环境变量配置清单

**目标**: 部署 Flask 后端 API 到 Render.com
**日期**: 2025-11-10

---

## 📋 完整环境变量配置

将以下所有环境变量添加到 Render.com > 你的服务 > Environment

### 🔴 **必须修改/添加的** (PostgreSQL迁移)

```ini
# === 核心数据库配置 (最重要!) ===
DB_TYPE=postgresql
DATABASE_URL=<DATABASE_URL>

# === Flask环境 (生产环境配置) ===
FLASK_ENV=production
FLASK_DEBUG=false
FLASK_PORT=5000

# === Dashboard URL (部署后更新) ===
DASHBOARD_BASE_URL=https://你的应用名.onrender.com
```

### ✅ **直接复制的** (从本地.env)

```ini
# === LLM配置 ===
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
OPENAI_API_KEY=从本地.env复制
LLM_USE_BATCH_API=true

# === 邮件服务配置 ===
EMAIL_PROVIDER=smtp
EMAIL_FROM=从本地.env复制
EMAIL_TO_LIST=从本地.env复制
EMAIL_SCHEDULE_CRON=0 8 * * *

# SMTP配置
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=从本地.env复制
SMTP_PASSWORD=从本地.env复制
SMTP_USE_TLS=true

# === JWT认证 ===
JWT_SECRET_KEY=从本地.env复制
TOKEN_EXPIRY_HOURS=24
TOKEN_REQUIRE_IP_MATCH=false

# === Stripe支付 ===
STRIPE_SECRET_KEY=从本地.env复制
STRIPE_PUBLISHABLE_KEY=从本地.env复制
STRIPE_PRICE_ID_MONTHLY=从本地.env复制
STRIPE_PRICE_ID_YEARLY=从本地.env复制
STRIPE_WEBHOOK_SECRET=从本地.env复制

# === API配置 ===
YOUTUBE_API_KEY=从本地.env复制
REDDIT_CLIENT_ID=从本地.env复制
REDDIT_CLIENT_SECRET=从本地.env复制
REDDIT_USER_AGENT=AI-Opportunity-Matcher/1.0
GITHUB_TOKEN=从本地.env复制

# === 数据抓取配置 ===
SCRAPER_RATE_LIMIT=1.0
SCRAPER_MAX_RETRIES=3
SCRAPER_TIMEOUT=10

# === 评分权重配置 ===
SCORE_WEIGHT_PAIN_CLARITY=0.4
SCORE_WEIGHT_MVP_SPEED=0.3
SCORE_WEIGHT_MONETIZATION=0.3
SCORE_WEIGHT_JAPAN_MARKET=0.2
SCORE_WEIGHT_US_EU_MARKET=0.2
SCORE_WEIGHT_TRENDING=0.3

# === 日志配置 ===
LOG_LEVEL=INFO
LOG_FORMAT=json

# === GitHub数据源 ===
GITHUB_DATA_URL=https://raw.githubusercontent.com/Leolihuanyu/ai-tool-hotspot-dashboard/main/data/latest.json
```

---

## 🚫 **需要删除的**

从截图中看到的这些变量,在 Render.com 中**不需要**:

```
DATABASE_PATH  # 删除 - 这是SQLite专用
```

---

## 📝 配置步骤

### 1. 登录 Render.com

访问: https://render.com/

### 2. 创建新的 Web Service

1. 点击 "New" → "Web Service"
2. 连接你的 GitHub 仓库: `Leolihuanyu/ai-tool-hotspot-dashboard`
3. 配置如下:

```yaml
Name: ai-tool-hotspot-api (或自定义)
Region: Singapore (或选择离你最近的)
Branch: main
Root Directory: (留空)
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: gunicorn src.dashboard.app:app
```

### 3. 添加环境变量

在 "Environment" 标签页,添加上面列出的所有环境变量。

**方法1: 手动添加** (一个一个添加)
- 点击 "Add Environment Variable"
- 复制粘贴 Key 和 Value

**方法2: 批量添加** (推荐)
- 点击 "Add from .env"
- 复制粘贴下面的内容 ↓

### 4. 批量导入格式

```ini
DB_TYPE=postgresql
DATABASE_URL=<从Supabase获取的PostgreSQL连接字符串>
FLASK_ENV=production
FLASK_DEBUG=false
FLASK_PORT=5000
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
OPENAI_API_KEY=<从本地.env复制>
LLM_USE_BATCH_API=true
EMAIL_PROVIDER=smtp
EMAIL_FROM=<你的邮箱>
EMAIL_TO_LIST=<接收通知的邮箱>
EMAIL_SCHEDULE_CRON=0 8 * * *
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=<你的SMTP用户名>
SMTP_PASSWORD=<你的SMTP密码>
SMTP_USE_TLS=true
JWT_SECRET_KEY=<从本地.env复制>
TOKEN_EXPIRY_HOURS=24
TOKEN_REQUIRE_IP_MATCH=false
STRIPE_SECRET_KEY=<从本地.env复制>
STRIPE_PUBLISHABLE_KEY=<从本地.env复制>
STRIPE_PRICE_ID_MONTHLY=<从本地.env复制>
STRIPE_PRICE_ID_YEARLY=<从本地.env复制>
STRIPE_WEBHOOK_SECRET=<从本地.env复制>
YOUTUBE_API_KEY=<从本地.env复制>
REDDIT_CLIENT_ID=<从本地.env复制>
REDDIT_CLIENT_SECRET=<从本地.env复制>
REDDIT_USER_AGENT=AI-Opportunity-Matcher/1.0
GITHUB_TOKEN=<从本地.env复制>
SCRAPER_RATE_LIMIT=1.0
SCRAPER_MAX_RETRIES=3
SCRAPER_TIMEOUT=10
SCORE_WEIGHT_PAIN_CLARITY=0.4
SCORE_WEIGHT_MVP_SPEED=0.3
SCORE_WEIGHT_MONETIZATION=0.3
SCORE_WEIGHT_JAPAN_MARKET=0.2
SCORE_WEIGHT_US_EU_MARKET=0.2
SCORE_WEIGHT_TRENDING=0.3
LOG_LEVEL=INFO
LOG_FORMAT=json
GITHUB_DATA_URL=https://raw.githubusercontent.com/Leolihuanyu/ai-tool-hotspot-dashboard/main/data/latest.json
```

### 5. 部署后需要更新的变量

部署成功后,Render会给你一个URL,例如:
```
https://ai-tool-hotspot-api.onrender.com
```

然后回到 Environment 变量,更新:
```ini
DASHBOARD_BASE_URL=https://ai-tool-hotspot-api.onrender.com
```

---

## ⚠️ 重要提示

### 1. Stripe Webhook配置

部署后需要在 Stripe Dashboard 配置 webhook endpoint:

```
Endpoint URL: https://ai-tool-hotspot-api.onrender.com/api/stripe/webhook
Events to send:
  - checkout.session.completed
  - customer.subscription.created
  - customer.subscription.updated
  - customer.subscription.deleted
```

### 2. CORS配置

你的 `src/dashboard/app.py` 已经配置了CORS,允许的源包括:
```python
allowed_origins = [
    "https://ai-tool-hotspot-dashboard.vercel.app",  # Vercel前端
    "https://*.vercel.app",
    "http://localhost:5173",
]
```

如果前端部署在其他域名,需要添加到CORS配置。

### 3. 冷启动优化

Render.com 免费套餐有15分钟不活动自动休眠的特性。可以通过以下方式保持活跃:

**方案A**: 使用 UptimeRobot 每5分钟ping一次健康检查端点
**方案B**: 升级到付费套餐($7/月)

---

## 🔍 验证清单

部署完成后,验证以下端点:

```bash
# 1. 健康检查
curl https://你的应用名.onrender.com/api/health

# 2. 获取数据
curl https://你的应用名.onrender.com/api/opportunities

# 3. 测试邀请码验证
curl -X POST https://你的应用名.onrender.com/api/auth/validate-invite \
  -H "Content-Type: application/json" \
  -d '{"invite_code": "测试码"}'
```

---

## 📦 下一步

完成 Render.com 部署后:

1. ✅ 记录部署的URL
2. ✅ 更新 Vercel 前端的 API_URL 环境变量
3. ✅ 配置 Stripe Webhook
4. ✅ 端到端测试用户注册流程
5. ✅ 生成100个Beta邀请码

---

## 🆘 故障排除

### 部署失败?

1. 检查 Build Logs
2. 确认 `requirements.txt` 包含所有依赖
3. 确认 `gunicorn` 命令正确

### API无法访问?

1. 检查 Service Logs
2. 确认 PostgreSQL 连接字符串正确
3. 测试 Supabase 连接是否正常

### 数据库连接失败?

1. 确认 `DB_TYPE=postgresql`
2. 确认 `DATABASE_URL` 完整且正确
3. 在 Render 控制台测试连接:
   ```bash
   python -c "from src.database.connection import get_connection; print(get_connection())"
   ```
