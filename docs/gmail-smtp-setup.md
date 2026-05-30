# Gmail SMTP 配置指南

本文档详细说明如何配置Gmail SMTP用于项目的邮件发送功能。

## 📋 前提条件

- 拥有Gmail账号
- 能够访问Google账户设置（可能需要科学上网）

## ⚠️ 重要提醒

**从2025年5月1日起，Gmail不再支持"不太安全的应用"访问方式。**

你**必须**：
1. 开启两步验证
2. 使用"应用专用密码"（不能直接用Gmail登录密码）

## 🔧 配置步骤

### 步骤1：开启两步验证

1. 访问Google账户安全设置：
   ```
   https://myaccount.google.com/security
   ```

2. 找到"两步验证"部分
   - 如果未开启，点击"开始使用"
   - 按照指引完成设置（通常需要手机验证）

3. 验证是否成功
   - 看到"两步验证已开启"即可

### 步骤2：生成应用专用密码

1. 访问应用密码生成页面：
   ```
   https://myaccount.google.com/apppasswords
   ```

2. 如果系统提示登录，输入Gmail密码

3. 生成应用密码：
   - 在"选择应用"下拉菜单中选择"其他（自定义名称）"
   - 输入名称：`AI Dashboard` 或任意名称
   - 点击"生成"

4. **立即复制16位密码！**
   ```
   示例格式：aaaa bbbb cccc dddd
   ```
   ⚠️ 这个密码只显示一次，请立即保存！

### 步骤3：配置.env文件

编辑项目根目录的 `.env` 文件：

```bash
# 邮件发送方式
EMAIL_PROVIDER=smtp

# Gmail SMTP配置
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=你的邮箱@gmail.com
SMTP_PASSWORD=<SMTP_PASSWORD>  # 应用专用密码（去掉空格）
SMTP_USE_TLS=true

# 发件人和收件人
EMAIL_FROM=你的邮箱@gmail.com
EMAIL_TO_LIST=收件人@example.com
```

**重要提示：**
- `SMTP_PASSWORD` 填写应用专用密码，**不是Gmail登录密码**
- 将16位密码的空格去掉（aaaa bbbb cccc dddd → aaaabbbbccccdddd）
- `EMAIL_FROM` 必须与 `SMTP_USERNAME` 一致

### 步骤4：测试邮件发送

运行测试命令：

```bash
# 激活虚拟环境
source venv/bin/activate

# 发送测试邮件
python -m src.cli.main send-email --dashboard-url "http://localhost:5000"
```

如果配置正确，你应该：
1. 看到控制台输出"✅ Email sent successfully"
2. 收到测试邮件

## 🔍 常见问题排查

### 问题1：认证失败（535 5.7.8 Username and Password not accepted）

**原因：** 密码错误或未使用应用专用密码

**解决方法：**
1. 确认使用的是"应用专用密码"，不是Gmail登录密码
2. 重新生成应用专用密码
3. 确保密码中没有空格

### 问题2：连接超时

**原因：** 网络问题或防火墙阻止

**解决方法：**
1. 检查网络连接
2. 确认能否访问 smtp.gmail.com:587
3. 尝试使用科学上网工具
4. 临时关闭防火墙测试

```bash
# 测试SMTP连接
telnet smtp.gmail.com 587
```

### 问题3：两步验证无法开启

**原因：** 可能是企业Google账户或有其他限制

**解决方法：**
1. 确认使用的是个人Gmail账号（不是Google Workspace账号）
2. 联系Google支持
3. 考虑使用QQ邮箱作为替代方案

### 问题4：没收到邮件

**可能原因：**
- 邮件进入垃圾箱
- 收件人地址错误
- 发送失败但未报错

**检查步骤：**
1. 查看垃圾邮件文件夹
2. 检查 `.env` 中的 `EMAIL_TO_LIST` 配置
3. 查看日志文件 `logs/app.log`

## 📊 Gmail SMTP 限制

| 限制项 | 免费账号 |
|-------|---------|
| 每天发送上限 | 500封 |
| 单封邮件收件人 | 100个 |
| 限制周期 | 滚动24小时 |
| 超限后恢复 | 1-24小时 |

**对本项目影响：**
每天发送1封报告邮件，完全在限额内 ✅

## 🆚 其他SMTP邮箱对比

如果Gmail不可用，可以考虑以下替代方案：

### QQ邮箱（推荐国内用户）

```bash
SMTP_SERVER=smtp.qq.com
SMTP_PORT=587
SMTP_USERNAME=你的QQ号@qq.com
SMTP_PASSWORD=QQ邮箱授权码  # 在QQ邮箱设置中生成
SMTP_USE_TLS=true
```

**优点：** 国内访问稳定，无需科学上网

**获取授权码：**
1. 登录QQ邮箱网页版
2. 设置 → 账户 → 开启SMTP服务
3. 生成授权码

### 163邮箱

```bash
SMTP_SERVER=smtp.163.com
SMTP_PORT=465
SMTP_USERNAME=你的邮箱@163.com
SMTP_PASSWORD=163邮箱授权码
SMTP_USE_TLS=false  # 使用SSL
```

### iCloud邮箱

```bash
SMTP_SERVER=smtp.mail.me.com
SMTP_PORT=587
SMTP_USERNAME=你的邮箱@icloud.com
SMTP_PASSWORD=iCloud专用App密码
SMTP_USE_TLS=true
```

**获取专用App密码：**
1. 访问 https://appleid.apple.com
2. 登录 → 安全 → App专用密码
3. 生成密码

## 📚 相关资源

- [Gmail SMTP官方文档](https://support.google.com/mail/answer/7126229)
- [应用专用密码说明](https://support.google.com/accounts/answer/185833)
- [Gmail发送限制](https://support.google.com/mail/answer/22839)

## 🆘 需要帮助？

如果遇到问题：
1. 查看 `logs/app.log` 日志文件
2. 确认所有配置项都正确填写
3. 尝试使用其他SMTP服务（QQ/163）作为替代

---

配置完成后，你的AI工具热点仪表板就可以通过Gmail发送每日报告邮件了！📧
