.PHONY: help install scrape reproduce run-pipeline clean test lint format

help:  ## 显示帮助信息
	@echo "可用命令："
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## 安装依赖
	pip install -r requirements.txt
	@echo "✅ 依赖安装完成"

init-db:  ## 初始化数据库
	python -m src.cli.main init-db
	@echo "✅ 数据库初始化完成"

scrape:  ## 运行数据抓取
	python -m src.cli.main scrape

scrape-test:  ## 运行测试模式数据抓取（仅5条记录）
	python -m src.cli.main scrape --test-mode --limit 5

run-pipeline:  ## 运行完整数据处理流程
	python -m src.cli.main run-pipeline

reproduce:  ## 重新处理最新数据（用于调试评分逻辑）
	python -m src.cli.main reproduce

send-email:  ## 发送每日报告邮件
	python -m src.cli.main send-email

run-dashboard:  ## 启动Web仪表板
	python -m src.dashboard.app

test:  ## 运行测试
	pytest tests/ -v

test-cov:  ## 运行测试并生成覆盖率报告
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

lint:  ## 运行代码检查
	flake8 src/ tests/ --max-line-length=120
	mypy src/

format:  ## 格式化代码
	black src/ tests/ --line-length=120

clean:  ## 清理临时文件
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .mypy_cache
	@echo "✅ 清理完成"

clean-data:  ## 清理旧数据（保留最近7天）
	python -m src.cli.main cleanup --days 7

optimize-db:  ## 优化数据库
	python -m src.cli.main optimize-db

setup-schedule:  ## 配置定时任务（交互式）
	./scripts/setup_schedule.sh

test-schedule:  ## 测试定时任务脚本
	./scripts/run_daily_pipeline.sh
