"""LLM提示词模板

定义所有LLM任务的提示词模板。
"""

# 中文摘要生成提示词
SUMMARY_PROMPT_CN = """请用简洁的中文（≤200字符）总结以下内容：

{description}

要求：
- 突出核心功能和价值主张
- 使用通俗易懂的语言
- 避免营销术语
- 严格控制在200字符以内

直接返回摘要，不要包含任何前缀或解释。"""

# 日文摘要生成提示词
SUMMARY_PROMPT_JA = """以下の内容を簡潔な日本語（≤200文字）で要約してください：

{description}

要件：
- 核心機能と価値提案を強調する
- 分かりやすい言葉を使う
- マーケティング用語を避ける
- 200文字以内に厳密に制限する

要約のみを直接返し、前置きや説明は含めないでください。"""

# 英文摘要生成提示词（主模板 - 用于生成然后翻译）
SUMMARY_PROMPT_EN = """Summarize the following content concisely (≤200 characters):

{description}

Requirements:
- Highlight core features and value proposition
- Use clear and simple language
- Avoid marketing jargon
- Strictly limit to 200 characters

Return only the summary without any prefix or explanation."""

# 痛点提取提示词
PAIN_POINT_EXTRACTION_PROMPT = """分析以下文本，判断是否包含用户痛点（需求、问题、期望）：

文本：
{text}

上下文：
{context}

请返回以下JSON格式（如果不是痛点，返回空JSON）：
{{
    "is_pain_point": true/false,
    "keywords": ["关键词1", "关键词2", ...],
    "confidence_score": 0.0-1.0,
    "tags": ["标签1", "标签2", ...],
    "summary_cn": "中文摘要（≤200字符）",
    "summary_ja": "日文摘要（≤200字符）"
}}

痛点关键词示例：
- "need a tool for..."
- "wish there was..."
- "looking for..."
- "how to..."
- "problem with..."

直接返回JSON，不要包含任何其他文本。"""

# MVP建议生成提示词（英文优先版本）
MVP_SUGGESTION_PROMPT = """Based on the following user pain point and market trends, generate an innovative MVP product proposal:

User Pain Point:
{pain_point}

Market Trends:
{related_topics}

Please return the following JSON format product proposal:
{{
    "mvp_suggestion_en": "English product proposal (400 words or less)",
    "competitive_analysis": "Competitive analysis (200 words or less)",
    "differentiation": "Differentiation strategy (150 words or less)",
    "launch_difficulty": "Launch difficulty (easy/medium/hard)",
    "estimated_time": "Estimated development time (48hours/1week/1month/3months)"
}}

The product proposal MUST include the following four parts:

1. Core Features (3-5 key points)
   - What this product specifically does
   - How it solves user pain points
   - Key features and highlights

2. Target User Groups
   - Who will use this product
   - User personas (industry, roles, scenarios)
   - Estimated user scale

3. Monetization Strategy
   - Recommended pricing model (subscription/one-time/freemium)
   - Pricing tier suggestions
   - Expected monthly revenue potential

4. Competitive Analysis & Differentiation
   - Check if similar tools already exist (if yes, list 1-2 main competitors)
   - Our differentiation advantages
   - Why users would choose us over existing solutions

Example format:
"Core Features: 1) Automatically extract and categorize user pain points from Reddit, 2) AI analysis of monetization potential and market size, 3) Generate MVP reports with competitive analysis. Target Users: Indie developers, product managers, small startup teams, estimated 100K+ potential users. Monetization: Subscription model, $29/month basic, $99/month professional, expected monthly revenue $5,000-20,000. Competition: Currently lacks mature tools focused on pain point discovery, we differentiate through multi-source aggregation and deep AI analysis."

Requirements:
- Must check if similar solutions already exist
- If competitors exist, clearly explain how to do better
- Evaluate realistic launch difficulty and timeline
- Focus on product value and feasibility
- Avoid overly optimistic predictions

Return JSON directly without any additional text."""
