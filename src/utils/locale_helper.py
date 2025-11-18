"""
时区和语言工具函数

提供timezone和language之间的相互推断和验证功能
"""
from typing import Optional, Tuple


# 时区到语言的映射表
TIMEZONE_TO_LANGUAGE_MAP = {
    # 中文时区
    'Asia/Shanghai': 'zh',
    'Asia/Beijing': 'zh',
    'Asia/Hong_Kong': 'zh',
    'Asia/Taipei': 'zh',
    'Asia/Chongqing': 'zh',
    'Asia/Urumqi': 'zh',

    # 日语时区
    'Asia/Tokyo': 'ja',

    # 英语时区（默认）
    'UTC': 'en',
    'America/New_York': 'en',
    'America/Los_Angeles': 'en',
    'America/Chicago': 'en',
    'America/Denver': 'en',
    'America/Phoenix': 'en',
    'Europe/London': 'en',
    'Australia/Sydney': 'en',
    'Australia/Melbourne': 'en',
}

# 语言到时区的映射表（用于注册时推断）
LANGUAGE_TO_TIMEZONE_MAP = {
    'zh': 'Asia/Shanghai',
    'ja': 'Asia/Tokyo',
    'en': 'America/New_York',  # 修改：英文用户使用美东时区而非UTC
}

# 时区的主要语言（用于兼容性检查）
TIMEZONE_PRIMARY_LANGUAGES = {
    'Asia/Shanghai': ['zh'],
    'Asia/Beijing': ['zh'],
    'Asia/Hong_Kong': ['zh', 'en'],  # 香港支持中英文
    'Asia/Taipei': ['zh'],
    'Asia/Tokyo': ['ja'],
    'UTC': ['en'],
    'America/New_York': ['en'],
    'America/Los_Angeles': ['en'],
    'Europe/London': ['en'],
}


def infer_language_from_timezone(timezone: str) -> str:
    """
    根据时区推断最可能的语言

    Args:
        timezone: IANA时区字符串，如 'Asia/Shanghai'

    Returns:
        推断的语言代码 (zh/ja/en)，默认返回 'en'

    Examples:
        >>> infer_language_from_timezone('Asia/Shanghai')
        'zh'
        >>> infer_language_from_timezone('Asia/Tokyo')
        'ja'
        >>> infer_language_from_timezone('America/New_York')
        'en'
        >>> infer_language_from_timezone('Unknown/Timezone')
        'en'
    """
    if not timezone:
        return 'en'

    # 精确匹配
    if timezone in TIMEZONE_TO_LANGUAGE_MAP:
        return TIMEZONE_TO_LANGUAGE_MAP[timezone]

    # 模糊匹配：检查时区前缀
    if timezone.startswith('Asia/'):
        # 亚洲时区，可能是中文或日文
        if 'China' in timezone or 'Shanghai' in timezone or 'Beijing' in timezone:
            return 'zh'
        elif 'Tokyo' in timezone or 'Japan' in timezone:
            return 'ja'
    elif timezone.startswith('America/'):
        return 'en'
    elif timezone.startswith('Europe/'):
        return 'en'

    # 默认英语
    return 'en'


def infer_timezone_from_language(language: str) -> str:
    """
    根据语言推断默认时区

    Args:
        language: 语言代码 (zh/ja/en)

    Returns:
        推断的时区字符串，默认返回 'UTC'

    Examples:
        >>> infer_timezone_from_language('zh')
        'Asia/Shanghai'
        >>> infer_timezone_from_language('ja')
        'Asia/Tokyo'
        >>> infer_timezone_from_language('en')
        'UTC'
    """
    if not language:
        return 'UTC'

    return LANGUAGE_TO_TIMEZONE_MAP.get(language, 'UTC')


def is_timezone_language_compatible(timezone: str, language: str) -> bool:
    """
    检查时区和语言是否合理匹配

    不是严格验证，而是检查是否"合理"：
    - 如果时区的主要语言包含该语言，返回True
    - 如果没有明确的不兼容，也返回True（宽松策略）

    Args:
        timezone: IANA时区字符串
        language: 语言代码

    Returns:
        True表示匹配合理，False表示可能不匹配

    Examples:
        >>> is_timezone_language_compatible('Asia/Shanghai', 'zh')
        True
        >>> is_timezone_language_compatible('Asia/Tokyo', 'zh')
        False
        >>> is_timezone_language_compatible('Asia/Tokyo', 'ja')
        True
        >>> is_timezone_language_compatible('America/New_York', 'en')
        True
        >>> is_timezone_language_compatible('UTC', 'zh')
        True  # UTC是中性的，任何语言都可以
    """
    if not timezone or not language:
        return True  # 缺少信息，无法判断，返回True

    # UTC是中性的，任何语言都合理
    if timezone == 'UTC':
        return True

    # 检查是否在主要语言列表中
    if timezone in TIMEZONE_PRIMARY_LANGUAGES:
        primary_languages = TIMEZONE_PRIMARY_LANGUAGES[timezone]
        return language in primary_languages

    # 如果推断的语言与给定语言一致，认为合理
    inferred_language = infer_language_from_timezone(timezone)
    return inferred_language == language


