# 🚀 AI工具热点Dashboard - 2周快速上线实装计划

**文档版本**: 1.0
**创建日期**: 2025-11-07
**计划周期**: 14天（2周）
**目标**: 实现访问控制、数据质量提升、付费+Beta并行的增长机制

---

## 📋 执行摘要

### 核心目标
根据运营计划书的三大课题，在14天内完成核心商业化功能：
1. **访问控制** - 防止Dashboard数据外泄，实现签名URL方案
2. **数据质量提升** - 实现数据源分级、LLM反射过滤、双层摘要
3. **增长机制** - 支持邀请码Beta测试 + Stripe付费订阅并行

### 关键指标（KPI）
| 指标 | 目标 | 验证方式 |
|-----|------|---------|
| **数据质量** | "Yes"占比≥70% | 查看latest.json的pain_points |
| **访问安全性** | token泄露无法访问 | 测试过期/异IP访问 |
| **Beta用户** | 获得30-50个种子用户 | users表统计 |
| **付费转化** | 至少1个付费订阅 | Stripe Dashboard |
| **邮件打开率** | ≥40% | SendGrid统计 |
| **Dashboard响应** | 首屏加载<2s | Lighthouse测试 |

---

## 📅 总体进度概览

### 整体进度
```
总任务数: 32个
已完成: 5个 (15.6%)
进行中: 0个
待完成: 27个 (84.4%)
```

### 阶段进度
| 阶段 | 任务数 | 已完成 | 进行中 | 待完成 | 完成率 |
|------|--------|--------|--------|--------|--------|
| **第一周 (Day 1-7)** | 13 | 5 | 0 | 8 | 38.5% |
| **第二周 (Day 8-14)** | 19 | 0 | 0 | 19 | 0% |

---

## 🎯 第一周：核心功能实装（Day 1-7）

### Day 1-3：访问控制系统（签名URL方案）

#### 进度：5/6 任务完成 (83.3%)

| 任务ID | 任务名称 | 优先级 | 预计工时 | 状态 | 完成日期 | 负责文件 |
|--------|---------|--------|---------|------|---------|---------|
| **1.1** | 创建JWT Token管理模块 | P0 | 3h | ✅ 已完成 | 2025-11-07 | `src/auth/token_manager.py` |
| **1.2** | 扩展数据库schema | P0 | 2h | ✅ 已完成 | 2025-11-07 | `src/database/schema.sql` |
| **1.3** | 创建用户管理模块 | P0 | 2h | ✅ 已完成 | 2025-11-07 | `src/user/user_manager.py` |
| **1.4** | Flask添加认证中间件 | P0 | 2h | ✅ 已完成 | 2025-11-07 | `src/dashboard/auth_middleware.py` |
| **1.5** | Flask添加认证路由 | P0 | 1h | ✅ 已完成 | 2025-11-07 | `src/dashboard/routes.py` |
| **1.6** | 邮件系统生成签名URL | P0 | 2h | ⏳ 待完成 | - | `src/email/sender.py` |
| **1.7** | 前端token验证逻辑 | P0 | 3h | ⏳ 待完成 | - | `frontend/src/utils/auth.js` |
| **1.8** | 创建过期提示页面 | P1 | 2h | ⏳ 待完成 | - | `frontend/src/pages/Expired.jsx` |

#### 已完成详情

##### ✅ 1.1 JWT Token管理模块
**文件**: `src/auth/token_manager.py`
**功能**:
- ✅ 生成24小时有效期的签名token
- ✅ 验证token合法性和有效期
- ✅ 邮箱绑定验证
- ✅ 可选IP地址绑定（防转发攻击）
- ✅ 生成完整Dashboard访问URL
- ✅ 测试通过（5个测试用例）

**关键API**:
```python
tm = TokenManager()
token = tm.generate_token(email="user@example.com", subscription_type="beta")
result = tm.verify_token(token)  # {"valid": True, "email": "...", ...}
url = tm.generate_dashboard_url("https://dashboard.com", email="user@example.com")
```

##### ✅ 1.2 数据库Schema v1.2
**文件**: `src/database/schema.sql`
**新增表**:
- ✅ `users` - 用户信息（id, email, subscription_type, subscription_status, invite_code, referrer_id, free_until, stripe_customer_id, stripe_subscription_id, created_at, updated_at, last_accessed_at）
- ✅ `access_logs` - 访问日志（id, email, token_hash, accessed_at, ip_address, user_agent, access_result, error_message）
- ✅ `referrals` - 推荐关系（id, referrer_email, referee_email, invite_code, reward_status, reward_granted_at, created_at）
- ✅ `invite_codes` - 邀请码管理（id, code, code_type, max_uses, current_uses, created_by, expires_at, created_at, is_active）

