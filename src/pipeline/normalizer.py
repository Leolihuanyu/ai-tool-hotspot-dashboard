"""pnÄpipeline


pnËpnlb:ßpn!
"""

from typing import List, Dict, Any, Union
from src.models.tool import AITool
from src.models.trend import TrendingTopic
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataNormalizer:
    """pnÄh

    
,kÖËpnlb:ßPydantic!
    """

    def __init__(self):
        """ËÄh"""
        self.scrapers_map = {}

    def register_scraper(self, scraper_instance):
        """è,k

        Args:
            scraper_instance: ,k(Å{°normalize¹Õ)
        """
        source_name = getattr(scraper_instance, 'source_name', scraper_instance.__class__.__name__)
        self.scrapers_map[source_name] = scraper_instance
        logger.debug(f"Registered scraper: {source_name}")

    def normalize_ai_tools(self, raw_data_list: List[Dict[str, Any]], source: str) -> List[AITool]:
        """ÄAIåwpn

        Args:
            raw_data_list: Ëpnh
            source: pn
ð

        Returns:
            AIToolùah
        """
        if not raw_data_list:
            logger.warning(f"No raw data to normalize from source: {source}")
            return []

        scraper = self.scrapers_map.get(source)
        if not scraper:
            logger.error(f"No scraper registered for source: {source}")
            return []

        normalized_tools = []
        for raw_data in raw_data_list:
            try:
                tool = scraper.normalize(raw_data)
                normalized_tools.append(tool)
            except Exception as e:
                logger.error(f"Failed to normalize data from {source}: {e}")
                logger.debug(f"Problematic data: {raw_data}")
                continue

        logger.info(f"Normalized {len(normalized_tools)}/{len(raw_data_list)} records from {source}")
        return normalized_tools

    def normalize_trending_topics(self, raw_data_list: List[Dict[str, Any]], source: str) -> List[TrendingTopic]:
        """Äí¹Ýpn

        Args:
            raw_data_list: Ëpnh
            source: pn
ð

        Returns:
            TrendingTopicùah
        """
        if not raw_data_list:
            logger.warning(f"No raw data to normalize from source: {source}")
            return []

        scraper = self.scrapers_map.get(source)
        if not scraper:
            logger.error(f"No scraper registered for source: {source}")
            return []

        normalized_topics = []
        for raw_data in raw_data_list:
            try:
                topic = scraper.normalize(raw_data)
                normalized_topics.append(topic)
            except Exception as e:
                logger.error(f"Failed to normalize data from {source}: {e}")
                logger.debug(f"Problematic data: {raw_data}")
                continue

        logger.info(f"Normalized {len(normalized_topics)}/{len(raw_data_list)} records from {source}")
        return normalized_topics

    def normalize_batch(
        self,
        data_by_source: Dict[str, List[Dict[str, Any]]],
        data_type: str = 'ai_tools'
    ) -> Union[List[AITool], List[TrendingTopic]]:
        """yÏÄpn

        Args:
            data_by_source: 	pnÄÇËpnWx
                            <: {"source_name": [raw_data1, raw_data2, ...]}
            data_type: pn{ ('ai_tools'  'trending_topics')

        Returns:
            Äpnh
        """
        all_normalized = []

        for source, raw_data_list in data_by_source.items():
            try:
                if data_type == 'ai_tools':
                    normalized = self.normalize_ai_tools(raw_data_list, source)
                elif data_type == 'trending_topics':
                    normalized = self.normalize_trending_topics(raw_data_list, source)
                else:
                    logger.error(f"Unknown data type: {data_type}")
                    continue

                all_normalized.extend(normalized)

            except Exception as e:
                logger.error(f"Failed to normalize batch from {source}: {e}")
                # 单个数据源失败不影响其他源 (FR-016)
                continue

        logger.info(f"Total normalized records: {len(all_normalized)} ({data_type})")
        return all_normalized

    def validate_model(self, model_instance: Union[AITool, TrendingTopic]) -> bool:
        """Á!

        Args:
            model_instance: !

        Returns:
            /&ÁÇ
        """
        try:
            # Pydanticê¨Á
            # ìêÀås.Wµ
            if isinstance(model_instance, AITool):
                required_fields = ['name', 'url', 'source', 'description']
            elif isinstance(model_instance, TrendingTopic):
                required_fields = ['title', 'url', 'source', 'description']
            else:
                logger.error(f"Unknown model type: {type(model_instance)}")
                return False

            for field in required_fields:
                if not getattr(model_instance, field, None):
                    logger.warning(f"Missing required field: {field}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Model validation failed: {e}")
            return False
