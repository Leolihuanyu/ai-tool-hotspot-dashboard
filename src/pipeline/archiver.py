"""历史数据归档

将每日数据保存到归档目录,符合宪法原则VI(可重现性)。
"""
import os
import shutil
from datetime import datetime
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataArchiver:
    """数据归档器"""

    def __init__(self, archive_dir: str = 'data/archive'):
        self.archive_dir = archive_dir
        os.makedirs(archive_dir, exist_ok=True)

    def archive_latest(self, source_file: str = 'data/latest.json'):
        """归档最新数据"""
        try:
            if not os.path.exists(source_file):
                logger.warning(f"源文件不存在: {source_file}")
                return None
            
            today = datetime.now().strftime('%Y-%m-%d')
            archive_file = os.path.join(self.archive_dir, f"{today}.json")
            
            shutil.copy2(source_file, archive_file)
            logger.info(f"数据归档成功: {archive_file}")
            return archive_file
        except Exception as e:
            logger.error(f"数据归档失败: {e}")
            raise
