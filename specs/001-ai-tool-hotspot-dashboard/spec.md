# Feature Specification: AI工具与热点机会发现仪表板

**Feature Branch**: `001-ai-tool-hotspot-dashboard`
**Created**: 2025-11-03
**Status**: Draft
**Input**: User description: "范围：
1. 数据源：
   - AI工具：Futurepedia RSS、There's an AI for That、ProductHunt Trending；
   - 大众热点：TikTok Trending、YouTube Shorts、X Trending、Reddit热门讨论、Google Trends；
   - 痛点提取：Reddit / X / ProductHunt 评论中带有 "need a tool for…"、"wish there was an app that…" 等关键词的帖子。
2. 流程：
   抓取 → 规范化 → 去重 → 分类 → 痛点提取 → 相关性匹配 → 评分 → 摘要（中日双语） → 输出JSON → 仪表板+日报。
3. 输出：
   - Flask Web仪表板（含AI工具榜、热点榜、机会榜三页）
   - 每日Top10机会邮件日报（含中日双语摘要与MVP建议）

目标：
- 帮助个人或小团队快速发现"可做、能卖、能落地"的AI产品创意；
- 将分散的热点信息转化为结构化的创业灵感。

成功标准：
- 每日聚合≥30条有效信息；
- 任一数据源失败不影响整体；
- 仪表板3秒内加载；
- 邮件日报按计划发送；
- 报告中自动生成Top5机会榜。

非目标：
- 用户账户系统；
- 实时推送；
- 移动App或Notion同步。"

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - 查看每日AI工具趋势榜单 (Priority: P1)

作为产品创业者,我希望每天能在仪表板上看到最新的AI工具趋势,以便快速了解市场动态和竞争对手。

**Why this priority**: 这是核心价值主张的基础,提供市场洞察是系统的首要功能。没有数据聚合和展示,其他功能都无法实现。

