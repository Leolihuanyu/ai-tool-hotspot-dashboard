# Stripe支付集成测试指南

**版本**: 1.0
**创建日期**: 2025-11-08
**测试环境**: Stripe测试模式

---

## 📋 测试前准备

### 1. 环境配置

确保 `.env` 文件包含以下Stripe测试密钥：

```bash
# Stripe测试环境密钥
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxxxxxxxxxx

# Stripe价格ID（需要在Stripe Dashboard创建）
STRIPE_PRICE_ID_MONTHLY=price_xxxxxxxxxxxxx
STRIPE_PRICE_ID_YEARLY=price_xxxxxxxxxxxxx

# Webhook密钥
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxx

# Dashboard URL
DASHBOARD_BASE_URL=http://localhost:5000
```

### 2. 启动服务

```bash
# 后端
python -m src.dashboard.app

# 前端
cd frontend
npm run dev
```

### 3. 配置Webhook（本地测试）

使用Stripe CLI监听webhook事件：

```bash
# 安装Stripe CLI
brew install stripe/stripe-cli/stripe

# 登录
stripe login

# 转发webhook到本地
stripe listen --forward-to localhost:5000/api/payment/webhook
```

这将输出一个webhook签名密钥（`whsec_xxx`），将其设置到环境变量 `STRIPE_WEBHOOK_SECRET`。

---

## 🧪 测试场景

### 场景1：月付订阅成功流程

#### 步骤：

1. **访问定价页面**
   - URL: `http://localhost:5173/pricing`
   - 验证页面正常加载，显示月付和年付两个选项

2. **点击"开始月付订阅"按钮**
   - 验证跳转到Stripe Checkout页面
   - 验证URL包含 `checkout.stripe.com`

3. **填写测试支付信息**
   ```
   卡号: 4242 4242 4242 4242
   过期日期: 任意未来日期（如 12/25）
   CVC: 任意3位数字（如 123）
   邮政编码: 任意5位数字（如 12345）
   ```

4. **完成支付**
   - 点击"订阅"按钮
   - 验证支付成功，跳转到成功页面

5. **验证数据库**
   ```sql
   SELECT * FROM users WHERE email = '测试邮箱';
   -- 验证：
   -- subscription_type = 'paid'
   -- subscription_status = 'active'
   -- stripe_customer_id 不为空
   -- stripe_subscription_id 不为空
   ```

6. **验证Webhook**
   - 在Stripe CLI输出中查看 `checkout.session.completed` 事件
   - 在后端日志中确认事件处理成功

7. **验证邮件**
   - 检查是否收到欢迎邮件
   - 验证邮件内容包含Dashboard访问链接

#### 预期结果：
- ✅ 支付成功
- ✅ 数据库更新正确
- ✅ Webhook处理成功
- ✅ 欢迎邮件发送成功

---

### 场景2：年付订阅成功流程

重复场景1的步骤，但选择"开始年付订阅"按钮。

**预期结果**: 与场景1相同

---

### 场景3：支付失败场景

#### 步骤：

1. 访问定价页面
2. 点击订阅按钮
3. 使用失败测试卡号：
   ```
   卡号: 4000 0000 0000 0002  （通用拒绝卡）
   ```

4. 尝试完成支付

#### 预期结果：
- ✅ Stripe显示支付失败提示
- ✅ 用户未被创建或状态未更新
- ✅ 返回定价页面或显示错误消息

---

### 场景4：查询订阅状态

#### 步骤：

1. 使用已订阅用户的token登录Dashboard
2. 调用API查询订阅状态：
   ```bash
   curl -X GET http://localhost:5000/api/payment/subscription-status \
     -H "Authorization: Bearer <用户token>"
   ```

#### 预期结果：
```json
{
  "success": true,
  "subscription": {
    "type": "paid",
    "status": "active",
    "email": "user@example.com",
    "stripe_details": {
      "id": "sub_xxxxx",
      "status": "active",
      "current_period_end": 1234567890,
      "cancel_at_period_end": false
    }
  }
}
```

---

### 场景5：取消订阅

#### 步骤：

1. 使用已订阅用户的token
2. 调用取消订阅API：
   ```bash
   curl -X POST http://localhost:5000/api/payment/cancel-subscription \
     -H "Authorization: Bearer <用户token>" \
     -H "Content-Type: application/json" \
     -d '{"immediately": false}'
   ```

3. 验证Webhook事件 `customer.subscription.updated`

4. 查询订阅状态验证 `cancel_at_period_end = true`

#### 预期结果：
- ✅ API返回成功消息
- ✅ Stripe订阅标记为将在周期结束时取消
- ✅ 数据库状态保持 `active`（直到周期结束）

---

### 场景6：客户门户访问

#### 步骤：

1. 调用创建门户会话API：
   ```bash
   curl -X POST http://localhost:5000/api/payment/portal-session \
     -H "Authorization: Bearer <用户token>"
   ```

2. 获取返回的 `url`，在浏览器中打开

3. 在Stripe客户门户中：
   - 查看订阅详情
   - 更新支付方式
   - 查看发票历史

#### 预期结果：
- ✅ 成功跳转到Stripe客户门户
- ✅ 能够管理订阅
- ✅ 更新会反映到数据库

---

### 场景7：Webhook事件处理

使用Stripe CLI触发测试事件：

