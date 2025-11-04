#!/bin/bash

################################################################################
# AI Tool Hotspot Dashboard - 每日定时任务脚本
#
# 功能：
# 1. 运行完整Pipeline抓取数据
# 2. 生成并发送每日邮件报告
# 3. 记录运行日志
#
# 使用方法：
#   chmod +x scripts/run_daily_pipeline.sh
#   ./scripts/run_daily_pipeline.sh
################################################################################

# 错误时退出
set -e

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 切换到项目根目录
cd "$PROJECT_ROOT"

# 日志目录
LOG_DIR="$PROJECT_ROOT/logs/cron"
mkdir -p "$LOG_DIR"

# 日志文件
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_FILE="$LOG_DIR/daily_run_${TIMESTAMP}.log"

# 开始记录日志
echo "================================================" | tee -a "$LOG_FILE"
echo "AI Tool Hotspot Dashboard - 每日任务" | tee -a "$LOG_FILE"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "================================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 激活虚拟环境
echo ">>> 激活虚拟环境..." | tee -a "$LOG_FILE"
if [ -d "$PROJECT_ROOT/venv" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
    echo "✓ 虚拟环境激活成功" | tee -a "$LOG_FILE"
else
    echo "✗ 虚拟环境不存在: $PROJECT_ROOT/venv" | tee -a "$LOG_FILE"
    exit 1
fi

# 运行Pipeline
echo "" | tee -a "$LOG_FILE"
echo ">>> 运行Pipeline..." | tee -a "$LOG_FILE"
if python -m src.cli.main run-pipeline >> "$LOG_FILE" 2>&1; then
    echo "✓ Pipeline运行成功" | tee -a "$LOG_FILE"
    PIPELINE_SUCCESS=true
else
    echo "✗ Pipeline运行失败" | tee -a "$LOG_FILE"
    PIPELINE_SUCCESS=false
fi

# 发送邮件报告
echo "" | tee -a "$LOG_FILE"
echo ">>> 发送邮件报告..." | tee -a "$LOG_FILE"

if [ "$PIPELINE_SUCCESS" = true ]; then
    if python -m src.cli.main send-email >> "$LOG_FILE" 2>&1; then
        echo "✓ 邮件发送成功" | tee -a "$LOG_FILE"
        EMAIL_SUCCESS=true
    else
        echo "✗ 邮件发送失败" | tee -a "$LOG_FILE"
        EMAIL_SUCCESS=false
    fi
else
    echo "⊘ 跳过邮件发送（Pipeline失败）" | tee -a "$LOG_FILE"
    EMAIL_SUCCESS=false
fi

# 任务总结
echo "" | tee -a "$LOG_FILE"
echo "================================================" | tee -a "$LOG_FILE"
echo "任务完成时间: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "Pipeline状态: $( [ "$PIPELINE_SUCCESS" = true ] && echo "✓ 成功" || echo "✗ 失败" )" | tee -a "$LOG_FILE"
echo "邮件发送状态: $( [ "$EMAIL_SUCCESS" = true ] && echo "✓ 成功" || echo "✗ 失败" )" | tee -a "$LOG_FILE"
echo "完整日志: $LOG_FILE" | tee -a "$LOG_FILE"
echo "================================================" | tee -a "$LOG_FILE"

# 清理旧日志（保留最近30天）
echo "" | tee -a "$LOG_FILE"
echo ">>> 清理旧日志..." | tee -a "$LOG_FILE"
find "$LOG_DIR" -name "daily_run_*.log" -mtime +30 -delete 2>/dev/null || true
echo "✓ 旧日志已清理（保留30天）" | tee -a "$LOG_FILE"

# 退出码
if [ "$PIPELINE_SUCCESS" = true ] && [ "$EMAIL_SUCCESS" = true ]; then
    exit 0
elif [ "$PIPELINE_SUCCESS" = true ]; then
    exit 2  # Pipeline成功但邮件失败
else
    exit 1  # Pipeline失败
fi
