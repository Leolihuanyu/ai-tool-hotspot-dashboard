# Supabase 连接问题诊断

## 当前问题
DNS 无法解析: `db.pdezvkbhbynfgqtwaqaw.supabase.co`

## 可能原因和解决方案

### 1. 使用错误的连接字符串类型
Supabase 提供多种连接字符串:

**在 Supabase Dashboard 中获取正确的连接字符串:**
1. 进入你的项目: https://supabase.com/dashboard/project/pdezvkbhbynfgqtwaqaw
2. 点击左侧 "Project Settings" (设置图标)
3. 点击 "Database"
4. 找到 "Connection string" 部分

**重要: 选择 "Connection Pooling" (连接池) 模式:**
- URI 选择: "Session" 或 "Transaction" 模式
- 端口通常是 5432 (Session) 或 6543 (Transaction)
- 格式示例: `postgresql://postgres.pdezvkbhbynfgqtwaqaw:[YOUR-PASSWORD]@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres`

### 2. 项目可能还在初始化中
- 新创建的项目需要 2-5 分钟完成初始化
- 检查 Dashboard 顶部是否有 "Project is being set up" 提示

### 3. 项目可能已暂停
- Supabase 免费项目如果 7 天不活动会暂停
- 在 Dashboard 中查看是否有 "Resume" 按钮

## 下一步操作

请前往 Supabase Dashboard 确认:
1. 项目状态是否为 "Active" (绿色)
2. 复制 "Connection Pooling" 下的连接字符串 (不是 Direct Connection)
3. 选择 "Transaction" 或 "Session" 模式
4. 将 `[YOUR-PASSWORD]` 替换为你的密码: NG86DDhGUIehlLZ8

预期的连接字符串格式应该类似:
```
postgresql://postgres.pdezvkbhbynfgqtwaqaw:NG86DDhGUIehlLZ8@aws-0-[region].pooler.supabase.com:6543/postgres
```

而不是:
```
postgresql://postgres:NG86DDhGUIehlLZ8@db.pdezvkbhbynfgqtwaqaw.supabase.co:5432/postgres
```
