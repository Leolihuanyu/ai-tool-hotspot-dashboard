"""
SMTP配置验证工具
用于验证SMTP邮件发送配置是否正确
可在本地或Render环境中运行
"""

import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


def print_section(title: str):
    """打印分节标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def check_environment_variables():
    """检查所有必需的环境变量"""
    print_section("📋 检查环境变量配置")

    required_vars = {
        "EMAIL_PROVIDER": "邮件提供商（smtp/sendgrid）",
        "SMTP_SERVER": "SMTP服务器地址",
        "SMTP_PORT": "SMTP端口",
        "SMTP_USERNAME": "SMTP用户名",
        "SMTP_PASSWORD": "SMTP密码",
        "SMTP_USE_TLS": "是否使用TLS",
        "EMAIL_FROM": "发件人邮箱"
    }

    config = {}
    missing = []

    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # 隐藏密码显示
            if var == "SMTP_PASSWORD":
                display_value = "*" * 8 + value[-4:] if len(value) > 4 else "*" * len(value)
            else:
                display_value = value
            print(f"✅ {var:20s} = {display_value} ({description})")
            config[var] = value
        else:
            print(f"❌ {var:20s} = [未配置] ({description})")
            missing.append(var)

    if missing:
        print(f"\n⚠️  缺少 {len(missing)} 个必需的环境变量")
        return None, missing

    print(f"\n✅ 所有环境变量配置完整")
    return config, []


def test_smtp_connection(config: dict):
    """测试SMTP服务器连接"""
    print_section("🔌 测试SMTP服务器连接")

    try:
        server = config["SMTP_SERVER"]
        port = int(config["SMTP_PORT"])
        use_tls = config.get("SMTP_USE_TLS", "true").lower() == "true"

        print(f"正在连接到 {server}:{port}...")

        if use_tls:
            smtp = smtplib.SMTP(server, port, timeout=10)
            print(f"✅ 成功连接到SMTP服务器")
            smtp.starttls()
            print(f"✅ TLS加密已启用")
        else:
            smtp = smtplib.SMTP_SSL(server, port, timeout=10)
            print(f"✅ 成功连接到SMTP服务器（SSL）")

        return smtp

    except Exception as e:
        print(f"❌ SMTP连接失败: {str(e)}")
        return None


def test_smtp_authentication(smtp, config: dict):
    """测试SMTP认证"""
    print_section("🔐 测试SMTP认证")

    try:
        username = config["SMTP_USERNAME"]
        password = config["SMTP_PASSWORD"]

        print(f"正在使用用户名 {username} 进行认证...")
        smtp.login(username, password)
        print(f"✅ SMTP认证成功")
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP认证失败: {str(e)}")
        print("\n可能的原因：")
        print("  1. Gmail账户需要生成应用专用密码（16位）")
        print("  2. 密码包含空格或特殊字符")
        print("  3. 密码已过期或被撤销")
        print("\n解决方案：")
        print("  • 访问 https://myaccount.google.com/apppasswords")
        print("  • 生成新的应用专用密码")
        print("  • 确保密码中没有空格")
        return False

    except Exception as e:
        print(f"❌ 认证过程出错: {str(e)}")
        return False


def send_test_email(smtp, config: dict, test_email: str = None):
    """发送测试邮件"""
    print_section("📧 发送测试邮件")

    try:
        from_email = config["EMAIL_FROM"]
        to_email = test_email or from_email

        # 创建邮件
        msg = MIMEMultipart('alternative')
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = f"[测试] SMTP配置验证 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        # HTML内容
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #10B981;">✅ SMTP配置验证成功</h2>
            <p>您的SMTP邮件发送配置工作正常！</p>

            <h3>配置信息：</h3>
            <ul>
                <li><strong>SMTP服务器：</strong>{config["SMTP_SERVER"]}</li>
                <li><strong>端口：</strong>{config["SMTP_PORT"]}</li>
                <li><strong>用户名：</strong>{config["SMTP_USERNAME"]}</li>
                <li><strong>发件人：</strong>{from_email}</li>
            </ul>

            <h3>测试详情：</h3>
            <ul>
                <li><strong>测试时间：</strong>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                <li><strong>环境：</strong>{os.getenv('FLASK_ENV', 'development')}</li>
            </ul>

            <p style="margin-top: 30px; color: #666;">
                此邮件由SMTP配置验证工具自动发送<br>
                AI工具热点Dashboard
            </p>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_content, 'html', 'utf-8'))

        print(f"正在发送测试邮件...")
        print(f"  发件人: {from_email}")
        print(f"  收件人: {to_email}")

        smtp.send_message(msg)
        print(f"✅ 测试邮件发送成功！")
        print(f"\n请检查邮箱 {to_email} 是否收到测试邮件")
        return True

    except Exception as e:
        print(f"❌ 发送测试邮件失败: {str(e)}")
        return False


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("  🧪 SMTP配置验证工具")
    print("  AI工具热点Dashboard - 邮件发送诊断")
    print("=" * 70)
    print(f"  执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  环境: {os.getenv('FLASK_ENV', 'development')}")
    print("=" * 70)

    # 步骤1: 检查环境变量
    config, missing = check_environment_variables()
    if not config:
        print("\n❌ 验证失败：缺少必需的环境变量")
        print("\n请在Render Dashboard或.env文件中配置以下变量：")
        for var in missing:
            print(f"  - {var}")
        return 1

    # 步骤2: 测试SMTP连接
    smtp = test_smtp_connection(config)
    if not smtp:
        print("\n❌ 验证失败：无法连接到SMTP服务器")
        return 1

    # 步骤3: 测试SMTP认证
    auth_success = test_smtp_authentication(smtp, config)
    if not auth_success:
        smtp.quit()
        print("\n❌ 验证失败：SMTP认证失败")
        return 1

    # 步骤4: 发送测试邮件
    test_email = input("\n请输入测试邮箱地址（直接回车使用发件人邮箱）: ").strip()
    if not test_email:
        test_email = None

    email_success = send_test_email(smtp, config, test_email)
    smtp.quit()

    # 总结
    print_section("📊 验证结果总结")
    if email_success:
        print("✅ 所有测试通过！SMTP配置工作正常")
        print("\n您的邮件发送功能已准备就绪：")
        print(f"  • 服务器连接: 正常")
        print(f"  • 认证验证: 通过")
        print(f"  • 邮件发送: 成功")
        return 0
    else:
        print("⚠️  部分测试失败，请检查配置")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  用户取消操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 发生未预期的错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
