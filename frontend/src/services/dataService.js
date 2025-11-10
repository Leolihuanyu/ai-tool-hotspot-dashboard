/**
 * 数据服务 - 负责从数据源加载数据
 */

// 数据源URL - 优先使用环境变量，否则使用默认的GitHub Raw URL
const DATA_URL = import.meta.env.VITE_DATA_URL ||
  'https://raw.githubusercontent.com/Leolihuanyu/ai-tool-hotspot-dashboard/main/data/latest.json';

const CACHE_KEY = 'dashboard_data';
const CACHE_DURATION = 5 * 60 * 1000; // 5分钟缓存

// 打印当前使用的数据源（仅开发环境）
if (import.meta.env.DEV) {
  console.log('数据源URL:', DATA_URL);
}

/**
 * 从缓存或网络加载数据
 * @returns {Promise<Object>} Dashboard 数据
 */
export async function loadDashboardData() {
  try {
    // 检查缓存
    const cached = getFromCache();
    if (cached) {
      console.log('从缓存加载数据');
      return cached;
    }

    // 从网络加载
    console.log('从网络加载数据');
    const response = await fetch(DATA_URL);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    // 保存到缓存
    saveToCache(data);

    return data;
  } catch (error) {
    console.error('加载数据失败:', error);

    // 尝试从缓存返回（即使过期）
    const cached = getFromCache(true);
    if (cached) {
      console.warn('使用过期缓存数据');
      return cached;
    }

    // 返回空数据结构
    return getEmptyData();
  }
}

/**
 * enrichOpportunities - 将机会列表中的 ID 引用替换为完整对象
 * @param {Object} data - 原始数据
 * @returns {Object} 处理后的数据
 */
export function enrichOpportunities(data) {
  if (!data || !data.opportunities) return data;

  // 创建查找表
  const toolsMap = new Map((data.ai_tools || []).map(t => [t.id, t]));
  const topicsMap = new Map((data.trending_topics || []).map(t => [t.id, t]));
  const painPointsMap = new Map((data.pain_points || []).map(p => [p.id, p]));

  // 处理机会列表
  const enrichedOpportunities = data.opportunities.map(opp => {
    return {
      ...opp,
      related_pain_points: (opp.related_pain_points || [])
        .map(id => painPointsMap.get(id))
        .filter(Boolean),
      related_tools: (opp.related_tools || [])
        .map(id => toolsMap.get(id))
        .filter(Boolean),
      related_topics: (opp.related_topics || [])
        .map(id => topicsMap.get(id))
        .filter(Boolean),
    };
  });

  return {
    ...data,
    opportunities: enrichedOpportunities
  };
}

/**
 * 获取统计数据
 * @param {Object} data - Dashboard 数据
 * @returns {Object} 统计信息
 */
export function getStats(data) {
  if (!data) return { tools: 0, topics: 0, opportunities: 0 };

  return {
    tools: (data.ai_tools || []).length,
    topics: (data.trending_topics || []).length,
    opportunities: (data.opportunities || []).length,
    painPoints: (data.pain_points || []).length,
  };
}

// ========== 私有函数 ==========

/**
 * 从缓存获取数据
 * @param {boolean} ignoreExpiry - 是否忽略过期时间
 * @returns {Object|null} 缓存的数据或 null
 */
function getFromCache(ignoreExpiry = false) {
  try {
    const cached = localStorage.getItem(CACHE_KEY);
    if (!cached) return null;

    const { data, timestamp } = JSON.parse(cached);
    const age = Date.now() - timestamp;

    if (!ignoreExpiry && age > CACHE_DURATION) {
      return null;
    }

    return data;
  } catch (error) {
    console.error('读取缓存失败:', error);
    return null;
  }
}

/**
 * 保存数据到缓存
 * @param {Object} data - 要缓存的数据
 */
function saveToCache(data) {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify({
      data,
      timestamp: Date.now()
    }));
  } catch (error) {
    console.error('保存缓存失败:', error);
  }
}

/**
 * 获取空数据结构
 * @returns {Object} 空数据对象
 */
function getEmptyData() {
  return {
    schema_version: "1.0",
    generated_at: new Date().toISOString(),
    ai_tools: [],
    trending_topics: [],
    pain_points: [],
    opportunities: []
  };
}

/**
 * 根据当前语言获取本地化字段值
 * @param {Object} item - 数据项（tool、topic、pain_point、opportunity等）
 * @param {string} fieldName - 基础字段名（如 'summary'、'mvp_suggestion'）
 * @param {string} language - 语言代码 ('en'、'ja'、'zh')
 * @returns {string} 本地化的字段值，如果不存在则降级到中文
 */
export function getLocalizedField(item, fieldName, language) {
  if (!item) return '';

  // 字段映射表
  const fieldMap = {
    'summary': {
      'en': 'summary_en',
      'ja': 'summary_ja',
      'zh': 'summary_cn'
    },
    'mvp_suggestion': {
      'en': 'mvp_suggestion_en',
      'ja': 'mvp_suggestion_ja',
      'zh': 'mvp_suggestion_cn'
    }
  };

  // 标准化语言代码（提取主要语言部分，如 'en-US' -> 'en'）
  const normalizedLang = language?.split('-')[0] || 'zh';

  // 获取对应语言的字段名
  const localizedFieldName = fieldMap[fieldName]?.[normalizedLang];

  if (localizedFieldName && item[localizedFieldName]) {
    return item[localizedFieldName];
  }

  // 降级处理：尝试使用中文版本
  const fallbackFieldName = fieldMap[fieldName]?.['zh'];
  if (fallbackFieldName && item[fallbackFieldName]) {
    return item[fallbackFieldName];
  }

  // 最后降级：返回空字符串
  return '';
}
