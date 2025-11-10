#!/usr/bin/env python3
"""
实装计划进度追踪工具
用于更新和查看项目实装进度

使用方法：
    python docs/progress_tracker.py status           # 查看当前进度
    python docs/progress_tracker.py complete 1.6     # 标记任务1.6为已完成
    python docs/progress_tracker.py start 1.7        # 标记任务1.7为进行中
    python docs/progress_tracker.py report           # 生成每日进度报告
"""

import json
import os
from datetime import datetime
from pathlib import Path

# 任务定义
TASKS = {
    # Day 1-3: 访问控制系统
    "1.1": {"name": "创建JWT Token管理模块", "priority": "P0", "hours": 3, "status": "completed", "date": "2025-11-07"},
    "1.2": {"name": "扩展数据库schema", "priority": "P0", "hours": 2, "status": "completed", "date": "2025-11-07"},
    "1.3": {"name": "创建用户管理模块", "priority": "P0", "hours": 2, "status": "completed", "date": "2025-11-07"},
    "1.4": {"name": "Flask添加认证中间件", "priority": "P0", "hours": 2, "status": "completed", "date": "2025-11-07"},
    "1.5": {"name": "Flask添加认证路由", "priority": "P0", "hours": 1, "status": "completed", "date": "2025-11-07"},
    "1.6": {"name": "邮件系统生成签名URL", "priority": "P0", "hours": 2, "status": "pending", "date": None},
    "1.7": {"name": "前端token验证逻辑", "priority": "P0", "hours": 3, "status": "pending", "date": None},
    "1.8": {"name": "创建过期提示页面", "priority": "P1", "hours": 2, "status": "pending", "date": None},

    # Day 4-5: 数据质量提升
    "2.1": {"name": "实现数据源分级权重系统", "priority": "P0", "hours": 3, "status": "pending", "date": None},
    "2.2": {"name": "修改评分器集成权重", "priority": "P0", "hours": 2, "status": "pending", "date": None},
    "2.3": {"name": "添加LLM反射过滤机制", "priority": "P0", "hours": 4, "status": "pending", "date": None},
    "2.4": {"name": "实现双层摘要策略", "priority": "P1", "hours": 3, "status": "pending", "date": None},
    "2.5": {"name": "优化去重阈值和规则", "priority": "P1", "hours": 2, "status": "pending", "date": None},

    # Day 6-7: Dashboard功能增强
    "3.1": {"name": "创建搜索与过滤组件", "priority": "P1", "hours": 4, "status": "pending", "date": None},
    "3.2": {"name": "实现历史趋势可视化", "priority": "P2", "hours": 5, "status": "pending", "date": None},
    "3.3": {"name": "移动端响应式优化", "priority": "P1", "hours": 3, "status": "pending", "date": None},

    # Day 8-9: 邀请码系统
    "4.1": {"name": "创建邀请码管理模块", "priority": "P0", "hours": 3, "status": "pending", "date": None},
    "4.2": {"name": "创建CLI邀请码生成工具", "priority": "P0", "hours": 2, "status": "pending", "date": None},
    "4.3": {"name": "实现邀请注册页面", "priority": "P0", "hours": 4, "status": "pending", "date": None},
    "4.4": {"name": "实现推荐奖励逻辑", "priority": "P1", "hours": 3, "status": "pending", "date": None},

    # Day 10-12: Stripe付费集成
    "5.1": {"name": "安装Stripe依赖并配置", "priority": "P0", "hours": 1, "status": "pending", "date": None},
    "5.2": {"name": "创建Stripe订阅处理器", "priority": "P0", "hours": 4, "status": "pending", "date": None},
    "5.3": {"name": "实现Webhook回调处理", "priority": "P0", "hours": 3, "status": "pending", "date": None},
    "5.4": {"name": "创建前端订阅页面", "priority": "P0", "hours": 4, "status": "pending", "date": None},
    "5.5": {"name": "创建Landing Page", "priority": "P1", "hours": 5, "status": "pending", "date": None},
    "5.6": {"name": "测试支付流程", "priority": "P0", "hours": 2, "status": "pending", "date": None},

    # Day 13: 获客渠道搭建
    "6.1": {"name": "实现Twitter自动发布", "priority": "P1", "hours": 3, "status": "pending", "date": None},
    "6.2": {"name": "实现Reddit周报发布", "priority": "P2", "hours": 2, "status": "pending", "date": None},
    "6.3": {"name": "SEO优化和公开周报页", "priority": "P1", "hours": 3, "status": "pending", "date": None},

    # Day 14: 测试与上线
    "7.1": {"name": "端到端测试", "priority": "P0", "hours": 3, "status": "pending", "date": None},
    "7.2": {"name": "性能测试", "priority": "P1", "hours": 2, "status": "pending", "date": None},
    "7.3": {"name": "安全测试", "priority": "P0", "hours": 2, "status": "pending", "date": None},
    "7.4": {"name": "生产环境部署", "priority": "P0", "hours": 2, "status": "pending", "date": None},
    "7.5": {"name": "生成50个Beta邀请码", "priority": "P0", "hours": 1, "status": "pending", "date": None},
    "7.6": {"name": "发送Beta测试邀请", "priority": "P0", "hours": 2, "status": "pending", "date": None},
}

# 状态文件路径
PROGRESS_FILE = Path(__file__).parent / "progress.json"


