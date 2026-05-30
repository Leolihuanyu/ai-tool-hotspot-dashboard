
import sys
import json
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.llm.client import LLMClient
from dotenv import load_dotenv

load_dotenv()

def test_generate_tweet():
    print("🚀 Testing LLM Tweet Generation...")

    # 1. 加载数据
    try:
        with open('data/latest.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ data/latest.json not found.")
        return

    # 简化的数据摘要
    summary = {
        "trends": [t.get('title') for t in data.get('trending_topics', [])[:3]],
        "tools": [t.get('name') for t in data.get('ai_tools', [])[:3]],
        "opportunities": [o.get('mvp_suggestion_en', '')[:100] for o in data.get('opportunities', [])[:1]]
    }

    print(f"📊 Data loaded: {json.dumps(summary, indent=2)}")

    # 2. 初始化LLM
    try:
        llm = LLMClient()
        print(f"✅ LLM Client initialized (Provider: {llm.provider}, Model: {llm.model})")
    except Exception as e:
        print(f"❌ LLM Client initialization failed: {e}")
        print("💡 Please configure OPENAI_API_KEY or ANTHROPIC_API_KEY in .env")
        return

    # 3. 构造Prompt
    prompt = f"""
Role: You are a top-tier tech influencer on Twitter/X, specializing in AI and Indie Hacking.
Task: Write a viral tweet based on the following daily AI data.

Data:
{json.dumps(summary)}

Requirements:
1. **Strictly under 280 characters**. This is CRITICAL.
2. Don't just list items. Pick the ONE most interesting trend or tool and hype it up.
3. Use a punchy hook.
4. Include 1-2 relevant emojis.
5. End with: "Follow for daily AI alpha 🚀"
6. Tone: Insightful, exciting, professional yet accessible.
7. Language: English.
"""

    print("\n🤖 Generating tweet...")
    tweet = llm.generate(prompt)

    if tweet:
        print("\n" + "="*50)
        print("✨ Generated Tweet:")
        print("="*50)
        print(tweet)
        print("="*50)
        print(f"Character count: {len(tweet)}")
    else:
        print("❌ Failed to generate tweet.")

if __name__ == "__main__":
    test_generate_tweet()
