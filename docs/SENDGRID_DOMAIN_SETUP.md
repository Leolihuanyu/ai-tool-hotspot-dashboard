# SendGrid 域名认证配置指南

## 概述

使用公司域名 `jereo.co.jp` 配置 SendGrid 域名认证，解决邮件被标记为垃圾邮件的问题。

## 配置流程

### 1. SendGrid 域名认证设置

#### 1.1 登录 SendGrid Dashboard

访问：https://app.sendgrid.com/settings/sender_auth

#### 1.2 开始域名认证

1. 点击 **"Authenticate Your Domain"**
2. 选择 DNS Host：
   - 如果使用 Cloudflare：选择 "Cloudflare"
   - 如果使用其他：选择 "Other Host (Not Listed)"
3. 输入域名：`jereo.co.jp`
4. 勾选 **"Would you also like to brand the links for this domain?"** （可选，推荐）
5. 点击 **"Next"**

#### 1.3 SendGrid 生成 DNS 记录

SendGrid 会生成类似这样的 DNS 记录（示例）：

**CNAME 记录（用于 DKIM）：**
```
Host: s1._domainkey.jereo.co.jp
Value: s1.domainkey.u12345.wl123.sendgrid.net
```

```
Host: s2._domainkey.jereo.co.jp
Value: s2.domainkey.u12345.wl123.sendgrid.net
```

**CNAME 记录（用于链接品牌化，如果选择）：**
```
Host: em1234.jereo.co.jp
Value: u12345.wl123.sendgrid.net
```

⚠️ **注意**：实际的记录值会不同，请以 SendGrid 实际生成的为准！

### 2. 配置 DNS 记录

#### 2.1 访问域名 DNS 管理

根据您公司域名的DNS托管商：
- **Cloudflare**：登录 Cloudflare Dashboard → 选择域名 → DNS
- **阿里云**：登录阿里云控制台 → 域名 → 解析设置
- **腾讯云**：登录腾讯云控制台 → 域名注册 → 解析
- **GoDaddy**：登录 GoDaddy → 我的产品 → DNS

#### 2.2 添加 SendGrid 提供的 CNAME 记录

将 SendGrid 生成的所有 CNAME 记录逐一添加：

| 类型  | 名称 (Host)                    | 值 (Value)                           | TTL  |
|-------|-------------------------------|--------------------------------------|------|
| CNAME | s1._domainkey                 | s1.domainkey.u12345.wl123.sendgrid.net | 3600 |
| CNAME | s2._domainkey                 | s2.domainkey.u12345.wl123.sendgrid.net | 3600 |
| CNAME | em1234                        | u12345.wl123.sendgrid.net           | 3600 |

⚠️ **DNS 记录注意事项**：
- 有些DNS托管商会自动添加域名后缀，只需输入 `s1._domainkey` 而不是 `s1._domainkey.jereo.co.jp`
- Cloudflare 用户：确保 Proxy Status 设置为 **DNS Only（灰色云朵）**

#### 2.3 等待 DNS 生效

- DNS 记录生效通常需要 **5-30分钟**
- 最长可能需要 **48小时**（罕见）

### 3. 验证 DNS 配置

#### 3.1 在 SendGrid 验证

1. 返回 SendGrid Dashboard
2. 在 Sender Authentication 页面，点击域名旁的 **"Verify"**
3. 如果配置正确，状态会变为 ✅ **"Verified"**

如果验证失败：
- 检查 DNS 记录是否正确输入
- 等待更长时间让 DNS 生效
- 使用 DNS 检查工具验证记录

#### 3.2 使用命令行验证 DNS 记录

在终端执行以下命令检查 DNS 记录是否生效：

```bash
# 检查 DKIM CNAME 记录
dig s1._domainkey.jereo.co.jp CNAME +short
dig s2._domainkey.jereo.co.jp CNAME +short

# 或使用 nslookup（Windows）
nslookup -type=CNAME s1._domainkey.jereo.co.jp
```

### 4. 配置 SPF 和 DMARC（推荐）

虽然 SendGrid 的域名认证主要配置 DKIM，但添加 SPF 和 DMARC 记录可以进一步提高邮件投递率。

#### 4.1 添加 SPF 记录（TXT）

| 类型 | 名称 (Host) | 值 (Value)                                    | TTL  |
|------|-------------|-----------------------------------------------|------|
| TXT  | @           | `v=spf1 include:sendgrid.net ~all`            | 3600 |

⚠️ **如果已有 SPF 记录**：
- 不要创建多个 SPF 记录（会导致失效）
- 将 `include:sendgrid.net` 添加到现有记录中
- 例如：`v=spf1 include:_spf.google.com include:sendgrid.net ~all`

