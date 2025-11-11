# 域名迁移操作清单

将邮件发件人从 `leolihuanyu@gmail.com` 迁移到 `noreply@jereo.co.jp`

## 前置准备

- [ ] 确认有 jereo.co.jp 的 DNS 管理权限
- [ ] 确认公司允许使用该域名发送应用邮件
- [ ] 决定使用的发件人邮箱地址：
  - 推荐：`noreply@jereo.co.jp`
  - 备选：`support@jereo.co.jp` 或 `ri.kanu@jereo.co.jp`

## 第一阶段：SendGrid 域名认证配置

### 1. SendGrid Dashboard 配置

- [ ] 登录 https://app.sendgrid.com/settings/sender_auth
- [ ] 点击 "Authenticate Your Domain"
- [ ] 输入域名：`jereo.co.jp`
- [ ] 复制 SendGrid 生成的 DNS 记录（CNAME）

### 2. DNS 记录配置

- [ ] 登录 jereo.co.jp 域名的 DNS 管理界面
- [ ] 添加 SendGrid 生成的 CNAME 记录（通常 2-3 条）
  - s1._domainkey.jereo.co.jp
  - s2._domainkey.jereo.co.jp
  - em*.jereo.co.jp（如果启用链接品牌化）
- [ ] 添加 SPF 记录（TXT）：`v=spf1 include:sendgrid.net ~all`
- [ ] 添加 DMARC 记录（TXT）：`v=DMARC1; p=none; rua=mailto:ri.kanu@jereo.co.jp`
- [ ] 等待 DNS 生效（5-30分钟）

### 3. 验证配置

- [ ] 在 SendGrid Dashboard 点击 "Verify"
- [ ] 确认域名认证状态为 ✅ Verified
- [ ] 使用 `dig` 或 `nslookup` 命令验证 DNS 记录

```bash
dig s1._domainkey.jereo.co.jp CNAME +short
dig s2._domainkey.jereo.co.jp CNAME +short
```

## 第二阶段：代码配置更新

### 4. 更新环境变量（Render）

- [ ] 登录 Render Dashboard
- [ ] 进入 backend service → Environment
- [ ] 更新以下变量：
  ```
  EMAIL_FROM=noreply@jereo.co.jp
  EMAIL_FROM_NAME=AI Tool Hotspot
  ```
- [ ] 保存并等待服务重启

### 5. 更新代码默认值

- [ ] 修改 `src/utils/config.py` 的默认发件人邮箱
- [ ] 修改所有邮件模板中的发件人信息（如有硬编码）
- [ ] 提交代码到 Git
- [ ] 推送到 main 分支（自动触发 Render 部署）

## 第三阶段：测试验证

### 6. 发送测试邮件

- [ ] 运行测试脚本：`python test_send_email.py`
- [ ] 检查测试邮件是否成功发送
- [ ] 查看邮件原始内容，确认：
  - From: noreply@jereo.co.jp
  - DKIM: PASS
  - SPF: PASS
  - DMARC: PASS

### 7. 测试真实场景

- [ ] 创建一个测试 Stripe 订阅
- [ ] 确认收到订阅欢迎邮件
- [ ] 检查邮件是否在收件箱（不在垃圾箱）
- [ ] 点击邮件中的 Dashboard 链接，确认 token 有效

### 8. 监控投递情况

- [ ] 在 SendGrid Dashboard → Activity 查看邮件投递统计
- [ ] 关注 Delivered / Bounced / Spam Reports 比例
- [ ] 目标：Delivered > 95%

## 第四阶段：优化和清理

### 9. 更新 Single Sender Verification

- [ ] 在 SendGrid Dashboard → Settings → Sender Authentication
- [ ] 删除或停用旧的 `leolihuanyu@gmail.com` Single Sender
- [ ] （可选）添加新的 Single Sender：`noreply@jereo.co.jp`
  - 注意：域名认证后，Single Sender 不再必需

### 10. DMARC 策略优化（1-2周后）

- [ ] 确认邮件投递率稳定在 95%+
- [ ] 将 DMARC 策略从 `p=none` 升级到 `p=quarantine`
- [ ] 继续监控 1-2 周
- [ ] （可选）升级到 `p=reject`（最严格）

## 回滚计划

如果遇到问题需要回滚：

- [ ] 在 Render 恢复旧的环境变量：
  ```
  EMAIL_FROM=leolihuanyu@gmail.com
  ```
- [ ] Git revert 代码更改
- [ ] 重新部署

## 预期时间线

| 阶段 | 时间 | 说明 |
|------|------|------|
| DNS 配置 | 30-60分钟 | 包含 DNS 生效时间 |
| 代码部署 | 5-10分钟 | Render 自动部署 |
| 测试验证 | 15-30分钟 | 完整测试流程 |
| **总计** | **1-2小时** | DNS 生效可能更久 |

## 成功标准

✅ 完成标志：
- SendGrid 域名认证状态为 Verified
- 测试邮件 DKIM/SPF/DMARC 全部 PASS
- 邮件不进入垃圾箱
- Dashboard token 访问正常
- 投递率 > 95%

## 需要的信息

在开始之前，请确认：
1. 您是否有 jereo.co.jp 的 DNS 管理权限？
2. 公司是否批准使用该域名发送应用邮件？
3. 希望使用哪个发件人邮箱地址？
   - noreply@jereo.co.jp（推荐）
   - support@jereo.co.jp
   - ri.kanu@jereo.co.jp

---

**准备好后，请按照清单逐步执行，或告诉我开始执行自动化配置。**
