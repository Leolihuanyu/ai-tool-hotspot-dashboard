#!/bin/bash
# 测试 send-email --use-db 命令（不实际发送邮件）

echo "======================================"
echo "测试 send-email --use-db 功能"
echo "======================================"
echo ""

# 激活虚拟环境
source venv/bin/activate

echo "1. 测试从数据库读取订阅者（--use-db）"
echo "--------------------------------------"
echo "注意：由于未配置SMTP，将会在验证阶段失败，但应该能看到成功读取订阅者"
echo ""

# 运行命令（预期会在SMTP验证阶段失败，但能看到订阅者读取成功）
python -m src.cli.main send-email --use-db 2>&1 | head -20

echo ""
echo "======================================"
echo "如果看到 '✅ Found X active subscribers' 则说明功能正常"
echo "======================================"
