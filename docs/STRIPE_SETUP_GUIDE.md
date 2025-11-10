# Stripe环境变量配置指南

本指南将帮助您一步步配置Stripe支付系统所需的所有环境变量。

---

## 📋 配置清单

需要在`.env`文件中配置以下5个变量：

- [ ] `STRIPE_SECRET_KEY` - Stripe测试密钥（后端使用）
- [ ] `STRIPE_PUBLISHABLE_KEY` - Stripe公钥（前端使用）
- [ ] `STRIPE_PRICE_ID_MONTHLY` - 月付订阅价格ID
- [ ] `STRIPE_PRICE_ID_YEARLY` - 年付订阅价格ID
- [ ] `STRIPE_WEBHOOK_SECRET` - Webhook签名密钥

---

## 步骤 1：注册/登录 Stripe

### 1.1 访问Stripe官网

打开浏览器访问：https://dashboard.stripe.com/register

### 1.2 注册账户

- 如果您已有账户，直接登录
- 如果没有，填写注册信息（邮箱、密码、公司名称）

### 1.3 切换到测试模式

⚠️ **重要**：确保您在**测试模式**下操作（Dashboard右上角会显示"测试模式"标志）

测试模式使用测试密钥，不会产生真实交易。

---

## 步骤 2：获取API密钥

### 2.1 访问API密钥页面

登录后，访问：https://dashboard.stripe.com/test/apikeys

或通过导航：**开发者** → **API密钥**

### 2.2 复制密钥

您会看到两个密钥：

#### ① 可发布密钥（Publishable key）
- 格式：`pk_test_xxxxxxxxxxxxx`
- 用于前端，可以公开
- 点击"显示测试密钥"按钮查看
- 复制完整的密钥字符串

#### ② 秘密密钥（Secret key）
- 格式：`sk_test_xxxxxxxxxxxxx`
- 用于后端，必须保密
- 点击"显示测试密钥"按钮查看
- 复制完整的密钥字符串

### 2.3 更新.env文件

打开项目根目录的`.env`文件，替换以下两行：

```bash
STRIPE_SECRET_KEY=sk_test_您刚才复制的秘密密钥
STRIPE_PUBLISHABLE_KEY=pk_test_您刚才复制的公钥
```

---

## 步骤 3：创建产品和价格

### 3.1 访问产品页面

访问：https://dashboard.stripe.com/test/products

或通过导航：**产品目录** → **产品**

### 3.2 创建产品

点击右上角的 **"+ 创建产品"** 按钮

填写产品信息：
- **名称**：AI工具热点Dashboard订阅
- **描述**：AI工具热点趋势聚合Dashboard服务订阅
- **图片**：（可选）上传产品图片

### 3.3 添加月付价格

在"定价"部分：

1. 点击 **"添加价格"**
2. 填写价格信息：
   - **价格模式**：选择 **"标准定价"**
   - **价格**：输入 `19`
   - **货币**：选择 **"USD - 美元"**
   - **计费周期**：选择 **"按月"**（Monthly）
   - **价格描述**（可选）：月度订阅计划
3. 点击 **"添加价格"** 保存

### 3.4 添加年付价格

继续在同一个产品页面：

1. 再次点击 **"添加价格"**
2. 填写价格信息：
   - **价格模式**：选择 **"标准定价"**
   - **价格**：输入 `190`
   - **货币**：选择 **"USD - 美元"**
   - **计费周期**：选择 **"按年"**（Yearly）
   - **价格描述**（可选）：年度订阅计划（节省10%）
3. 点击 **"添加价格"** 保存

### 3.5 复制价格ID

在产品详情页面，您会看到两个价格：

- 月付价格（$19/月）
- 年付价格（$190/年）

**点击每个价格旁边的"⋯"菜单 → "复制价格ID"**

您会得到两个ID：
- 月付：`price_xxxxxxxxxxxxx`
- 年付：`price_xxxxxxxxxxxxx`

### 3.6 更新.env文件

打开`.env`文件，替换以下两行：

```bash
STRIPE_PRICE_ID_MONTHLY=price_月付价格ID
STRIPE_PRICE_ID_YEARLY=price_年付价格ID
```

---

## 步骤 4：配置Webhook密钥

### 方法A：使用Stripe CLI（推荐，用于本地测试）

#### 4.1 安装Stripe CLI

**macOS**（使用Homebrew）：
```bash
brew install stripe/stripe-cli/stripe
```

**其他系统**：访问 https://stripe.com/docs/stripe-cli 查看安装说明

#### 4.2 登录Stripe CLI

```bash
stripe login
```

这会打开浏览器，点击"允许访问"授权CLI访问您的Stripe账户。

#### 4.3 启动Webhook转发

```bash
stripe listen --forward-to localhost:5000/api/payment/webhook
```

#### 4.4 获取Webhook签名密钥

CLI会输出类似以下内容：

```
> Ready! Your webhook signing secret is whsec_xxxxxxxxxxxxx
```

复制这个密钥（`whsec_`开头）。

⚠️ **注意**：这个密钥是临时的，只在CLI运行期间有效。每次运行`stripe listen`都会生成新的密钥。

#### 4.5 更新.env文件

打开`.env`文件，替换：

```bash
STRIPE_WEBHOOK_SECRET=whsec_您刚才复制的webhook密钥
```

---

### 方法B：使用Stripe Dashboard（用于生产环境）

#### 4.1 访问Webhook页面

