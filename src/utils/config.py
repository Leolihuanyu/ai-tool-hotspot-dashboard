"""配置加载工具

使用python-dotenv从.env文件加载配置,遵循宪法原则III(最小依赖)。
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Config:
    """应用配置类"""

    def __init__(self, env_file: str = ".env"):
        """初始化配置

        Args:
            env_file: .env文件路径
        """
        # 加载.env文件
        env_path = Path(env_file)
        if env_path.exists():
            load_dotenv(env_path)

    # === LLM API配置 ===
    @property
    def anthropic_api_key(self) -> Optional[str]:
        return os.getenv("ANTHROPIC_API_KEY")

    @property
    def openai_api_key(self) -> Optional[str]:
        return os.getenv("OPENAI_API_KEY")

    @property
    def llm_provider(self) -> str:
        return os.getenv("LLM_PROVIDER", "claude")

    @property
    def llm_model(self) -> str:
        return os.getenv("LLM_MODEL", "claude-haiku-3-20240307")

    @property
    def llm_use_batch_api(self) -> bool:
        return os.getenv("LLM_USE_BATCH_API", "true").lower() == "true"

    # === 邮件服务配置 ===
    @property
    def email_provider(self) -> str:
        """邮件发送方式: smtp 或 sendgrid"""
        return os.getenv("EMAIL_PROVIDER", "smtp")

    @property
    def sendgrid_api_key(self) -> Optional[str]:
        return os.getenv("SENDGRID_API_KEY")

    @property
    def smtp_server(self) -> Optional[str]:
        return os.getenv("SMTP_SERVER")

    @property
    def smtp_port(self) -> int:
        return int(os.getenv("SMTP_PORT", "587"))

    @property
    def smtp_username(self) -> Optional[str]:
        return os.getenv("SMTP_USERNAME")

    @property
    def smtp_password(self) -> Optional[str]:
        return os.getenv("SMTP_PASSWORD")

    @property
    def smtp_use_tls(self) -> bool:
        return os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    @property
    def email_from(self) -> Optional[str]:
        return os.getenv("EMAIL_FROM")

    @property
    def email_to_list(self) -> list:
        to_list = os.getenv("EMAIL_TO_LIST", "")
        return [email.strip() for email in to_list.split(",") if email.strip()]

    @property
    def email_schedule_cron(self) -> str:
        return os.getenv("EMAIL_SCHEDULE_CRON", "0 8 * * *")

    # === 数据库配置 ===
    @property
    def database_path(self) -> str:
        return os.getenv("DATABASE_PATH", "data/db.sqlite")

    # === 数据抓取配置 ===
    @property
    def scraper_rate_limit(self) -> float:
        return float(os.getenv("SCRAPER_RATE_LIMIT", "1.0"))

    @property
    def scraper_max_retries(self) -> int:
        return int(os.getenv("SCRAPER_MAX_RETRIES", "3"))

    @property
    def scraper_timeout(self) -> int:
        return int(os.getenv("SCRAPER_TIMEOUT", "10"))

    # === 爬虫启用/禁用配置 ===
    # AI工具爬虫
    @property
    def enable_scraper_futurepedia(self) -> bool:
        return os.getenv("ENABLE_SCRAPER_FUTUREPEDIA", "true").lower() == "true"

    @property
    def enable_scraper_producthunt(self) -> bool:
        return os.getenv("ENABLE_SCRAPER_PRODUCTHUNT", "true").lower() == "true"

    @property
    def enable_scraper_theresanai(self) -> bool:
        return os.getenv("ENABLE_SCRAPER_THERESANAI", "false").lower() == "true"

    # 热点趋势爬虫
    @property
    def enable_scraper_reddit(self) -> bool:
        return os.getenv("ENABLE_SCRAPER_REDDIT", "true").lower() == "true"

    @property
    def enable_scraper_hackernews(self) -> bool:
        return os.getenv("ENABLE_SCRAPER_HACKERNEWS", "true").lower() == "true"

    @property
    def enable_scraper_github(self) -> bool:
        return os.getenv("ENABLE_SCRAPER_GITHUB", "true").lower() == "true"

    @property
    def enable_scraper_tiktok(self) -> bool:
        return os.getenv("ENABLE_SCRAPER_TIKTOK", "true").lower() == "true"

    @property
    def enable_scraper_youtube(self) -> bool:
        return os.getenv("ENABLE_SCRAPER_YOUTUBE", "true").lower() == "true"

    @property
    def enable_scraper_x_twitter(self) -> bool:
        return os.getenv("ENABLE_SCRAPER_X_TWITTER", "true").lower() == "true"

    @property
    def enable_scraper_google_trends(self) -> bool:
        return os.getenv("ENABLE_SCRAPER_GOOGLE_TRENDS", "true").lower() == "true"

    # === 评分权重配置 ===
    @property
    def score_weight_pain_clarity(self) -> float:
        return float(os.getenv("SCORE_WEIGHT_PAIN_CLARITY", "0.4"))

    @property
    def score_weight_mvp_speed(self) -> float:
        return float(os.getenv("SCORE_WEIGHT_MVP_SPEED", "0.3"))

    @property
    def score_weight_monetization(self) -> float:
        return float(os.getenv("SCORE_WEIGHT_MONETIZATION", "0.3"))

    @property
    def score_weight_japan_market(self) -> float:
        return float(os.getenv("SCORE_WEIGHT_JAPAN_MARKET", "0.2"))

    @property
    def score_weight_us_eu_market(self) -> float:
        return float(os.getenv("SCORE_WEIGHT_US_EU_MARKET", "0.2"))

    @property
    def score_weight_trending(self) -> float:
        return float(os.getenv("SCORE_WEIGHT_TRENDING", "0.3"))

    # === Flask配置 ===
    @property
    def flask_env(self) -> str:
        return os.getenv("FLASK_ENV", "development")

    @property
    def flask_debug(self) -> bool:
        return os.getenv("FLASK_DEBUG", "true").lower() == "true"

    @property
    def flask_port(self) -> int:
        return int(os.getenv("FLASK_PORT", "5000"))

    @property
    def dashboard_url(self) -> str:
        """Dashboard URL（用于邮件等外部链接）"""
        return os.getenv("DASHBOARD_URL", "http://127.0.0.1:5000")

    # === YouTube API配置 ===
    @property
    def youtube_api_key(self) -> Optional[str]:
        return os.getenv("YOUTUBE_API_KEY")

    # === Reddit API配置 ===
    @property
    def reddit_client_id(self) -> Optional[str]:
        return os.getenv("REDDIT_CLIENT_ID")

    @property
    def reddit_client_secret(self) -> Optional[str]:
        return os.getenv("REDDIT_CLIENT_SECRET")

    @property
    def reddit_user_agent(self) -> str:
        return os.getenv("REDDIT_USER_AGENT", "AI-Opportunity-Matcher/1.0")

    # === GitHub API配置 ===
    @property
    def github_token(self) -> Optional[str]:
        """GitHub Personal Access Token用于访问Discussions API"""
        return os.getenv("GITHUB_TOKEN")

    # === 日志配置 ===
    @property
    def log_level(self) -> str:
        return os.getenv("LOG_LEVEL", "INFO")

    @property
    def log_format(self) -> str:
        return os.getenv("LOG_FORMAT", "json")

    def validate(self) -> tuple[bool, list[str]]:
        """验证必需的配置项

        Returns:
            (是否通过验证, 缺失的配置项列表)
        """
        missing = []

        # 检查LLM API密钥
        if self.llm_provider == "claude" and not self.anthropic_api_key:
            missing.append("ANTHROPIC_API_KEY")
        elif self.llm_provider == "openai" and not self.openai_api_key:
            missing.append("OPENAI_API_KEY")

        return len(missing) == 0, missing


# 创建全局配置实例
config = Config()
