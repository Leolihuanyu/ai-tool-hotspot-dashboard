# 邀请码系统测试指南

本文档提供邀请码系统的完整测试步骤和验证方法。

---

## 📋 测试前准备

### 1. 确保数据库已初始化

```bash
# 初始化数据库（如果还没有）
python -m src.cli.main init-db
```

### 2. 检查必要的环境变量

确保 `.env` 文件包含以下配置：

```bash
# JWT密钥（必须）
JWT_SECRET_KEY=your-secret-key-here

# 邮件配置（用于测试注册）
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=<SMTP_PASSWORD>
FROM_EMAIL=your-email@gmail.com

# Dashboard URL
DASHBOARD_BASE_URL=http://localhost:5000

# 数据库路径
DATABASE_PATH=data/db.sqlite
```

---

## 🧪 测试步骤

### 步骤1: 测试邀请码管理模块

#### 1.1 生成单个邀请码

```bash
# 生成自定义邀请码
python -c "
from src.user.invite_manager import InviteManager
im = InviteManager()
result = im.generate_code(
    code='TEST2025',
    code_type='beta',
    max_uses=10,
    expires_in_days=30
)
print('生成结果:', result)
"
```

**预期输出**:
```python
生成结果: {
    'success': True,
    'code': 'TEST2025',
    'code_id': 1,
    'message': '邀请码生成成功'
}
```

#### 1.2 批量生成邀请码

```bash
# 批量生成5个测试邀请码
python -c "
from src.user.invite_manager import InviteManager
im = InviteManager()
result = im.generate_batch(
    count=5,
    code_type='beta',
    max_uses=1,
    expires_in_days=30,
    prefix='TEST'
)
print(f'批量生成: {result[\"count\"]}个成功')
for code in result['codes'][:3]:
    print(f'  - {code}')
"
```

**预期输出**:
```
批量生成: 5个成功
  - TEST********
  - TEST********
  - TEST********
```

#### 1.3 验证邀请码

```bash
# 验证邀请码有效性
python -c "
from src.user.invite_manager import InviteManager
im = InviteManager()
result = im.validate_code('TEST2025')
print('验证结果:')
print(f'  有效: {result[\"valid\"]}')
print(f'  原因: {result[\"reason\"]}')
if result['valid']:
    info = result['code_info']
    print(f'  类型: {info[\"code_type\"]}')
    print(f'  使用次数: {info[\"current_uses\"]}/{info[\"max_uses\"]}')
"
```

**预期输出**:
```
验证结果:
  有效: True
  原因: 邀请码有效
  类型: beta
  使用次数: 0/10
```

---

### 步骤2: 测试CLI工具

#### 2.1 使用CLI生成邀请码

```bash
# 生成10个Beta邀请码
python -m src.cli.generate_invites \
    --count 10 \
    --type beta \
    --expires 30 \
    --prefix "CLI"
```

**预期输出**:
```
🎫 批量生成邀请码
   数量: 10
   类型: beta
   最大使用次数: 1
   有效期: 30天
   前缀: CLI

✅ 批量生成完成！
   成功: 10个

📋 生成的邀请码（前10个）:
   1. CLI********
   2. CLI********
   ...
```

#### 2.2 查看所有邀请码

```bash
# 列出所有激活的邀请码
python -m src.cli.generate_invites --list --active-only
```

**预期输出**:
```
📋 邀请码列表

找到 15 个邀请码:

邀请码          类型       使用情况        有效期                    状态
---------------------------------------------------------------------------------
TEST2025        beta       0/10            永久                      ✅
CLI********     beta       0/1             2025-12-08T...            ✅
...
```

#### 2.3 验证邀请码（CLI）

```bash
# 验证邀请码
python -m src.cli.generate_invites --validate TEST2025
```

**预期输出**:
```
🔍 验证邀请码: TEST2025

✅ 邀请码有效！
   类型: beta
   使用情况: 0/10
   有效期: 永久
```

#### 2.4 导出邀请码到CSV

```bash
# 生成邀请码并导出CSV
python -m src.cli.generate_invites \
    --count 20 \
    --output test_invites.csv \
    --type beta \
    --expires 60
```

**验证CSV文件**:
```bash
# 查看CSV内容
cat test_invites.csv | head -5
```

**预期输出**:
```csv
邀请码,类型,最大使用次数,当前使用次数,有效期,创建时间,状态
ABC12345,beta,1,0,2025-12-08T...,2025-11-08T...,激活
DEF67890,beta,1,0,2025-12-08T...,2025-11-08T...,激活
...
```

---

### 步骤3: 测试用户注册流程

#### 3.1 启动Flask服务器

```bash
# 启动Dashboard
python -m src.dashboard.app
```

服务器应该在 `http://localhost:5000` 启动。

#### 3.2 测试邀请码验证API

在新终端窗口测试：

```bash
# 测试验证API
curl "http://localhost:5000/api/invite/validate?code=TEST2025"
```