##### ✅ 1.3 用户管理模块
**文件**: `src/user/user_manager.py`
**功能**:
- ✅ `create_user()` - 创建新用户（支持Beta/付费）
- ✅ `get_user()` - 查询用户信息
- ✅ `update_user()` - 更新订阅状态
- ✅ `log_access()` - 记录访问日志（IP、User Agent、结果）
- ✅ `get_access_logs()` - 查询访问历史
- ✅ `get_all_active_users()` - 获取活跃用户（用于邮件发送）
- ✅ 测试通过

##### ✅ 1.4 Flask认证中间件
**文件**: `src/dashboard/auth_middleware.py`
**功能**:
- ✅ `verify_token_from_request()` - 从URL/Cookie/Header提取并验证token
- ✅ `@require_auth` - 装饰器，强制认证
- ✅ `@optional_auth` - 装饰器，可选认证
- ✅ 自动记录访问日志
- ✅ 支持IP验证开关（环境变量控制）

**使用示例**:
```python
@app.route('/protected')
@require_auth
def protected_route():
    # request.user_email 和 request.subscription_type 已注入
    return f"Welcome {request.user_email}"
```

##### ✅ 1.5 Flask认证路由
**文件**: `src/dashboard/routes.py`
**新增路由**:
- ✅ `GET/POST /api/verify-token` - 验证token有效性
- ✅ `GET /access-expired` - 过期/无效提示页面
- ✅ `GET /api/data` - 受保护的完整数据获取API（需认证）

**配置更新**:
- ✅ `.env.example` - 添加JWT_SECRET_KEY、TOKEN_EXPIRY_HOURS、TOKEN_REQUIRE_IP_MATCH、DASHBOARD_BASE_URL、Stripe配置

#### 待完成任务详情

##### ⏳ 1.6 邮件系统生成签名URL
**文件**: `src/email/sender.py`
**目标**: 为每封邮件生成唯一签名URL
**实现要点**:
```python
from src.auth.token_manager import TokenManager

tm = TokenManager()
for user in active_users:
    dashboard_url = tm.generate_dashboard_url(
        base_url=os.getenv("DASHBOARD_BASE_URL"),
        email=user["email"],
        subscription_type=user["subscription_type"]
    )
    # 在邮件模板中使用 dashboard_url
```

**预计工时**: 2小时
**依赖**: 1.1 (已完成)
**验收标准**:
- [ ] 邮件包含形如 `https://dashboard.com/?token=xxx&email=yyy` 的链接
- [ ] Token有效期24小时
- [ ] 点击链接可正常访问Dashboard

---

##### ⏳ 1.7 前端token验证逻辑
**文件**: `frontend/src/utils/auth.js` (新建)
**目标**: 前端解析URL参数并存储token
**实现要点**:
```javascript
// 1. 解析URL参数
export function getTokenFromURL() {
  const params = new URLSearchParams(window.location.search);
  return {
    token: params.get('token'),
    email: params.get('email')
  };
}

// 2. 存储到localStorage（24小时过期）
export function saveToken(token, email) {
  const expiry = Date.now() + 24 * 60 * 60 * 1000;
  localStorage.setItem('access_token', token);
  localStorage.setItem('user_email', email);
  localStorage.setItem('token_expiry', expiry);
}

// 3. 验证token是否过期
export function isTokenValid() {
  const expiry = localStorage.getItem('token_expiry');
  return expiry && Date.now() < parseInt(expiry);
}

// 4. 调用后端验证API
export async function verifyToken(token) {
  const response = await fetch('/api/verify-token?token=' + token);
  return response.json();
}
```

**修改**: `frontend/src/App.jsx`
```jsx
import { useEffect } from 'react';
import { getTokenFromURL, saveToken, isTokenValid, verifyToken } from './utils/auth';

function App() {
  useEffect(() => {
    const { token, email } = getTokenFromURL();

    if (token && email) {
      // 验证token
      verifyToken(token).then(result => {
        if (result.valid) {
          saveToken(token, email);
        } else {
          window.location.href = '/access-expired?error=' + result.error;
        }
      });
    } else if (!isTokenValid()) {
      // 没有token且localStorage中的token已过期
      window.location.href = '/access-expired?error=未提供访问token';
    }
  }, []);

  return <Routes>...</Routes>;
}
```

**预计工时**: 3小时
**依赖**: 1.5 (已完成)
**验收标准**:
- [ ] 用户点击邮件链接后，token自动保存到localStorage
- [ ] 过期token自动跳转到过期提示页
- [ ] 无效token自动跳转到过期提示页

---

##### ⏳ 1.8 创建过期提示页面
**文件**: `frontend/src/pages/Expired.jsx` (新建)
**目标**: 友好的过期/无效提示页面
**设计要求**:
- 显示错误类型（过期/IP不匹配/无效）
- 引导用户重新订阅或联系管理员
- 简洁美观的UI（使用TailwindCSS）

