# AI Tool Hotspot Dashboard 部署指南

本文档提供完整的免费部署方案，让您可以随时随地访问Dashboard。

## 📋 目录

1. [部署架构概览](#部署架构概览)
2. [前置准备](#前置准备)
3. [步骤1：配置GitHub Secrets](#步骤1配置github-secrets)
4. [步骤2：部署到Render.com](#步骤2部署到rendercom)
5. [步骤3：验证部署](#步骤3验证部署)
6. [步骤4：配置自定义域名（可选）](#步骤4配置自定义域名可选)
7. [常见问题](#常见问题)
8. [成本分析](#成本分析)

---

## 部署架构概览

```
┌─────────────────────────────────────────────────────────┐
│                   完全免费部署架构                        │
└─────────────────────────────────────────────────────────┘

┌─────────────────┐
│  GitHub Actions │  ← 每天UTC 00:00自动运行
│   (免费2000分钟/月) │
└────────┬────────┘
         │
         ├── 1. 数据抓取 (AI工具 + 热点趋势)
         ├── 2. 痛点提取 (LLM分析)
         ├── 3. 机会匹配 (评分算法)
         ├── 4. 生成报告 (JSON + 邮件)
         │
         ▼
┌─────────────────┐
│  GitHub仓库      │  ← 数据存储和版本控制
│  (data/latest.json) │
└────────┬────────┘
         │
         │ 读取数据
         ▼
┌─────────────────┐
│  Render.com     │  ← Flask Dashboard托管
│  (免费750小时/月) │  ← 自动HTTPS + 全球CDN
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   用户浏览器     │  ← https://your-app.onrender.com
│  (随时随地访问)  │
└─────────────────┘

         │
         ▼ (可选)
┌─────────────────┐
│  Gmail SMTP     │  ← 每日邮件报告
│  (免费)          │
└─────────────────┘
```

**关键特性：**
- ✅ **完全免费** - 无需信用卡
- ✅ **自动化** - GitHub Actions每天自动运行
- ✅ **持久化** - 数据存储在GitHub（带版本历史）
- ✅ **全球访问** - Render提供HTTPS和CDN
- ✅ **零维护** - 无需管理服务器

---

## 前置准备

### 必需项

1. **GitHub账号**
   - 免费账号即可
   - 已创建本项目仓库

2. **Render.com账号**
   - 访问：https://render.com
   - 使用GitHub账号注册（推荐）
   - **无需信用卡**

3. **LLM API密钥**（二选一）
   - **OpenAI API** (推荐，价格更低)
     - 注册：https://platform.openai.com
     - 创建API Key：https://platform.openai.com/api-keys
     - 成本：~$0.50/天（gpt-3.5-turbo）

   - **Anthropic Claude API**
     - 注册：https://console.anthropic.com
     - 创建API Key
     - 成本：~$0.30/天（claude-haiku）

### 可选项

4. **邮件服务**（用于每日报告）
   - **Gmail** (推荐，免费)
     - 需要开启"两步验证"
     - 生成"应用专用密码"
     - 教程：https://support.google.com/accounts/answer/185833

   - 或使用QQ邮箱/163邮箱/iCloud邮箱

5. **API Keys**（提升数据质量）
   - **Reddit API** (推荐)
     - 注册：https://www.reddit.com/prefs/apps
     - 创建"script"类型应用

   - **GitHub Token** (推荐)
     - 生成：https://github.com/settings/tokens
     - 权限：`public_repo`, `read:discussion`

   - **YouTube API** (可选)
     - 申请：https://console.cloud.google.com

---

## 步骤1：配置GitHub Secrets

### 1.1 访问Secrets设置

1. 打开GitHub仓库
2. 点击 **Settings** → **Secrets and variables** → **Actions**
3. 点击 **New repository secret**

### 1.2 添加必需的Secrets

#### LLM配置（必需）

**如果使用OpenAI：**

| Name | Value | 说明 |
|------|-------|------|
| `OPENAI_API_KEY` | `sk-proj-...` | OpenAI API密钥 |
| `LLM_PROVIDER` | `openai` | 使用OpenAI |
| `LLM_MODEL` | `gpt-3.5-turbo` | 模型名称 |

**如果使用Claude：**

| Name | Value | 说明 |
|------|-------|------|
| `ANTHROPIC_API_KEY` | `sk-ant-api03-...` | Claude API密钥 |
| `LLM_PROVIDER` | `claude` | 使用Claude |
| `LLM_MODEL` | `claude-haiku-3-20240307` | 模型名称 |

### 1.3 添加邮件配置（可选）

**如果使用Gmail：**

| Name | Value | 示例 |
|------|-------|------|
| `EMAIL_PROVIDER` | `smtp` | 使用SMTP |
| `SMTP_SERVER` | `smtp.gmail.com` | Gmail SMTP服务器 |
| `SMTP_PORT` | `587` | 端口 |
| `SMTP_USERNAME` | `your-email@gmail.com` | 您的Gmail地址 |
| `SMTP_PASSWORD` | `abcd efgh ijkl mnop` | 应用专用密码（16位） |
| `EMAIL_FROM` | `your-email@gmail.com` | 发件人地址 |
| `EMAIL_TO_LIST` | `recipient1@example.com,recipient2@example.com` | 收件人列表（逗号分隔） |

**如果使用SendGrid：**

| Name | Value | 说明 |
|------|-------|------|
| `EMAIL_PROVIDER` | `sendgrid` | 使用SendGrid |
| `SENDGRID_API_KEY` | `SG.xxx...` | SendGrid API密钥 |
| `EMAIL_FROM` | `your-email@example.com` | 发件人地址 |
| `EMAIL_TO_LIST` | `recipient1@example.com` | 收件人列表 |

### 1.4 添加API Keys（可选，提升数据质量）

| Name | Value | 说明 |
|------|-------|------|
| `REDDIT_CLIENT_ID` | `xxx` | Reddit应用ID |
| `REDDIT_CLIENT_SECRET` | `xxx` | Reddit应用密钥 |
| `GH_PAT` | `ghp_xxx` | GitHub Personal Access Token |
| `YOUTUBE_API_KEY` | `AIza...` | YouTube Data API密钥 |

### 1.5 添加Dashboard URL（可选，用于健康检查）

部署到Render后，回来添加这个Secret：

| Name | Value | 示例 |
|------|-------|------|
| `DASHBOARD_URL` | `https://your-app-name.onrender.com` | Render提供的URL |

---

## 步骤2：部署到Render.com

### 2.1 创建Web Service

1. 访问 https://dashboard.render.com
2. 点击 **New +** → **Web Service**
3. 选择 **Build and deploy from a Git repository** → **Next**

### 2.2 连接GitHub仓库

1. 点击 **Connect account** 连接GitHub
2. 授权Render访问仓库
3. 选择 `ai-tool-hotspot-dashboard` 仓库
4. 点击 **Connect**

### 2.3 配置Service

Render会自动检测到 `render.yaml`，您可以直接使用默认配置，或手动设置：

| 配置项 | 值 | 说明 |
|--------|-----|------|
| **Name** | `ai-tool-hotspot-dashboard` | 服务名称（会成为URL的一部分） |
| **Region** | `Singapore` 或 `Oregon` | 选择离您最近的区域 |
| **Branch** | `main` | 部署的分支 |
| **Runtime** | `Docker` | 使用Docker部署 |
| **Instance Type** | `Free` | 免费计划 |

### 2.4 配置环境变量（在Render Dashboard）

在Render的Environment设置中添加以下环境变量：

**必需配置：**

| Key | Value | 说明 |
|-----|-------|------|
| `LLM_PROVIDER` | `openai` 或 `claude` | 从GitHub Secrets复制 |
| `LLM_MODEL` | `gpt-3.5-turbo` 等 | 从GitHub Secrets复制 |
| `OPENAI_API_KEY` | `sk-proj-...` | 从GitHub Secrets复制 |
| `FLASK_ENV` | `production` | 生产环境 |
| `FLASK_DEBUG` | `false` | 关闭调试模式 |

**可选配置（邮件）：**

将GitHub Secrets中的邮件配置复制到这里。

**爬虫配置（使用默认值）：**

Render会从 `render.yaml` 读取默认配置，无需手动添加。

### 2.5 部署

1. 点击 **Create Web Service**
2. Render开始构建Docker镜像（约3-5分钟）
3. 构建完成后自动部署

### 2.6 获取Dashboard URL

部署成功后，您会看到：

```
✓ Your service is live at https://ai-tool-hotspot-dashboard-xxx.onrender.com
```

复制这个URL，您就可以随时访问Dashboard了！

---

## 步骤3：验证部署

### 3.1 测试Dashboard

1. 访问您的Dashboard URL
2. 首次访问可能需要等待10-30秒（冷启动）
3. 应该看到Dashboard界面

**如果看到"请等待GitHub Actions运行数据抓取任务"：**
- 这是正常的，因为还没有数据
- 继续下一步手动触发数据抓取

### 3.2 手动触发数据抓取

1. 访问GitHub仓库
2. 点击 **Actions** 标签
3. 选择 **每日数据抓取** workflow
4. 点击 **Run workflow** → **Run workflow**
5. 等待workflow完成（约10-15分钟）

### 3.3 验证数据更新

workflow完成后：

1. 检查仓库的 `data/` 目录
2. 应该看到 `latest.json` 和 `archive/YYYY-MM-DD.json`
3. 刷新Dashboard，应该能看到数据

### 3.4 健康检查

访问 `https://your-app.onrender.com/health`

应该返回：

```json
{
  "status": "ok",
  "timestamp": "2024-01-15T08:00:00Z"
}
```

---

## 步骤4：配置自定义域名（可选）

### 4.1 在Render添加自定义域名

1. 在Service页面，点击 **Settings**
2. 滚动到 **Custom Domain**
3. 点击 **Add Custom Domain**
4. 输入您的域名，例如：`dashboard.yourdomain.com`
5. Render会提供CNAME记录

### 4.2 配置DNS

在您的域名DNS设置中添加CNAME记录：

| Type | Name | Value |
|------|------|-------|
| CNAME | `dashboard` | `ai-tool-hotspot-dashboard-xxx.onrender.com` |

### 4.3 等待生效

- DNS传播需要几分钟到几小时
- Render会自动配置Let's Encrypt SSL证书
- 完成后访问：`https://dashboard.yourdomain.com`

---

## 常见问题

### Q1: Dashboard打开很慢？

**A:** Render免费计划会在15分钟无活动后休眠。首次访问需要10-30秒冷启动。

**解决方案：**
- 启用 `.github/workflows/health-check.yml` workflow
- 或升级到Render付费计划（$7/月）

### Q2: GitHub Actions失败？

**A:** 检查以下几点：

1. **Secrets配置错误**
   - 确认所有必需的Secrets已正确添加
   - 检查API Key是否有效

2. **LLM API配额不足**
   - 检查OpenAI/Claude账户余额
   - 查看API usage dashboard

3. **爬虫被限流**
   - 某些网站可能临时限流
   - workflow会自动重试，通常能恢复

### Q3: 邮件发送失败？

**A:** Gmail用户常见问题：

1. **未开启"两步验证"**
   - 必须先开启两步验证
   - 然后才能生成应用专用密码

2. **使用了账户密码而非应用专用密码**
   - 必须使用16位应用专用密码
   - 不是您的Gmail登录密码

3. **SMTP端口被阻止**
   - 确认使用587端口（TLS）
   - 或使用465端口（SSL）

### Q4: 数据不更新？

**A:** 检查GitHub Actions：

1. 访问 **Actions** 标签
2. 查看最近的workflow运行
3. 如果失败，点击查看日志

**常见原因：**
- API Key过期或无效
- LLM账户余额不足
- 某个爬虫失败（通常不影响其他爬虫）

### Q5: 能否不用GitHub Actions，直接在Render定时运行？

**A:** Render免费计划不支持Cron Jobs。

**替代方案：**
- 使用GitHub Actions（推荐，免费且稳定）
- 使用外部Cron服务（如cron-job.org）触发webhook
- 升级到Render付费计划

### Q6: 数据存储在哪里？

**A:** 数据存储策略：

1. **主要存储：GitHub仓库**
   - `data/latest.json` - 最新数据
   - `data/archive/` - 历史归档
   - 优点：免费、带版本控制、永久保存

2. **临时存储：Render容器**
   - `data/db.sqlite` - SQLite数据库
   - 注意：免费计划容器重启后丢失
   - 不影响Dashboard（读取GitHub的JSON）

### Q7: 如何禁用某个爬虫？

**A:** 在GitHub Secrets或Render环境变量中设置：

```
ENABLE_SCRAPER_THERESANAI=false
```

可配置的爬虫：
- `ENABLE_SCRAPER_FUTUREPEDIA`
- `ENABLE_SCRAPER_PRODUCTHUNT`
- `ENABLE_SCRAPER_THERESANAI`
- `ENABLE_SCRAPER_REDDIT`
- `ENABLE_SCRAPER_HACKERNEWS`
- `ENABLE_SCRAPER_GITHUB`
- `ENABLE_SCRAPER_TIKTOK`
- `ENABLE_SCRAPER_YOUTUBE`
- `ENABLE_SCRAPER_X_TWITTER`
- `ENABLE_SCRAPER_GOOGLE_TRENDS`

### Q8: 如何查看运行成本？

**A:** 成本监控：

1. **GitHub Actions**
   - 访问：Settings → Billing
   - 免费：2000分钟/月
   - 本项目约消耗：30分钟/天 = 900分钟/月

2. **OpenAI API**
   - 访问：https://platform.openai.com/usage
   - 预估：$0.50/天 = $15/月

3. **Render**
   - 访问：Dashboard → Usage
   - 免费：750小时/月（足够使用）

---

## 成本分析

### 完全免费方案

| 服务 | 成本 | 限制 |
|------|------|------|
| GitHub Actions | $0/月 | 2000分钟/月 |
| Render Dashboard | $0/月 | 750小时/月，可休眠 |
| GitHub存储 | $0/月 | 1GB免费 |
| **总计** | **$0/月** | 只需支付LLM API费用 |

### LLM API成本（唯一付费项）

| 提供商 | 模型 | 成本/天 | 成本/月 |
|--------|------|---------|---------|
| OpenAI | gpt-3.5-turbo | ~$0.50 | ~$15 |
| OpenAI | gpt-4o-mini | ~$0.30 | ~$9 |
| Anthropic | claude-haiku | ~$0.30 | ~$9 |

**降低LLM成本的方法：**
1. 使用Claude Batch API（节省50%）
2. 减少每日运行次数
3. 禁用不必要的爬虫
4. 使用更便宜的模型

### 可选升级

如果需要更好的性能：

| 服务 | 升级成本 | 获得 |
|------|----------|------|
| Render Starter | $7/月 | 永不休眠、更多资源 |
| Render Pro | $25/月 | 持久化存储、更高性能 |

**推荐策略：**
- 先使用完全免费方案
- 如果Dashboard休眠影响体验，升级Render
- 总成本：$7/月（Render）+ $9/月（LLM）= $16/月

---

## 下一步

✅ 部署完成！现在您可以：

1. **访问Dashboard** - 随时随地查看AI工具和热点趋势
2. **接收邮件报告** - 每天早上8点（如果配置了邮件）
3. **监控GitHub Actions** - 查看每日数据抓取状态
4. **查看历史数据** - `data/archive/` 目录

**推荐阅读：**
- [ARCHITECTURE.md](./ARCHITECTURE.md) - 了解系统架构
- [README.md](../README.md) - 项目概览
- [constitution.md](../specs/constitution.md) - 项目原则

**需要帮助？**
- 提交Issue：https://github.com/your-username/ai-tool-hotspot-dashboard/issues
- 查看GitHub Actions日志
- 查看Render部署日志

---

**祝您使用愉快！** 🎉
