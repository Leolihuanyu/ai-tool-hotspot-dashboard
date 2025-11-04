"""基础爬虫类

实现所有爬虫共享的功能:重试逻辑、速率限制、robots.txt检查。
遵循宪法原则I(数据可靠性)。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from ratelimit import limits, sleep_and_retry
from datetime import datetime

from src.models import AITool, TrendingTopic
from src.utils.config import config
from src.utils.logger import setup_logger


class BaseScraper(ABC):
    """爬虫基类

    所有爬虫都应继承此类并实现抽象方法。

    Attributes:
        source_name: 数据源名称
        base_url: 数据源基础URL
        user_agent: User-Agent标识
        rate_limit: 速率限制(秒/请求)
        max_retries: 最大重试次数
        timeout: 请求超时时间(秒)
    """

    def __init__(self, source_name: str, base_url: str):
        """初始化爬虫

        Args:
            source_name: 数据源名称
            base_url: 数据源基础URL
        """
        self.source_name = source_name
        self.base_url = base_url
        self.user_agent = "AI-Opportunity-Matcher/1.0 (+https://github.com/yourproject)"
        self.rate_limit = config.scraper_rate_limit
        self.max_retries = config.scraper_max_retries
        self.timeout = config.scraper_timeout

        # 初始化requests session（用于保持连接和设置默认headers）
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent
        })

        self.logger = setup_logger(
            f"scraper.{source_name.lower().replace(' ', '_')}",
            log_level=config.log_level,
            log_file=f"logs/scraper_{source_name.lower().replace(' ', '_')}.log",
            json_format=(config.log_format == "json")
        )

        # 初始化robots.txt parser
        self.robots_parser = RobotFileParser()
        try:
            robots_url = f"{self.base_url}/robots.txt"
            self.robots_parser.set_url(robots_url)
            self.robots_parser.read()
        except Exception as e:
            self.logger.warning(f"Failed to read robots.txt: {e}")

    def can_fetch(self, url: str) -> bool:
        """检查是否允许爬取该URL

        Args:
            url: 要检查的URL

        Returns:
            True如果允许爬取,False如果不允许
        """
        try:
            return self.robots_parser.can_fetch(self.user_agent, url)
        except Exception:
            # 如果检查失败,默认允许
            return True

    @sleep_and_retry
    @limits(calls=1, period=1)  # 默认1秒1次请求
    def rate_limited_request(self, url: str, **kwargs) -> requests.Response:
        """速率限制的HTTP请求

        Args:
            url: 请求URL
            **kwargs: 传递给requests.get的其他参数

        Returns:
            Response对象

        Raises:
            requests.RequestException: 请求失败
        """
        # 设置默认headers
        headers = kwargs.pop('headers', {})
        headers['User-Agent'] = self.user_agent

        # 设置默认timeout
        timeout = kwargs.pop('timeout', self.timeout)

        return requests.get(url, headers=headers, timeout=timeout, **kwargs)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def fetch_with_retry(self, url: str, **kwargs) -> requests.Response:
        """带重试的HTTP请求

        使用指数退避策略重试失败的请求。

        Args:
            url: 请求URL
            **kwargs: 传递给rate_limited_request的其他参数

        Returns:
            Response对象

        Raises:
            requests.RequestException: 所有重试都失败后抛出
        """
        # 检查robots.txt
        if not self.can_fetch(url):
            self.logger.warning(f"Blocked by robots.txt: {url}")
            raise requests.RequestException(f"Blocked by robots.txt: {url}")

        # 执行速率限制的请求
        response = self.rate_limited_request(url, **kwargs)
        response.raise_for_status()

        return response

    @abstractmethod
    def scrape(self, limit: int = None) -> List[Dict[str, Any]]:
        """抓取数据

        子类必须实现此方法。

        Args:
            limit: 限制抓取数量(可选,用于测试)

        Returns:
            原始数据字典列表

        Raises:
            Exception: 抓取失败
        """
        pass

    @abstractmethod
    def normalize(self, raw_data: Dict[str, Any]) -> Union[AITool, TrendingTopic]:
        """将原始数据转换为标准模型

        子类必须实现此方法。

        Args:
            raw_data: 原始数据字典

        Returns:
            AITool或TrendingTopic对象

        Raises:
            ValidationError: 数据验证失败
        """
        pass

    def run(self, limit: int = None) -> tuple[List[Union[AITool, TrendingTopic]], float]:
        """运行完整的抓取流程

        抓取数据并规范化。

        Args:
            limit: 限制抓取数量(可选,用于测试)

        Returns:
            (规范化后的数据列表, 耗时秒数)
        """
        start_time = datetime.now()

        try:
            self.logger.info(f"Starting scraping from {self.source_name}")

            # 抓取原始数据
            raw_data_list = self.scrape(limit=limit)

            # 规范化数据
            normalized_data = []
            for raw_data in raw_data_list:
                try:
                    normalized = self.normalize(raw_data)
                    normalized_data.append(normalized)
                except Exception as e:
                    self.logger.warning(
                        f"Failed to normalize data: {e}",
                        extra={"extra_fields": {"raw_data": raw_data}}
                    )
                    continue

            duration = (datetime.now() - start_time).total_seconds()

            self.logger.info(
                f"Scraping completed: {len(normalized_data)} records in {duration:.2f}s",
                extra={"extra_fields": {
                    "source": self.source_name,
                    "count": len(normalized_data),
                    "duration_seconds": duration
                }}
            )

            return normalized_data, duration

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()

            self.logger.error(
                f"Scraping failed: {e}",
                extra={"extra_fields": {
                    "source": self.source_name,
                    "error": str(e),
                    "duration_seconds": duration
                }}
            )

            raise