**实现示例**:
```jsx
import React from 'react';
import { useSearchParams } from 'react-router-dom';
import { AlertCircle, Clock, Shield, Mail } from 'lucide-react';

export default function Expired() {
  const [searchParams] = useSearchParams();
  const error = searchParams.get('error') || '访问链接已过期或无效';

  // 根据错误信息判断类型
  let icon, title, suggestion;
  if (error.includes('过期')) {
    icon = <Clock className="w-16 h-16 text-orange-500" />;
    title = "访问链接已过期";
    suggestion = "您的访问链接有效期为24小时。请查收最新的每日邮件，或订阅以获得持续访问权限。";
  } else if (error.includes('IP') || error.includes('转发')) {
    icon = <Shield className="w-16 h-16 text-red-500" />;
    title = "安全验证失败";
    suggestion = "检测到您的访问来自不同的IP地址，可能是链接被转发。请使用原始邮件中的链接访问。";
  } else {
    icon = <AlertCircle className="w-16 h-16 text-gray-500" />;
    title = "访问被拒绝";
    suggestion = "您的访问链接无效或已被篡改。";
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center">
        <div className="flex justify-center mb-6">
          {icon}
        </div>

        <h1 className="text-2xl font-bold text-gray-900 mb-4">
          {title}
        </h1>

        <p className="text-gray-600 mb-6">
          {suggestion}
        </p>

        <div className="text-sm text-gray-500 mb-6">
          错误详情: {error}
        </div>

        <div className="space-y-3">
          <a
            href="mailto:support@your-dashboard.com?subject=访问链接问题"
            className="flex items-center justify-center gap-2 w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 transition"
          >
            <Mail className="w-5 h-5" />
            联系支持
          </a>

          <a
            href="/subscribe"
            className="block w-full bg-gray-100 text-gray-700 py-3 px-6 rounded-lg hover:bg-gray-200 transition"
          >
            立即订阅
          </a>
        </div>
      </div>
    </div>
  );
}
```

**路由配置**: 在 `frontend/src/App.jsx` 添加:
```jsx
<Route path="/access-expired" element={<Expired />} />
```

**预计工时**: 2小时
**依赖**: 无
**验收标准**:
- [ ] 显示友好的错误提示
- [ ] 提供"联系支持"和"立即订阅"按钮
- [ ] 移动端显示正常

---

### Day 4-5：数据质量提升

#### 进度：0/4 任务完成 (0%)

| 任务ID | 任务名称 | 优先级 | 预计工时 | 状态 | 负责文件 |
|--------|---------|--------|---------|------|---------|
| **2.1** | 实现数据源分级权重系统 | P0 | 3h | ⏳ 待完成 | `src/config/source_weights.py` |
| **2.2** | 修改评分器集成权重 | P0 | 2h | ⏳ 待完成 | `src/pipeline/scorer.py` |
| **2.3** | 添加LLM反射过滤机制 | P0 | 4h | ⏳ 待完成 | `src/llm/pain_extractor.py` |
| **2.4** | 实现双层摘要策略 | P1 | 3h | ⏳ 待完成 | `src/llm/summarizer.py` |
| **2.5** | 优化去重阈值和规则 | P1 | 2h | ⏳ 待完成 | `src/pipeline/deduplicator.py` |

#### 任务详情

##### ⏳ 2.1 实现数据源分级权重系统
**文件**: `src/config/source_weights.py` (新建)
**目标**: 为不同数据源设置信号强度权重
**实现**:
```python
"""
数据源信号权重配置
根据运营计划书，将数据源分为A/B/C三类
"""

# A类强信号（权重4）：新产品、技术趋势最集中
A_TIER_SOURCES = {
    "ProductHunt": 4,
    "GitHub Trending": 4,
    "HackerNews": 4,
}

# B类中信号（权重2）：话题热但噪音较多
B_TIER_SOURCES = {
    "Reddit": 2,
    "YouTube": 2,
    "X": 2,
}

# C类弱信号（权重1）：偶尔能挖掘小众机会
C_TIER_SOURCES = {
    "GoogleTrends": 1,
    "Futurepedia": 1,
}

# 合并所有权重
SOURCE_WEIGHTS = {
    **A_TIER_SOURCES,
    **B_TIER_SOURCES,
    **C_TIER_SOURCES,
}

def get_source_weight(source: str) -> float:
    """获取数据源权重"""
    return SOURCE_WEIGHTS.get(source, 1.0)
```

**预计工时**: 3小时
**验收标准**:
- [ ] 配置文件创建完成
- [ ] 所有9个数据源都有权重定义
- [ ] 测试获取权重功能正常

---

##### ⏳ 2.2 修改评分器集成权重
**文件**: `src/pipeline/scorer.py`
**目标**: 将数据源权重纳入评分公式
**修改要点**:
```python
from src.config.source_weights import get_source_weight

# 在机会评分时加入权重
def score_opportunity(opportunity, pain_point):
    base_score = calculate_base_score(opportunity, pain_point)
    source_weight = get_source_weight(pain_point.source)

    # 最终评分 = 基础分 * 来源权重
    final_score = base_score * source_weight

    return final_score
```

