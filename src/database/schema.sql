-- SQLite数据库Schema
-- Schema版本: 1.1
-- 创建日期: 2025-11-03

-- AI工具表
CREATE TABLE IF NOT EXISTS ai_tools (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    source TEXT NOT NULL CHECK(source IN ('Futurepedia', 'ProductHunt', 'There''s an AI for That')),
    url TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    tags TEXT NOT NULL,  -- JSON array
    features TEXT NOT NULL,  -- JSON array (v1.1)
    pricing_model TEXT NOT NULL CHECK(pricing_model IN ('free', 'freemium', 'paid', 'subscription')),  -- v1.1
    summary_cn TEXT DEFAULT '',
    summary_ja TEXT DEFAULT '',
    data_quality_score REAL DEFAULT 0.7 CHECK(data_quality_score >= 0 AND data_quality_score <= 1),  -- v1.1
    schema_version TEXT DEFAULT '1.1',
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_ai_tools_source ON ai_tools(source);
CREATE INDEX IF NOT EXISTS idx_ai_tools_timestamp ON ai_tools(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ai_tools_created_at ON ai_tools(created_at DESC);

-- 热点话题表
CREATE TABLE IF NOT EXISTS trending_topics (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    source TEXT NOT NULL CHECK(source IN ('TikTok', 'YouTube', 'X', 'Reddit', 'Google Trends')),
    url TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    heat_score REAL NOT NULL CHECK(heat_score >= 0 AND heat_score <= 100),
    trend_direction TEXT NOT NULL CHECK(trend_direction IN ('rising', 'falling', 'stable')),  -- v1.1
    tags TEXT NOT NULL,  -- JSON array
    summary_cn TEXT DEFAULT '',
    summary_ja TEXT DEFAULT '',
    data_quality_score REAL DEFAULT 0.7 CHECK(data_quality_score >= 0 AND data_quality_score <= 1),  -- v1.1
    schema_version TEXT DEFAULT '1.1',
    platforms TEXT,  -- JSON array (可选)
    trend_velocity REAL,  -- v1.1 (可选)
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_trending_topics_source ON trending_topics(source);
CREATE INDEX IF NOT EXISTS idx_trending_topics_heat_score ON trending_topics(heat_score DESC);
CREATE INDEX IF NOT EXISTS idx_trending_topics_timestamp ON trending_topics(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_trending_topics_created_at ON trending_topics(created_at DESC);

-- 用户痛点表
CREATE TABLE IF NOT EXISTS pain_points (
    id TEXT PRIMARY KEY,
    original_text TEXT NOT NULL,
    context_title TEXT NOT NULL,  -- v1.1
    extracted_keywords TEXT NOT NULL,  -- JSON array
    source TEXT NOT NULL CHECK(source IN ('Reddit', 'X', 'ProductHunt')),
    url TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    engagement_score REAL NOT NULL CHECK(engagement_score >= 0 AND engagement_score <= 100),
    confidence_score REAL NOT NULL CHECK(confidence_score >= 0 AND confidence_score <= 1),  -- v1.1
    tags TEXT NOT NULL,  -- JSON array
    summary_cn TEXT DEFAULT '',
    summary_ja TEXT DEFAULT '',
    data_quality_score REAL DEFAULT 0.7 CHECK(data_quality_score >= 0 AND data_quality_score <= 1),  -- v1.1
    schema_version TEXT DEFAULT '1.1',
    author_metadata TEXT,  -- JSON object (可选, v1.1)
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_pain_points_source ON pain_points(source);
CREATE INDEX IF NOT EXISTS idx_pain_points_confidence_score ON pain_points(confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_pain_points_timestamp ON pain_points(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_pain_points_created_at ON pain_points(created_at DESC);

-- 产品机会表
CREATE TABLE IF NOT EXISTS opportunities (
    id TEXT PRIMARY KEY,
    pain_point_id TEXT NOT NULL REFERENCES pain_points(id),
    related_tools TEXT NOT NULL,  -- JSON array of tool IDs
    related_topics TEXT NOT NULL,  -- JSON array of topic IDs
    opportunity_score REAL NOT NULL CHECK(opportunity_score >= 0 AND opportunity_score <= 100),
    mvp_suggestion_cn TEXT NOT NULL,
    mvp_suggestion_ja TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    tags TEXT NOT NULL,  -- JSON array
    data_quality_score REAL DEFAULT 0.7 CHECK(data_quality_score >= 0 AND data_quality_score <= 1),  -- v1.1
    schema_version TEXT DEFAULT '1.1',
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_opportunities_opportunity_score ON opportunities(opportunity_score DESC);
CREATE INDEX IF NOT EXISTS idx_opportunities_pain_point_id ON opportunities(pain_point_id);
CREATE INDEX IF NOT EXISTS idx_opportunities_timestamp ON opportunities(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_opportunities_created_at ON opportunities(created_at DESC);

-- 爬取日志表
CREATE TABLE IF NOT EXISTS scraping_logs (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('success', 'failed', 'partial')),
    records_count INTEGER NOT NULL CHECK(records_count >= 0),
    errors TEXT NOT NULL,  -- JSON array
    duration_seconds REAL NOT NULL CHECK(duration_seconds >= 0),
    timestamp TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_scraping_logs_source ON scraping_logs(source);
CREATE INDEX IF NOT EXISTS idx_scraping_logs_status ON scraping_logs(status);
CREATE INDEX IF NOT EXISTS idx_scraping_logs_timestamp ON scraping_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_scraping_logs_created_at ON scraping_logs(created_at DESC);

-- 版本信息表
CREATE TABLE IF NOT EXISTS schema_version (
    version TEXT PRIMARY KEY,
    applied_at TEXT DEFAULT (datetime('now')),
    description TEXT
);

-- 插入当前版本
INSERT OR IGNORE INTO schema_version (version, description) VALUES ('1.1', 'Initial schema with v1.1 enhancements');
