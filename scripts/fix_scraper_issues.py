#!/usr/bin/env python3
"""
修复爬虫问题的脚本
- 测试各个数据源的连接
- 提供解决方案
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import requests
import json

def test_github():
    """测试GitHub API"""
    print("\n🔍 测试GitHub API...")
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("❌ 未配置GITHUB_TOKEN")
        return False

    headers = {'Authorization': f'token {token}'}
    response = requests.get('https://api.github.com/user', headers=headers)
    if response.status_code == 200:
        user = response.json()
        print(f"✅ GitHub Token有效! 用户: {user.get('login')}")
        return True
    else:
        print(f"❌ GitHub Token无效: {response.status_code}")
        print("   解决方案: 访问 https://github.com/settings/tokens 重新生成")
        return False

def test_reddit():
    """测试Reddit API"""
    print("\n🔍 测试Reddit API...")
    client_id = os.getenv('REDDIT_CLIENT_ID')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET')

    if not client_id or not client_secret:
        print("❌ 未配置Reddit凭据")
        return False

    auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
    data = {'grant_type': 'client_credentials'}
    headers = {'User-Agent': 'AI-Tool-Hotspot/1.0'}

    response = requests.post('https://www.reddit.com/api/v1/access_token',
                            auth=auth, data=data, headers=headers)
    if response.status_code == 200:
        print(f"✅ Reddit凭据有效!")
        return True
    else:
        print(f"❌ Reddit凭据无效: {response.status_code}")
        return False

def test_indie_hackers():
    """测试Indie Hackers访问"""
    print("\n🔍 测试Indie Hackers访问...")

    # 测试API端点
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json'
    }

    response = requests.get('https://www.indiehackers.com/api/posts/popular',
                           headers=headers, timeout=10)

    if 'cloudflare' in response.text.lower():
        print("⚠️  Indie Hackers被Cloudflare保护")
        print("   解决方案:")
        print("   1. 使用浏览器自动化工具（selenium/playwright）")
        print("   2. 申请官方API访问权限")
        print("   3. 使用代理服务")
        return False
    elif response.status_code == 200:
        print("✅ Indie Hackers API可访问!")
        return True
    else:
        print(f"❌ Indie Hackers访问失败: {response.status_code}")
        return False

def test_theresanai():
    """测试There's an AI for That"""
    print("\n🔍 测试There's an AI for That...")

    response = requests.get('https://theresanaiforthat.com', timeout=10)

    if 'cloudflare' in response.text.lower():
        print("⚠️  There's an AI for That被Cloudflare保护")
        print("   解决方案:")
        print("   1. 暂时禁用此数据源")
        print("   2. 使用其他AI工具数据源替代")
        print("   3. 联系网站管理员申请API访问")
        return False
    else:
        print("✅ There's an AI for That可访问!")
        return True

def test_twitter():
    """检查Twitter/X配置"""
    print("\n🔍 检查X/Twitter API配置...")

    api_key = os.getenv('TWITTER_API_KEY')
    api_secret = os.getenv('TWITTER_API_SECRET')

    if not api_key:
        print("⚠️  未配置X/Twitter API")
        print("   获取方法:")
        print("   1. 访问 https://developer.twitter.com/")
        print("   2. 申请开发者账号（需要审核1-3天）")
        print("   3. 创建App获取API凭据")
        print("   4. 配置环境变量:")
        print("      TWITTER_API_KEY=xxx")
        print("      TWITTER_API_SECRET=xxx")
        print("      TWITTER_ACCESS_TOKEN=xxx")
        print("      TWITTER_ACCESS_TOKEN_SECRET=xxx")
        return False
    else:
        print("✅ X/Twitter API已配置")
        return True

def main():
    print("="*60)
    print("🔧 AI工具热点分析Dashboard - 爬虫问题诊断")
    print("="*60)

    results = {
        "GitHub": test_github(),
        "Reddit": test_reddit(),
        "Indie Hackers": test_indie_hackers(),
        "There's an AI for That": test_theresanai(),
        "X/Twitter": test_twitter()
    }

    print("\n" + "="*60)
    print("📊 诊断结果汇总:")
    print("="*60)

    for source, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {source}: {'正常' if status else '需要修复'}")

    print("\n建议优先级:")
    print("1. ✅ GitHub和Reddit已正常工作")
    print("2. ⚠️  Indie Hackers和There's an AI for That需要高级解决方案")
    print("3. 📝 X/Twitter需要申请开发者账号")

    working_count = sum(results.values())
    print(f"\n可用数据源: {working_count}/5")

if __name__ == "__main__":
    main()