```bash
# 触发订阅更新事件
stripe trigger customer.subscription.updated

# 触发订阅删除事件
stripe trigger customer.subscription.deleted

# 触发支付失败事件
stripe trigger invoice.payment_failed
```

#### 验证点：
- ✅ 后端日志显示事件接收和处理
- ✅ 数据库状态正确更新
- ✅ 相应的通知邮件发送（如果配置）

---

## 🔍 测试用例检查表

### 支付流程
- [ ] 月付订阅创建成功
- [ ] 年付订阅创建成功
- [ ] 支付失败正确处理
- [ ] Checkout Session URL正确生成
- [ ] 成功后正确跳转

### Webhook处理
- [ ] `checkout.session.completed` 正确处理
- [ ] `customer.subscription.updated` 正确处理
- [ ] `customer.subscription.deleted` 正确处理
- [ ] `invoice.payment_failed` 正确处理
- [ ] Webhook签名验证通过
- [ ] 无效签名被拒绝

### 数据库
- [ ] 用户订阅状态正确更新
- [ ] `stripe_customer_id` 正确保存
- [ ] `stripe_subscription_id` 正确保存
- [ ] 订阅类型正确（paid）
- [ ] 订阅状态正确（active/cancelled/expired）

### API端点
- [ ] `/api/payment/create-checkout-session` 正常工作
- [ ] `/api/payment/webhook` 正常接收事件
- [ ] `/api/payment/subscription-status` 返回正确信息
- [ ] `/api/payment/cancel-subscription` 正常工作
- [ ] `/api/payment/portal-session` 生成正确URL

### 前端
- [ ] Pricing页面正常显示
- [ ] 订阅按钮点击正常
- [ ] 加载状态正确显示
- [ ] 错误消息正确显示
- [ ] Landing Page正常显示

### 邮件通知
- [ ] 订阅成功发送欢迎邮件
- [ ] 订阅取消发送确认邮件
- [ ] 支付失败发送提醒邮件
- [ ] 邮件内容格式正确
- [ ] 邮件链接可点击

---

## 🐛 常见问题排查

### 问题1：Webhook签名验证失败

**症状**: 返回400错误，日志显示"Webhook签名验证失败"

**解决方案**:
1. 确认 `STRIPE_WEBHOOK_SECRET` 环境变量设置正确
2. 使用Stripe CLI时，使用其输出的webhook密钥
3. 生产环境需要在Stripe Dashboard配置webhook端点

### 问题2：支付成功但数据库未更新

**症状**: Stripe显示支付成功，但用户订阅状态未更新

**排查步骤**:
1. 检查Stripe CLI是否正常转发webhook
2. 检查后端日志是否收到 `checkout.session.completed` 事件
3. 检查webhook处理函数是否有错误
4. 验证用户邮箱是否正确传递

### 问题3：无法跳转到Stripe Checkout

**症状**: 点击订阅按钮后无响应或报错

**排查步骤**:
1. 检查浏览器控制台错误
2. 确认 `STRIPE_PRICE_ID_MONTHLY/YEARLY` 已配置
3. 确认用户已认证（token有效）
4. 检查网络请求是否成功

### 问题4：邮件未发送

**症状**: 订阅成功但未收到欢迎邮件

**排查步骤**:
1. 检查SMTP配置是否正确
2. 查看后端日志的邮件发送记录
3. 检查垃圾邮件文件夹
4. 验证 `EMAIL_FROM` 和 `SMTP_USERNAME` 配置

---

## 📊 测试数据记录

### 测试卡号

| 场景 | 卡号 | 结果 |
|------|------|------|
| 成功支付 | 4242 4242 4242 4242 | 立即成功 |
| 拒绝支付 | 4000 0000 0000 0002 | 拒绝（通用拒绝） |
| 需要认证 | 4000 0025 0000 3155 | 需要3D Secure认证 |
| 余额不足 | 4000 0000 0000 9995 | 余额不足 |

更多测试卡号: https://stripe.com/docs/testing#cards

### 测试用户

| 邮箱 | 订阅类型 | 测试场景 |
|------|---------|---------|
| test-monthly@example.com | 月付 | 月付订阅流程 |
| test-yearly@example.com | 年付 | 年付订阅流程 |
| test-cancel@example.com | 月付 | 取消订阅流程 |

---

## ✅ 测试完成标准

- [ ] 所有测试场景通过
- [ ] 所有检查表项目完成
- [ ] 无遗留的高优先级Bug
- [ ] 测试数据记录完整
- [ ] 文档更新完毕

---

## 🚀 生产环境部署前检查

1. **切换到生产密钥**
   ```bash
   # 将测试密钥替换为生产密钥
   STRIPE_SECRET_KEY=sk_live_xxxxx
   STRIPE_PUBLISHABLE_KEY=pk_live_xxxxx
   ```

2. **配置生产Webhook**
   - 在Stripe Dashboard创建webhook端点
   - URL: `https://your-domain.com/api/payment/webhook`
   - 选择以下事件：
     - checkout.session.completed
     - customer.subscription.updated
     - customer.subscription.deleted
     - invoice.payment_failed

3. **更新环境变量**
   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_<生产环境的webhook密钥>
   DASHBOARD_BASE_URL=https://your-domain.com
   ```

4. **测试生产环境**
   - 进行一次真实的小额支付测试（可以立即取消）
   - 验证webhook正常接收
   - 验证邮件发送正常

---

**测试文档结束**
**下次更新**: 发现新问题或场景时更新