**预计工时**: 2小时
**依赖**: 2.1
**验收标准**:
- [ ] ProductHunt来源的痛点得分 ≈ Reddit的2倍
- [ ] 输出的JSON中包含 `source_weight` 字段

---

##### ⏳ 2.3 添加LLM反射过滤机制
**文件**: `src/llm/pain_extractor.py`
**目标**: 在痛点提取后，用LLM判断是否有价值
**实现**:
```python
def reflect_filter(self, extracted_pain: dict) -> dict:
    """
    LLM反射过滤：判断痛点是否对专业读者有价值

    Returns:
        {
            "is_valuable": True/False,
            "reason": "判断理由",
            "original_pain": {...}
        }
    """
    prompt = f"""
请判断以下用户痛点是否对"想了解最新AI产品与趋势的专业读者"有价值。

痛点内容：{extracted_pain['summary_cn']}
关键词：{extracted_pain['extracted_keywords']}

判断标准：
✅ 有价值：明确表达需求、有商业潜力、市场空白、愿意付费
❌ 无价值：闲聊、重复话题、小众极端需求、纯抱怨

请只返回JSON格式：
{{
    "is_valuable": true/false,
    "reason": "判断理由（20字内）"
}}
"""

    response = self.llm_client.generate(prompt, temperature=0.3)
    result = json.loads(response)

    return {
        **result,
        "original_pain": extracted_pain
    }
```

**修改orchestrator.py**:
```python
# Phase 4: 提取痛点
extracted_pains = extract_pain_points(top_topics)

# Phase 4.5: 反射过滤（新增）
valuable_pains = []
for pain in extracted_pains:
    result = pain_extractor.reflect_filter(pain)
    if result["is_valuable"]:
        valuable_pains.append(pain)
    else:
        logger.info(f"过滤低价值痛点: {result['reason']}")

logger.info(f"反射过滤后保留 {len(valuable_pains)}/{len(extracted_pains)} 个痛点")
```

**预计工时**: 4小时
**验收标准**:
- [ ] "Yes"占比 ≥ 70%
- [ ] 日志显示过滤统计信息
- [ ] LLM成本增加 < 20%

---

##### ⏳ 2.4 实现双层摘要策略
**文件**: `src/llm/summarizer.py`
**目标**: 生成简短事实层 + 详细分类层摘要
**实现**:
```python
def generate_two_tier_summary(self, item: dict) -> dict:
    """
    双层摘要生成

    Returns:
        {
            "summary_short": "主题 + 功能 + 来源（30字内）",
            "summary_full": "详细描述（100字内）",
            "category": "DevTool/Creative/Agent/Productivity"
        }
    """

    # 第一层：事实要约
    prompt_short = f"""
请用30字内总结以下内容：
标题：{item['title']}
描述：{item['description']}

格式：主题 + 功能 + 来源
示例：Claude推出Artifacts功能，支持实时预览代码，来自ProductHunt
"""

    # 第二层：分类总结
    prompt_category = f"""
请将以下工具/话题归类到4个类别之一：
1. DevTool - 开发者工具
2. Creative - 创意工具
3. Agent - AI代理
4. Productivity - 生产力

内容：{item['title']} - {item['description']}

只返回类别名称。
"""

    summary_short = self.llm_client.generate(prompt_short, temperature=0.3)
    category = self.llm_client.generate(prompt_category, temperature=0.3).strip()

    return {
        "summary_short": summary_short,
        "summary_full": item.get("summary_cn", ""),  # 保留原有完整摘要
        "category": category
    }
```

**预计工时**: 3小时
**验收标准**:
- [ ] 输出JSON包含 `summary_short` 和 `category`
- [ ] 4个类别分布合理

---

##### ⏳ 2.5 优化去重阈值和规则
**文件**: `src/pipeline/deduplicator.py`
**目标**: 减少过度去重，提高输出数量
**修改**:
```python
# 调整阈值
PAIN_POINT_SIMILARITY_THRESHOLD = 0.70  # 从 0.60 提高到 0.70

# 新增规则：同一来源7天内不重复
def is_duplicate_with_history(pain_point, history_days=7):
    """检查与历史数据是否重复"""
    historical_pains = load_historical_pains(days=history_days)

    for historical in historical_pains:
        # 如果来源相同 + 关键词重叠 > 70%
        if (pain_point['source'] == historical['source'] and
            keyword_overlap(pain_point, historical) > 0.70):
            return True

    return False
```

**预计工时**: 2小时
**验收标准**:
- [ ] 输出机会数量 ≥ 10个（当前6个）
- [ ] 同一话题不在7天内重复出现

