"""There's an AI for That 爬虫

从 There's an AI for That 网站抓取AI工具数据。
网站: https://theresanaiforthat.com
"""

from typing import List, Dict, Any
from datetime import datetime
import requests
from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TheresAnAIForThatScraper(BaseScraper):
    """There's an AI for That 爬虫"""

    def __init__(self):
        """初始化爬虫"""
        super().__init__(
            source_name="There's an AI for That",
            base_url="https://theresanaiforthat.com"
        )

    def scrape(self, limit: int = None) -> List[Dict[str, Any]]:
        """抓取AI工具数据

        Args:
            limit: 限制返回记录数

        Returns:
            工具数据列表
        """
        try:
            # 注意: There's an AI for That 可能需要JavaScript渲染
            # 这里提供一个基础实现，实际可能需要使用Playwright

            # 尝试抓取首页
            url = f"{self.base_url}/ai-tools"
            response = self.fetch_with_retry(url)

            if not response:
                logger.warning(f"无法获取 {url}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')

            # 查找工具卡片（需要根据实际HTML结构调整）
            tools = []
            tool_cards = soup.find_all('div', class_='tool-card', limit=limit)

            if not tool_cards:
                # 尝试其他可能的选择器
                tool_cards = soup.find_all('article', limit=limit)

            for card in tool_cards:
                try:
                    # 提取工具信息（需要根据实际HTML结构调整）
                    title_elem = card.find('h2') or card.find('h3')
                    link_elem = card.find('a')
                    desc_elem = card.find('p')

                    if not title_elem or not link_elem:
                        continue

                    tool_data = {
                        'name': title_elem.get_text(strip=True),
                        'url': link_elem.get('href', ''),
                        'description': desc_elem.get_text(strip=True) if desc_elem else '',
                        'timestamp': datetime.now().isoformat(),
                        'tags': [],
                        'features': [],
                        'pricing_model': 'unknown'
                    }

                    # 确保URL是完整的
                    if tool_data['url'] and not tool_data['url'].startswith('http'):
                        tool_data['url'] = f"{self.base_url}{tool_data['url']}"

                    tools.append(tool_data)

                except Exception as e:
                    logger.error(f"解析工具卡片失败: {e}")
                    continue

            logger.info(f"There's an AI for That 抓取完成: {len(tools)} 条记录")
            return tools[:limit] if limit else tools

        except Exception as e:
            logger.error(f"There's an AI for That 抓取失败: {e}", exc_info=True)
            return []

    def normalize(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """规范化数据到标准格式

        Args:
            raw_data: 原始数据

        Returns:
            规范化后的数据
        """
        return {
            'name': raw_data.get('name', ''),
            'description': raw_data.get('description', ''),
            'url': raw_data.get('url', ''),
            'timestamp': raw_data.get('timestamp', datetime.now().isoformat()),
            'tags': raw_data.get('tags', []),
            'features': raw_data.get('features', []),
            'pricing_model': raw_data.get('pricing_model', 'unknown')
        }
