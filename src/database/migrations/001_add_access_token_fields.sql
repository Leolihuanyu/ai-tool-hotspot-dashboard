-- 数据库迁移脚本：添加 access_token 相关字段
-- 迁移版本: 1.3
-- 创建日期: 2025-11-14
-- 说明: 为 users 表添加长期访问token字段

-- 添加字段（如果不存在）
DO $$
BEGIN
    -- 添加 access_token 字段
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='users' AND column_name='access_token'
    ) THEN
        ALTER TABLE users ADD COLUMN access_token TEXT;
        RAISE NOTICE 'Added column: access_token';
    END IF;

    -- 添加 token_generated_at 字段
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='users' AND column_name='token_generated_at'
    ) THEN
        ALTER TABLE users ADD COLUMN token_generated_at TIMESTAMP;
        RAISE NOTICE 'Added column: token_generated_at';
    END IF;

    -- 添加 token_expires_at 字段
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='users' AND column_name='token_expires_at'
    ) THEN
        ALTER TABLE users ADD COLUMN token_expires_at TIMESTAMP;
        RAISE NOTICE 'Added column: token_expires_at';
    END IF;
END $$;

-- 创建索引（如果不存在）
CREATE INDEX IF NOT EXISTS idx_users_access_token ON users(access_token);

-- 记录迁移版本
INSERT INTO schema_version (version, description)
VALUES ('1.3', 'Added access_token fields to users table for long-term authentication')
ON CONFLICT (version) DO NOTHING;

-- 打印完成信息
DO $$
BEGIN
    RAISE NOTICE 'Migration 001_add_access_token_fields.sql completed successfully';
END $$;