**Independent Test**: 可以通过访问仪表板的AI工具榜页面,验证是否显示至少30条来自多个数据源(Futurepedia、There's an AI for That、ProductHunt)的最新AI工具信息,每条包含名称、描述、来源和时间戳。

**Acceptance Scenarios**:

1. **Given** 系统在过去24小时内成功抓取了多个数据源, **When** 用户访问仪表板的"AI工具榜"页面, **Then** 页面在3秒内加载并显示至少30条AI工具信息,按时间倒序排列
2. **Given** 某个数据源(如Futurepedia RSS)暂时不可用, **When** 系统执行数据抓取, **Then** 其他数据源的数据仍正常展示,不影响整体功能
3. **Given** 用户正在浏览AI工具榜, **When** 用户点击某条工具信息, **Then** 系统显示该工具的详细信息,包括来源URL、标签和中日双语摘要

---

### User Story 2 - 发现大众热点趋势 (Priority: P1)

作为内容创作者或产品经理,我希望看到当前社交媒体和搜索引擎上的热门话题,以便把握用户兴趣点和市场需求。

**Why this priority**: 热点发现是产品创意的另一个核心输入,与AI工具榜同等重要,帮助用户识别市场需求和用户关注点。

**Independent Test**: 可以通过访问"热点榜"页面,验证是否显示来自TikTok、YouTube Shorts、X、Reddit、Google Trends的热点话题,每条包含话题标题、热度指标、来源和时间。

**Acceptance Scenarios**:

1. **Given** 系统已从多个社交平台抓取热点数据, **When** 用户访问"热点榜"页面, **Then** 显示至少30条热点话题,包含来源标识和热度排名
2. **Given** 用户在浏览热点列表, **When** 用户按来源筛选(如只看TikTok或Reddit), **Then** 页面只显示选中来源的热点数据
3. **Given** 同一热点在多个平台出现, **When** 系统处理数据, **Then** 系统将其识别为同一热点并合并展示,标注出现的平台列表

---

### User Story 3 - 识别产品机会与痛点 (Priority: P1)

作为创业者,我希望系统能从用户评论中提取产品痛点(如"需要一个工具来..."、"希望有个应用能..."),并与AI工具和热点匹配,生成可行的产品创意。

**Why this priority**: 这是系统的核心差异化功能,将原始数据转化为可执行的商业洞察,直接支撑用户的创业决策。

**Independent Test**: 可以通过访问"机会榜"页面,验证是否显示Top 10产品机会,每条包含痛点描述、相关AI工具、相关热点、机会评分和MVP建议。

**Acceptance Scenarios**:

1. **Given** 系统已从Reddit、X、ProductHunt评论中提取至少50条痛点, **When** 用户访问"机会榜"页面, **Then** 显示Top 10机会,每条包含痛点原文、相关性评分、匹配的AI工具和热点
2. **Given** 用户查看某个机会详情, **When** 用户点击该机会, **Then** 系统显示中日双语的详细摘要和MVP实现建议
3. **Given** 某个痛点与多个AI工具相关, **When** 系统计算机会评分, **Then** 评分考虑痛点热度、工具数量、热点相关性三个维度

---

### User Story 4 - 接收每日机会报告邮件 (Priority: P2)

作为忙碌的产品经理,我希望每天早上能收到一封邮件,总结Top 10产品机会,这样我不用每天登录仪表板就能获取关键信息。

**Why this priority**: 这是便利性功能,提升用户留存和活跃度,但不影响核心数据处理流程。

**Independent Test**: 可以通过配置邮件地址并等待24小时,验证是否收到包含Top 10机会、中日双语摘要和MVP建议的邮件。

**Acceptance Scenarios**:

1. **Given** 用户已配置接收邮件的地址, **When** 系统每日定时任务运行(假设每天早上8点), **Then** 用户在30分钟内收到包含Top 10机会的邮件
2. **Given** 邮件发送失败(如邮件服务器不可用), **When** 系统检测到失败, **Then** 系统记录错误日志并在下次调度时重试,最多重试3次
3. **Given** 用户在邮件中看到某个机会, **When** 用户点击邮件中的链接, **Then** 浏览器打开仪表板并直接定位到该机会的详情页面

---

### User Story 5 - 浏览历史数据和趋势变化 (Priority: P3)

作为市场研究人员,我希望能查看过去7天或30天的AI工具和热点趋势变化,以便分析市场演进和预测未来方向。

**Why this priority**: 这是增强型分析功能,为深度用户提供额外价值,但不是MVP必需功能。

**Independent Test**: 可以通过在仪表板上选择时间范围(如"过去7天"),验证是否显示历史数据和趋势图表。

**Acceptance Scenarios**:

1. **Given** 系统已存储至少7天的历史数据, **When** 用户在仪表板选择"过去7天"时间范围, **Then** 页面显示该时间段内的所有数据,并生成趋势折线图
2. **Given** 用户查看某个AI工具的历史趋势, **When** 用户点击该工具的历史按钮, **Then** 系统显示该工具在过去30天的热度变化曲线
3. **Given** 用户想对比两个不同热点的趋势, **When** 用户选择两个热点并点击对比, **Then** 系统在同一图表上显示两条趋势线

---

### Edge Cases

- 当所有数据源同时失败时,系统应显示友好的错误提示,说明数据暂时不可用,并显示上次成功更新的时间
- 当抓取到的数据量不足30条时,系统应显示所有可用数据,并标注数据量不足的警告
- 当痛点提取逻辑未找到任何匹配关键词时,系统应记录日志但不影响其他数据的展示
- 当邮件地址格式无效或邮件服务配置错误时,系统应在配置界面显示错误提示,并提供配置验证功能
- 当用户网络较慢导致页面加载超过3秒时,系统应显示加载进度指示器,避免用户误以为系统卡死
- 当同一数据在多次抓取中重复出现时,去重逻辑应基于内容指纹(如标题+来源URL的哈希值)进行判断
- 当中文或日文摘要生成失败时,系统应显示原始英文内容或错误提示,不阻塞整体流程

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统必须每日从至少6个数据源抓取数据,包括Futurepedia RSS、There's an AI for That、ProductHunt Trending、TikTok Trending、YouTube Shorts、X Trending、Reddit热门讨论、Google Trends
- **FR-002**: 系统必须对所有抓取的数据进行规范化处理,统一为包含id、标题、描述、来源、URL、时间戳、标签的标准格式
- **FR-003**: 系统必须基于内容指纹(标题+URL哈希)对重复数据进行去重,避免同一信息重复展示
- **FR-004**: 系统必须将数据分类为"AI工具"、"热点话题"、"用户痛点"三类
- **FR-005**: 系统必须从Reddit、X、ProductHunt评论中提取包含特定关键词(如"need a tool for"、"wish there was an app that")的用户痛点
- **FR-006**: 系统必须将提取的痛点与AI工具和热点进行相关性匹配,基于关键词重叠度、语义相似度和时间接近度计算匹配分数
- **FR-007**: 系统必须为每个机会生成评分,综合考虑痛点热度(评论数/点赞数)、相关工具数量、热点相关性三个维度
- **FR-008**: 系统必须为所有数据生成中文和日文双语摘要,摘要长度不超过200字符
- **FR-009**: 系统必须将处理后的数据以JSON格式持久化存储,包含schema_version字段
- **FR-010**: 系统必须提供Web仪表板,包含"AI工具榜"、"热点榜"、"机会榜"三个独立页面
- **FR-011**: 仪表板的"AI工具榜"页面必须显示至少30条最新AI工具,按时间倒序排列,支持按来源筛选
- **FR-012**: 仪表板的"热点榜"页面必须显示至少30条热点话题,按热度排序,支持按平台筛选
- **FR-013**: 仪表板的"机会榜"页面必须显示Top 10产品机会,每条包含痛点描述、相关AI工具列表、相关热点列表、机会评分、MVP建议
- **FR-014**: 系统必须提供每日邮件报告功能,在指定时间(默认每天早上8点)发送包含Top 10机会的邮件
- **FR-015**: 邮件内容必须包含中日双语摘要、机会评分、MVP建议、以及跳转到仪表板详情页的链接
- **FR-016**: 系统必须在单个数据源失败时继续处理其他数据源,不中断整体流程
- **FR-017**: 系统必须记录所有数据抓取、处理、展示的错误日志,包含时间戳、错误类型、受影响的数据源
- **FR-018**: 系统必须提供数据抓取的手动触发接口,用于测试和紧急数据更新
- **FR-019**: 系统必须支持配置邮件接收地址,并提供邮件配置验证功能
- **FR-020**: 所有JSON输出必须包含schema_version字段,遵循Constitution Principle II(统一数据模型)
- **FR-021**: 系统必须在抓取用户痛点时同时获取帖子或讨论的标题(context_title),以提供完整的问题背景和上下文
- **FR-022**: 系统必须在抓取AI工具时提取功能列表(features)和定价模式(pricing_model),用于与痛点进行精确功能匹配
- **FR-023**: 系统必须为每条抓取的数据计算数据质量评分(data_quality_score,0-1),基于来源可靠性、内容完整性和数据新鲜度三个维度
- **FR-024**: 系统必须为用户痛点计算置信度评分(confidence_score,0-1),基于关键词匹配度、来源可靠性和互动质量,用于过滤低质量或噪音数据
- **FR-025**: 系统必须计算热点的趋势方向(trend_direction),通过对比当前热度与历史热度(如过去24小时)判断为上升、下降或稳定

### Key Entities

> **Constitution Principle II (Unified Data Model)**: All entities MUST be defined in `src/models/` with versioned schemas. Include schema_version in all JSON outputs.

- **AITool**: 代表从AI工具数据源抓取的工具信息
  - 必需属性: id(唯一标识符), name(工具名称), description(工具描述), source(数据来源,如"Futurepedia"、"ProductHunt"), url(原始链接), timestamp(抓取/发布时间), tags(标签列表,如["productivity", "image-generation"]), features(功能列表,如["text-generation", "image-editing"]), pricing_model(定价模式: "free"/"freemium"/"paid"/"subscription"), summary_cn(中文摘要), summary_ja(日文摘要), data_quality_score(数据质量评分,0-1), schema_version(数据模型版本)

- **TrendingTopic**: 代表从社交平台和搜索引擎抓取的热点话题
  - 必需属性: id, title(话题标题), description(话题描述), source(来源平台,如"TikTok"、"Reddit"、"Google Trends"), url, timestamp, heat_score(热度分数), trend_direction(趋势方向: "rising"上升/"falling"下降/"stable"稳定), tags, summary_cn, summary_ja, data_quality_score(数据质量评分,0-1), schema_version
  - 可选属性: platforms(如果同一热点在多个平台出现,记录所有平台列表), trend_velocity(趋势速度,热度增长率百分比)

- **UserPainPoint**: 代表从评论中提取的用户痛点
  - 必需属性: id, original_text(原始评论文本), context_title(帖子/讨论标题,提供完整背景), extracted_keywords(提取的关键词列表), source(来源,如"Reddit"、"X"、"ProductHunt"), url(评论链接), timestamp, engagement_score(互动分数,基于点赞/评论数), confidence_score(痛点置信度,0-1,基于关键词匹配度和来源可靠性), tags, summary_cn, summary_ja, data_quality_score(数据质量评分,0-1), schema_version
  - 可选属性: author_metadata(作者元信息,如账号类型、粉丝数等,用于判断痛点权威性)

- **Opportunity**: 代表匹配后的产品机会
  - 必需属性: id, pain_point_id(关联的痛点ID), related_tools(关联的AI工具ID列表), related_topics(关联的热点话题ID列表), opportunity_score(机会评分,0-100), mvp_suggestion_cn(中文MVP建议), mvp_suggestion_ja(日文MVP建议), timestamp, tags, data_quality_score(数据质量评分,0-1), schema_version
  - 评分计算: opportunity_score = [(pain_point.engagement_score * 0.4) + (related_tools.count * 10 * 0.3) + (related_topics.heat_score * 0.3)] * pain_point.confidence_score * 平均data_quality_score,归一化到0-100范围。低置信度或低质量数据会被降权

**Schema Version**: 1.1 (MAJOR.MINOR format - MAJOR for breaking changes, MINOR for additions)

**版本变更说明**:
- v1.0 → v1.1: 新增字段以支持更精确的LLM分析和数据质量控制
  - 所有实体新增 `data_quality_score`
  - AITool 新增 `features`, `pricing_model`
  - TrendingTopic 新增 `trend_direction`, `trend_velocity`(可选)
  - UserPainPoint 新增 `context_title`, `confidence_score`, `author_metadata`(可选)
  - Opportunity 评分公式优化,加入质量权重

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 系统每日聚合至少30条有效信息(跨所有数据源的总和),数据新鲜度在24小时内
- **SC-002**: 当任意单个数据源失败时,系统仍能正常运行并展示其他数据源的数据,整体可用性不低于80%(即最多2个数据源同时失败)
- **SC-003**: 仪表板任意页面(AI工具榜、热点榜、机会榜)在正常网络条件下(10Mbps带宽)3秒内完成首屏加载
- **SC-004**: 每日邮件报告在计划时间(如每天早上8点)后30分钟内成功发送,发送成功率不低于95%(每月统计)
- **SC-005**: 机会榜自动生成至少5条有效产品机会(opportunity_score >= 60),每条包含完整的中日双语摘要和MVP建议
- **SC-006**: 数据去重准确率达到90%以上,即同一内容重复出现时,90%以上情况被正确识别和去重
- **SC-007**: 用户能在仪表板上通过来源筛选、时间排序等方式,在10秒内找到自己关注的特定类型信息(通过用户测试验证)
- **SC-008**: 系统错误率低于5%,即每100次数据抓取操作中,成功完成至少95次(部分数据源失败但整体流程完成视为成功)

## Assumptions

1. **数据源API稳定性**: 假设大部分数据源(如Futurepedia RSS、ProductHunt)提供相对稳定的公开API或RSS feed,偶尔的不可用(如API限流、服务器维护)不超过10%的时间
2. **数据量规模**: 假设每日从所有数据源抓取的原始数据总量在100-500条之间,去重和分类后保留30-100条有效数据
3. **语言处理能力**: 假设使用现有的机器翻译或NLP工具(如Google Translate API、OpenAI API)生成中日双语摘要,翻译质量达到可读水平(无需完美翻译)
4. **邮件发送基础设施**: 假设系统可以访问SMTP服务器(如Gmail SMTP、SendGrid)进行邮件发送,配置由用户或部署环境提供
5. **用户数量**: 初期假设用户数量较少(个人或小团队使用,日活跃用户<100),不需要复杂的负载均衡或分布式架构
6. **数据存储**: 假设使用本地文件系统或轻量级数据库(如SQLite)存储JSON数据,数据量在初期不会超过10GB
7. **隐私和合规**: 假设所有抓取的数据来自公开平台,不涉及用户隐私数据,符合各平台的爬虫政策和使用条款
8. **MVP范围**: 假设MVP建议以文本描述为主,不涉及代码生成或原型设计工具集成

## Out of Scope

以下功能明确不在本次功能范围内,用户已明确排除:

1. **用户账户系统**: 不提供用户注册、登录、权限管理等功能,系统假设单用户或团队内部使用
2. **实时推送**: 不提供浏览器通知、WebSocket实时更新等功能,用户需手动刷新页面或依赖每日邮件
3. **移动App**: 不开发iOS或Android原生应用,仅提供Web仪表板
4. **Notion同步**: 不提供与Notion、Trello等第三方协作工具的集成或数据同步功能
5. **付费功能**: 不涉及订阅、付费解锁高级功能等商业模式
6. **社交功能**: 不提供评论、点赞、分享等社交互动功能
7. **AI生成工具**: 不提供基于机会自动生成产品原型、代码或设计稿的功能,仅提供文本建议
