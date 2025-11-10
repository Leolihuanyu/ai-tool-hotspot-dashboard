# Beta 用户过期提醒系统 - 部署指南

## 📋 功能概述

实现了完整的 Beta 用户试用期管理系统：

### ✅ 已实现的功能

1. **自动设置试用期**
   - 新注册的 Beta 用户自动获得 60 天试用期
   - 试用期可通过环境变量 `BETA_TRIAL_DAYS` 配置

2. **认证时过期检查**
   - 每次访问时自动检查账户是否过期
   - 过期用户会被拒绝访问，显示升级提示

3. **过期提醒邮件**
   - 14天提醒：温馨提醒 + 统计数据 + 订阅方案
   - 7天提醒：紧迫感提醒 + 限时优惠
   - 1天提醒：最后警告 + 转化激励
   - 支持多语言（中文、英文、日文）

4. **CLI 命令管理**
   - 手动触发过期检查
   - 可选择特定天数的提醒
   - 支持语言选择

5. **完整测试工具**
   - 自动化测试脚本
   - 验证整个过期流程

---

## 🚀 本地测试

### 1. 运行测试脚本

```bash
# 设置数据库连接
export DB_TYPE=postgresql
export DATABASE_URL='your_postgresql_connection_string'

# 运行完整测试
python test_expiry_flow.py
```

测试脚本会：
- ✅ 创建测试用户（14天、7天、1天后过期）
- ✅ 测试认证功能
- ✅ 测试过期提醒邮件发送
- ✅ 验证过期用户认证被拒绝

### 2. 手动测试 CLI 命令

```bash
# 测试 14 天提醒
python -m src.cli.main check-expiry --days 14

# 测试 7 天提醒
python -m src.cli.main check-expiry --days 7

# 测试 1 天提醒
python -m src.cli.main check-expiry --days 1

# 运行完整的每日检查（14天、7天、1天）
python -m src.cli.main check-expiry

# 指定邮件语言
python -m src.cli.main check-expiry --days 14 --language en
```

---

## 📦 部署到 Render.com

### 1. 环境变量配置

在 Render.com Dashboard 添加以下环境变量：

```bash
# 数据库配置（已有）
DB_TYPE=postgresql
DATABASE_URL=your_supabase_connection_string

# Beta 试用期配置（可选，默认60天）
BETA_TRIAL_DAYS=60

# 邮件配置（已有）
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com

# 前端URL（用于邮件中的升级链接）
UPGRADE_URL=https://ai-tool-hotspot-dashboard.vercel.app/upgrade
```

### 2. 部署代码

```bash
# 提交所有更改
git add .
git commit -m "feat: 实现Beta用户过期提醒系统

- 自动为Beta用户设置60天试用期
- 认证时检查账户过期状态
- 添加过期提醒邮件（14/7/1天）
- 创建check-expiry CLI命令
- 支持多语言邮件（zh/en/ja）
"

# 推送到远程仓库
git push origin main
```

Render.com 会自动检测到代码更新并重新部署。

### 3. 验证部署

部署完成后，通过 Render.com Shell 测试：

```bash
# 进入 Render.com Dashboard > Shell

# 测试过期检查命令
python -m src.cli.main check-expiry --days 14
```

---

## ⏰ 配置定时任务（GitHub Actions）

### 创建 `.github/workflows/daily-expiry-check.yml`

```yaml
name: Daily Expiry Check

on:
  schedule:
    # 每天 UTC 01:00 运行（北京时间 09:00）
    - cron: '0 1 * * *'
  workflow_dispatch:  # 允许手动触发

jobs:
  check-expiry:
    runs-on: ubuntu-latest

    steps:
      - name: Trigger Render.com cron job
        run: |
          curl -X POST "${{ secrets.RENDER_CRON_URL }}" \
            -H "Authorization: Bearer ${{ secrets.RENDER_API_KEY }}"
```

### 或者使用 Render.com Cron Jobs

Render.com 支持配置定时任务：

1. 在 Render Dashboard 创建新的 **Cron Job** 服务
2. 连接到同一个 GitHub 仓库
3. 配置运行命令：
   ```bash
   python -m src.cli.main check-expiry
   ```
4. 设置运行频率：每天 UTC 01:00

**推荐配置**：
- **时间**: 每天早上 1:00 UTC（北京时间 9:00 AM）
- **原因**:
  - 避免与每日邮件推送冲突
  - 用户活跃时段发送提醒邮件

---

## 🧪 测试清单

部署前请确认：

### 功能测试
- [ ] 创建新用户时自动设置 60 天 `free_until`
- [ ] 过期用户访问 Dashboard 时被拒绝
- [ ] 14天提醒邮件正常发送
- [ ] 7天提醒邮件正常发送
- [ ] 1天提醒邮件正常发送
- [ ] CLI 命令可以正常运行

### 邮件测试
- [ ] 中文邮件显示正常
- [ ] 英文邮件显示正常
- [ ] 日文邮件显示正常
- [ ] 邮件中的链接有效
- [ ] 邮件样式美观

### 性能测试
- [ ] 处理100+用户时性能正常
- [ ] 数据库查询优化
- [ ] 邮件发送不阻塞主流程

---

## 📊 监控和日志

### 查看运行日志

```bash
# Render.com Dashboard > Logs

# 搜索关键词：
# - "过期提醒" - 查看提醒执行情况
# - "expiry" - 查看英文日志
# - "邮件发送" - 查看邮件发送状态
```

### 关键指标

监控以下指标：
- 每日发送的提醒邮件数量
- 邮件发送失败率
- 过期用户访问尝试次数
- 试用转付费转化率

---

## 🔧 故障排查

### 问题1: 邮件没有发送

**可能原因**：
- SMTP 配置错误
- 邮件服务商限流
- 没有符合条件的用户

**解决方案**：
```bash
# 1. 检查环境变量
echo $SMTP_HOST
echo $SMTP_USERNAME

# 2. 测试邮件发送
python -m src.cli.main send-email --test

# 3. 查看日志
tail -f logs/app.log | grep "expiry"
```

### 问题2: 用户没有设置过期时间

**可能原因**：
- 旧用户数据未迁移
- 创建用户时逻辑错误

**解决方案**：
```sql
-- 为现有Beta用户批量设置过期时间
UPDATE users
SET free_until = created_at + INTERVAL '60 days'
WHERE subscription_type = 'beta'
  AND free_until IS NULL;
```

### 问题3: 定时任务没有运行

**可能原因**：
- Cron Job 配置错误
- Render.com 服务暂停

**解决方案**：
1. 检查 Render.com Cron Job 配置
2. 查看 Cron Job 运行历史
3. 手动触发测试：`python -m src.cli.main check-expiry`

---

## 📈 未来优化建议

### 短期（1-2周）
- [ ] 添加用户统计数据（已发现多少机会、浏览多少工具）
- [ ] 实现邮件发送去重（避免同一用户收到多次提醒）
- [ ] 添加邮件打开率跟踪

### 中期（1个月）
- [ ] 实现自动降级功能（过期后自动标记为 expired）
- [ ] 添加用户语言偏好设置
- [ ] 创建过期用户重新激活流程

### 长期（3个月）
- [ ] A/B测试不同的邮件内容
- [ ] 个性化推荐（基于用户浏览历史）
- [ ] 实现推荐奖励计划（推荐1人获得额外天数）

---

## 🆘 需要帮助？

如有问题，请查看：
- 日志文件: `logs/app.log`
- 测试脚本: `test_expiry_flow.py`
- 代码文档: `src/email/expiry_reminder.py`

或联系开发团队。