**预期响应**:
```json
{
  "valid": true,
  "reason": "邀请码有效",
  "code_info": {
    "id": 1,
    "code": "TEST2025",
    "code_type": "beta",
    "max_uses": 10,
    "current_uses": 0,
    "created_by": null,
    "expires_at": null,
    "created_at": "2025-11-08T...",
    "is_active": 1
  }
}
```

#### 3.3 测试用户注册API

```bash
# 测试注册API
curl -X POST http://localhost:5000/api/invite/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test.user@example.com",
    "invite_code": "TEST2025"
  }'
```

**预期响应**:
```json
{
  "success": true,
  "user_id": 1,
  "message": "注册成功！欢迎邮件已发送到您的邮箱。"
}
```

**验证邮件**:
- 检查 `test.user@example.com` 邮箱
- 应该收到欢迎邮件，包含Dashboard访问链接

#### 3.4 验证邀请码使用次数

```bash
# 再次验证邀请码，检查使用次数
curl "http://localhost:5000/api/invite/validate?code=TEST2025"
```

**预期响应**:
```json
{
  "valid": true,
  "reason": "邀请码有效",
  "code_info": {
    "code": "TEST2025",
    "current_uses": 1,  // 使用次数应该增加
    "max_uses": 10,
    ...
  }
}
```

---

### 步骤4: 测试前端邀请注册页面

#### 4.1 启动前端开发服务器

```bash
cd frontend
npm install  # 如果还没安装依赖
npm run dev
```

前端应该在 `http://localhost:5173` 启动。

#### 4.2 访问邀请注册页面

在浏览器访问：
```
http://localhost:5173/invite?code=TEST2025
```

**验证界面**:
- ✅ 显示"欢迎加入 Beta 测试！"标题
- ✅ 显示邀请码信息卡片
- ✅ 显示邮箱输入框
- ✅ 显示"完成注册"按钮

#### 4.3 测试无效邀请码

访问：
```
http://localhost:5173/invite?code=INVALID123
```

**验证界面**:
- ❌ 显示"邀请码无效"错误
- ❌ 显示可能的原因列表
- ✅ 显示"联系技术支持"按钮

#### 4.4 测试注册流程

1. 访问 `http://localhost:5173/invite?code=TEST2025`
2. 输入测试邮箱：`test2@example.com`
3. 点击"完成注册"
4. 等待响应

**验证结果**:
- ✅ 显示"注册成功！"消息
- ✅ 显示绿色成功图标
- ✅ 显示后续步骤说明
- ✅ 显示"打开邮箱"按钮

---

### 步骤5: 测试推荐奖励系统

#### 5.1 为用户生成推荐码

```bash
# 为用户生成推荐码
python -c "
from src.user.referral_manager import ReferralManager
rm = ReferralManager()
result = rm.generate_referral_code('test.user@example.com')
print(f'推荐码: {result[\"code\"]}')
"
```

**预期输出**:
```
推荐码: REF-ABC12345
```

#### 5.2 使用推荐码注册新用户

```bash
# 先在数据库中创建推荐码
python -c "
from src.user.invite_manager import InviteManager
im = InviteManager()
im.generate_code(
    code='REF-ABC12345',
    code_type='referral',
    max_uses=5,
    created_by='test.user@example.com',
    expires_in_days=90
)
"

# 使用推荐码注册新用户
curl -X POST http://localhost:5000/api/invite/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "referred.user@example.com",
    "invite_code": "REF-ABC12345"
  }'
```

#### 5.3 验证推荐奖励是否发放

```bash
# 查看推荐人的免费期是否延长
python -c "
from src.user.user_manager import UserManager
um = UserManager()
user = um.get_user('test.user@example.com')
print(f'推荐人免费期: {user[\"free_until\"]}')
"
```

**预期输出**:
```
推荐人免费期: 2025-11-15T...  # 应该是当前时间+7天
```

#### 5.4 查看推荐统计

```bash
# 查看推荐统计
python -c "
from src.user.referral_manager import ReferralManager
rm = ReferralManager()
stats = rm.get_referral_stats('test.user@example.com')
print(f'推荐总数: {stats[\"total_referrals\"]}')
print(f'已发放奖励: {stats[\"granted_rewards\"]}')
print(f'累计奖励天数: {stats[\"total_reward_days\"]}')
"
```

**预期输出**:
```
推荐总数: 1
已发放奖励: 1
累计奖励天数: 7
```

---

### 步骤6: 测试推荐API（需要认证）

#### 6.1 获取访问token

```bash
# 为测试用户生成token
python -c "
from src.auth.token_manager import TokenManager
tm = TokenManager()
result = tm.generate_token('test.user@example.com')
print(f'Token: {result[\"token\"]}')
print(f'Dashboard URL: {result[\"dashboard_url\"]}')
"
```

#### 6.2 测试推荐统计API

```bash
# 使用token查询推荐统计
TOKEN="your-token-here"
curl "http://localhost:5000/api/referrals/stats?token=$TOKEN&email=test.user@example.com"
```

