-- PostgreSQL数据库Schema
-- Schema版本: 1.1 (PostgreSQL兼容版本)
-- 创建日期: 2025-11-03
-- 转换日期: 2025-11-10
-- 说明: 从SQLite语法转换为PostgreSQL语法

-- AI工具表
CREATE TABLE IF NOT EXISTS ai_tools (
    id VARCHAR(255) PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    source TEXT NOT NULL CHECK(source IN ('Futurepedia', 'ProductHunt', 'There''s an AI for That')),
    url TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    tags TEXT NOT NULL,  -- JSON array (可使用JSONB类型优化)
    features TEXT NOT NULL,  -- JSON array (v1.1) (可使用JSONB类型优化)
    pricing_model TEXT NOT NULL CHECK(pricing_model IN ('free', 'freemium', 'paid', 'subscription')),  -- v1.1
    summary_cn TEXT DEFAULT '',
    summary_ja TEXT DEFAULT '',
    data_quality_score REAL DEFAULT 0.7 CHECK(data_quality_score >= 0 AND data_quality_score <= 1),  -- v1.1
    schema_version VARCHAR(10) DEFAULT '1.1',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ai_tools_source ON ai_tools(source);
CREATE INDEX IF NOT EXISTS idx_ai_tools_timestamp ON ai_tools(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ai_tools_created_at ON ai_tools(created_at DESC);

-- 热点话题表
CREATE TABLE IF NOT EXISTS trending_topics (
    id VARCHAR(255) PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    source TEXT NOT NULL CHECK(source IN ('TikTok', 'YouTube', 'X', 'Reddit', 'Google Trends')),
    url TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    heat_score REAL NOT NULL CHECK(heat_score >= 0 AND heat_score <= 100),
    trend_direction TEXT NOT NULL CHECK(trend_direction IN ('rising', 'falling', 'stable')),  -- v1.1
    tags TEXT NOT NULL,  -- JSON array (可使用JSONB类型优化)
    summary_cn TEXT DEFAULT '',
    summary_ja TEXT DEFAULT '',
    data_quality_score REAL DEFAULT 0.7 CHECK(data_quality_score >= 0 AND data_quality_score <= 1),  -- v1.1
    schema_version VARCHAR(10) DEFAULT '1.1',
    platforms TEXT,  -- JSON array (可选) (可使用JSONB类型优化)
    trend_velocity REAL,  -- v1.1 (可选)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_trending_topics_source ON trending_topics(source);
CREATE INDEX IF NOT EXISTS idx_trending_topics_heat_score ON trending_topics(heat_score DESC);
CREATE INDEX IF NOT EXISTS idx_trending_topics_timestamp ON trending_topics(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_trending_topics_created_at ON trending_topics(created_at DESC);

-- 用户痛点表
CREATE TABLE IF NOT EXISTS pain_points (
    id VARCHAR(255) PRIMARY KEY,
    original_text TEXT NOT NULL,
    context_title TEXT NOT NULL,  -- v1.1
    extracted_keywords TEXT NOT NULL,  -- JSON array (可使用JSONB类型优化)
    source TEXT NOT NULL CHECK(source IN ('Reddit', 'X', 'ProductHunt')),
    url TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    engagement_score REAL NOT NULL CHECK(engagement_score >= 0 AND engagement_score <= 100),
    confidence_score REAL NOT NULL CHECK(confidence_score >= 0 AND confidence_score <= 1),  -- v1.1
    tags TEXT NOT NULL,  -- JSON array (可使用JSONB类型优化)
    summary_cn TEXT DEFAULT '',
    summary_ja TEXT DEFAULT '',
    data_quality_score REAL DEFAULT 0.7 CHECK(data_quality_score >= 0 AND data_quality_score <= 1),  -- v1.1
    schema_version VARCHAR(10) DEFAULT '1.1',
    author_metadata TEXT,  -- JSON object (可选, v1.1) (可使用JSONB类型优化)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pain_points_source ON pain_points(source);
CREATE INDEX IF NOT EXISTS idx_pain_points_confidence_score ON pain_points(confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_pain_points_timestamp ON pain_points(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_pain_points_created_at ON pain_points(created_at DESC);

-- 产品机会表
CREATE TABLE IF NOT EXISTS opportunities (
    id VARCHAR(255) PRIMARY KEY,
    pain_point_id VARCHAR(255) NOT NULL REFERENCES pain_points(id),
    related_tools TEXT NOT NULL,  -- JSON array of tool IDs (可使用JSONB类型优化)
    related_topics TEXT NOT NULL,  -- JSON array of topic IDs (可使用JSONB类型优化)
    opportunity_score REAL NOT NULL CHECK(opportunity_score >= 0 AND opportunity_score <= 100),
    mvp_suggestion_cn TEXT NOT NULL,
    mvp_suggestion_ja TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    tags TEXT NOT NULL,  -- JSON array (可使用JSONB类型优化)
    data_quality_score REAL DEFAULT 0.7 CHECK(data_quality_score >= 0 AND data_quality_score <= 1),  -- v1.1
    schema_version VARCHAR(10) DEFAULT '1.1',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_opportunities_opportunity_score ON opportunities(opportunity_score DESC);
CREATE INDEX IF NOT EXISTS idx_opportunities_pain_point_id ON opportunities(pain_point_id);
CREATE INDEX IF NOT EXISTS idx_opportunities_timestamp ON opportunities(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_opportunities_created_at ON opportunities(created_at DESC);

-- 爬取日志表
CREATE TABLE IF NOT EXISTS scraping_logs (
    id VARCHAR(255) PRIMARY KEY,
    source TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('success', 'failed', 'partial')),
    records_count INTEGER NOT NULL CHECK(records_count >= 0),
    errors TEXT NOT NULL,  -- JSON array (可使用JSONB类型优化)
    duration_seconds REAL NOT NULL CHECK(duration_seconds >= 0),
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_scraping_logs_source ON scraping_logs(source);
CREATE INDEX IF NOT EXISTS idx_scraping_logs_status ON scraping_logs(status);
CREATE INDEX IF NOT EXISTS idx_scraping_logs_timestamp ON scraping_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_scraping_logs_created_at ON scraping_logs(created_at DESC);

-- 用户表（访问控制）
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    subscription_type TEXT NOT NULL CHECK(subscription_type IN ('beta', 'paid', 'free')),
    subscription_status TEXT DEFAULT 'active' CHECK(subscription_status IN ('active', 'cancelled', 'expired')),
    invite_code VARCHAR(50) UNIQUE,  -- 用户使用的邀请码
    referrer_id INTEGER,  -- 推荐人ID（用于推荐奖励）
    free_until TIMESTAMP,  -- 免费使用截止时间（推荐奖励）
    stripe_customer_id VARCHAR(255),  -- Stripe客户ID
    stripe_subscription_id VARCHAR(255),  -- Stripe订阅ID
    language VARCHAR(10) DEFAULT 'en',  -- 语言偏好 (zh/en/ja)
    timezone VARCHAR(50) DEFAULT 'UTC',  -- 用户时区 (IANA时区格式，如 Asia/Shanghai)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP,
    FOREIGN KEY (referrer_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_subscription_type ON users(subscription_type);
CREATE INDEX IF NOT EXISTS idx_users_invite_code ON users(invite_code);
CREATE INDEX IF NOT EXISTS idx_users_referrer_id ON users(referrer_id);
CREATE INDEX IF NOT EXISTS idx_users_timezone ON users(timezone);  -- 用于按时区查询订阅者

-- 访问日志表（安全审计）
CREATE TABLE IF NOT EXISTS access_logs (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    token_hash VARCHAR(64) NOT NULL,  -- token的SHA256哈希值（隐私保护）
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),  -- 访问IP地址 (支持IPv6)
    user_agent TEXT,  -- 浏览器User Agent
    access_result TEXT NOT NULL CHECK(access_result IN ('success', 'expired', 'invalid', 'ip_mismatch')),
    error_message TEXT,  -- 如果验证失败，记录错误信息
    FOREIGN KEY (email) REFERENCES users(email) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_access_logs_email ON access_logs(email);
CREATE INDEX IF NOT EXISTS idx_access_logs_accessed_at ON access_logs(accessed_at DESC);
CREATE INDEX IF NOT EXISTS idx_access_logs_access_result ON access_logs(access_result);

-- 推荐关系表（用于推荐奖励）
CREATE TABLE IF NOT EXISTS referrals (
    id SERIAL PRIMARY KEY,
    referrer_email VARCHAR(255) NOT NULL,  -- 推荐人邮箱
    referee_email VARCHAR(255) NOT NULL,  -- 被推荐人邮箱
    invite_code VARCHAR(50) NOT NULL,  -- 使用的邀请码
    reward_status TEXT DEFAULT 'pending' CHECK(reward_status IN ('pending', 'granted', 'expired')),
    reward_granted_at TIMESTAMP,  -- 奖励发放时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (referrer_email) REFERENCES users(email) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (referee_email) REFERENCES users(email) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE(referrer_email, referee_email)  -- 防止重复推荐
);

CREATE INDEX IF NOT EXISTS idx_referrals_referrer_email ON referrals(referrer_email);
CREATE INDEX IF NOT EXISTS idx_referrals_referee_email ON referrals(referee_email);
CREATE INDEX IF NOT EXISTS idx_referrals_reward_status ON referrals(reward_status);

-- 邀请码表（管理邀请码生成与使用）
CREATE TABLE IF NOT EXISTS invite_codes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,  -- 邀请码
    code_type TEXT NOT NULL CHECK(code_type IN ('beta', 'referral', 'partner')),
    max_uses INTEGER DEFAULT 1,  -- 最大使用次数（-1表示无限）
    current_uses INTEGER DEFAULT 0,  -- 当前使用次数
    created_by VARCHAR(255),  -- 创建人邮箱（如果是referral类型）
    expires_at TIMESTAMP,  -- 过期时间（可选）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,  -- 是否激活
    FOREIGN KEY (created_by) REFERENCES users(email) ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_invite_codes_code ON invite_codes(code);
CREATE INDEX IF NOT EXISTS idx_invite_codes_code_type ON invite_codes(code_type);
CREATE INDEX IF NOT EXISTS idx_invite_codes_is_active ON invite_codes(is_active);

-- 版本信息表
CREATE TABLE IF NOT EXISTS schema_version (
    version VARCHAR(10) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- 插入当前版本
INSERT INTO schema_version (version, description)
VALUES ('1.1', 'Initial schema with v1.1 enhancements')
ON CONFLICT (version) DO NOTHING;

INSERT INTO schema_version (version, description)
VALUES ('1.2', 'Added user management and access control tables')
ON CONFLICT (version) DO NOTHING;

-- PostgreSQL特定优化建议:
-- 1. 可将所有TEXT类型的JSON字段改为JSONB类型，提升查询性能
-- 2. 可添加GIN索引到JSONB字段上，加速JSON查询
-- 3. 考虑使用UUID类型替代VARCHAR主键
-- 4. 可添加触发器自动更新updated_at字段
