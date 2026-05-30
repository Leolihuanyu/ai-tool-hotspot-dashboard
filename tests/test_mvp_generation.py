#!/usr/bin/env python3
"""
测试MVP建议生成能力
"""
import sys
import os
sys.path.insert(0, '/Users/ri/Projects/ai-tool-hotspot-dashboard')

from dotenv import load_dotenv
load_dotenv()

import json
from src.llm.pain_extractor import PainPointExtractor
from src.llm.mvp_suggester import MVPSuggester
from src.models import TrendingTopic
from datetime import datetime

# 模拟一些含痛点的热点话题
test_topics = [
    TrendingTopic(
        title="I need a tool to automate my email marketing",
        description="Looking for something that can help me send personalized emails at scale",
        source="Reddit",
        url="https://reddit.com/test1",
        heat_score=90.0,
        timestamp=datetime.now(),
        trend_direction="rising",
        tags=["email", "marketing", "automation"]
    ),
    TrendingTopic(
        title="Struggling with customer support response time",
        description="Our team takes hours to respond to customer tickets, need a better solution",
        source="Hacker News",
        url="https://news.ycombinator.com/test2",
        heat_score=85.0,
        timestamp=datetime.now(),
        trend_direction="stable",
        tags=["support", "customer", "efficiency"]
    ),
    TrendingTopic(
        title="How to monetize my side project?",
        description="Built a tool with 1000 users but don't know how to price it",
        source="Reddit",  # 使用Reddit代替Indie Hackers（模型限制）
        url="https://indiehackers.com/test3",
        heat_score=80.0,
        timestamp=datetime.now(),
        trend_direction="rising",
        tags=["monetization", "pricing", "saas"]
    ),
    TrendingTopic(
        title="需要一个工具来管理多个项目的进度",
        description="每天在不同项目间切换，效率很低，希望有统一的管理工具",
        source="Reddit",
        url="https://reddit.com/test4",
        heat_score=75.0,
        timestamp=datetime.now(),
        trend_direction="stable",
        tags=["project", "management", "productivity"]
    ),
    TrendingTopic(
        title="First customer acquisition is so hard",
        description="Launched my SaaS 2 months ago, still struggling to get paying customers",
        source="Reddit",
        url="https://reddit.com/test5",
        heat_score=95.0,
        timestamp=datetime.now(),
        trend_direction="rising",
        tags=["customer", "acquisition", "saas"]
    )
]

print("="*60)
print("🔍 测试MVP建议生成能力")
print("="*60)

# 初始化提取器和生成器
pain_extractor = PainPointExtractor()
mvp_suggester = MVPSuggester()

# Step 1: 提取痛点
print("\n📊 Step 1: 提取用户痛点...")
pain_points = []

for topic in test_topics:
    # 检查是否包含痛点关键词
    text = f"{topic.title} {topic.description}"
    if pain_extractor.contains_pain_keyword(text):
        print(f"  ✅ 发现痛点: {topic.title[:50]}...")

        # 模拟痛点提取（实际会调用LLM）
        try:
            pain_point = pain_extractor.extract(
                text=text,
                context_title=topic.title,
                source=topic.source,
                url=topic.url
            )
            if pain_point:
                pain_points.append(pain_point)
        except Exception as e:
            print(f"    ⚠️ 提取失败: {e}")
    else:
        print(f"  ❌ 无痛点关键词: {topic.title[:50]}...")

print(f"\n✅ 成功提取 {len(pain_points)} 个痛点")

# Step 2: 生成MVP建议
print("\n🚀 Step 2: 生成MVP建议...")

if pain_points:
    # 为前3个痛点生成MVP建议
    mvp_count = 0
    for i, pain_point in enumerate(pain_points[:3], 1):
        print(f"\n  处理痛点 {i}: {pain_point.description[:50]}...")

        try:
            mvp = mvp_suggester.generate(
                pain_points=[pain_point],
                trending_topics=test_topics[:2]  # 提供一些热点作为背景
            )

            if mvp:
                mvp_count += 1
                print(f"    ✅ MVP建议生成成功!")
                print(f"    中文: {mvp['mvp_suggestion_cn'][:100]}...")
                print(f"    日文: {mvp['mvp_suggestion_ja'][:100]}...")
        except Exception as e:
            print(f"    ❌ MVP生成失败: {e}")

    print(f"\n✅ 成功生成 {mvp_count} 个MVP建议")
else:
    print("\n⚠️ 没有提取到痛点，无法生成MVP建议")

print("\n" + "="*60)
print("📈 测试总结:")
print("="*60)
print(f"- 输入话题数: {len(test_topics)}")
print(f"- 提取痛点数: {len(pain_points)}")
print(f"- 生成MVP数: {mvp_count if 'mvp_count' in locals() else 0}")

# 根据orchestrator.py的逻辑
print("\n📝 根据系统设计:")
print("- 从热点话题中提取痛点（最多20个）")
print("- 为前15个痛点生成MVP建议")
print("- 筛选出Top 10个MVP机会")
print("\n💡 理论最大MVP数量: 10个")
print("🎯 实际MVP数量取决于:")
print("  1. 抓取到的话题数量")
print("  2. 话题中包含的痛点数量")
print("  3. LLM API调用成功率")