def load_progress():
    """加载进度数据"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            saved_tasks = json.load(f)
            # 合并保存的进度和默认任务
            for task_id, task_data in saved_tasks.items():
                if task_id in TASKS:
                    TASKS[task_id].update(task_data)
    return TASKS


def save_progress():
    """保存进度数据"""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(TASKS, f, ensure_ascii=False, indent=2)


def show_status():
    """显示当前进度"""
    load_progress()

    # 统计数据
    total = len(TASKS)
    completed = sum(1 for t in TASKS.values() if t['status'] == 'completed')
    in_progress = sum(1 for t in TASKS.values() if t['status'] == 'in_progress')
    pending = sum(1 for t in TASKS.values() if t['status'] == 'pending')

    print("=" * 70)
    print("🚀 AI工具热点Dashboard - 实装进度")
    print("=" * 70)
    print(f"\n📊 总体进度: {completed}/{total} 任务完成 ({completed/total*100:.1f}%)")
    print(f"   ✅ 已完成: {completed}")
    print(f"   🔄 进行中: {in_progress}")
    print(f"   ⏳ 待完成: {pending}\n")

    # 按阶段分组
    phases = {
        "Day 1-3: 访问控制": ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8"],
        "Day 4-5: 数据质量": ["2.1", "2.2", "2.3", "2.4", "2.5"],
        "Day 6-7: Dashboard增强": ["3.1", "3.2", "3.3"],
        "Day 8-9: 邀请码系统": ["4.1", "4.2", "4.3", "4.4"],
        "Day 10-12: Stripe集成": ["5.1", "5.2", "5.3", "5.4", "5.5", "5.6"],
        "Day 13: 获客渠道": ["6.1", "6.2", "6.3"],
        "Day 14: 测试上线": ["7.1", "7.2", "7.3", "7.4", "7.5", "7.6"],
    }

    for phase_name, task_ids in phases.items():
        phase_total = len(task_ids)
        phase_completed = sum(1 for tid in task_ids if TASKS[tid]['status'] == 'completed')
        phase_progress = phase_completed / phase_total * 100

        print(f"\n{phase_name} ({phase_completed}/{phase_total} - {phase_progress:.0f}%)")
        print("-" * 70)

        for task_id in task_ids:
            task = TASKS[task_id]
            status_icon = {
                'completed': '✅',
                'in_progress': '🔄',
                'pending': '⏳'
            }[task['status']]

            priority_color = {
                'P0': '🔴',
                'P1': '🟡',
                'P2': '🟢'
            }[task['priority']]

            date_str = f"({task['date']})" if task['date'] else ""
            print(f"  {status_icon} {task_id} - {task['name']} {priority_color} {task['priority']} {date_str}")

    print("\n" + "=" * 70)


def complete_task(task_id):
    """标记任务为已完成"""
    load_progress()

    if task_id not in TASKS:
        print(f"❌ 错误: 任务 {task_id} 不存在")
        return

    TASKS[task_id]['status'] = 'completed'
    TASKS[task_id]['date'] = datetime.now().strftime("%Y-%m-%d")

    save_progress()
    print(f"✅ 任务 {task_id} - {TASKS[task_id]['name']} 已标记为完成")


def start_task(task_id):
    """标记任务为进行中"""
    load_progress()

    if task_id not in TASKS:
        print(f"❌ 错误: 任务 {task_id} 不存在")
        return

    TASKS[task_id]['status'] = 'in_progress'

    save_progress()
    print(f"🔄 任务 {task_id} - {TASKS[task_id]['name']} 已标记为进行中")


def generate_report():
    """生成每日进度报告"""
    load_progress()

    today = datetime.now().strftime("%Y-%m-%d")
    today_completed = [tid for tid, task in TASKS.items() if task['date'] == today]

    print("=" * 70)
    print(f"📋 每日进度报告 - {today}")
    print("=" * 70)

    print(f"\n✅ 今日完成任务 ({len(today_completed)}个):")
    total_hours = 0
    for task_id in today_completed:
        task = TASKS[task_id]
        total_hours += task['hours']
        print(f"  • {task_id} - {task['name']} ({task['hours']}h)")

    print(f"\n⏱️  今日工作时长: {total_hours}小时")

    # 找出进行中的任务
    in_progress_tasks = [tid for tid, task in TASKS.items() if task['status'] == 'in_progress']
    print(f"\n🔄 进行中任务 ({len(in_progress_tasks)}个):")
    for task_id in in_progress_tasks:
        task = TASKS[task_id]
        print(f"  • {task_id} - {task['name']} (预计{task['hours']}h)")

    # 找出下一个待完成的P0任务
    next_p0_tasks = [tid for tid, task in TASKS.items()
                     if task['status'] == 'pending' and task['priority'] == 'P0'][:3]
    print(f"\n📅 下一步计划 (P0任务):")
    for task_id in next_p0_tasks:
        task = TASKS[task_id]
        print(f"  • {task_id} - {task['name']} (预计{task['hours']}h)")

    print("\n" + "=" * 70)


def main():
    import sys

    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python progress_tracker.py status           # 查看当前进度")
        print("  python progress_tracker.py complete 1.6     # 标记任务1.6为已完成")
        print("  python progress_tracker.py start 1.7        # 标记任务1.7为进行中")
        print("  python progress_tracker.py report           # 生成每日进度报告")
        sys.exit(1)

    command = sys.argv[1]

    if command == "status":
        show_status()
    elif command == "complete" and len(sys.argv) >= 3:
        complete_task(sys.argv[2])
    elif command == "start" and len(sys.argv) >= 3:
        start_task(sys.argv[2])
    elif command == "report":
        generate_report()
    else:
        print(f"❌ 未知命令: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