访问：https://dashboard.stripe.com/test/webhooks

或通过导航：**开发者** → **Webhook**

#### 4.2 添加Endpoint

1. 点击 **"+ 添加端点"** 按钮
2. 填写端点URL：
   ```
   http://your-domain.com/api/payment/webhook
   ```
   （本地测试可以使用ngrok等工具暴露本地服务器）

3. 选择要监听的事件：
   - `checkout.session.completed` - 支付成功
   - `customer.subscription.updated` - 订阅更新
   - `customer.subscription.deleted` - 订阅取消
   - `invoice.payment_failed` - 支付失败

4. 点击 **"添加端点"** 保存

#### 4.3 获取签名密钥

创建endpoint后，点击进入详情页面，您会看到：

- **签名密钥**（Signing secret）：`whsec_xxxxxxxxxxxxx`

点击"显示"按钮，复制这个密钥。

#### 4.4 更新.env文件

打开`.env`文件，替换：

```bash
STRIPE_WEBHOOK_SECRET=whsec_您刚才复制的webhook密钥
```

---

## 步骤 5：验证配置

### 5.1 检查.env文件

确保您的`.env`文件现在包含以下内容（示例）：

```bash
# === Stripe支付配置 ===
STRIPE_SECRET_KEY=sk_test_51QTPBfBZabc123...
STRIPE_PUBLISHABLE_KEY=pk_test_51QTPBfBZabc123...
STRIPE_PRICE_ID_MONTHLY=price_1QabcdefMonthly
STRIPE_PRICE_ID_YEARLY=price_1QabcdefYearly
STRIPE_WEBHOOK_SECRET=whsec_abc123...
```

### 5.2 重启Flask服务

```bash
# 停止当前服务（如果在运行）
# 然后启动：
./venv/bin/python -m src.dashboard.app
```

### 5.3 启动前端服务

```bash
cd frontend
npm run dev
```

### 5.4 启动Stripe CLI（如果使用方法A）

在新的终端窗口：

```bash
stripe listen --forward-to localhost:5000/api/payment/webhook
```

---

## 步骤 6：测试支付流程

### 6.1 访问Pricing页面

打开浏览器访问：http://localhost:5173/pricing

### 6.2 点击订阅按钮

选择"月付订阅"或"年付订阅"，点击"开始订阅"按钮

### 6.3 在Stripe Checkout填写信息

使用Stripe测试卡号：

- **卡号**：`4242 4242 4242 4242`
- **过期日期**：任意未来日期（例如 `12/25`）
- **CVC**：任意3位数字（例如 `123`）
- **邮箱**：输入您的测试邮箱

### 6.4 完成支付

点击"订阅"按钮，等待支付完成。

### 6.5 验证结果

- ✅ 支付成功后应跳转到成功页面
- ✅ Stripe CLI终端应显示接收到webhook事件
- ✅ 后端日志应显示用户创建成功
- ✅ 您的邮箱应收到欢迎邮件（包含Dashboard访问链接）

---

## 🐛 常见问题

### Q1: "Invalid API Key provided"

**原因**：API密钥配置错误

**解决**：
1. 检查`.env`文件中的密钥是否完整复制
2. 确认是否在测试模式下（密钥应以`sk_test_`开头）
3. 检查密钥是否有多余的空格或换行

### Q2: "No such price"

**原因**：价格ID配置错误

**解决**：
1. 访问 https://dashboard.stripe.com/test/products
2. 点击产品，复制正确的价格ID
3. 更新`.env`文件

### Q3: Webhook事件未收到

**原因**：Webhook配置问题

**解决**：
1. 如果使用Stripe CLI，确保`stripe listen`正在运行
2. 检查CLI输出的webhook密钥是否与`.env`中一致
3. 检查Flask服务是否在运行（端口5000）

### Q4: "No module named 'stripe'"

**原因**：Python包未安装

**解决**：
```bash
./venv/bin/pip install -r requirements.txt
```

---

## 📊 配置完成检查清单

配置完成后，使用此清单验证：

- [ ] `.env`文件包含所有5个Stripe变量
- [ ] 所有密钥值都已替换（不再是"请替换为..."）
- [ ] Flask服务启动无报错
- [ ] 前端服务启动无报错
- [ ] Stripe CLI（如使用）正在运行并转发webhook
- [ ] 访问 http://localhost:5173/pricing 页面正常显示
- [ ] 点击订阅按钮可以跳转到Stripe Checkout
- [ ] 使用测试卡号完成支付成功
- [ ] Webhook事件被成功接收和处理

---

## 📚 相关文档

- [Stripe API文档](https://stripe.com/docs/api)
- [Stripe测试卡号](https://stripe.com/docs/testing#cards)
- [Stripe CLI文档](https://stripe.com/docs/stripe-cli)
- [Stripe Checkout文档](https://stripe.com/docs/payments/checkout)
- [项目测试指南](./STRIPE_TESTING.md)

---

## 🎯 下一步

配置完成后，建议：

1. ✅ 运行完整的测试流程（参考 `STRIPE_TESTING.md`）
2. ✅ 检查webhook事件日志，确保所有事件正确处理
3. ✅ 测试用户从支付到收到邮件的完整流程
4. ✅ 在Stripe Dashboard检查客户和订阅记录
5. 📝 记录任何问题或改进建议

---

**配置完成时间**: _______________
**配置人**: _______________
**测试状态**: [ ] 待测试 [ ] 测试通过 [ ] 有问题（需修复）