---

### Day 6-7：Dashboard功能增强

#### 进度：0/3 任务完成 (0%)

| 任务ID | 任务名称 | 优先级 | 预计工时 | 状态 | 负责文件 |
|--------|---------|--------|---------|------|---------|
| **3.1** | 创建搜索与过滤组件 | P1 | 4h | ⏳ 待完成 | `frontend/src/components/SearchBar.jsx` |
| **3.2** | 实现历史趋势可视化 | P2 | 5h | ⏳ 待完成 | `frontend/src/pages/TrendsHistory.jsx` |
| **3.3** | 移动端响应式优化 | P1 | 3h | ⏳ 待完成 | `frontend/src/index.css` |

#### 任务详情

##### ⏳ 3.1 创建搜索与过滤组件
**文件**: `frontend/src/components/SearchBar.jsx` (新建)
**目标**: 支持关键词搜索和多维过滤
**功能**:
- 关键词搜索（工具名、描述、标签）
- 来源过滤（ProductHunt、Reddit等）
- 类别过滤（DevTool、Creative等）
- 评分范围过滤（slider）

**实现示例**:
```jsx
import React, { useState } from 'react';
import { Search, Filter } from 'lucide-react';

export default function SearchBar({ onSearch, onFilter }) {
  const [keyword, setKeyword] = useState('');
  const [filters, setFilters] = useState({
    source: 'all',
    category: 'all',
    scoreMin: 0,
    scoreMax: 100
  });

  const handleSearch = () => {
    onSearch(keyword);
  };

  const handleFilterChange = (key, value) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFilter(newFilters);
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-4 mb-6">
      {/* 搜索框 */}
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          placeholder="搜索工具名称、描述、标签..."
          className="flex-1 px-4 py-2 border rounded-lg"
        />
        <button
          onClick={handleSearch}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Search className="w-5 h-5" />
        </button>
      </div>

      {/* 过滤器 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* 来源过滤 */}
        <select
          value={filters.source}
          onChange={(e) => handleFilterChange('source', e.target.value)}
          className="px-4 py-2 border rounded-lg"
        >
          <option value="all">所有来源</option>
          <option value="ProductHunt">ProductHunt</option>
          <option value="Reddit">Reddit</option>
          <option value="HackerNews">Hacker News</option>
        </select>

        {/* 类别过滤 */}
        <select
          value={filters.category}
          onChange={(e) => handleFilterChange('category', e.target.value)}
          className="px-4 py-2 border rounded-lg"
        >
          <option value="all">所有类别</option>
          <option value="DevTool">开发工具</option>
          <option value="Creative">创意工具</option>
          <option value="Agent">AI代理</option>
          <option value="Productivity">生产力</option>
        </select>

        {/* 评分范围 */}
        <div>
          <label className="text-sm text-gray-600">评分: {filters.scoreMin} - {filters.scoreMax}</label>
          <input
            type="range"
            min="0"
            max="100"
            value={filters.scoreMin}
            onChange={(e) => handleFilterChange('scoreMin', e.target.value)}
            className="w-full"
          />
        </div>
      </div>
    </div>
  );
}
```

**集成到页面**: 修改 `frontend/src/pages/Opportunities.jsx`
```jsx
import SearchBar from '../components/SearchBar';

export default function Opportunities() {
  const [filteredData, setFilteredData] = useState([]);

  const handleSearch = (keyword) => {
    // 实现搜索逻辑
  };

  const handleFilter = (filters) => {
    // 实现过滤逻辑
  };

  return (
    <div>
      <SearchBar onSearch={handleSearch} onFilter={handleFilter} />
      {/* 渲染筛选后的数据 */}
    </div>
  );
}
```

**预计工时**: 4小时
**验收标准**:
- [ ] 搜索功能正常
- [ ] 过滤器可联动
- [ ] 移动端显示友好

---

##### ⏳ 3.2 实现历史趋势可视化
**文件**: `frontend/src/pages/TrendsHistory.jsx` (新建)
**目标**: 展示历史数据趋势图表
**功能**:
- 每日机会数量趋势（折线图）
- 热门类别分布（饼图）
- Top 10机会7日追踪（表格）

**实现示例**:
```jsx
import React, { useState, useEffect } from 'react';
import { LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export default function TrendsHistory() {
  const [historyData, setHistoryData] = useState([]);

  useEffect(() => {
    // 加载历史数据（从 data/archive/ 读取）
    loadHistoricalData();
  }, []);

  const loadHistoricalData = async () => {
    // 读取最近7天的数据
    const dates = getLast7Days();
    const data = [];

    for (const date of dates) {
      const response = await fetch(`/data/archive/${date}.json`);
      if (response.ok) {
        const json = await response.json();
        data.push({
          date,
          opportunities_count: json.opportunities.length,
          ai_tools_count: json.ai_tools.length
        });
      }
    }

    setHistoryData(data);
  };

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">历史趋势分析</h1>

      {/* 机会数量趋势 */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">每日机会数量趋势</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={historyData}>
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="opportunities_count" stroke="#3b82f6" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* 类别分布 */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4">类别分布（最近7天）</h2>
        {/* 饼图实现 */}
      </div>
    </div>
  );
}
```

