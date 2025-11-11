# 📧 SendGrid 配置指南

## 为什么需要 SendGrid？

在 Render 等云平台上，SMTP 端口（587/465）通常被防火墙阻止，导致无法直接使用 Gmail SMTP 发送邮件。SendGrid 通过 HTTP API 发送邮件，不受端口限制，是推荐的解决方案。

**SMTP vs SendGrid：**

| 特性 | SMTP (Gmail) | SendGrid |
|------|--------------|----------|
| 连接方式 | SMTP 端口 587 | HTTP API |
| Render 支持 | ❌ 端口被阻止 | ✅ 完全支持 |
| 免费额度 | N/A | 100封/天 |
| 配置难度 | 中等 | 简单 |
| 可靠性 | 低（网络限制） | 高 |

---

## 📝 Step 1: 注册 SendGrid 账号

### 1.1 访问注册页面

```
https://signup.sendgrid.com/
```

### 1.2 填写注册信息

- **Email**：`leolihuanyu@gmail.com`（或你的工作邮箱）
- **Password**：设置一个强密码
- 勾选 "I agree to the SendGrid Terms of Service"
- 点击 **"Create Account"**

### 1.3 验证邮箱

1. 检查邮箱收到的验证邮件
2. 点击邮件中的 **"Verify Email Address"** 链接
3. 完成邮箱验证

### 1.4 填写账户信息

- **First Name / Last Name**：你的姓名
- **Company Name**：`AI Tool Hotspot Dashboard`（或任意项目名）
- **Website URL**：`https://ai-tool-hotspot-dashboard.vercel.app`
- **Role**：选择 `Developer`
- **Company Size**：选择适合的选项（如 "Just me"）
- **I'm here to**：选择 **"Send transactional emails"**（事务性邮件）
- **Expected Email Volume**：选择 `Less than 40K/month`

---

## 🔑 Step 2: 创建 API Key

### 2.1 导航到 API Keys 页面

**方法A：通过菜单导航**
1. 登录 SendGrid Dashboard：https://app.sendgrid.com/
2. 点击左侧菜单 **"Settings"**
3. 选择 **"API Keys"**

**方法B：直接访问**
```
https://app.sendgrid.com/settings/api_keys
```

### 2.2 创建新的 API Key

1. 点击右上角蓝色按钮 **"Create API Key"**

2. 填写 API Key 信息：
   - **API Key Name**：`ai-dashboard-production`（或任意有意义的名称）
   - **API Key Permissions**：选择 **"Restricted Access"**（受限访问）

3. 配置权限（重要！）：
   - 展开 **"Mail Send"** 权限组
   - 勾选 **"Mail Send"** → **"Full Access"**
   - 其他权限保持关闭（安全起见）

4. 点击 **"Create & View"**

### 2.3 保存 API Key ⚠️

**关键提示：** API Key 只显示一次！

```
格式类似：
SG.xxxxxxxxxxxxxxxxxxxxxxxx.yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy
```

1. **立即复制** API Key 到安全的地方（如密码管理器）
2. ⚠️ 关闭窗口后无法再次查看
3. 如果忘记保存，需要删除并重新创建

---

## ✉️ Step 3: 验证发件人邮箱

SendGrid 要求验证发件人身份才能发送邮件。推荐使用 **Single Sender Verification**（单一发件人验证），简单快捷。

### 3.1 导航到 Sender Authentication

**方法A：通过菜单**
1. 左侧菜单：**"Settings"** → **"Sender Authentication"**

**方法B：直接访问**
```
https://app.sendgrid.com/settings/sender_auth
```

### 3.2 选择 Single Sender Verification

1. 找到 **"Single Sender Verification"** 部分
2. 点击 **"Get Started"** 或 **"Create New Sender"**

### 3.3 填写发件人信息

| 字段 | 填写内容 |
|------|---------|
| **From Name** | `AI工具热点Dashboard` 或 `AI Tool Hotspot` |
| **From Email Address** | `leolihuanyu@gmail.com` |
| **Reply To** | `leolihuanyu@gmail.com` |
| **Company Address** | 你的公司/个人地址 |
| **City** | 城市名称 |
| **State/Province** | 省份/州 |
| **Zip Code** | 邮编 |
| **Country** | 选择国家 |

