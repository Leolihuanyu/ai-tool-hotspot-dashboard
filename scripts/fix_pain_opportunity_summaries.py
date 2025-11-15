#!/usr/bin/env python3
"""修复痛点和机会的三语摘要"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.llm.summarizer import TrilingualSummarizer
from src.utils.logger import get_logger
from src.utils.config import Config

logger = get_logger(__name__)


def fix_pain_points_summaries():
    """修复痛点的英文摘要"""

    # 加载数据
    data_path = "data/latest.json"
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not data.get('pain_points'):
        logger.warning("没有找到痛点数据")
        return

    config = Config()
    summarizer = TrilingualSummarizer(config)

    logger.info(f"开始修复 {len(data['pain_points'])} 个痛点的英文摘要")

    for i, pain_point in enumerate(data['pain_points']):
        # 如果已有中文摘要但没有英文摘要，直接翻译
        if pain_point.get('summary_cn') and not pain_point.get('summary_en'):
            logger.info(f"修复痛点 {i+1} 的英文摘要")

            # 使用中文摘要反向翻译成英文
            from deep_translator import GoogleTranslator
            translator_cn_to_en = GoogleTranslator(source='zh-CN', target='en')

            try:
                pain_point['summary_en'] = translator_cn_to_en.translate(pain_point['summary_cn'])
                logger.info(f"  ✓ 生成英文摘要: {pain_point['summary_en'][:50]}...")
            except Exception as e:
                logger.error(f"  ✗ 翻译失败: {e}")
                # 如果翻译失败，使用原始文本生成
                if pain_point.get('original_text'):
                    summaries = summarizer.generate_summary(pain_point['original_text'])
                    if summaries:
                        pain_point['summary_en'] = summaries['summary_en']
                        pain_point['summary_cn'] = summaries['summary_cn']
                        pain_point['summary_ja'] = summaries['summary_ja']

    # 保存更新后的数据
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info("✅ 痛点英文摘要修复完成")


def fix_opportunities_summaries():
    """为机会生成三语摘要"""

    # 加载数据
    data_path = "data/latest.json"
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not data.get('opportunities'):
        logger.warning("没有找到机会数据")
        return

    config = Config()
    summarizer = TrilingualSummarizer(config)

    logger.info(f"开始为 {len(data['opportunities'])} 个机会生成三语摘要")

    for i, opportunity in enumerate(data['opportunities']):
        # 检查是否缺少摘要
        if not opportunity.get('summary_en') or not opportunity.get('summary_cn') or not opportunity.get('summary_ja'):
            logger.info(f"生成机会 {i+1} 的三语摘要")

            # 使用描述或建议生成摘要
            description = opportunity.get('description', '')
            suggestion = opportunity.get('suggestion', '')
            full_text = f"{description} {suggestion}".strip()

            if full_text:
                summaries = summarizer.generate_summary(full_text)
                if summaries:
                    opportunity['summary_en'] = summaries['summary_en']
                    opportunity['summary_cn'] = summaries['summary_cn']
                    opportunity['summary_ja'] = summaries['summary_ja']
                    logger.info(f"  ✓ 英文: {opportunity['summary_en'][:50]}...")
                    logger.info(f"  ✓ 中文: {opportunity['summary_cn'][:50]}...")
                    logger.info(f"  ✓ 日文: {opportunity['summary_ja'][:50]}...")

    # 保存更新后的数据
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info("✅ 机会三语摘要生成完成")


def analyze_extraction_issues():
    """分析为什么提取的痛点和机会这么少"""

    data_path = "data/latest.json"
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    logger.info("\n=== 数据提取情况分析 ===")
    logger.info(f"热点话题总数: {len(data.get('trending_topics', []))}")
    logger.info(f"痛点总数: {len(data.get('pain_points', []))}")
    logger.info(f"机会总数: {len(data.get('opportunities', []))}")

    # 分析热点话题的来源分布
    topics_by_source = {}
    for topic in data.get('trending_topics', []):
        source = topic.get('source', 'unknown')
        topics_by_source[source] = topics_by_source.get(source, 0) + 1

    logger.info("\n热点话题来源分布:")
    for source, count in topics_by_source.items():
        logger.info(f"  {source}: {count}")

    # 检查核心源话题数量
    core_sources = ['hackernews', 'reddit', 'github']
    core_count = sum(1 for topic in data.get('trending_topics', [])
                    if any(s in topic.get('source', '').lower() for s in core_sources))
    logger.info(f"\n核心源(HN/Reddit/GitHub)话题数: {core_count}")

    # 分析痛点信号
    pain_keywords = ['problem', 'issue', 'difficult', 'hard', 'frustrat', 'pain',
                     'struggle', 'annoying', 'wish', 'need', 'want', 'help',
                     '问题', '困难', '痛点', '需要', '希望']

    topics_with_signal = 0
    for topic in data.get('trending_topics', []):
        title = topic.get('title', '').lower()
        desc = topic.get('description', '').lower()
        if any(keyword in title + desc for keyword in pain_keywords):
            topics_with_signal += 1

    logger.info(f"包含痛点关键词的话题数: {topics_with_signal}")

    logger.info("\n建议:")
    logger.info("1. 降低痛点提取的confidence_score阈值")
    logger.info("2. 扩大痛点关键词列表")
    logger.info("3. 调整LLM提示词，降低判断标准")
    logger.info("4. 增加从YouTube和Google Trends提取痛点的能力")


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("修复痛点和机会的三语摘要")
    logger.info("=" * 50)

    # 先分析问题
    analyze_extraction_issues()

    # 修复痛点英文摘要
    logger.info("\n" + "=" * 50)
    fix_pain_points_summaries()

    # 生成机会三语摘要
    logger.info("\n" + "=" * 50)
    fix_opportunities_summaries()

    logger.info("\n✅ 所有修复完成！")