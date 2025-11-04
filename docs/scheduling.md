# 定时任务调度配置

本文档说明如何设置定时任务,以实现每日自动数据抓取和邮件报告发送。

---

## 推荐调度时间

根据功能需求FR-014,推荐以下调度安排:

| 任务 | 推荐时间 | 说明 |
|------|---------|------|
| **数据抓取** | 每天 07:30 | 抓取最新数据,预计耗时10-20分钟 |
| **邮件发送** | 每天 08:00 | 发送Top 10机会报告,预计耗时<1分钟 |

**时间间隔原因**: 留出30分钟确保数据抓取和处理完成,避免邮件发送时数据尚未就绪。

---

## Linux/macOS 配置(cron)

### 1. 编辑crontab

```bash
crontab -e
```

### 2. 添加定时任务

将以下内容添加到crontab文件中(根据实际路径修改):

```bash
# AI工具热点仪表板 - 每日数据抓取和邮件发送
#
# 注意: 使用绝对路径,确保环境变量正确加载

# 项目路径
PROJECT_DIR=/path/to/ai-tool-hotspot-dashboard
VENV_PYTHON=/path/to/ai-tool-hotspot-dashboard/venv/bin/python

# 每天早上7:30 - 运行完整数据处理流程
30 7 * * * cd $PROJECT_DIR && $VENV_PYTHON -m src.cli.main run-pipeline >> logs/cron.log 2>&1

# 每天早上8:00 - 发送每日机会报告邮件
0 8 * * * cd $PROJECT_DIR && $VENV_PYTHON -m src.cli.main send-email --dashboard-url https://your-dashboard-url.com >> logs/email.log 2>&1
```

### 3. 获取绝对路径

**查找项目路径**:
```bash
cd /path/to/ai-tool-hotspot-dashboard
pwd
# 输出示例: /Users/username/Projects/ai-tool-hotspot-dashboard
```

**查找venv Python路径**:
```bash
which python  # 在激活虚拟环境后运行
# 输出示例: /Users/username/Projects/ai-tool-hotspot-dashboard/venv/bin/python
```

### 4. 验证crontab配置

```bash
# 列出当前的crontab任务
crontab -l

# 检查cron日志(macOS)
tail -f /var/log/system.log | grep cron

# 检查cron日志(Linux)
tail -f /var/log/syslog | grep CRON
```

### 5. 手动测试调度命令

在添加到crontab之前,建议手动运行以验证命令正确:

```bash
cd /path/to/ai-tool-hotspot-dashboard
source venv/bin/activate
python -m src.cli.main run-pipeline
python -m src.cli.main send-email
```

---

## Windows 配置(Task Scheduler)

### 1. 打开任务计划程序

- 按 `Win + R`,输入 `taskschd.msc`,按回车
- 或搜索"任务计划程序"(Task Scheduler)

### 2. 创建数据抓取任务

1. 点击右侧"创建基本任务"(Create Basic Task)
2. 填写任务信息:
   - **名称**: `AI Dashboard - Daily Scrape`
   - **描述**: `每日数据抓取和处理流程`
3. 触发器设置:
   - 选择"每天"(Daily)
   - 开始时间: `07:30:00`
   - 重复间隔: `每 1 天`
4. 操作设置:
   - 选择"启动程序"(Start a program)
   - **程序/脚本**: `C:\path\to\ai-tool-hotspot-dashboard\venv\Scripts\python.exe`
   - **参数**: `-m src.cli.main run-pipeline`
   - **起始于**: `C:\path\to\ai-tool-hotspot-dashboard`
5. 完成设置

### 3. 创建邮件发送任务

重复上述步骤,但修改:
- **名称**: `AI Dashboard - Daily Email`
- **描述**: `每日机会报告邮件发送`
- **开始时间**: `08:00:00`
- **参数**: `-m src.cli.main send-email --dashboard-url https://your-dashboard-url.com`

### 4. 配置日志输出(可选)

为了捕获输出日志,可以创建批处理脚本:

**scrape.bat**:
```batch
@echo off
cd C:\path\to\ai-tool-hotspot-dashboard
venv\Scripts\python.exe -m src.cli.main run-pipeline >> logs\cron.log 2>&1
```

**send_email.bat**:
```batch
@echo off
cd C:\path\to\ai-tool-hotspot-dashboard
venv\Scripts\python.exe -m src.cli.main send-email --dashboard-url https://your-dashboard-url.com >> logs\email.log 2>&1
```

然后在任务计划程序中,将"程序/脚本"设置为这些bat文件的路径。

### 5. 验证任务

- 在任务计划程序库中,右键点击创建的任务
- 选择"运行"(Run)手动测试
- 查看"历史记录"(History)标签页检查执行状态

---

## Docker环境配置

如果项目运行在Docker容器中,可以在容器内使用cron:

### 1. Dockerfile添加cron

```dockerfile
FROM python:3.10-slim

# 安装cron
RUN apt-get update && apt-get install -y cron

# 复制crontab配置
COPY crontab /etc/cron.d/ai-dashboard-cron
RUN chmod 0644 /etc/cron.d/ai-dashboard-cron
RUN crontab /etc/cron.d/ai-dashboard-cron

# 其他项目配置...
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt

# 启动cron服务和Flask应用
CMD cron && python -m src.dashboard.app
```