def get_compatibility_info(timezone: str, language: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    获取时区和语言兼容性的详细信息

    Args:
        timezone: IANA时区字符串
        language: 语言代码

    Returns:
        (is_compatible, suggested_language, suggested_timezone)
        - is_compatible: 是否兼容
        - suggested_language: 建议的语言（基于timezone推断）
        - suggested_timezone: 建议的时区（基于language推断）

    Examples:
        >>> get_compatibility_info('Asia/Tokyo', 'zh')
        (False, 'ja', 'Asia/Shanghai')
    """
    is_compatible = is_timezone_language_compatible(timezone, language)
    suggested_language = infer_language_from_timezone(timezone) if timezone else None
    suggested_timezone = infer_timezone_from_language(language) if language else None

    return is_compatible, suggested_language, suggested_timezone


def normalize_timezone(timezone: str) -> str:
    """
    规范化时区，确保只返回邮件系统支持的三个时区之一

    邮件系统仅支持以下三个时区的用户接收每日邮件：
    - Asia/Tokyo (日本时间 UTC+9)
    - Asia/Shanghai (中国时间 UTC+8)
    - America/New_York (美东时间 UTC-5/-4)

    Args:
        timezone: 原始时区字符串（可能是任意IANA时区或UTC）

    Returns:
        str: 规范化后的时区，保证是上述三个时区之一

    Examples:
        >>> normalize_timezone('UTC')
        'Asia/Shanghai'
        >>> normalize_timezone('Asia/Tokyo')
        'Asia/Tokyo'
        >>> normalize_timezone('Asia/Hong_Kong')
        'Asia/Shanghai'
        >>> normalize_timezone('Europe/London')
        'America/New_York'
        >>> normalize_timezone('')
        'Asia/Shanghai'
    """
    # 如果是UTC、空值或None，默认使用中国时区
    if not timezone or timezone == 'UTC':
        return 'Asia/Shanghai'

    # 定义支持的三个时区
    SUPPORTED_TIMEZONES = ['Asia/Tokyo', 'Asia/Shanghai', 'America/New_York']

    # 如果已经是三个支持的时区之一，直接返回
    if timezone in SUPPORTED_TIMEZONES:
        return timezone

    # 根据时区前缀和名称映射到支持的时区
    if timezone.startswith('Asia/'):
        # 亚洲时区：根据具体位置映射
        if any(keyword in timezone for keyword in ['Tokyo', 'Japan']):
            return 'Asia/Tokyo'
        else:
            # 其他亚洲时区（包括香港、台北、北京等）统一映射到上海
            return 'Asia/Shanghai'
    elif timezone.startswith('America/'):
        # 美洲时区统一映射到纽约（美东时间）
        return 'America/New_York'
    elif timezone.startswith('Europe/'):
        # 欧洲时区映射到美东（考虑到时差和业务分布）
        return 'America/New_York'
    elif timezone.startswith('Africa/'):
        # 非洲时区映射到美东
        return 'America/New_York'
    elif timezone.startswith('Australia/') or timezone.startswith('Pacific/'):
        # 澳洲和太平洋时区映射到亚洲时区（时差较近）
        return 'Asia/Shanghai'
    else:
        # 其他未知时区默认使用中国时区
        return 'Asia/Shanghai'


# 测试函数
if __name__ == '__main__':
    import doctest
    doctest.testmod()

    # 额外的测试用例
    print("\n=== 测试用例 ===")
    test_cases = [
        ('Asia/Shanghai', 'zh'),
        ('Asia/Tokyo', 'zh'),
        ('Asia/Tokyo', 'ja'),
        ('UTC', 'en'),
        ('America/New_York', 'zh'),
    ]

    for tz, lang in test_cases:
        compatible, sugg_lang, sugg_tz = get_compatibility_info(tz, lang)
        print(f"\n时区: {tz}, 语言: {lang}")
        print(f"  兼容: {compatible}")
        print(f"  建议语言: {sugg_lang}")
        print(f"  建议时区: {sugg_tz}")
