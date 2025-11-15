#!/usr/bin/env python3
"""测试三语摘要生成功能

这个脚本用于测试新的TrilingualSummarizer类，
验证英文生成+翻译的功能是否正常工作。
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.llm.summarizer import TrilingualSummarizer
from src.utils.logger import get_logger

logger = get_logger(__name__)


def test_summary_generation():
    """测试摘要生成功能"""

    # 测试数据
    test_descriptions = [
        {
            "name": "ChatGPT",
            "description": "ChatGPT is an advanced language model developed by OpenAI that can engage in conversational interactions, answer questions, help with writing, coding, analysis, and creative tasks. It uses transformer architecture and has been trained on diverse internet text to understand and generate human-like responses across a wide range of topics."
        },
        {
            "name": "Midjourney",
            "description": "Midjourney is an AI-powered image generation tool that creates stunning artworks from text prompts. Users can describe what they want to see, and the AI generates unique, high-quality images in various artistic styles. It's particularly known for its aesthetic quality and creative interpretations."
        },
        {
            "name": "GitHub Copilot",
            "description": "GitHub Copilot is an AI pair programmer that helps developers write code faster. It suggests whole lines and entire functions in real-time, right from your editor. Trained on billions of lines of code, it turns natural language prompts into coding suggestions across dozens of languages."
        }
    ]

    # 初始化摘要生成器
    logger.info("初始化TrilingualSummarizer...")
    summarizer = TrilingualSummarizer()

    logger.info("=" * 60)
    logger.info("开始测试三语摘要生成")
    logger.info("=" * 60)

    for test_case in test_descriptions:
        logger.info(f"\n测试工具: {test_case['name']}")
        logger.info(f"原始描述 ({len(test_case['description'])}字符):")
        logger.info(f"  {test_case['description'][:100]}...")

        try:
            # 生成三语摘要
            logger.info("\n生成三语摘要...")
            summaries = summarizer.generate_summary(test_case['description'])

            # 显示结果
            logger.info("\n生成结果:")
            logger.info(f"  英文摘要 ({len(summaries['summary_en'])}字符):")
            logger.info(f"    {summaries['summary_en']}")

            logger.info(f"\n  中文摘要 ({len(summaries['summary_cn'])}字符):")
            logger.info(f"    {summaries['summary_cn']}")

            logger.info(f"\n  日文摘要 ({len(summaries['summary_ja'])}字符):")
            logger.info(f"    {summaries['summary_ja']}")

            # 验证长度限制
            if len(summaries['summary_en']) > 200:
                logger.warning(f"  ⚠️ 英文摘要超过200字符限制")
            if len(summaries['summary_cn']) > 200:
                logger.warning(f"  ⚠️ 中文摘要超过200字符限制")
            if len(summaries['summary_ja']) > 200:
                logger.warning(f"  ⚠️ 日文摘要超过200字符限制")

            logger.info("\n✅ 测试成功")

        except Exception as e:
            logger.error(f"\n❌ 测试失败: {e}")

        logger.info("\n" + "-" * 60)


def test_translation_only():
    """测试纯翻译功能（不调用LLM）"""

    logger.info("\n" + "=" * 60)
    logger.info("测试Google翻译功能")
    logger.info("=" * 60)

    from deep_translator import GoogleTranslator

    test_texts = [
        "AI-powered tool for creating stunning visual content",
        "Automated code review and optimization platform",
        "Real-time collaboration workspace for remote teams"
    ]

    for text in test_texts:
        logger.info(f"\n原始英文: {text}")

        try:
            # 翻译成中文
            cn_translator = GoogleTranslator(source='en', target='zh-CN')
            cn_result = cn_translator.translate(text)
            logger.info(f"中文翻译: {cn_result}")

            # 翻译成日文
            ja_translator = GoogleTranslator(source='en', target='ja')
            ja_result = ja_translator.translate(text)
            logger.info(f"日文翻译: {ja_result}")

            logger.info("✅ 翻译成功")

        except Exception as e:
            logger.error(f"❌ 翻译失败: {e}")


def test_error_handling():
    """测试错误处理"""

    logger.info("\n" + "=" * 60)
    logger.info("测试错误处理")
    logger.info("=" * 60)

    summarizer = TrilingualSummarizer()

    # 测试空输入
    logger.info("\n测试空输入...")
    result = summarizer.generate_summary("")
    logger.info(f"空输入结果: {result}")

    # 测试超长输入
    logger.info("\n测试超长输入...")
    long_text = "This is a very long description. " * 100
    result = summarizer.generate_summary(long_text)
    logger.info(f"超长输入结果:")
    logger.info(f"  英文: {result['summary_en'][:50]}...")
    logger.info(f"  中文: {result['summary_cn'][:50]}...")
    logger.info(f"  日文: {result['summary_ja'][:50]}...")


def main():
    """主函数"""

    logger.info("=" * 70)
    logger.info("三语摘要生成测试脚本")
    logger.info("=" * 70)

    # 选择测试模式
    print("\n请选择测试模式:")
    print("1. 完整测试（包括LLM调用）")
    print("2. 仅测试翻译功能")
    print("3. 测试错误处理")
    print("4. 运行所有测试")

    choice = input("\n请输入选择 (1-4): ")

    if choice == '1':
        test_summary_generation()
    elif choice == '2':
        test_translation_only()
    elif choice == '3':
        test_error_handling()
    elif choice == '4':
        test_summary_generation()
        test_translation_only()
        test_error_handling()
    else:
        logger.error("无效的选择")
        sys.exit(1)

    logger.info("\n" + "=" * 70)
    logger.info("测试完成！")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()