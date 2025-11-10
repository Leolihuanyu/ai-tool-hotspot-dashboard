"""Flask Web应用

Dashboard Web界面入口：AI工具热点分析。
"""

import os
from flask import Flask
from flask_cors import CORS
from src.utils.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)


def create_app():
    """创建Flask应用

    Returns:
        Flask应用实例
    """
    app = Flask(__name__)

    # 基础配置
    app.config['DEBUG'] = config.flask_debug
    app.config['PORT'] = config.flask_port
    app.config['SECRET_KEY'] = getattr(config, 'flask_secret_key', 'dev-secret-key-change-in-production')

    # CORS配置（用于前后端分离架构）
    # 允许Vercel前端和本地开发环境访问
    allowed_origins = [
        "https://ai-tool-hotspot-dashboard.vercel.app",  # Vercel生产环境
        "https://*.vercel.app",  # Vercel预览环境
        "http://localhost:5173",  # Vite本地开发
        "http://localhost:3000",  # 备用本地端口
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # 从环境变量获取额外的允许域名
    custom_origin = os.getenv('ALLOWED_ORIGIN')
    if custom_origin:
        allowed_origins.append(custom_origin)

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": allowed_origins,
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
                "expose_headers": ["Content-Type"],
                "supports_credentials": True,
                "max_age": 3600
            }
        }
    )

    logger.info(f"CORS配置完成，允许的域名: {allowed_origins}")

    # 注册路由
    from src.dashboard.routes import register_routes
    register_routes(app)

    logger.info("Flask应用创建完成")
    return app


def run_app():
    """启动Flask应用"""
    app = create_app()

    port = config.flask_port
    debug = config.flask_debug

    logger.info(f"启动Flask应用: http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=debug)


# 为生产环境（Gunicorn）创建app实例
# 这样Gunicorn可以通过 "src.dashboard.app:app" 找到Flask应用对象
app = create_app()


if __name__ == '__main__':
    run_app()
