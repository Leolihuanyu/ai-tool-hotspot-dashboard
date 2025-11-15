#!/usr/bin/env python3
"""批量生成英文摘要脚本

这个脚本为现有数据生成英文摘要，并通过翻译更新中文和日文摘要。
使用新的TrilingualSummarizer类，只需一次LLM调用即可生成三语摘要。
"""

import os
import sys
import json
import time
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.llm.summarizer import TrilingualSummarizer
from src.utils.logger import get_logger
from src.utils.config import Config

logger = get_logger(__name__)


def load_json_data(file_path):
    """加载JSON数据文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"无法加载文件 {file_path}: {e}")
        return None


def save_json_data(file_path, data):
    """保存JSON数据文件"""
    try:
        # 创建备份
        backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                backup_data = f.read()
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(backup_data)
            logger.info(f"已创建备份: {backup_path}")

        # 保存更新后的数据
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"数据已保存到: {file_path}")
        return True
    except Exception as e:
        logger.error(f"保存文件失败 {file_path}: {e}")
        return False


def generate_summaries_for_tools(tools, summarizer):
    """为AI工具生成摘要"""
    updated_count = 0
    skipped_count = 0
    failed_count = 0

    for idx, tool in enumerate(tools, 1):
        # 检查是否需要生成摘要
        if tool.get('summary_en') and tool.get('summary_cn') and tool.get('summary_ja'):
            logger.debug(f"[{idx}/{len(tools)}] 跳过已有摘要的工具: {tool.get('name', 'Unknown')}")
            skipped_count += 1
            continue

        logger.info(f"[{idx}/{len(tools)}] 生成摘要: {tool.get('name', 'Unknown')}")

        try:
            # 获取描述文本
            description = tool.get('description', '')
            if not description:
                logger.warning(f"工具缺少描述: {tool.get('name', 'Unknown')}")
                failed_count += 1
                continue

            # 生成三语摘要
            summaries = summarizer.generate_summary(description)

            # 更新工具数据
            tool['summary_en'] = summaries['summary_en']
            tool['summary_cn'] = summaries['summary_cn']
            tool['summary_ja'] = summaries['summary_ja']

            updated_count += 1
            logger.info(f"✓ 成功生成摘要 ({updated_count}个已更新)")

            # 每10个工具暂停一下，避免API限制
            if updated_count % 10 == 0:
                time.sleep(1)

        except Exception as e:
            logger.error(f"生成摘要失败: {e}")
            failed_count += 1

    return updated_count, skipped_count, failed_count


def generate_summaries_for_topics(topics, summarizer):
    """为热点话题生成摘要"""
    updated_count = 0
    skipped_count = 0
    failed_count = 0

    for idx, topic in enumerate(topics, 1):
        # 检查是否需要生成摘要
        if topic.get('summary_en') and topic.get('summary_cn') and topic.get('summary_ja'):
            logger.debug(f"[{idx}/{len(topics)}] 跳过已有摘要的话题: {topic.get('title', 'Unknown')}")
            skipped_count += 1
            continue

        logger.info(f"[{idx}/{len(topics)}] 生成摘要: {topic.get('title', 'Unknown')}")

        try:
            # 获取描述文本
            description = topic.get('description', '')
            if not description:
                logger.warning(f"话题缺少描述: {topic.get('title', 'Unknown')}")
                failed_count += 1
                continue

            # 生成三语摘要
            summaries = summarizer.generate_summary(description)

            # 更新话题数据
            topic['summary_en'] = summaries['summary_en']
            topic['summary_cn'] = summaries['summary_cn']
            topic['summary_ja'] = summaries['summary_ja']

            updated_count += 1
            logger.info(f"✓ 成功生成摘要 ({updated_count}个已更新)")

            # 每10个话题暂停一下，避免API限制
            if updated_count % 10 == 0:
                time.sleep(1)

        except Exception as e:
            logger.error(f"生成摘要失败: {e}")
            failed_count += 1

    return updated_count, skipped_count, failed_count


def generate_summaries_for_pain_points(pain_points, summarizer):
    """为用户痛点生成摘要"""
    updated_count = 0
    skipped_count = 0
    failed_count = 0

    for idx, pain_point in enumerate(pain_points, 1):
        # 检查是否需要生成摘要
        if pain_point.get('summary_en') and pain_point.get('summary_cn') and pain_point.get('summary_ja'):
            logger.debug(f"[{idx}/{len(pain_points)}] 跳过已有摘要的痛点")
            skipped_count += 1
            continue

        logger.info(f"[{idx}/{len(pain_points)}] 生成痛点摘要")

        try:
            # 获取原始文本
            text = pain_point.get('original_text', '')
            if not text:
                logger.warning(f"痛点缺少原始文本")
                failed_count += 1
                continue

            # 生成三语摘要
            summaries = summarizer.generate_summary(text)

            # 更新痛点数据
            pain_point['summary_en'] = summaries['summary_en']
            pain_point['summary_cn'] = summaries['summary_cn']
            pain_point['summary_ja'] = summaries['summary_ja']

            updated_count += 1
            logger.info(f"✓ 成功生成摘要 ({updated_count}个已更新)")

            # 每10个痛点暂停一下，避免API限制
            if updated_count % 10 == 0:
                time.sleep(1)

        except Exception as e:
            logger.error(f"生成摘要失败: {e}")
            failed_count += 1

    return updated_count, skipped_count, failed_count


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("批量生成英文摘要脚本")
    logger.info("=" * 60)

    # 初始化摘要生成器
    logger.info("初始化TrilingualSummarizer...")
    summarizer = TrilingualSummarizer()

    # 数据文件路径
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    latest_file = os.path.join(data_dir, 'latest.json')

    if not os.path.exists(latest_file):
        # 尝试从frontend/public/data目录
        frontend_data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'frontend', 'public', 'data'
        )
        latest_file = os.path.join(frontend_data_dir, 'latest.json')

    if not os.path.exists(latest_file):
        logger.error(f"找不到数据文件: {latest_file}")
        sys.exit(1)

    # 加载数据
    logger.info(f"加载数据文件: {latest_file}")
    data = load_json_data(latest_file)
    if not data:
        logger.error("无法加载数据")
        sys.exit(1)

    # 统计信息
    total_tools = len(data.get('ai_tools', []))
    total_topics = len(data.get('trending_topics', []))
    total_pain_points = len(data.get('pain_points', []))

    logger.info(f"数据统计:")
    logger.info(f"  - AI工具: {total_tools}")
    logger.info(f"  - 热点话题: {total_topics}")
    logger.info(f"  - 用户痛点: {total_pain_points}")

    # 询问用户是否继续
    response = input("\n是否开始生成英文摘要？(y/n): ")
    if response.lower() != 'y':
        logger.info("用户取消操作")
        return

    # 处理AI工具
    if total_tools > 0:
        logger.info("\n" + "=" * 40)
        logger.info("处理AI工具...")
        tools_updated, tools_skipped, tools_failed = generate_summaries_for_tools(
            data['ai_tools'], summarizer
        )
        logger.info(f"AI工具处理完成: {tools_updated}个更新, {tools_skipped}个跳过, {tools_failed}个失败")

    # 处理热点话题
    if total_topics > 0:
        logger.info("\n" + "=" * 40)
        logger.info("处理热点话题...")
        topics_updated, topics_skipped, topics_failed = generate_summaries_for_topics(
            data['trending_topics'], summarizer
        )
        logger.info(f"热点话题处理完成: {topics_updated}个更新, {topics_skipped}个跳过, {topics_failed}个失败")

    # 处理用户痛点
    if total_pain_points > 0:
        logger.info("\n" + "=" * 40)
        logger.info("处理用户痛点...")
        pain_points_updated, pain_points_skipped, pain_points_failed = generate_summaries_for_pain_points(
            data['pain_points'], summarizer
        )
        logger.info(f"用户痛点处理完成: {pain_points_updated}个更新, {pain_points_skipped}个跳过, {pain_points_failed}个失败")

    # 保存更新后的数据
    logger.info("\n" + "=" * 40)
    logger.info("保存更新后的数据...")
    if save_json_data(latest_file, data):
        logger.info("✅ 数据已成功保存")

        # 总结
        logger.info("\n" + "=" * 60)
        logger.info("批量生成摘要完成！")
        logger.info(f"总计更新: {tools_updated + topics_updated + pain_points_updated} 条记录")
        logger.info("=" * 60)
    else:
        logger.error("❌ 保存数据失败")
        sys.exit(1)


if __name__ == "__main__":
    main()