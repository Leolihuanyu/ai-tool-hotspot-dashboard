#!/bin/bash

################################################################################
# 定时任务快速设置脚本
#
# 自动配置launchd定时任务
################################################################################

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 获取项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "========================================"
echo "AI Tool Hotspot Dashboard"
echo "定时任务快速设置"
echo "========================================"
echo ""

# 1. 检查必要文件
echo ">>> 检查必要文件..."
if [ ! -f "$PROJECT_ROOT/scripts/run_daily_pipeline.sh" ]; then
    echo -e "${RED}✗ 缺少文件: run_daily_pipeline.sh${NC}"
    exit 1
fi

if [ ! -f "$PROJECT_ROOT/scripts/com.aitools.dashboard.daily.plist" ]; then
    echo -e "${RED}✗ 缺少文件: com.aitools.dashboard.daily.plist${NC}"
    exit 1
fi
echo -e "${GREEN}✓ 文件检查通过${NC}"
echo ""

# 2. 设置可执行权限
echo ">>> 设置脚本权限..."
chmod +x "$PROJECT_ROOT/scripts/run_daily_pipeline.sh"
echo -e "${GREEN}✓ 权限设置完成${NC}"
echo ""

# 3. 创建日志目录
echo ">>> 创建日志目录..."
mkdir -p "$PROJECT_ROOT/logs/cron"
echo -e "${GREEN}✓ 日志目录已创建${NC}"
echo ""

# 4. 检查环境配置
echo ">>> 检查环境配置..."
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${YELLOW}⚠ .env文件不存在，将从.env.example创建${NC}"
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        echo -e "${GREEN}✓ .env文件已创建${NC}"
        echo -e "${YELLOW}请编辑.env文件并配置邮件参数${NC}"
    else
        echo -e "${RED}✗ .env.example也不存在${NC}"
    fi
else
    echo -e "${GREEN}✓ .env文件已存在${NC}"
fi
echo ""

# 5. 测试脚本执行（可选）
echo ">>> 是否测试脚本执行？(y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "运行测试..."
    cd "$PROJECT_ROOT"
    if "$PROJECT_ROOT/scripts/run_daily_pipeline.sh"; then
        echo -e "${GREEN}✓ 脚本测试成功${NC}"
    else
        echo -e "${RED}✗ 脚本测试失败${NC}"
        echo "请检查日志: logs/cron/"
        exit 1
    fi
fi
echo ""

# 6. 配置launchd
echo "========================================"
echo "选择定时任务方案："
echo "  1) launchd (macOS推荐)"
echo "  2) cron (跨平台)"
echo "  3) 跳过（手动配置）"
echo "========================================"
read -p "请选择 (1/2/3): " choice

case $choice in
    1)
        echo ""
        echo ">>> 配置launchd..."

        # 复制plist文件
        PLIST_SOURCE="$PROJECT_ROOT/scripts/com.aitools.dashboard.daily.plist"
        PLIST_DEST="$HOME/Library/LaunchAgents/com.aitools.dashboard.daily.plist"

        # 如果已存在，先卸载
        if [ -f "$PLIST_DEST" ]; then
            echo "检测到已存在的任务，先卸载..."
            launchctl unload "$PLIST_DEST" 2>/dev/null || true
        fi

        # 复制并加载
        cp "$PLIST_SOURCE" "$PLIST_DEST"
        launchctl load "$PLIST_DEST"

        echo -e "${GREEN}✓ launchd任务已配置${NC}"
        echo ""
        echo "任务信息："
        echo "  - 执行时间: 每天 08:00"
        echo "  - 任务名称: com.aitools.dashboard.daily"
        echo "  - 日志位置: $PROJECT_ROOT/logs/cron/"
        echo ""
        echo "常用命令："
        echo "  查看状态: launchctl list | grep com.aitools.dashboard.daily"
        echo "  立即执行: launchctl start com.aitools.dashboard.daily"
        echo "  卸载任务: launchctl unload $PLIST_DEST"
        echo "  查看日志: tail -f $PROJECT_ROOT/logs/cron/launchd_stdout.log"
        ;;

    2)
        echo ""
        echo ">>> 配置cron..."
        echo ""
        echo "请将以下行添加到crontab中（执行: crontab -e）："
        echo ""
        echo "0 8 * * * $PROJECT_ROOT/scripts/run_daily_pipeline.sh >> $PROJECT_ROOT/logs/cron/cron.log 2>&1"
        echo ""
        echo "或查看完整示例: $PROJECT_ROOT/scripts/crontab.example"
        ;;

    3)
        echo ""
        echo "跳过自动配置。"
        echo "请参考文档手动配置: docs/SCHEDULING_GUIDE.md"
        ;;

    *)
        echo -e "${RED}无效选择${NC}"
        exit 1
        ;;
esac

echo ""
echo "========================================"
echo -e "${GREEN}✓ 设置完成！${NC}"
echo "========================================"
echo ""
echo "下一步："
echo "  1. 配置邮件参数: vim .env"
echo "  2. 测试邮件发送: python -m src.cli.main send-email"
echo "  3. 查看完整文档: docs/SCHEDULING_GUIDE.md"
echo ""
