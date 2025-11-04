"""pn(ÏÄ

¡pn(Ïp,(ÇäN(Ïpn
&data-model.md,50-56LÄl
"""

from datetime import datetime, timedelta
from typing import Union
from src.models.tool import AITool
from src.models.trend import TrendingTopic
from src.models.pain_point import UserPainPoint
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataQualityScorer:
    """pn(ÏÄh

    úeï`'¹t'pn°¦¡(Ïp
    """

    # eï`'Ä 
    SOURCE_RELIABILITY = {
        # AIåwpn
        "ProductHunt": 1.0,
        "Futurepedia": 0.9,
        "There's an AI for That": 0.7,

        # í¹pn
        "Google Trends": 0.9,
        "Reddit": 0.8,
        "X": 0.7,
        "TikTok": 0.7,
        "YouTube": 0.7,

        # Ø¤<
        "default": 0.5
    }

    def __init__(self):
        """Ë(ÏÄh"""
        pass

    def calculate_data_quality_score(
        self,
        item: Union[AITool, TrendingTopic, UserPainPoint]
    ) -> float:
        """¡pn(ÏÄ

        Args:
            item: pn!

        Returns:
            (ÏÄ(0-1)
        """
        try:
            # 1. eï`'
            source_reliability = self._get_source_reliability(item.source)

            # 2. ¹t'
            content_completeness = self._calculate_content_completeness(item)

            # 3. pn°¦
            data_freshness = self._calculate_data_freshness(item.timestamp)

            # ¡C;
            quality_score = (
                source_reliability * 0.4 +
                content_completeness * 0.4 +
                data_freshness * 0.2
            )

            return round(quality_score, 2)

        except Exception as e:
            logger.error(f"Failed to calculate data quality score: {e}")
            return 0.5  # ÔÞ-I(Ïp\:Ø¤<

    def _get_source_reliability(self, source: str) -> float:
        """·Öeï`'Ä

        Args:
            source: pn
ð

        Returns:
            ï`'Ä(0-1)
        """
        return self.SOURCE_RELIABILITY.get(source, self.SOURCE_RELIABILITY["default"])

    def _calculate_content_completeness(
        self,
        item: Union[AITool, TrendingTopic, UserPainPoint]
    ) -> float:
        """¡¹t'Ä

        Args:
            item: pn!

        Returns:
            t'Ä(0-1)
        """
        try:
            # ÀåÅWµ
            if isinstance(item, AITool):
                required_fields = ['name', 'description', 'url', 'source', 'tags']
                optional_fields = ['features', 'summary_cn', 'summary_ja']
            elif isinstance(item, TrendingTopic):
                required_fields = ['title', 'description', 'url', 'source', 'heat_score']
                optional_fields = ['tags', 'summary_cn', 'summary_ja']
            elif isinstance(item, UserPainPoint):
                required_fields = ['original_text', 'url', 'source', 'extracted_keywords']
                optional_fields = ['context_title', 'summary_cn', 'summary_ja']
            else:
                logger.warning(f"Unknown item type: {type(item)}")
                return 0.5

            # ¡ÅWµt'
            required_score = sum(
                1.0 for field in required_fields
                if getattr(item, field, None)
            ) / len(required_fields)

            # ¡ï	Wµt'
            optional_score = sum(
                1.0 for field in optional_fields
                if getattr(item, field, None)
            ) / len(optional_fields) if optional_fields else 0.0

            # ÅWµ`80%,ï	Wµ`20%
            completeness = required_score * 0.8 + optional_score * 0.2

            return completeness

        except Exception as e:
            logger.error(f"Failed to calculate content completeness: {e}")
            return 0.5

    def _calculate_data_freshness(self, timestamp: datetime) -> float:
        """¡pn°¦Ä

        Args:
            timestamp: pnöô3

        Returns:
            °¦Ä(0-1)
        """
        try:
            now = datetime.now()

            # timestamp/naive datetime,lb:aware
            if timestamp.tzinfo is None:
                # G¾:UTCöô
                from datetime import timezone
                timestamp = timestamp.replace(tzinfo=timezone.utc)
                now = now.replace(tzinfo=timezone.utc)

            age = now - timestamp

            # 9npntÄ
            if age < timedelta(hours=24):
                # <24ö: °
                return 1.0
            elif age < timedelta(days=7):
                # <7): °
                return 0.7
            elif age < timedelta(days=30):
                # <30): ,
                return 0.5
            else:
                # >30): ç
                return 0.3

        except Exception as e:
            logger.error(f"Failed to calculate data freshness: {e}")
            return 0.5

    def batch_score(self, items: list) -> list:
        """yÏ¡pn(ÏÄ

        Args:
            items: pn!h

        Returns:
            ô°data_quality_scoreh
        """
        if not items:
            return []

        scored_items = []
        total = len(items)

        for idx, item in enumerate(items, 1):
            try:
                # ¡(Ïp
                quality_score = self.calculate_data_quality_score(item)

                # ô°itemquality_scoreWµ
                item.data_quality_score = quality_score

                scored_items.append(item)

                if idx % 50 == 0:
                    logger.info(f"Batch quality scoring progress: {idx}/{total}")

            except Exception as e:
                logger.error(f"Failed to score item {idx}: {e}")
                # s1%_ÝYitem
                scored_items.append(item)
                continue

        logger.info(f"Batch quality scoring completed: {len(scored_items)} items")
        return scored_items

    def filter_low_quality(
        self,
        items: list,
        min_quality_score: float = 0.5
    ) -> list:
        """ÇäN(Ïpn

        Args:
            items: pn!h
            min_quality_score: N(Ïp<

        Returns:
            Çäh
        """
        if not items:
            return []

        filtered = [
            item for item in items
            if getattr(item, 'data_quality_score', 0.0) >= min_quality_score
        ]

        removed_count = len(items) - len(filtered)
        logger.info(
            f"Filtered {removed_count}/{len(items)} low-quality items "
            f"(min_score={min_quality_score})"
        )

        return filtered
