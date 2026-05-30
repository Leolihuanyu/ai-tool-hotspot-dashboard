# PostgreSQL/SQLite 兼容性修复报告

## 修复日期
2025-11-10

## 问题描述
`src/user/user_manager.py` 和 `src/user/referral_manager.py` 使用 `row[0]`, `row[1]` 等索引访问数据库查询结果,但:
- **SQLite**: 使用 `sqlite3.Row` 工厂,支持索引和字典访问
- **PostgreSQL**: 使用 `RealDictCursor`,返回字典,只能用键名访问(如 `row['id']`)

这导致代码在 PostgreSQL 环境下会报错 `TypeError: 'dict' object does not support indexing`

## 修复方案
参考 `src/user/invite_manager.py` 中已完成的修复,添加兼容两种格式的代码:

```python
# 兼容 SQLite (tuple/Row) 和 PostgreSQL (dict)
if isinstance(row, dict):
    user_info = {
        "id": row['id'],
        "email": row['email'],
        ...
    }
else:
    user_info = {
        "id": row[0],
        "email": row[1],
        ...
    }
```

## 修复文件和方法

### 1. src/user/user_manager.py

#### 修复的方法:

1. **`create_user()`** (第74-82行)
   - 修复推荐人ID查询的兼容性
   - 变更: `referrer_id = referrer[0]` → 兼容代码

2. **`get_user()`** (第170-200行)
   - 修复用户信息返回的兼容性
   - 影响字段: id, email, subscription_type, subscription_status, invite_code, referrer_id, free_until, stripe_customer_id, stripe_subscription_id, created_at, updated_at, last_accessed_at

3. **`get_access_logs()`** (第393-417行)
   - 修复访问日志列表的兼容性
   - 影响字段: id, email, token_hash, accessed_at, ip_address, user_agent, access_result, error_message

4. **`get_all_active_users()`** (第451-480行)
   - 修复活跃用户列表的兼容性
   - 影响字段: id, email, subscription_type, free_until

### 2. src/user/referral_manager.py

#### 修复的方法:

1. **`grant_referral_reward()`** (第81-87行, 第114-115行)
   - 修复推荐关系记录查询的兼容性
   - 影响字段: id, reward_status (第一处)
   - 影响字段: free_until (第二处)

2. **`get_referral_history()`** (第227-249行)
   - 修复推荐历史列表的兼容性
   - 影响字段: id, referrer_email, referee_email, invite_code, reward_status, reward_granted_at, created_at

3. **`get_referral_stats()`** (第294-302行)
   - 修复推荐统计查询的兼容性
   - 影响字段: total, pending, granted (聚合查询结果)

4. **`auto_grant_pending_rewards()`** (第415-422行)
   - 修复待处理推荐列表的兼容性
   - 影响字段: referrer_email, referee_email

## 测试结果

### SQLite 测试 (默认环境)
```bash
$ source venv/bin/activate
$ python test_db_compatibility.py

✅ InviteManager 所有测试通过!
✅ UserManager 所有测试通过!
   - get_user: ✓
   - get_access_logs: ✓
   - get_all_active_users: ✓
✅ ReferralManager 所有测试通过!
   - grant_referral_reward: ✓
   - get_referral_history: ✓
   - get_referral_stats: ✓
   - auto_grant_pending_rewards: ✓
```

### PostgreSQL 测试
设置环境变量后测试:
```bash
export DB_TYPE=postgresql
export DATABASE_URL=<DATABASE_URL>
python test_db_compatibility.py
```

## 代码规范

### 字典键名规范
确保字典键名与 SELECT 语句中的列名完全匹配:

```python
# ✓ 正确
query = "SELECT id, email, created_at FROM users"
...
user_id = row['id'] if isinstance(row, dict) else row[0]
email = row['email'] if isinstance(row, dict) else row[1]

# ✗ 错误 (键名不匹配)
user_id = row['user_id'] if isinstance(row, dict) else row[0]  # 查询中是 'id' 不是 'user_id'
```

### 聚合查询规范
聚合函数需要使用 `AS` 别名:

```python
# ✓ 正确
query = """
    SELECT COUNT(*) as total,
           SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_count
    FROM users
"""
total = row['total'] if isinstance(row, dict) else row[0]

# ✗ 错误 (没有别名)
query = "SELECT COUNT(*) FROM users"
total = row['COUNT(*)'] if isinstance(row, dict) else row[0]  # PostgreSQL 可能不支持
```

## 参考实现

完整的兼容性代码参考 `src/user/invite_manager.py`:
- `validate_code()` 方法 (第231-255行)
- `get_code_info()` 方法 (第334-358行)
- `get_all_codes()` 方法 (第422-446行)

## 影响范围

### 已修复
- ✅ `src/user/invite_manager.py` (已完成,作为参考)
- ✅ `src/user/user_manager.py` (本次修复)
- ✅ `src/user/referral_manager.py` (本次修复)

### 待检查
建议检查以下模块是否有类似问题:
- `src/auth/token_manager.py`
- `src/payment/*` (如果有数据库访问)
- `src/dashboard/routes.py` (如果直接执行SQL)

## 注意事项

1. **不要修改 SQL 查询语句** - 只修改数据访问部分
2. **保持列名一致性** - 字典键名必须与 SELECT 列名匹配
3. **测试两种环境** - SQLite 和 PostgreSQL 都要测试
4. **使用 isinstance() 检查** - 这是最可靠的类型检查方法

## 相关文档

- 数据库连接管理: `src/database/connection.py`
- SQLite Row 工厂: https://docs.python.org/3/library/sqlite3.html#sqlite3.Row
- psycopg2 RealDictCursor: https://www.psycopg.org/docs/extras.html#psycopg2.extras.RealDictCursor