**预计工时**: 5小时
**验收标准**:
- [ ] 折线图显示正常
- [ ] 饼图显示正常
- [ ] 可切换日期范围

---

##### ⏳ 3.3 移动端响应式优化
**文件**: `frontend/src/index.css` 和各页面组件
**目标**: 确保所有页面在手机端显示正常
**检查点**:
- [ ] 首页卡片在小屏幕上垂直排列
- [ ] 表格在手机上横向滚动
- [ ] 搜索栏在手机上堆叠
- [ ] 图表在手机上正确缩放
- [ ] 按钮和链接足够大（至少44x44px）

**测试设备**:
- iPhone SE (375px)
- iPhone 14 Pro (390px)
- iPad (768px)

**预计工时**: 3小时
**验收标准**:
- [ ] Chrome DevTools移动设备测试通过
- [ ] 实际设备测试通过

---

## 🚀 第二周：增长机制与商业化（Day 8-14）

### Day 8-9：邀请码系统

#### 进度：0/4 任务完成 (0%)

| 任务ID | 任务名称 | 优先级 | 预计工时 | 状态 | 负责文件 |
|--------|---------|--------|---------|------|---------|
| **4.1** | 创建邀请码管理模块 | P0 | 3h | ⏳ 待完成 | `src/user/invite_manager.py` |
| **4.2** | 创建CLI邀请码生成工具 | P0 | 2h | ⏳ 待完成 | `src/cli/generate_invites.py` |
| **4.3** | 实现邀请注册页面 | P0 | 4h | ⏳ 待完成 | `frontend/src/pages/Invite.jsx` |
| **4.4** | 实现推荐奖励逻辑 | P1 | 3h | ⏳ 待完成 | `src/user/referral_manager.py` |

---

### Day 10-12：Stripe付费集成

#### 进度：0/6 任务完成 (0%)

| 任务ID | 任务名称 | 优先级 | 预计工时 | 状态 | 负责文件 |
|--------|---------|--------|---------|------|---------|
| **5.1** | 安装Stripe依赖并配置 | P0 | 1h | ⏳ 待完成 | `requirements.txt` |
| **5.2** | 创建Stripe订阅处理器 | P0 | 4h | ⏳ 待完成 | `src/payment/stripe_handler.py` |
| **5.3** | 实现Webhook回调处理 | P0 | 3h | ⏳ 待完成 | `src/payment/stripe_handler.py` |
| **5.4** | 创建前端订阅页面 | P0 | 4h | ⏳ 待完成 | `frontend/src/pages/Subscribe.jsx` |
| **5.5** | 创建Landing Page | P1 | 5h | ⏳ 待完成 | `frontend/src/pages/Landing.jsx` |
| **5.6** | 测试支付流程 | P0 | 2h | ⏳ 待完成 | - |

---

### Day 13：获客渠道搭建

#### 进度：0/3 任务完成 (0%)

| 任务ID | 任务名称 | 优先级 | 预计工时 | 状态 | 负责文件 |
|--------|---------|--------|---------|------|---------|
| **6.1** | 实现Twitter自动发布 | P1 | 3h | ⏳ 待完成 | `src/social/twitter_bot.py` |
| **6.2** | 实现Reddit周报发布 | P2 | 2h | ⏳ 待完成 | `src/social/reddit_poster.py` |
| **6.3** | SEO优化和公开周报页 | P1 | 3h | ⏳ 待完成 | `frontend/src/pages/WeeklyPublic.jsx` |

---

### Day 14：测试与上线

#### 进度：0/6 任务完成 (0%)

| 任务ID | 任务名称 | 优先级 | 预计工时 | 状态 | 验收标准 |
|--------|---------|--------|---------|------|---------|
| **7.1** | 端到端测试 | P0 | 3h | ⏳ 待完成 | 所有测试用例通过 |
| **7.2** | 性能测试 | P1 | 2h | ⏳ 待完成 | 首屏加载<2s |
| **7.3** | 安全测试 | P0 | 2h | ⏳ 待完成 | token泄露无法访问 |
| **7.4** | 生产环境部署 | P0 | 2h | ⏳ 待完成 | Render部署成功 |
| **7.5** | 生成50个Beta邀请码 | P0 | 1h | ⏳ 待完成 | 邀请码CSV导出 |
| **7.6** | 发送Beta测试邀请 | P0 | 2h | ⏳ 待完成 | 至少30人接受邀请 |

---

## 📊 进度追踪表

### 按优先级统计