### 3.4 验证邮箱

1. 点击 **"Create"**
2. SendGrid 会发送验证邮件到 `leolihuanyu@gmail.com`
3. 打开邮件，点击 **"Verify Single Sender"** 按钮
4. 验证成功后，状态显示为 **"Verified"** ✅

**提示：**
- 检查垃圾邮件文件夹
- 如果未收到，可在 SendGrid Dashboard 重新发送
- 验证通常在几分钟内完成

---

## ⚙️ Step 4: 配置 Render 环境变量

### 4.1 登录 Render Dashboard

```
https://dashboard.render.com
```

### 4.2 选择你的服务

找到并点击 `ai-tool-hotspot-dashboard` 服务

### 4.3 进入 Environment 配置

点击左侧 **"Environment"** 标签

### 4.4 添加/更新环境变量

添加或修改以下环境变量：

```bash
# 邮件提供商（必须改为 sendgrid）
EMAIL_PROVIDER=sendgrid

# SendGrid API Key（从 Step 2 获取）
SENDGRID_API_KEY=SG.你的API_Key

# 发件人邮箱（必须与 Step 3 验证的邮箱一致）
EMAIL_FROM=leolihuanyu@gmail.com

# 收件人列表（可选，用于测试）
EMAIL_TO_LIST=leolihuanyu@gmail.com
```

**重要配置检查：**
- ✅ `EMAIL_PROVIDER` 必须是 `sendgrid`（小写）
- ✅ `SENDGRID_API_KEY` 以 `SG.` 开头
- ✅ `EMAIL_FROM` 与 SendGrid 验证的邮箱完全一致
- ✅ 删除或保留 SMTP 相关变量（不影响，但可以清理）

### 4.5 保存并重启

1. 点击 **"Save Changes"**
2. Render 会自动重启服务（约 1-2 分钟）
3. 等待部署完成

---

## ✅ Step 5: 验证配置

### 5.1 查看启动日志

部署完成后，在 Render Dashboard → **Logs**：

**期待看到（成功）：**
```
✅ "使用SendGrid邮件发送器"
✅ "邮件发送器初始化成功 (provider: sendgrid)"
```

**如果看到（失败）：**
```
❌ "SENDGRID_API_KEY未配置,邮件功能将不可用"
```
→ 检查 Step 4.4 的环境变量配置

### 5.2 测试订阅流程

#### 方法 A：真实订阅测试

1. 访问前端订阅页面
2. 使用 Stripe 测试卡号：`4242 4242 4242 4242`
3. 填写邮箱：`leolihuanyu@gmail.com`
4. 完成支付

#### 检查结果

**A. 查看 Render 日志：**
```
✅ "订阅激活成功: leolihuanyu@gmail.com"
✅ "SendGrid邮件发送成功"
✅ "订阅欢迎邮件已发送至: leolihuanyu@gmail.com"
```

**B. 检查邮箱：**
- 应该收到订阅欢迎邮件
- 包含 Dashboard 访问链接
- 支持多语言（根据订阅时选择的语言）

### 5.3 查看 SendGrid Dashboard

在 SendGrid Dashboard → **Activity** 可以看到：
- 发送的邮件数量
- 投递状态
- 打开率/点击率（如果启用跟踪）

---

## 🐛 常见问题排查

### Q1: "SENDGRID_API_KEY未配置" 错误

**原因：** Render 环境变量未配置或拼写错误

**解决方案：**
1. 检查 Render Environment 是否有 `SENDGRID_API_KEY`
2. 确认变量名拼写正确（区分大小写）
3. 确认 API Key 以 `SG.` 开头
4. 保存后重启服务

### Q2: "Unauthorized sender" 错误

**原因：** 发件人邮箱未验证

**解决方案：**
1. 登录 SendGrid Dashboard
2. Settings → Sender Authentication
3. 确认发件人状态为 **"Verified"** ✅
4. 确保 `EMAIL_FROM` 与验证的邮箱完全一致

