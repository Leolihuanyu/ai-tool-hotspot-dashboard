"""Flask Webêh(

ÐWebLbU:AIåwí¹:
"""

from flask import Flask
from src.utils.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)


def create_app():
    """úFlask(

    Returns:
        Flask(
    """
    app = Flask(__name__)

    # }Mn
    app.config['DEBUG'] = config.flask_debug
    app.config['PORT'] = config.flask_port
    app.config['SECRET_KEY'] = getattr(config, 'flask_secret_key', 'dev-secret-key-change-in-production')

    # èï1
    from src.dashboard.routes import register_routes
    register_routes(app)

    logger.info("Flask(Ë")
    return app


def run_app():
    """ÐLFlask("""
    app = create_app()

    port = config.flask_port
    debug = config.flask_debug

    logger.info(f"/¨Flask(: http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=debug)


# 为生产环境（Gunicorn）创建app实例
# 这样Gunicorn可以通过 "src.dashboard.app:app" 找到Flask应用对象
app = create_app()


if __name__ == '__main__':
    run_app()
