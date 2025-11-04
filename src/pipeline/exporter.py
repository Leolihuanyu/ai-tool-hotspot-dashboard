"""JSON数据导出

将处理后的数据导出为JSON格式,符合宪法原则I(原子写入)。
"""
import json
import os
from datetime import datetime
from typing import List
from src.models.tool import AITool
from src.models.trend import TrendingTopic
from src.models.opportunity import Opportunity
from src.models.pain_point import UserPainPoint
from src.utils.storage import atomic_write_json
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataExporter:
    """数据导出器"""

    def __init__(self, output_dir: str = 'data'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def export_to_json(self, ai_tools: List[AITool], trending_topics: List[TrendingTopic] = None, pain_points: List[UserPainPoint] = None, opportunities: List[Opportunity] = None, output_file: str = 'latest.json'):
        """导出数据到JSON文件"""
        try:
            data = {
                'schema_version': '1.1',
                'generated_at': datetime.now().isoformat(),
                'ai_tools': [tool.model_dump(mode='json') for tool in (ai_tools or [])],
                'trending_topics': [topic.model_dump(mode='json') for topic in (trending_topics or [])],
                'pain_points': [pp.model_dump(mode='json') for pp in (pain_points or [])],
                'opportunities': [opp.model_dump(mode='json') for opp in (opportunities or [])]
            }
            
            file_path = os.path.join(self.output_dir, output_file)
            atomic_write_json(file_path, data)
            logger.info(f"数据导出成功: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"数据导出失败: {e}")
            raise
