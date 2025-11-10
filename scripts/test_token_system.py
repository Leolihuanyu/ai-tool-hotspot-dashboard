#!/usr/bin/env python3
"""
Token认证系统完整测试脚本

测试内容：
1. 环境配置检查
2. TokenManager单元测试
3. 后端API测试
4. 生成测试用签名URL

使用方法：
    python scripts/test_token_system.py
"""

import os
import sys
import time
import json
import subprocess
import signal
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载.env文件
env_file = project_root / ".env"
if env_file.exists():
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# 配色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """打印标题"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 70}{Colors.RESET}\n")

def print_success(text):
    """打印成功信息"""
    print(f"{Colors.GREEN}✓{Colors.RESET} {text}")

def print_error(text):
    """打印错误信息"""
    print(f"{Colors.RED}✗{Colors.RESET} {text}")

def print_warning(text):
    """打印警告信息"""
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {text}")

def print_info(text):
    """打印信息"""
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {text}")


class TokenSystemTester:
    """Token系统测试器"""

    def __init__(self):
        self.flask_process = None
        self.test_results = {
            "environment": False,
            "token_manager": False,
            "api_test": False
        }

    def check_environment(self):
        """检查环境配置"""
        print_header("1. 环境配置检查")

        checks_passed = True

        # 检查.env文件
        env_file = project_root / ".env"
        if env_file.exists():
            print_success(f".env文件存在: {env_file}")
        else:
            print_error(".env文件不存在")
            checks_passed = False

        # 检查JWT_SECRET_KEY
        jwt_secret = os.getenv("JWT_SECRET_KEY")
        if jwt_secret:
            print_success(f"JWT_SECRET_KEY已配置 (长度: {len(jwt_secret)})")
        else:
            print_error("JWT_SECRET_KEY未配置")
            checks_passed = False

        # 检查Flask端口配置
        flask_port = os.getenv("FLASK_PORT", "8010")
        print_success(f"Flask端口配置: {flask_port}")

        # 检查DASHBOARD_BASE_URL
        dashboard_url = os.getenv("DASHBOARD_BASE_URL", "http://127.0.0.1:3010")
        print_success(f"Dashboard URL: {dashboard_url}")

        # 检查必需的Python模块
        try:
            from src.auth.token_manager import TokenManager
            print_success("TokenManager模块可导入")
        except Exception as e:
            print_error(f"TokenManager模块导入失败: {e}")
            checks_passed = False

        self.test_results["environment"] = checks_passed
        return checks_passed

    def test_token_manager(self):
        """测试TokenManager"""
        print_header("2. TokenManager单元测试")

        try:
            from src.auth.token_manager import TokenManager

            tm = TokenManager()
            test_email = "test@example.com"
            tests_passed = 0
            total_tests = 5

            # 测试1: 生成token
            print_info("测试1: 生成token...")
            token = tm.generate_token(test_email, subscription_type="beta")
            if token:
                print_success(f"Token生成成功 (长度: {len(token)})")
                tests_passed += 1
            else:
                print_error("Token生成失败")

            # 测试2: 验证有效token
            print_info("测试2: 验证有效token...")
            result = tm.verify_token(token)
            if result.get("valid") and result.get("email") == test_email:
                print_success(f"Token验证成功: {result}")
                tests_passed += 1
            else:
                print_error(f"Token验证失败: {result}")

            # 测试3: 生成Dashboard URL
            print_info("测试3: 生成Dashboard URL...")
            dashboard_url = tm.generate_dashboard_url(
                base_url="http://127.0.0.1:3010",
                email=test_email
            )
            if "token=" in dashboard_url and "email=" in dashboard_url:
                print_success(f"Dashboard URL生成成功")
                print_info(f"   URL: {dashboard_url[:80]}...")
                tests_passed += 1
            else:
                print_error("Dashboard URL生成失败")

            # 测试4: 测试无效token
            print_info("测试4: 测试无效token...")
            invalid_result = tm.verify_token("invalid-token-string")
            if not invalid_result.get("valid"):
                print_success(f"正确拒绝无效token: {invalid_result.get('error')}")
                tests_passed += 1
            else:
                print_error("未能拒绝无效token")

            # 测试5: 获取token信息
            print_info("测试5: 获取token详细信息...")
            token_info = tm.get_token_info(token)
            if token_info.get("valid_signature"):
                print_success(f"Token信息获取成功: email={token_info.get('email')}")
                tests_passed += 1
            else:
                print_error("Token信息获取失败")

            print(f"\n{Colors.BOLD}测试结果: {tests_passed}/{total_tests} 通过{Colors.RESET}")

            self.test_results["token_manager"] = tests_passed == total_tests
            return tests_passed == total_tests

        except Exception as e:
            print_error(f"TokenManager测试失败: {e}")
            import traceback
            traceback.print_exc()
            self.test_results["token_manager"] = False
            return False

    def start_flask_server(self):
        """启动Flask服务器（后台进程）"""
        print_header("3. 启动Flask后端服务器")

        try:
            flask_port = os.getenv("FLASK_PORT", "8010")
            print_info(f"在端口 {flask_port} 启动Flask服务器...")

            # 启动Flask服务器
            self.flask_process = subprocess.Popen(
                ["python", "-m", "src.dashboard.app"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(project_root)
            )

            # 等待服务器启动
            print_info("等待服务器就绪...")
            time.sleep(3)

            # 检查进程是否还在运行
            if self.flask_process.poll() is None:
                print_success(f"Flask服务器已启动 (PID: {self.flask_process.pid})")
                return True
            else:
                stdout, stderr = self.flask_process.communicate()
                print_error("Flask服务器启动失败")
                print_error(f"stdout: {stdout.decode()}")
                print_error(f"stderr: {stderr.decode()}")
                return False

        except Exception as e:
            print_error(f"启动Flask服务器失败: {e}")
            return False

    def test_api_endpoints(self):
        """测试API端点"""
        print_header("4. 后端API测试")

        try:
            import requests
            from src.auth.token_manager import TokenManager

            tm = TokenManager()
            test_email = "api-test@example.com"
            flask_port = os.getenv("FLASK_PORT", "8010")
            base_url = f"http://127.0.0.1:{flask_port}"

            tests_passed = 0
            total_tests = 2

            # 生成测试token
            token = tm.generate_token(test_email, subscription_type="beta")

            # 测试1: GET /api/verify-token (有效token)
            print_info("测试1: GET /api/verify-token (有效token)...")
            try:
                response = requests.get(
                    f"{base_url}/api/verify-token",
                    params={"token": token},
                    timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("valid"):
                        print_success(f"API返回有效响应: {data}")
                        tests_passed += 1
                    else:
                        print_error(f"Token验证失败: {data}")
                else:
                    print_error(f"API返回错误状态码: {response.status_code}")
            except Exception as e:
                print_error(f"API请求失败: {e}")

            # 测试2: GET /api/verify-token (无效token)
            print_info("测试2: GET /api/verify-token (无效token)...")
            try:
                response = requests.get(
                    f"{base_url}/api/verify-token",
                    params={"token": "invalid-token"},
                    timeout=5
                )
                data = response.json()
                if not data.get("valid"):
                    print_success(f"正确拒绝无效token: {data.get('error')}")
                    tests_passed += 1
                else:
                    print_error("未能拒绝无效token")
            except Exception as e:
                print_error(f"API请求失败: {e}")

            print(f"\n{Colors.BOLD}API测试结果: {tests_passed}/{total_tests} 通过{Colors.RESET}")

            self.test_results["api_test"] = tests_passed == total_tests
            return tests_passed == total_tests

        except ImportError:
            print_error("requests模块未安装，跳过API测试")
            print_info("提示: 运行 'pip install requests' 安装")
            return False
        except Exception as e:
            print_error(f"API测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def generate_test_url(self):
        """生成测试用签名URL"""
        print_header("5. 生成测试URL")

        try:
            from src.auth.token_manager import TokenManager

            tm = TokenManager()
            test_email = "demo@example.com"
            dashboard_base_url = os.getenv("DASHBOARD_BASE_URL", "http://127.0.0.1:3010")

            # 生成Dashboard URL
            dashboard_url = tm.generate_dashboard_url(
                base_url=dashboard_base_url,
                email=test_email,
                subscription_type="beta"
            )

            print_success("测试URL已生成！")
            print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'─' * 70}{Colors.RESET}")
            print(f"{Colors.BOLD}📧 测试邮箱:{Colors.RESET} {test_email}")
            print(f"{Colors.BOLD}🔗 访问URL:{Colors.RESET}\n")
            print(f"{Colors.CYAN}{dashboard_url}{Colors.RESET}\n")
            print(f"{Colors.BOLD}{Colors.MAGENTA}{'─' * 70}{Colors.RESET}")

            print(f"\n{Colors.BOLD}📋 使用方法:{Colors.RESET}")
            print("1. 复制上面的URL")
            print("2. 在浏览器中打开")
            print("3. 观察认证流程：")
            print(f"   {Colors.GREEN}✓{Colors.RESET} URL中的token自动验证")
            print(f"   {Colors.GREEN}✓{Colors.RESET} Token保存到localStorage")
            print(f"   {Colors.GREEN}✓{Colors.RESET} URL参数被清除")
            print(f"   {Colors.GREEN}✓{Colors.RESET} 成功访问Dashboard")
            print(f"\n{Colors.YELLOW}💡 提示:{Colors.RESET} Token有效期24小时")

            return True

        except Exception as e:
            print_error(f"生成测试URL失败: {e}")
            return False

    def cleanup(self):
        """清理资源"""
        if self.flask_process:
            print_info("正在关闭Flask服务器...")
            self.flask_process.send_signal(signal.SIGTERM)
            self.flask_process.wait(timeout=5)
            print_success("Flask服务器已关闭")

    def print_summary(self):
        """打印测试摘要"""
        print_header("测试摘要")

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)

        print(f"{Colors.BOLD}测试项目:{Colors.RESET}")
        for test_name, result in self.test_results.items():
            status = f"{Colors.GREEN}✓ 通过{Colors.RESET}" if result else f"{Colors.RED}✗ 失败{Colors.RESET}"
            print(f"  - {test_name}: {status}")

        print(f"\n{Colors.BOLD}总体结果: {passed_tests}/{total_tests} 通过{Colors.RESET}")

        if passed_tests == total_tests:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 所有测试通过！认证系统工作正常。{Colors.RESET}")
        else:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  部分测试失败，请检查上面的错误信息。{Colors.RESET}")


def main():
    """主函数"""
    tester = TokenSystemTester()

    try:
        # 1. 环境检查
        if not tester.check_environment():
            print_error("\n环境配置检查失败，请先修复配置问题。")
            return 1

        # 2. TokenManager测试
        if not tester.test_token_manager():
            print_warning("\nTokenManager测试失败，但继续执行...")

        # 3. 启动Flask服务器
        if tester.start_flask_server():
            # 4. API测试
            tester.test_api_endpoints()

        # 5. 生成测试URL
        tester.generate_test_url()

        # 6. 打印摘要
        tester.print_summary()

        return 0

    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}测试被用户中断{Colors.RESET}")
        return 130

    except Exception as e:
        print_error(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        # 清理资源
        tester.cleanup()


if __name__ == "__main__":
    sys.exit(main())
