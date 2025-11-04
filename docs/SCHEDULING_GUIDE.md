# 定时任务配置指南

本指南说明如何配置自动定时运行Pipeline并发送邮件报告。

## 📋 目录

- [环境准备](#环境准备)
- [方案一：launchd（macOS推荐）](#方案一launchd-macos推荐)
- [方案二：cron（跨平台）](#方案二cron-跨平台)
- [邮件配置](#邮件配置)
- [测试验证](#测试验证)
- [故障排查](#故障排查)

---

## 环境准备

### 1. 确认环境变量配置

编辑 `.env` 文件，确保以下配置正确：

```bash
# 邮件提供商（sendgrid 或 smtp）
EMAIL_PROVIDER=smtp

# SMTP配置（如果使用smtp）
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com
EMAIL_TO_LIST=recipient1@example.com,recipient2@example.com

# SendGrid配置（如果使用sendgrid）
# SENDGRID_API_KEY=your-sendgrid-api-key
# EMAIL_FROM=noreply@yourdomain.com
# EMAIL_TO_LIST=recipient1@example.com,recipient2@example.com
```

### 2. Gmail SMTP配置（推荐）

如果使用Gmail发送邮件：

1. 开启两步验证：https://myaccount.google.com/security
2. 生成应用专用密码：https://myaccount.google.com/apppasswords
3. 将应用密码填入 `SMTP_PASSWORD`

### 3. 创建日志目录

```bash
mkdir -p logs/cron
```

---

## 方案一：launchd（macOS推荐）

launchd是macOS系统推荐的任务调度工具，比cron更可靠。

### 1. 编辑plist文件

确认 `scripts/com.aitools.dashboard.daily.plist` 中的路径正确：

```xml
<!-- 脚本路径 -->
<key>Program</key>
<string>/Users/ri/Projects/ai-tool-hotspot-dashboard/scripts/run_daily_pipeline.sh</string>

<!-- 工作目录 -->
<key>WorkingDirectory</key>
<string>/Users/ri/Projects/ai-tool-hotspot-dashboard</string>
```

### 2. 修改执行时间

默认为每天早上8:00，如需修改：

```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>8</integer>  <!-- 修改这里 -->
    <key>Minute</key>
    <integer>0</integer>
</dict>
```

### 3. 安装launchd任务

```bash
# 复制plist到LaunchAgents目录
cp scripts/com.aitools.dashboard.daily.plist ~/Library/LaunchAgents/

# 加载任务
launchctl load ~/Library/LaunchAgents/com.aitools.dashboard.daily.plist

# 查看任务状态
launchctl list | grep com.aitools.dashboard.daily
```

### 4. launchd常用命令

```bash
# 查看任务列表
launchctl list | grep com.aitools

# 卸载任务
launchctl unload ~/Library/LaunchAgents/com.aitools.dashboard.daily.plist

# 重新加载任务（修改配置后）
launchctl unload ~/Library/LaunchAgents/com.aitools.dashboard.daily.plist
launchctl load ~/Library/LaunchAgents/com.aitools.dashboard.daily.plist

# 立即执行任务（测试用）
launchctl start com.aitools.dashboard.daily

# 查看日志
tail -f logs/cron/launchd_stdout.log
tail -f logs/cron/launchd_stderr.log
```

---

## 方案二：cron（跨平台）

如果不使用launchd，可以使用传统的cron。

### 1. 编辑crontab

```bash
# 打开crontab编辑器
crontab -e
```

### 2. 添加定时任务

复制以下内容（修改路径为实际路径）：

```cron
# 每天早上8:00执行
0 8 * * * /Users/ri/Projects/ai-tool-hotspot-dashboard/scripts/run_daily_pipeline.sh >> /Users/ri/Projects/ai-tool-hotspot-dashboard/logs/cron/cron.log 2>&1
```

### 3. 其他时间选项

```cron
# 每天中午12:00执行
0 12 * * * /path/to/run_daily_pipeline.sh

# 每天早上8:00和下午18:00执行
0 8,18 * * * /path/to/run_daily_pipeline.sh

# 每周一早上8:00执行
0 8 * * 1 /path/to/run_daily_pipeline.sh

# 每小时执行一次
0 * * * * /path/to/run_daily_pipeline.sh
```

### 4. cron常用命令

```bash
# 查看当前cron任务
crontab -l

# 编辑cron任务
crontab -e

# 删除所有cron任务
crontab -r

# 查看cron日志
tail -f logs/cron/cron.log
```

---

## 邮件配置

### 选项A：使用Gmail SMTP（推荐）

**.env配置：**
```bash
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-16-digit-app-password
EMAIL_FROM=your-email@gmail.com
EMAIL_TO_LIST=recipient1@example.com,recipient2@example.com
```

### 选项B：使用SendGrid API

**.env配置：**
```bash
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxx
EMAIL_FROM=noreply@yourdomain.com
EMAIL_TO_LIST=recipient1@example.com,recipient2@example.com
```

**SendGrid设置：**
1. 注册SendGrid账号：https://sendgrid.com/
2. 创建API Key：Settings → API Keys
3. 验证发件人域名：Settings → Sender Authentication

### 选项C：使用其他SMTP服务

**.env配置示例：**
```bash
EMAIL_PROVIDER=smtp

# Outlook/Hotmail
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587

# QQ邮箱
SMTP_HOST=smtp.qq.com
SMTP_PORT=465  # 或587

# 163邮箱
SMTP_HOST=smtp.163.com
SMTP_PORT=465
```

---

## 测试验证

### 1. 手动测试脚本

```bash
# 直接运行脚本
./scripts/run_daily_pipeline.sh

# 检查日志
ls -lh logs/cron/
```

### 2. 测试邮件发送

```bash
# 测试邮件配置
python -m src.cli.main send-email

# 或使用测试脚本
python -c "
from src.email.sender import get_email_sender
sender = get_email_sender()
is_valid, missing = sender.validate_config()
print(f'配置有效: {is_valid}')
if not is_valid:
    print(f'缺失配置: {missing}')
"
```

### 3. 测试launchd任务

```bash
# 立即执行任务
launchctl start com.aitools.dashboard.daily

# 查看日志
tail -f logs/cron/launchd_stdout.log

# 检查执行状态
launchctl list | grep com.aitools.dashboard.daily
```

---

## 故障排查

### 问题1：launchd任务未执行

**检查步骤：**

1. 查看任务是否加载：
```bash
launchctl list | grep com.aitools.dashboard.daily
```

2. 检查plist文件权限：
```bash
ls -l ~/Library/LaunchAgents/com.aitools.dashboard.daily.plist
```

3. 查看系统日志：
```bash
log show --predicate 'eventMessage contains "com.aitools.dashboard.daily"' --last 1h
```

4. 检查脚本权限：
```bash
ls -l scripts/run_daily_pipeline.sh
# 应该显示 -rwxr-xr-x
```

### 问题2：邮件发送失败

**检查步骤：**

1. 验证邮件配置：
```bash
python -c "
from src.utils.config import config
print(f'EMAIL_PROVIDER: {config.email_provider}')
print(f'SMTP_HOST: {config.smtp_host}')
print(f'EMAIL_FROM: {config.email_from}')
print(f'EMAIL_TO_LIST: {config.email_to_list}')
"
```

2. 测试SMTP连接：
```bash
python -c "
import smtplib
from src.utils.config import config
try:
    server = smtplib.SMTP(config.smtp_host, config.smtp_port)
    server.starttls()
    server.login(config.smtp_username, config.smtp_password)
    print('✓ SMTP连接成功')
    server.quit()
except Exception as e:
    print(f'✗ SMTP连接失败: {e}')
"
```

3. 检查Gmail应用密码：
   - 确认已开启两步验证
   - 应用密码是16位无空格的字符串
   - 不要使用Gmail账号密码

### 问题3：Pipeline运行失败

**检查步骤：**

1. 查看详细日志：
```bash
tail -100 logs/cron/daily_run_*.log | less
```

2. 检查虚拟环境：
```bash
source venv/bin/activate
python -c "import sys; print(sys.executable)"
```

3. 手动运行Pipeline：
```bash
source venv/bin/activate
python -m src.cli.main run-pipeline
```

### 问题4：权限问题

```bash
# 修复脚本权限
chmod +x scripts/run_daily_pipeline.sh

# 修复日志目录权限
chmod -R 755 logs/cron
```

---

## 日志管理

### 日志文件位置

```
logs/cron/
├── daily_run_2025-11-03_08-00-00.log  # 脚本运行日志
├── launchd_stdout.log                 # launchd标准输出
├── launchd_stderr.log                 # launchd错误输出
└── cron.log                           # cron日志（如使用cron）
```

### 自动清理

脚本会自动清理30天前的日志文件。可修改脚本中的清理天数：

```bash
# 在 run_daily_pipeline.sh 中修改
find "$LOG_DIR" -name "daily_run_*.log" -mtime +30 -delete
#                                                 ^^^ 修改这里
```

---

## 监控建议

### 1. 设置失败告警

在 `.env` 中配置管理员邮箱，当任务失败时接收告警：

```bash
ADMIN_EMAIL=admin@example.com
```

### 2. 定期检查日志

```bash
# 查看最近的运行日志
ls -lt logs/cron/daily_run_*.log | head -5

# 检查是否有错误
grep -i error logs/cron/daily_run_*.log
```

### 3. 监控磁盘空间

```bash
# 检查data目录大小
du -sh data/

# 检查日志目录大小
du -sh logs/
```

---

## 常见问题

**Q: 能否一天执行多次？**

A: 可以。在launchd plist中添加多个 `StartCalendarInterval`，或在crontab中添加多行。

**Q: 如何暂停定时任务？**

A:
- launchd: `launchctl unload ~/Library/LaunchAgents/com.aitools.dashboard.daily.plist`
- cron: `crontab -e` 然后注释掉对应行（添加#）

**Q: 可以发送到多个邮箱吗？**

A: 可以，在 `EMAIL_TO_LIST` 中用逗号分隔多个邮箱。

**Q: 邮件中没有数据？**

A: 确保Pipeline成功运行并生成了 `data/latest.json` 文件。

---

## 更多帮助

- 查看项目README: [README.md](../README.md)
- 查看邮件模板: [src/email/templates/](../src/email/templates/)
- 提交Issue: [GitHub Issues](https://github.com/yourrepo/issues)
