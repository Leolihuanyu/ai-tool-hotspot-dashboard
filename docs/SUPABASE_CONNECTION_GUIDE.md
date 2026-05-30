# Supabase 连接配置指南

## 问题诊断

当前遇到的 DNS 解析错误:
```
could not translate host name "db.<SUPABASE_PROJECT_REF>.supabase.co" to address
```

**原因**: 使用了错误的连接字符串格式。Supabase 推荐使用 **Connection Pooling** 模式,而不是 Direct Connection。

---

## 获取正确连接字符串的步骤

### 1. 登录 Supabase Dashboard

访问: https://supabase.com/dashboard/project/<SUPABASE_PROJECT_REF>

### 2. 进入数据库设置

1. 点击左侧边栏的 **Settings** (齿轮图标)
2. 在设置菜单中点击 **Database**

### 3. 找到 Connection String 区域

在 Database 设置页面,你会看到多个连接字符串选项:

```
Connection string
├─ URI (默认选中)
├─ JDBC
├─ .NET
└─ ...
```

### 4. 选择 Connection Pooling (重要!)

**不要使用** "Connection string" 部分的内容!

往下滚动,找到 **"Connection Pooling"** 部分。

在 Connection Pooling 中,你会看到:
- **Mode** 下拉选择: `Transaction` / `Session`
- **URI** 格式的连接字符串

### 5. 选择 Mode

推荐使用 **Transaction** 模式 (适合短连接,性能更好)

或者使用 **Session** 模式 (适合长连接)

### 6. 复制 URI 连接字符串

连接字符串格式应该类似:

```
# Transaction mode (推荐):
<DATABASE_URL>

# Session mode:
<DATABASE_URL>
```

**注意事项**:
- 主机名应该是 `aws-0-<region>.pooler.supabase.com` 格式
- Transaction 模式端口是 `6543`
- Session 模式端口是 `5432`
- `[YOUR-PASSWORD]` 需要替换为你的数据库密码: `<DB_PASSWORD>`

---

## 正确 vs 错误的连接字符串

### ❌ 错误 (Direct Connection - 会导致 DNS 错误):
```
<DATABASE_URL>
```

### ✅ 正确 (Connection Pooling):
```
<DATABASE_URL>
```

**关键区别**:
1. 用户名格式: `postgres.项目ID` (不是 `postgres`)
2. 主机名: `aws-0-region.pooler.supabase.com` (不是 `db.项目ID.supabase.co`)
3. 端口: `6543` for Transaction / `5432` for Session

---

## 验证项目状态

在继续之前,请确认:

1. **项目状态**: Dashboard 顶部应该显示项目为 "Active" (绿色状态)
2. **数据库已启动**: Database 设置页面能正常加载
3. **没有暂停提示**: 如果看到 "Paused" 或 "Resume" 按钮,需要先恢复项目

---

## 下一步

获取正确的连接字符串后:

1. 将连接字符串提供给我
2. 我会更新测试脚本
3. 运行连接测试
4. 初始化数据库表结构
5. 测试 CRUD 操作

---

## 常见问题

**Q: 为什么要使用 Connection Pooling?**
A: Connection Pooling 提供连接复用和负载均衡,更适合生产环境和 serverless 应用。

**Q: Transaction 和 Session 模式有什么区别?**
A:
- Transaction: 每次查询后自动释放连接,适合短连接和无状态应用
- Session: 保持连接直到客户端关闭,适合需要事务或临时表的场景

**Q: 我的项目显示 "Paused" 怎么办?**
A: 点击 "Resume" 按钮恢复项目。Supabase 免费项目如果 7 天无活动会自动暂停。

**Q: 端口 6543 和 5432 有什么区别?**
A:
- 6543: Transaction mode (Pgbouncer pooler)
- 5432: Session mode 或 Direct connection
