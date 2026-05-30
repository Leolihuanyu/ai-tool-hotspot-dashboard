# 🤖 自动化任务总结

## 功能概述

系统会在每天设定的时间自动：
1. ✅ 抓取AI工具、热点话题数据
2. ✅ 分析用户痛点
3. ✅ 生成MVP机会建议
4. ✅ 发送每日邮件报告

**即使电脑关机，系统开机后也会自动执行！**

## 📂 已创建的文件

```
scripts/
├── run_daily_pipeline.sh              # 主执行脚本
├── setup_schedule.sh                  # 一键配置脚本
├── com.aitools.dashboard.daily.plist  # launchd配置
└── crontab.example                    # cron配置示例

docs/
├── SCHEDULING_GUIDE.md                # 完整配置指南
├── QUICK_START_SCHEDULING.md          # 快速开始指南
└── AUTOMATION_SUMMARY.md              # 本文件
```

## 🚀 快速开始

### 3步配置完成

#### 1️⃣ 配置邮件

编辑 `.env` 文件：

```bash
# Gmail配置（推荐）
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=<SMTP_PASSWORD>
EMAIL_FROM=your-email@gmail.com
EMAIL_TO_LIST=recipient1@example.com,recipient2@example.com
```

> **获取Gmail应用密码：** https://myaccount.google.com/apppasswords

#### 2️⃣ 运行自动配置

```bash
make setup-schedule
```

或手动配置：

```bash
# macOS（推荐）
cp scripts/com.aitools.dashboard.daily.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.aitools.dashboard.daily.plist

# 或使用cron
crontab -e
# 添加：0 8 * * * /path/to/run_daily_pipeline.sh
```

#### 3️⃣ 测试验证

```bash
# 测试邮件配置
make send-email

# 测试完整脚本
make test-schedule

# 或立即执行任务
launchctl start com.aitools.dashboard.daily
```

## ⚙️ 系统架构

```
┌─────────────────────────────────────────────────┐
│           launchd / cron 定时触发                │
│                 (每天 08:00)                     │
└─────────────────┬───────────────────────────────┘
                  │
                  v
┌─────────────────────────────────────────────────┐
│      run_daily_pipeline.sh 主脚本                │
│                                                  │
│  1. 激活虚拟环境                                 │
│  2. 运行 Pipeline                                │
│  3. 发送邮件报告                                 │
│  4. 记录日志                                     │
│  5. 清理旧日志（30天）                           │
└─────────────────┬───────────────────────────────┘
                  │
      ┌───────────┴───────────┐
      │                       │
      v                       v
┌────────────┐         ┌──────────────┐
│  Pipeline  │         │  邮件发送     │
│            │         │              │
│ • 数据抓取  │         │ • 生成HTML   │
│ • 规范化    │         │ • SMTP/SendGrid │
│ • 去重      │         │ • 重试机制   │
│ • 筛选      │         └──────────────┘
│ • 痛点提取  │
│ • MVP生成   │
│ • 导出JSON  │
└────────────┘
      │
      v
┌────────────────────────────────┐
│  data/latest.json               │
│  data/archive/2025-11-03.json  │
└────────────────────────────────┘
```

## 📧 邮件报告内容

每天邮件会包含：

1. **Top 10 AI工具**
   - 工具名称和描述
   - 来源和链接
   - 定价模式

2. **Top 20 热点话题**
   - 话题标题
   - 热度分数
   - 数据来源

3. **Top 10 产品机会**
   - 用户痛点描述
   - MVP建议（中文+日文）
   - 机会评分
   - 相关资源

4. **Dashboard链接**
   - 可直接访问完整数据

## 📊 执行日志

### 日志位置

```
logs/cron/
├── daily_run_2025-11-03_08-00-00.log  # 每次运行的完整日志
├── launchd_stdout.log                 # launchd标准输出
├── launchd_stderr.log                 # launchd错误输出
└── cron.log                           # cron日志（如使用cron）
```

### 查看日志

```bash
# 查看最新执行日志
ls -lt logs/cron/daily_run_*.log | head -1

# 实时查看launchd输出
tail -f logs/cron/launchd_stdout.log

# 查看错误
tail -f logs/cron/launchd_stderr.log

# 查看cron日志
tail -f logs/cron/cron.log
```

## 🛠️ 常用操作

