-- ========================================
-- 清空并重建Supabase生产数据库
-- ========================================
-- ⚠️  警告：此脚本会删除所有数据！
-- 请在Supabase SQL Editor中执行
-- ========================================

-- 步骤1: 删除所有表（按依赖关系倒序）
-- ========================================

-- 删除有外键依赖的表
DROP TABLE IF EXISTS access_logs CASCADE;
DROP TABLE IF EXISTS referrals CASCADE;
DROP TABLE IF EXISTS invite_codes CASCADE;
DROP TABLE IF EXISTS schema_version CASCADE;

-- 删除users表（被referrals和access_logs引用）
DROP TABLE IF EXISTS users CASCADE;

-- 删除业务数据表
DROP TABLE IF EXISTS scraping_logs CASCADE;
DROP TABLE IF EXISTS opportunities CASCADE;
DROP TABLE IF EXISTS pain_points CASCADE;
DROP TABLE IF EXISTS trending_topics CASCADE;
DROP TABLE IF EXISTS ai_tools CASCADE;

-- ========================================
-- 步骤2: 重建所有表（从schema.sql复制）
-- ========================================
--
-- 请在Supabase SQL Editor中执行以下操作：
-- 1. 先执行上面的DROP语句
-- 2. 然后复制粘贴 src/database/schema.sql 的全部内容
--
-- 或者直接在终端执行：
-- psql $DATABASE_URL < src/database/schema.sql
--
-- ========================================

-- 完成后，数据库将包含：
-- ✅ 所有表结构（包括access_token等新字段）
-- ✅ 所有索引
-- ✅ 所有约束
-- ❌ 无任何数据（需要重新注册用户）
