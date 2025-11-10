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

# 2. 初始化数据库（根据DB_TYPE环境变量）
echo "[2/4] 检查数据库配置..."
if [ "${DB_TYPE}" = "postgresql" ]; then
    echo "✓ 使用PostgreSQL数据库 (外部托管)"
    echo "   数据库URL: ${DATABASE_URL:0:50}..."
    echo "   跳过本地数据库初始化"
else
    echo "✓ 使用SQLite数据库 (本地文件)"
    if [ ! -f "data/db.sqlite" ]; then
        echo "   正在初始化SQLite数据库..."
        python -m src.cli.main init-db
        echo "   ✓ 数据库初始化完成"
    else
        echo "   ✓ 数据库文件已存在，跳过初始化"
    fi
fi

# 3. 检查数据文件
if [ -f "data/latest.json" ]; then
    FILE_SIZE=$(stat -f%z "data/latest.json" 2>/dev/null || stat -c%s "data/latest.json" 2>/dev/null || echo "0")
    echo "[3/4] 数据文件已存在 (大小: $FILE_SIZE bytes)"

    # 验证文件不是空的或太小
    if [ "$FILE_SIZE" -lt 100 ]; then
        echo "⚠️  数据文件太小，可能是占位文件"
        echo "   等待GitHub Actions更新数据..."
    else
        # 显示数据文件生成时间和统计信息
        GENERATED_AT=$(python -c "import json; print(json.load(open('data/latest.json')).get('generated_at', '未知'))" 2>/dev/null || echo "无法读取")
        TOOLS_COUNT=$(python -c "import json; print(len(json.load(open('data/latest.json')).get('ai_tools', [])))" 2>/dev/null || echo "0")
        OPPS_COUNT=$(python -c "import json; print(len(json.load(open('data/latest.json')).get('opportunities', [])))" 2>/dev/null || echo "0")
        echo "   ✓ 数据生成时间: $GENERATED_AT"
        echo "   ✓ AI工具数量: $TOOLS_COUNT"
        echo "   ✓ 机会数量: $OPPS_COUNT"
    fi
else
    echo "[3/4] 数据文件不存在"
    echo "⚠️  注意：Dashboard将显示空数据，请等待GitHub Actions运行数据抓取"
    echo "   提示：确保 data/latest.json 已被包含在Git仓库中"
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