### 查看任务状态

```bash
# launchd
launchctl list | grep com.aitools.dashboard.daily

# cron
crontab -l
```

### 立即执行任务

```bash
# launchd
launchctl start com.aitools.dashboard.daily

# 或直接运行脚本
./scripts/run_daily_pipeline.sh

# 或使用Makefile
make test-schedule
```

### 停止/启动任务

```bash
# 停止launchd任务
launchctl unload ~/Library/LaunchAgents/com.aitools.dashboard.daily.plist

# 重新启动
launchctl load ~/Library/LaunchAgents/com.aitools.dashboard.daily.plist

# 停止cron（注释掉crontab中的行）
crontab -e
# 在行首添加 # 注释
```

### 修改执行时间

#### launchd方式

编辑 `~/Library/LaunchAgents/com.aitools.dashboard.daily.plist`：

```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>18</integer>  <!-- 改为18点 -->
    <key>Minute</key>
    <integer>0</integer>
</dict>
```

重新加载：
```bash
launchctl unload ~/Library/LaunchAgents/com.aitools.dashboard.daily.plist
launchctl load ~/Library/LaunchAgents/com.aitools.dashboard.daily.plist
```

#### cron方式

```bash
crontab -e

# 修改时间（例如改为18:00）
0 18 * * * /path/to/run_daily_pipeline.sh
```

## 🔍 监控建议

### 1. 定期检查日志

```bash
# 每周检查一次最近的运行日志
ls -lt logs/cron/daily_run_*.log | head -7

# 查找错误
grep -i error logs/cron/daily_run_*.log
```

### 2. 验证邮件接收

- 检查收件箱是否收到每日报告
- 检查垃圾邮件文件夹
- 验证邮件内容完整性

### 3. 监控数据文件

```bash
# 检查latest.json更新时间
ls -lh data/latest.json

# 检查归档数据
ls -lt data/archive/ | head -10

# 查看数据文件大小
du -sh data/
```

## ⚠️ 注意事项

1. **环境变量**
   - `.env` 文件必须存在且配置正确
   - 不要将 `.env` 提交到Git

2. **网络连接**
   - 确保运行时有网络连接
   - API限流会影响抓取成功率

3. **磁盘空间**
   - 日志会自动清理（保留30天）
   - 归档数据需手动管理

4. **权限问题**
   - 脚本必须有可执行权限（chmod +x）
   - launchd plist文件权限应为644

5. **邮件配额**
   - Gmail每天有发送限额（500封）
   - SendGrid免费版每天100封

## 📚 文档索引

| 文档 | 用途 |
|------|------|
| [QUICK_START_SCHEDULING.md](./QUICK_START_SCHEDULING.md) | 5分钟快速开始 |
| [SCHEDULING_GUIDE.md](./SCHEDULING_GUIDE.md) | 完整配置指南 |
| [AUTOMATION_SUMMARY.md](./AUTOMATION_SUMMARY.md) | 本文档（总结） |

## ❓ 常见问题

**Q: 电脑关机后任务还会执行吗？**

A:
- launchd: 下次开机后会检测并执行错过的任务
- cron: 开机时不会执行错过的任务

**Q: 可以一天执行多次吗？**

A: 可以。在plist中添加多个 `StartCalendarInterval`，或在crontab中添加多行。

**Q: 如何暂停任务？**

A:
- launchd: `launchctl unload ~/Library/LaunchAgents/com.aitools.dashboard.daily.plist`
- cron: `crontab -e` 然后注释掉对应行

**Q: Pipeline失败会影响下次执行吗？**

A: 不会。每次执行都是独立的，失败不会影响下次任务。

**Q: 邮件发送失败怎么办？**

A: 检查：
1. `.env` 配置是否正确
2. Gmail应用密码是否有效
3. 网络连接是否正常
4. 查看 `logs/cron/launchd_stderr.log`

## 🎯 下一步

配置完成后，建议：

1. ✅ 测试手动运行：`make test-schedule`
2. ✅ 验证邮件接收
3. ✅ 等待第一次自动执行
4. ✅ 检查日志确认成功
5. ✅ 设置提醒定期查看邮件报告

---

🎉 **恭喜！你的AI工具热点仪表板已经实现全自动化！**

每天定时抓取数据 → 分析机会 → 发送邮件，无需人工干预。
