# ⏰ 定时任务快速开始指南

5分钟配置自动定时运行 + 邮件通知！

## 🚀 快速配置（推荐）

### 方法A：一键自动配置

```bash
# 运行自动配置脚本
make setup-schedule

# 或
./scripts/setup_schedule.sh
```

脚本会引导你完成所有配置！

### 方法B：手动配置3步

#### 1. 配置邮件（编辑 `.env`）

**使用Gmail（推荐）：**
```bash
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=<SMTP_PASSWORD>  # 从Google生成
EMAIL_FROM=your-email@gmail.com
EMAIL_TO_LIST=recipient@example.com
```

> **获取Gmail应用密码：**
> 1. 开启两步验证：https://myaccount.google.com/security
> 2. 生成应用密码：https://myaccount.google.com/apppasswords
> 3. 复制16位密码（无空格）

#### 2. 安装定时任务

**macOS（推荐launchd）：**
```bash
# 复制配置文件
cp scripts/com.aitools.dashboard.daily.plist ~/Library/LaunchAgents/

# 加载任务（每天8:00自动运行）
launchctl load ~/Library/LaunchAgents/com.aitools.dashboard.daily.plist
```

**或使用cron：**
```bash
# 编辑crontab
crontab -e

# 添加以下行（每天8:00执行）
0 8 * * * /Users/ri/Projects/ai-tool-hotspot-dashboard/scripts/run_daily_pipeline.sh >> /Users/ri/Projects/ai-tool-hotspot-dashboard/logs/cron/cron.log 2>&1
```

#### 3. 测试运行

```bash
# 测试邮件配置
make send-email

# 测试完整脚本
make test-schedule

# 或立即执行launchd任务
launchctl start com.aitools.dashboard.daily
```

## ✅ 验证配置

### 检查launchd任务状态

```bash
# 查看任务是否加载
launchctl list | grep com.aitools.dashboard.daily

# 应该显示类似：
# -    0    com.aitools.dashboard.daily
```

### 查看日志

```bash
# 查看最新日志
ls -lt logs/cron/ | head -5

# 实时查看launchd日志
tail -f logs/cron/launchd_stdout.log
```

### 测试邮件

```bash
# 运行邮件测试
python -c "
from src.email.sender import get_email_sender
sender = get_email_sender()
is_valid, missing = sender.validate_config()
if is_valid:
    print('✓ 邮件配置正确')
else:
    print(f'✗ 缺少配置: {missing}')
"
```

## 📋 常用命令

### launchd命令

```bash
# 查看任务状态
launchctl list | grep com.aitools.dashboard.daily

# 立即执行任务（测试用）
launchctl start com.aitools.dashboard.daily

# 卸载任务
launchctl unload ~/Library/LaunchAgents/com.aitools.dashboard.daily.plist

# 重新加载任务（修改配置后）
launchctl unload ~/Library/LaunchAgents/com.aitools.dashboard.daily.plist
launchctl load ~/Library/LaunchAgents/com.aitools.dashboard.daily.plist
```

### cron命令

```bash
# 查看当前任务
crontab -l

# 编辑任务
crontab -e

# 删除所有任务
crontab -r
```

## ⏰ 修改执行时间

### launchd方式

编辑 `~/Library/LaunchAgents/com.aitools.dashboard.daily.plist`：

```xml
<!-- 修改执行时间为下午6点 -->
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>18</integer>  <!-- 修改这里 -->
    <key>Minute</key>
    <integer>0</integer>
</dict>
```

重新加载：
```bash
launchctl unload ~/Library/LaunchAgents/com.aitools.dashboard.daily.plist
launchctl load ~/Library/LaunchAgents/com.aitools.dashboard.daily.plist
```

### cron方式

执行 `crontab -e`，修改时间：

```cron
# 每天18:00执行
0 18 * * * /path/to/run_daily_pipeline.sh

# 每天8:00和18:00执行（一天两次）
0 8,18 * * * /path/to/run_daily_pipeline.sh

# 每小时执行
0 * * * * /path/to/run_daily_pipeline.sh
```

## 🔧 故障排查

### 问题：任务没有执行

**检查步骤：**

1. 确认任务已加载：
```bash
launchctl list | grep com.aitools.dashboard.daily
```

2. 查看错误日志：
```bash
tail -50 logs/cron/launchd_stderr.log
```

3. 检查脚本权限：
```bash
ls -l scripts/run_daily_pipeline.sh
# 应该显示 -rwxr-xr-x
```

### 问题：邮件发送失败

**检查步骤：**

1. 验证环境变量：
```bash
grep EMAIL .env
```

2. 测试SMTP连接：
```bash
python -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
print('✓ SMTP连接成功')
server.quit()
"
```

3. 检查Gmail设置：
   - 确认已开启两步验证
   - 使用应用专用密码（非Gmail密码）
   - 密码为16位无空格字符

### 问题：找不到Python模块

确保在脚本中使用了虚拟环境：

```bash
# 检查run_daily_pipeline.sh中是否有这行
source venv/bin/activate
```

## 📧 邮件提供商配置

### Gmail（推荐）

```bash
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=<SMTP_PASSWORD>  # 16位应用密码
```

### Outlook/Hotmail

```bash
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USERNAME=your-email@outlook.com
SMTP_PASSWORD=<SMTP_PASSWORD>
```

### QQ邮箱

```bash
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.qq.com
SMTP_PORT=465  # 或587
SMTP_USERNAME=your-email@qq.com
SMTP_PASSWORD=your-授权码  # QQ邮箱授权码
```

### SendGrid（专业）

```bash
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxx
EMAIL_FROM=noreply@yourdomain.com
```

## 📖 更多文档

- 完整配置指南：[SCHEDULING_GUIDE.md](./SCHEDULING_GUIDE.md)
- 项目README：[../README.md](../README.md)
- 邮件模板：[../src/email/templates/](../src/email/templates/)

## 💡 提示

- 日志会自动保留30天，无需手动清理
- 支持发送到多个邮箱（用逗号分隔）
- 可以随时通过 `launchctl start` 立即执行任务测试
- 如遇问题，先查看日志：`tail -f logs/cron/launchd_stdout.log`

---

有问题？查看[完整故障排查指南](./SCHEDULING_GUIDE.md#故障排查)