| 优先级 | 任务数 | 已完成 | 完成率 | 说明 |
|--------|--------|--------|--------|------|
| **P0 (必须)** | 18 | 5 | 27.8% | 核心功能，必须完成 |
| **P1 (重要)** | 10 | 0 | 0% | 重要功能，尽量完成 |
| **P2 (可选)** | 4 | 0 | 0% | 增强功能，时间充裕再做 |

### 按模块统计

| 模块 | 任务数 | 已完成 | 待完成 | 完成率 |
|------|--------|--------|--------|--------|
| **后端认证** | 6 | 5 | 1 | 83.3% |
| **前端认证** | 2 | 0 | 2 | 0% |
| **数据质量** | 5 | 0 | 5 | 0% |
| **Dashboard UI** | 3 | 0 | 3 | 0% |
| **邀请系统** | 4 | 0 | 4 | 0% |
| **支付系统** | 6 | 0 | 6 | 0% |
| **获客渠道** | 3 | 0 | 3 | 0% |
| **测试上线** | 6 | 0 | 6 | 0% |

---

## 🚦 里程碑和关键路径

### 里程碑定义

| 里程碑 | 完成标准 | 目标日期 | 状态 |
|--------|---------|---------|------|
| **M1: 访问控制完成** | 后端+前端认证全部完成，token验证通过 | Day 3 | 🟡 进行中 (83%) |
| **M2: 数据质量达标** | "Yes"占比≥70%，机会数≥10个 | Day 5 | ⏳ 未开始 |
| **M3: Dashboard增强** | 搜索、过滤、历史趋势功能上线 | Day 7 | ⏳ 未开始 |
| **M4: 邀请系统上线** | 可生成邀请码，用户可注册 | Day 9 | ⏳ 未开始 |
| **M5: 支付系统上线** | Stripe集成完成，测试支付成功 | Day 12 | ⏳ 未开始 |
| **M6: 正式上线** | Beta邀请发送，至少30人注册 | Day 14 | ⏳ 未开始 |

### 关键路径（Critical Path）

```
Day 1-3: 访问控制 (M1)
  ├─ 1.1-1.5 后端认证 ✅ (已完成)
  ├─ 1.6 邮件签名URL ⏳ (阻塞 M4, M5)
  └─ 1.7-1.8 前端认证 ⏳ (阻塞所有后续功能)

Day 4-5: 数据质量 (M2)
  └─ 2.1-2.5 权重、过滤、摘要 ⏳ (独立路径，可并行)

Day 6-7: Dashboard (M3)
  └─ 3.1-3.3 UI增强 ⏳ (依赖 M1)

Day 8-9: 邀请系统 (M4)
  └─ 4.1-4.4 邀请码 ⏳ (依赖 M1, 1.6)

Day 10-12: 支付系统 (M5)
  └─ 5.1-5.6 Stripe ⏳ (依赖 M1, 1.6)

Day 13: 获客 (M6 准备)
  └─ 6.1-6.3 社交媒体 ⏳ (独立路径)

Day 14: 上线 (M6)
  └─ 7.1-7.6 测试部署 ⏳ (依赖所有前置里程碑)
```

**🚨 关键阻塞点**:
- **1.6 邮件签名URL** - 阻塞邀请系统和支付系统
- **1.7 前端token验证** - 阻塞所有需要认证的功能

**建议**: 优先完成 1.6-1.8，解除阻塞。

---

## 📈 每日进度报告模板

### Day X 进度报告

**日期**: 2025-11-XX
**工作时长**: X 小时

#### ✅ 已完成任务
- [ ] 任务ID - 任务名称 (耗时Xh)
  - 关键成果：...
  - 文件修改：...

#### ⏳ 进行中任务
- [ ] 任务ID - 任务名称 (已耗时Xh，预计还需Xh)
  - 当前进度：...
  - 遇到的问题：...

#### 🚫 阻塞问题
- 问题描述：...
- 影响范围：...
- 解决方案：...

#### 📊 今日统计
- 完成任务数：X / Y
- 代码提交数：X
- 新增文件：X
- 修改文件：X
- 代码行数：+XXX / -XXX

#### 📅 明日计划
1. 任务ID - 任务名称
2. 任务ID - 任务名称
3. ...

---

## 🎯 风险管理

### 已识别风险

| 风险ID | 风险描述 | 影响 | 概率 | 缓解措施 | 负责人 |
|--------|---------|------|------|---------|--------|
| **R1** | 前端token验证复杂度超预期 | 延期1-2天 | 中 | 简化为仅URL参数验证，后续迭代Cookie | - |
| **R2** | Stripe集成遇到技术问题 | 延期2-3天 | 中 | 先上线邀请制Beta，支付功能可后置 | - |
| **R3** | LLM反射过滤成本过高 | 超预算 | 低 | 添加关键词预筛选，减少LLM调用 | - |
| **R4** | 数据质量提升效果不明显 | 用户流失 | 中 | 预留buffer时间，可快速回滚 | - |
| **R5** | Beta用户数不足30人 | 延期上线 | 低 | 提前准备多个获客渠道（Twitter/Reddit/个人网络） | - |