**预期响应**:
```json
{
  "success": true,
  "stats": {
    "total_referrals": 1,
    "pending_rewards": 0,
    "granted_rewards": 1,
    "total_reward_days": 7,
    "referral_list": [...]
  }
}
```

---

## 🔍 数据库验证

### 检查邀请码表

```bash
# 查看邀请码表
sqlite3 data/db.sqlite "
SELECT code, code_type, max_uses, current_uses, is_active
FROM invite_codes
ORDER BY created_at DESC
LIMIT 5;
"
```

### 检查用户表

```bash
# 查看用户表
sqlite3 data/db.sqlite "
SELECT email, subscription_type, invite_code, free_until
FROM users
ORDER BY created_at DESC
LIMIT 5;
"
```

### 检查推荐关系表

```bash
# 查看推荐关系
sqlite3 data/db.sqlite "
SELECT referrer_email, referee_email, invite_code, reward_status
FROM referrals
ORDER BY created_at DESC;
"
```

---

## ✅ 验收测试清单

### 邀请码管理模块
- [ ] 可以生成唯一的邀请码
- [ ] 邀请码有正确的有效期
- [ ] 邀请码有使用次数限制
- [ ] 可以批量生成邀请码
- [ ] 可以验证邀请码有效性
- [ ] 可以停用/激活邀请码

### CLI工具
- [ ] CLI工具可正常运行
- [ ] 支持导出CSV格式
- [ ] 可以列出所有邀请码
- [ ] 可以验证邀请码
- [ ] 支持筛选和查询

### 注册流程
- [ ] 无效邀请码显示错误提示
- [ ] 有效邀请码可以注册
- [ ] 注册后邀请码使用次数递增
- [ ] 自动发送欢迎邮件
- [ ] 邮件包含Dashboard访问链接
- [ ] 用户数据正确保存到数据库

### 推荐奖励
- [ ] 推荐关系正确记录
- [ ] 奖励自动发放
- [ ] 推荐人免费期正确延长
- [ ] 可以查看推荐历史
- [ ] 推荐统计数据准确

### 前端界面
- [ ] 邀请页面正常显示
- [ ] 邀请码验证实时反馈
- [ ] 注册成功显示确认信息
- [ ] 错误提示清晰明确
- [ ] 移动端显示友好

---

## 🐛 常见问题排查

### 问题1: 邀请码验证失败

**症状**: `validate_code` 返回 `valid: false`

**排查步骤**:
```bash
# 检查邀请码是否存在
sqlite3 data/db.sqlite "SELECT * FROM invite_codes WHERE code = 'TEST2025';"

# 检查邀请码是否过期
python -c "
from src.user.invite_manager import InviteManager
im = InviteManager()
info = im.get_code_info('TEST2025')
print(info)
"
```

### 问题2: 注册后没收到邮件

**排查步骤**:
1. 检查 `.env` 中的邮件配置
2. 查看应用日志: `tail -f logs/app.log`
3. 测试SMTP连接:
```python
import smtplib
smtp = smtplib.SMTP('smtp.gmail.com', 587)
smtp.starttls()
smtp.login('your-email@gmail.com', 'your-app-password')
print("SMTP连接成功！")
```

### 问题3: 推荐奖励未发放

**排查步骤**:
```bash
# 检查推荐关系是否记录
sqlite3 data/db.sqlite "
SELECT * FROM referrals
WHERE referee_email = 'referred.user@example.com';
"

# 手动触发奖励发放
python -c "
from src.user.referral_manager import ReferralManager
rm = ReferralManager()
result = rm.grant_referral_reward(
    'test.user@example.com',
    'referred.user@example.com'
)
print(result)
"
```

### 问题4: 前端页面空白

**排查步骤**:
1. 检查浏览器控制台错误
2. 确认后端API可访问: `curl http://localhost:5000/api/invite/validate?code=TEST2025`
3. 检查前端环境变量配置

---

## 📊 性能测试

### 批量生成测试

```bash
# 生成1000个邀请码并计时
time python -m src.cli.generate_invites --count 1000 --type beta
```

**预期**: 应该在10秒内完成

### 并发注册测试

使用 `ab` (Apache Bench) 测试并发注册:

```bash
# 需要先安装 apache2-utils
# Ubuntu: sudo apt-get install apache2-utils
# macOS: brew install httpd

# 并发10个请求测试
ab -n 10 -c 10 -p register.json -T application/json \
  http://localhost:5000/api/invite/register
```

其中 `register.json`:
```json
{
  "email": "concurrent.test@example.com",
  "invite_code": "TEST2025"
}
```

---

## 🎉 测试完成

完成所有测试后，你应该验证：

✅ 邀请码系统功能完整
✅ CLI工具运行正常
✅ 注册流程顺畅
✅ 推荐奖励正确发放
✅ 前端界面友好
✅ 数据持久化正确
✅ API响应符合预期

如果所有测试通过，邀请码系统已经可以投入使用！

**下一步**: 参考 [docs/IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) 继续Phase 5（Stripe付费集成）的开发。
