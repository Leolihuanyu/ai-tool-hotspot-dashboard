#!/bin/bash
# AI Tool Hotspot Dashboard 启动脚本
# 用于Render.com和其他Docker容器环境

set -e  # 遇到错误立即退出

echo "=========================================="
echo "AI Tool Hotspot Dashboard 正在启动..."
echo "=========================================="

# 1. 创建必要的目录
echo "[1/4] 创建数据目录..."
mkdir -p data/archive
echo "✓ 数据目录已创建"

# 2. 初始化数据库（如果不存在）
if [ ! -f "data/db.sqlite" ]; then
    echo "[2/4] 初始化数据库..."
    python -m src.cli.main init-db
    echo "✓ 数据库初始化完成"
else
    echo "[2/4] 数据库已存在，跳过初始化"
fi

# 3. 检查数据文件
if [ ! -f "data/latest.json" ]; then
    echo "[3/4] 未找到数据文件，创建占位文件..."
    echo '{"ai_tools": [], "trending_topics": [], "opportunities": [], "generated_at": "首次启动", "note": "请等待GitHub Actions运行数据抓取任务"}' > data/latest.json
    echo "⚠️  数据文件将由GitHub Actions生成"
else
    echo "[3/4] 数据文件已存在"
    # 显示数据文件生成时间
    GENERATED_AT=$(python -c "import json; print(json.load(open('data/latest.json')).get('generated_at', '未知'))" 2>/dev/null || echo "无法读取")
    echo "   数据生成时间: $GENERATED_AT"
fi

# 4. 启动Flask Dashboard
echo "[4/4] 启动Flask Dashboard..."
echo "=========================================="
echo "Dashboard URL: http://0.0.0.0:5000"
echo "健康检查: http://0.0.0.0:5000/health"
echo "=========================================="

# 生产环境使用gunicorn（如果可用），否则使用Flask内置服务器
if command -v gunicorn &> /dev/null; then
    echo "使用Gunicorn启动（生产模式）..."
    exec gunicorn \
        --bind 0.0.0.0:5000 \
        --workers 2 \
        --timeout 120 \
        --access-logfile - \
        --error-logfile - \
        "src.dashboard.app:app"
else
    echo "使用Flask内置服务器启动（开发模式）..."
    exec python -m src.dashboard.app
fi