### 应急预案

#### 场景1：Day 7未完成核心功能
**触发条件**: M1或M2未达成
**应急方案**:
1. 砍掉Dashboard增强功能（3.1-3.3）
2. 延期1周，专注核心功能
3. 与用户沟通延期原因

#### 场景2：Stripe集成失败
**触发条件**: Day 12支付测试失败
**应急方案**:
1. 改为纯邀请制Beta（免费）
2. 暂时不上线付费功能
3. 后续迭代时补充Stripe

#### 场景3：资源不足
**触发条件**: 单人开发时间不够
**应急方案**:
1. 启用MVP最小化策略
2. 仅完成P0任务（18个）
3. P1和P2任务移至Phase 2

---

## 📦 交付物清单

### 代码交付物

#### 后端模块
- [x] `src/auth/token_manager.py` - JWT Token管理器
- [x] `src/user/user_manager.py` - 用户管理器
- [x] `src/dashboard/auth_middleware.py` - Flask认证中间件
- [x] `src/database/schema.sql` - 数据库Schema v1.2
- [ ] `src/user/invite_manager.py` - 邀请码管理器
- [ ] `src/payment/stripe_handler.py` - Stripe支付处理器
- [ ] `src/config/source_weights.py` - 数据源权重配置
- [ ] `src/social/twitter_bot.py` - Twitter自动发布
- [ ] `src/social/reddit_poster.py` - Reddit周报发布

#### 前端组件
- [ ] `frontend/src/utils/auth.js` - 前端认证工具
- [ ] `frontend/src/pages/Expired.jsx` - 过期提示页
- [ ] `frontend/src/pages/Invite.jsx` - 邀请注册页
- [ ] `frontend/src/pages/Subscribe.jsx` - 订阅支付页
- [ ] `frontend/src/pages/Landing.jsx` - Landing Page
- [ ] `frontend/src/pages/WeeklyPublic.jsx` - 公开周报页
- [ ] `frontend/src/pages/TrendsHistory.jsx` - 历史趋势页
- [ ] `frontend/src/components/SearchBar.jsx` - 搜索过滤组件

#### 配置文件
- [x] `.env.example` - 环境变量配置（已更新JWT和Stripe）
- [ ] `requirements.txt` - Python依赖（需添加stripe）

### 文档交付物
- [x] `docs/IMPLEMENTATION_PLAN.md` - 本实装计划文档
- [ ] `docs/DEPLOYMENT_GUIDE.md` - 部署指南
- [ ] `docs/API_DOCUMENTATION.md` - API文档
- [ ] `docs/USER_GUIDE.md` - 用户使用指南

### 测试交付物
- [ ] 单元测试覆盖率报告
- [ ] 集成测试报告
- [ ] 端到端测试报告
- [ ] 性能测试报告

---

## 🔧 开发环境配置

### 本地开发启动清单

#### 后端启动
```bash
# 1. 激活虚拟环境
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化数据库
python -c "from src.database.init import init_database; init_database()"

# 4. 设置环境变量
cp .env.example .env
# 编辑 .env，填入必要的密钥

# 5. 启动Flask
python -m src.dashboard.app
```

#### 前端启动
```bash
cd frontend
npm install
npm run dev
```

### 必需的环境变量
```bash
# JWT密钥（必须）
JWT_SECRET_KEY=<生成强随机密钥>

# LLM API（必须）
OPENAI_API_KEY=sk-proj-xxx
LLM_PROVIDER=openai
LLM_MODEL=gpt-3.5-turbo

# 邮件服务（必须）
EMAIL_PROVIDER=smtp
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=<应用专用密码>

# Dashboard URL（必须）
DASHBOARD_BASE_URL=http://localhost:5000

# Stripe（支付功能必须）
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxx
```

---

## 📞 联系和支持

### 技术问题
- 认证系统问题：查看 `src/auth/token_manager.py` 注释
- 数据库问题：查看 `src/database/schema.sql` 注释
- 部署问题：参考 `docs/DEPLOYMENT_GUIDE.md`

### 进度追踪
- 使用本文档的进度表格
- 每日更新任务状态
- 每周生成进度报告

---

## 🎉 版本历史

| 版本 | 日期 | 更新内容 | 作者 |
|------|------|---------|------|
| 1.0 | 2025-11-07 | 初始版本，完整14天计划 | Claude Code |
| 1.1 | 2025-11-07 | 更新Day 1-3进度（5/6完成） | Claude Code |

---

**文档结束**
**最后更新**: 2025-11-07 13:50 UTC
**下次审查**: Day 3结束时