### 2. 创建crontab文件

**crontab**:
```cron
30 7 * * * cd /app && /usr/local/bin/python -m src.cli.main run-pipeline >> /app/logs/cron.log 2>&1
0 8 * * * cd /app && /usr/local/bin/python -m src.cli.main send-email >> /app/logs/email.log 2>&1
```

---

## 监控和调试

### 查看日志

**数据抓取日志**:
```bash
tail -f logs/cron.log
```

**邮件发送日志**:
```bash
tail -f logs/email.log
```

**应用日志**:
```bash
tail -f logs/app.log
```

### 常见问题排查

#### 问题1: cron任务未执行

**原因**: cron守护进程未运行或crontab语法错误

**解决方案**:
```bash
# 检查cron服务状态(Linux)
sudo systemctl status cron

# 启动cron服务
sudo systemctl start cron

# 验证crontab语法
crontab -l
```

---

#### 问题2: 任务执行但无输出/失败

**原因**: 环境变量未加载或路径错误

**解决方案**:
1. 在crontab中添加环境变量:
```cron
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
```

2. 使用绝对路径:
```cron
30 7 * * * cd /full/path && /full/path/venv/bin/python -m src.cli.main run-pipeline
```

3. 在脚本中手动设置环境:
```bash
#!/bin/bash
source /path/to/venv/bin/activate
export $(cat /path/to/.env | xargs)
python -m src.cli.main run-pipeline
```

---

#### 问题3: 邮件发送失败

**原因**: .env文件未加载或API密钥失效

**解决方案**:
1. 确认.env文件路径正确:
```bash
ls -la /path/to/ai-tool-hotspot-dashboard/.env
```

2. 验证SendGrid API密钥:
```bash
# 手动运行邮件发送命令
cd /path/to/ai-tool-hotspot-dashboard
source venv/bin/activate
python -m src.cli.main send-email
```

3. 检查邮件日志:
```bash
cat logs/email.log
```

---

#### 问题4: 数据文件锁定冲突

**原因**: 多个任务同时访问data/latest.json

**解决方案**:
调整调度时间,确保足够间隔:
```cron
# 增加间隔时间
30 7 * * * run-pipeline
5 8 * * * send-email  # 从8:00改为8:05
```

---

## 告警和监控

### 1. 邮件发送失败告警

如果邮件发送失败,系统会自动发送告警邮件给管理员(默认为EMAIL_FROM配置的邮箱)。

禁用告警:
```bash
python -m src.cli.main send-email --no-alert
```

### 2. 外部监控服务(可选)

推荐使用以下服务监控定时任务:

**Healthchecks.io**:
```bash
# 在crontab命令末尾添加ping
30 7 * * * cd $PROJECT_DIR && $VENV_PYTHON -m src.cli.main run-pipeline && curl -fsS https://hc-ping.com/your-uuid-here
```

**Cronitor**:
```bash
# 使用cronitor CLI包装命令
30 7 * * * cronitor exec your-monitor-key -- cd $PROJECT_DIR && $VENV_PYTHON -m src.cli.main run-pipeline
```

---

## 最佳实践

1. **使用绝对路径**: cron环境的PATH变量可能与交互式shell不同
2. **重定向输出**: 始终将stdout和stderr重定向到日志文件(`>> logs/xxx.log 2>&1`)
3. **日志轮转**: 定期清理旧日志,避免磁盘空间占满
4. **测试before部署**: 手动运行命令验证后再添加到crontab
5. **监控失败**: 配置邮件告警或使用外部监控服务
6. **时区注意**: 确认服务器时区与预期一致(`date`命令查看)

---

## 时区配置

### 查看当前时区

```bash
date
# 输出示例: Sun Nov  3 08:00:00 JST 2025
```

### 修改时区(Linux)

```bash
# 列出所有时区
timedatectl list-timezones

# 设置时区(示例: 东京)
sudo timedatectl set-timezone Asia/Tokyo

# 设置时区(示例: 纽约)
sudo timedatectl set-timezone America/New_York
```

### 修改时区(macOS)

系统偏好设置 > 日期与时间 > 时区

---

## 下一步

配置完成后:

1. ✅ 验证第一次自动运行结果
2. ✅ 检查日志文件确认无错误
3. ✅ 确认邮件正常送达
4. 📊 监控系统运行状态(可选:设置Healthchecks.io)

---

## 参考资料

- [Cron表达式生成器](https://crontab.guru/)
- [Linux cron文档](https://man7.org/linux/man-pages/man8/cron.8.html)
- [Windows Task Scheduler文档](https://learn.microsoft.com/en-us/windows/win32/taskschd/task-scheduler-start-page)
- [SendGrid API文档](https://docs.sendgrid.com/api-reference/how-to-use-the-sendgrid-v3-api/authentication)

---

**注意**: 调度配置涉及系统级操作,请根据实际部署环境调整。如有疑问,请参考操作系统官方文档或咨询系统管理员。