#### 4.2 添加 DMARC 记录（TXT）

| 类型 | 名称 (Host)      | 值 (Value)                                                      | TTL  |
|------|------------------|-----------------------------------------------------------------|------|
| TXT  | _dmarc           | `v=DMARC1; p=none; rua=mailto:ri.kanu@jereo.co.jp`              | 3600 |

**DMARC 策略说明**：
- `p=none`：监控模式（推荐初期使用）
- `p=quarantine`：将可疑邮件放入垃圾箱
- `p=reject`：直接拒绝未通过验证的邮件（最严格，慎用）

### 5. 更新代码配置

#### 5.1 更新环境变量

在 Render Dashboard 更新以下环境变量：

```bash
EMAIL_FROM=noreply@jereo.co.jp
EMAIL_FROM_NAME=AI Tool Hotspot
```

#### 5.2 更新代码中的默认值

编辑 `src/utils/config.py`：

```python
def get_email_config():
    return {
        "from_email": os.getenv("EMAIL_FROM", "noreply@jereo.co.jp"),  # 修改默认值
        "from_name": os.getenv("EMAIL_FROM_NAME", "AI Tool Hotspot"),
        # ...其他配置
    }
```

### 6. 测试邮件发送

#### 6.1 使用测试脚本

```bash
# 本地测试（需要配置 .env 文件）
python test_send_email.py

# 或使用生产环境
python scripts/send_test_email.py
```

#### 6.2 检查邮件头

收到测试邮件后，查看邮件原始内容（Show Original），检查以下内容：

✅ **应该看到**：
```
From: noreply@jereo.co.jp
DKIM: PASS (sendgrid.net)
SPF: PASS
DMARC: PASS
```

❌ **不应该看到**：
```
DKIM: FAIL
SPF: SOFTFAIL
Warning: This message may be spam
```

### 7. 监控和优化

#### 7.1 SendGrid Email Activity

在 SendGrid Dashboard → Activity 中监控：
- **Delivered**：成功投递的邮件
- **Bounced**：退信（检查邮箱地址是否有效）
- **Spam Reports**：被标记为垃圾邮件

#### 7.2 逐步提升 DMARC 策略

域名认证稳定运行 1-2 周后：
1. 将 DMARC 策略从 `p=none` 改为 `p=quarantine`
2. 再运行 1-2 周，如果投递率稳定在 95%+
3. 可考虑改为 `p=reject`（可选，更严格）

## 常见问题

### Q1: 为什么 DNS 记录一直验证失败？

**可能原因**：
- DNS 记录还未生效（等待更长时间）
- DNS 记录输入错误（仔细核对 Host 和 Value）
- Cloudflare 用户：Proxy Status 未设置为 DNS Only
- 有些 DNS 服务商自动添加域名后缀

### Q2: 邮件还是进入垃圾箱怎么办？

**排查步骤**：
1. 确认 SendGrid 域名认证状态为 ✅ Verified
2. 检查邮件原始内容，确认 DKIM/SPF/DMARC 都是 PASS
3. 检查邮件内容是否包含垃圾邮件关键词
4. 避免在邮件中放置过多链接
5. 确保邮件有明确的退订链接

### Q3: 需要验证邮箱地址吗？

SendGrid 域名认证完成后：
- ✅ **不需要** 逐个验证发件人邮箱
- ✅ 可以使用 `@jereo.co.jp` 下的任何邮箱地址发送
- 例如：`noreply@jereo.co.jp`、`support@jereo.co.jp` 都可以

### Q4: 免费计划够用吗？

SendGrid 免费计划：
- **100 封/天**（永久免费）
- 对于付费用户订阅邮件 + 过期提醒，通常够用
- 如果用户量增长，可升级到 $19.95/月（40,000 封）

## 预期效果

配置完成后，您将获得：
- ✅ **90-95% 投递率**（Gmail、Outlook、Yahoo 等主流邮箱）
- ✅ 邮件不再被标记为垃圾邮件
- ✅ 收件人看到可信的 `@jereo.co.jp` 发件人地址
- ✅ 符合现代邮件安全标准（DKIM/SPF/DMARC）

## 需要帮助？

如果在配置过程中遇到问题：
1. 检查 SendGrid 官方文档：https://docs.sendgrid.com/ui/account-and-settings/how-to-set-up-domain-authentication
2. 联系公司 IT 部门协助配置 DNS 记录
3. 使用 DNS 检查工具验证记录：https://mxtoolbox.com/

---

**配置完成时间预估**：30-60 分钟（DNS 生效时间除外）
