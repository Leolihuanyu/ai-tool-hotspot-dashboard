# Stripe快速配置（5分钟）

本文档提供最简化的Stripe配置步骤。详细说明请参考 [STRIPE_SETUP_GUIDE.md](./STRIPE_SETUP_GUIDE.md)。

---

## 🚀 快速步骤

### 1️⃣ 获取API密钥（2分钟）

访问：https://dashboard.stripe.com/test/apikeys

复制两个密钥：
- `STRIPE_SECRET_KEY` = `sk_test_xxxxxxxxxxxxx`（秘密密钥）
- `STRIPE_PUBLISHABLE_KEY` = `pk_test_xxxxxxxxxxxxx`（可发布密钥）

---

### 2️⃣ 创建价格（2分钟）

访问：https://dashboard.stripe.com/test/products

创建产品：**AI工具热点Dashboard订阅**

添加两个价格：
- **月付**：$19/月 → 复制价格ID → `STRIPE_PRICE_ID_MONTHLY`
- **年付**：$190/年 → 复制价格ID → `STRIPE_PRICE_ID_YEARLY`

---

### 3️⃣ 安装并启动Stripe CLI（1分钟）

```bash
# macOS安装
brew install stripe/stripe-cli/stripe

# 登录
stripe login

# 启动webhook转发（保持运行）
stripe listen --forward-to localhost:5000/api/payment/webhook
```

复制输出的webhook密钥：
- `STRIPE_WEBHOOK_SECRET` = `whsec_xxxxxxxxxxxxx`

---

### 4️⃣ 更新.env文件

打开项目根目录的`.env`文件，填入刚才获取的5个值：

```bash
# === Stripe支付配置 ===
STRIPE_SECRET_KEY=sk_test_您的秘密密钥
STRIPE_PUBLISHABLE_KEY=pk_test_您的公钥
STRIPE_PRICE_ID_MONTHLY=price_您的月付价格ID
STRIPE_PRICE_ID_YEARLY=price_您的年付价格ID
STRIPE_WEBHOOK_SECRET=whsec_您的webhook密钥
```

---

### 5️⃣ 启动服务并测试

```bash
# 终端1：启动后端
./venv/bin/python -m src.dashboard.app

# 终端2：启动前端
cd frontend
npm run dev

# 终端3：启动Stripe CLI
stripe listen --forward-to localhost:5000/api/payment/webhook
```

访问：http://localhost:5173/pricing

测试卡号：`4242 4242 4242 4242`

---

## ✅ 完成！

配置完成后，您应该能够：
- ✅ 访问Pricing页面
- ✅ 点击订阅按钮跳转到Stripe Checkout
- ✅ 使用测试卡号完成支付
- ✅ Webhook接收到事件并创建用户
- ✅ 收到欢迎邮件（包含Dashboard访问链接）

---

## 📝 配置值示例

```bash
STRIPE_SECRET_KEY=sk_test_51QTPB...
STRIPE_PUBLISHABLE_KEY=pk_test_51QTPB...
STRIPE_PRICE_ID_MONTHLY=price_1QabcdefMonthly
STRIPE_PRICE_ID_YEARLY=price_1QabcdefYearly
STRIPE_WEBHOOK_SECRET=whsec_abc123xyz...
```

---

## 🆘 遇到问题？

- 详细配置指南：[STRIPE_SETUP_GUIDE.md](./STRIPE_SETUP_GUIDE.md)
- 测试指南：[STRIPE_TESTING.md](./STRIPE_TESTING.md)
- 认证问题修复：[FIX_PRICING_AUTH.md](./FIX_PRICING_AUTH.md)
