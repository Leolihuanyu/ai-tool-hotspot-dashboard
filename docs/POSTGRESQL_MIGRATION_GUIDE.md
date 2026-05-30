# PostgreSQL 迁移指南

本指南说明如何从 SQLite 迁移到 PostgreSQL，以及如何在两种数据库之间切换。

## 已完成的兼容性修改

### 修改的文件

1. **src/user/user_manager.py**
   - 用户管理的所有数据库操作
   - 12 个 SQL 查询已支持 PostgreSQL

2. **src/user/invite_manager.py**
   - 邀请码管理的所有数据库操作
   - 6 个 SQL 查询已支持 PostgreSQL

3. **src/user/referral_manager.py**
   - 推荐系统的所有数据库操作
   - 8 个 SQL 查询已支持 PostgreSQL

### 修改原理

所有修改都遵循以下模式：

```python
# 修改前
cursor.execute("SELECT * FROM users WHERE email = ?", (email,))

# 修改后
from src.database.connection import convert_placeholder

query = convert_placeholder("SELECT * FROM users WHERE email = ?")
cursor.execute(query, (email,))
```

`convert_placeholder()` 函数会根据当前配置的数据库类型：
- **SQLite**: 保持 `?` 占位符不变
- **PostgreSQL**: 将 `?` 转换为 `%s`

## 配置方式

### 1. 使用 SQLite（默认）

```bash
# 不设置 DB_TYPE 或设置为 sqlite
export DB_TYPE=sqlite
export DATABASE_PATH=data/dashboard.db
```

或在 `.env` 文件中：
```
DB_TYPE=sqlite
DATABASE_PATH=data/dashboard.db
```

### 2. 切换到 PostgreSQL

```bash
# 设置数据库类型为 postgresql
export DB_TYPE=postgresql

# 设置 PostgreSQL 连接字符串
export DATABASE_URL=<DATABASE_URL>
```

或在 `.env` 文件中：
```
DB_TYPE=postgresql
DATABASE_URL=<DATABASE_URL>
```

## 数据库迁移步骤

### 准备工作

1. 安装 PostgreSQL 驱动：
```bash
pip install psycopg2-binary
```

2. 创建 PostgreSQL 数据库：
```sql
CREATE DATABASE ai_tool_hotspot;
```

### 迁移数据

#### 方案 1: 使用迁移脚本

```bash
# 导出 SQLite 数据
python scripts/export_sqlite_data.py

# 导入到 PostgreSQL
python scripts/import_to_postgres.py
```

#### 方案 2: 手动迁移

1. 导出 SQLite 数据：
```bash
sqlite3 data/dashboard.db .dump > backup.sql
```

2. 转换 SQL 语法（主要是占位符和类型）：
   - 将 `?` 替换为 `$1, $2, ...`
   - 将 `INTEGER PRIMARY KEY AUTOINCREMENT` 改为 `SERIAL PRIMARY KEY`
   - 将 `DATETIME` 改为 `TIMESTAMP`

3. 导入到 PostgreSQL：
```bash
psql -U username -d ai_tool_hotspot -f backup.sql
```

### 运行数据库迁移

```bash
# 应用 schema
python -m src.database.init_db
```

## 验证迁移

### 运行测试脚本

```bash
python test_postgres_compatibility.py
```

应该看到：
```
✓ 所有检查通过！
```

### 测试连接

```python
from src.database.connection import get_connection, get_db_type

print(f"当前数据库类型: {get_db_type()}")

conn = get_connection()
cursor = conn.cursor()

# 测试查询
cursor.execute("SELECT COUNT(*) FROM users")
count = cursor.fetchone()[0]
print(f"用户数量: {count}")

conn.close()
```

## 性能优化建议

### PostgreSQL 配置

1. **索引优化**：
```sql
-- 为常用查询字段添加索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_invite_codes_code ON invite_codes(code);
CREATE INDEX idx_access_logs_email ON access_logs(email);
CREATE INDEX idx_referrals_referrer ON referrals(referrer_email);
```

2. **连接池配置**：
```python
# 在 src/database/connection.py 中添加连接池
from psycopg2 import pool

connection_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    **connection_params
)
```

## 回滚方案

如果遇到问题需要回滚到 SQLite：

```bash
# 1. 切换环境变量
export DB_TYPE=sqlite
export DATABASE_PATH=data/dashboard.db

# 2. 重启应用
# 应用会自动使用 SQLite
```

## 常见问题

### Q: 如何在开发环境使用 SQLite，生产环境使用 PostgreSQL？

A: 使用不同的 `.env` 文件：

**开发环境** (`.env.development`):
```
DB_TYPE=sqlite
DATABASE_PATH=data/dashboard.db
```

**生产环境** (`.env.production`):
```
DB_TYPE=postgresql
DATABASE_URL=<DATABASE_URL>
```

### Q: 如何确认当前使用的数据库类型？

A: 运行以下命令：
```python
from src.database.connection import get_db_type
print(get_db_type())
```

### Q: 占位符转换会影响性能吗？

A: 不会。`convert_placeholder()` 只是简单的字符串替换操作，性能影响可以忽略不计（通常小于 1 微秒）。

### Q: 是否需要修改现有代码？

A: 不需要。所有使用 `UserManager`, `InviteManager`, `ReferralManager` 的代码都不需要修改，只需要切换环境变量即可。

## 下一步

- [ ] 在测试环境验证 PostgreSQL 功能
- [ ] 进行性能对比测试
- [ ] 迁移生产数据
- [ ] 监控生产环境性能

## 支持

如有问题，请查看：
- [数据库连接代码](../src/database/connection.py)
- [测试脚本](../test_postgres_compatibility.py)
- [原始调查报告](./SQLITE_POSTGRESQL_INVESTIGATION.md)
