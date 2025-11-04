"""原子存储工具

实现原子写入操作(write temp → rename),遵循宪法原则I(数据可靠性)。
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict
from datetime import datetime


def atomic_write_json(file_path: str, data: Dict[str, Any], indent: int = 2) -> None:
    """原子地写入JSON文件

    使用临时文件+重命名的方式确保写入的原子性。
    即使写入过程中发生错误,原文件也不会被破坏。

    Args:
        file_path: 目标文件路径
        data: 要写入的数据
        indent: JSON缩进空格数

    Raises:
        OSError: 文件写入失败
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # 创建临时文件
    fd, temp_path = tempfile.mkstemp(
        suffix='.json',
        dir=file_path.parent,
        text=True
    )

    try:
        # 写入数据到临时文件
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
            f.flush()
            os.fsync(f.fileno())  # 强制刷新到磁盘

        # 原子地重命名临时文件为目标文件
        os.replace(temp_path, file_path)

    except Exception:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


def read_json(file_path: str, default: Dict[str, Any] = None) -> Dict[str, Any]:
    """读取JSON文件

    Args:
        file_path: 文件路径
        default: 文件不存在时返回的默认值

    Returns:
        JSON数据字典

    Raises:
        json.JSONDecodeError: JSON解析失败
    """
    file_path = Path(file_path)

    if not file_path.exists():
        return default if default is not None else {}

    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def archive_data(data: Dict[str, Any], archive_dir: str = "data/archive") -> str:
    """将数据存档到历史快照目录

    文件命名格式: YYYY-MM-DD.json

    Args:
        data: 要存档的数据
        archive_dir: 存档目录路径

    Returns:
        存档文件路径

    Raises:
        OSError: 文件写入失败
    """
    archive_path = Path(archive_dir)
    archive_path.mkdir(parents=True, exist_ok=True)

    # 生成文件名: YYYY-MM-DD.json
    date_str = datetime.now().strftime("%Y-%m-%d")
    file_path = archive_path / f"{date_str}.json"

    atomic_write_json(str(file_path), data)

    return str(file_path)


def ensure_latest_exists(latest_path: str = "data/latest.json") -> bool:
    """确保latest.json文件存在

    如果文件不存在,创建一个空的最小结构。
    遵循宪法原则I: latest.json必须始终存在。

    Args:
        latest_path: latest.json文件路径

    Returns:
        True如果文件已存在或成功创建,False如果创建失败
    """
    file_path = Path(latest_path)

    if file_path.exists():
        return True

    # 创建最小结构
    min_structure = {
        "schema_version": "1.1",
        "generated_at": datetime.now().isoformat() + "Z",
        "ai_tools": [],
        "trending_topics": [],
        "pain_points": [],
        "opportunities": [],
        "scraping_logs": []
    }

    try:
        atomic_write_json(latest_path, min_structure)
        return True
    except Exception:
        return False