### Q3: 收不到测试邮件

**可能原因：**
1. 邮件在垃圾邮件文件夹
2. SendGrid API Key 权限不足
3. 发件人未验证
4. Render 日志显示错误

**解决方案：**
1. 检查垃圾邮件文件夹
2. 重新创建 API Key，确保 "Mail Send" 权限为 "Full Access"
3. 重新验证发件人邮箱
4. 查看 Render 日志中的详细错误信息

### Q4: API Key 忘记保存了怎么办？

**解决方案：**
1. 在 SendGrid Dashboard → Settings → API Keys
2. 找到之前创建的 API Key
3. 点击右侧的删除按钮（垃圾桶图标）
4. 重新创建新的 API Key（Step 2）

### Q5: 免费额度够用吗？

**SendGrid 免费计划：**
- **每天 100 封邮件**
- 适用于：
  - ✅ 订阅欢迎邮件
  - ✅ 支付失败通知
  - ✅ 订阅取消确认
  - ✅ 小规模测试

**估算：**
- 10 个订阅/天 × 1 封欢迎邮件 = 10 封/天 ✅
- 完全够用

**如需更多：**
- 升级到付费计划
- 或使用多个发件人账户

---

## 📊 配置对比：修复前 vs 修复后

### 修复前（使用 SMTP）

```
❌ Render 上 SMTP 端口被阻止
❌ 邮件发送失败: Network is unreachable
❌ webhook_handler 硬编码使用 SMTPEmailSender
❌ 忽略 EMAIL_PROVIDER 配置
❌ 模块导入时创建多个全局实例，日志混乱
```

### 修复后（使用 SendGrid）

```
✅ SendGrid 通过 HTTP API，无端口限制
✅ 邮件发送成功
✅ webhook_handler 使用 get_email_sender() 工厂函数
✅ 遵守 EMAIL_PROVIDER 配置
✅ 懒加载，只初始化需要的发送器
✅ 日志清晰，易于调试
```

---

## 🎯 检查清单

完成配置后，确认以下各项：

### SendGrid 配置
- [ ] SendGrid 账号已注册并验证
- [ ] API Key 已创建并保存
  - [ ] API Key 以 `SG.` 开头
  - [ ] 权限包含 "Mail Send" → "Full Access"
- [ ] 发件人邮箱已验证
  - [ ] 状态为 "Verified" ✅
  - [ ] 邮箱为 `leolihuanyu@gmail.com`

### Render 环境变量
- [ ] `EMAIL_PROVIDER=sendgrid`
- [ ] `SENDGRID_API_KEY=SG.xxxxx`（你的 API Key）
- [ ] `EMAIL_FROM=leolihuanyu@gmail.com`
- [ ] 已保存并重启服务

### 功能测试
- [ ] 启动日志显示 "使用SendGrid邮件发送器"
- [ ] 订阅测试成功
- [ ] 收到欢迎邮件
- [ ] Render 日志无错误

---

## 📚 相关文档

- **SendGrid 官方文档**：https://docs.sendgrid.com/
- **API Key 管理**：https://docs.sendgrid.com/ui/account-and-settings/api-keys
- **Sender Authentication**：https://docs.sendgrid.com/ui/sending-email/sender-verification
- **EMAIL_SENDING_FIX_SUMMARY.md**：详细的邮件发送修复总结

---

## 💡 提示

1. **保管好 API Key**：像密码一样保护，不要提交到 Git
2. **监控使用量**：在 SendGrid Dashboard 查看每日发送量
3. **测试环境**：本地测试时也可以使用 SendGrid
4. **日志监控**：定期检查 Render 日志，确保邮件发送正常
5. **备用方案**：如果 SendGrid 有问题，可以切换回本地 SMTP（本地环境）

---

**配置时间估计：** 20-30 分钟

**难度：** ⭐⭐☆☆☆ (简单)

**推荐度：** ⭐⭐⭐⭐⭐ (强烈推荐)

---

祝配置顺利！如有问题，请参考本文档的"常见问题排查"部分。 🎉
