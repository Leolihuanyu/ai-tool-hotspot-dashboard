/**
 * 过滤工具函数集合
 * 提供通用的数据过滤功能，支持关键词搜索、来源过滤、标签过滤等
 */

/**
 * 根据关键词过滤数据项
 * @param {Array} items - 数据项数组
 * @param {string} keyword - 搜索关键词
 * @param {Array<string>} searchFields - 要搜索的字段名数组
 * @returns {Array} 过滤后的数据项
 */
export function filterByKeyword(items, keyword, searchFields = []) {
  if (!keyword || !keyword.trim()) {
    return items;
  }

  const normalizedKeyword = keyword.toLowerCase().trim();

  return items.filter(item => {
    // 遍历所有搜索字段
    return searchFields.some(field => {
      const value = item[field];

      if (!value) return false;

      // 处理数组类型（如 tags、keywords）
      if (Array.isArray(value)) {
        return value.some(v =>
          String(v).toLowerCase().includes(normalizedKeyword)
        );
      }

      // 处理字符串类型
      return String(value).toLowerCase().includes(normalizedKeyword);
    });
  });
}

/**
 * 根据数据来源过滤
 * @param {Array} items - 数据项数组
 * @param {Array<string>} sources - 选中的数据来源数组
 * @returns {Array} 过滤后的数据项
 */
export function filterBySource(items, sources) {
  if (!sources || sources.length === 0) {
    return items;
  }

  return items.filter(item => {
    if (!item.source) return false;

    // 支持模糊匹配（不区分大小写）
    return sources.some(source =>
      item.source.toLowerCase().includes(source.toLowerCase()) ||
      source.toLowerCase().includes(item.source.toLowerCase())
    );
  });
}

/**
 * 根据标签过滤
 * @param {Array} items - 数据项数组
 * @param {Array<string>} tags - 选中的标签数组
 * @returns {Array} 过滤后的数据项
 */
export function filterByTags(items, tags) {
  if (!tags || tags.length === 0) {
    return items;
  }

  return items.filter(item => {
    if (!item.tags || !Array.isArray(item.tags)) return false;

    // 只要包含任意一个选中的标签即可
    return tags.some(tag =>
      item.tags.some(itemTag =>
        itemTag.toLowerCase() === tag.toLowerCase()
      )
    );
  });
}

/**
 * 根据评分范围过滤
 * @param {Array} items - 数据项数组
 * @param {number} min - 最小评分
 * @param {number} max - 最大评分
 * @param {string} scoreField - 评分字段名（默认为 'score'）
 * @returns {Array} 过滤后的数据项
 */
export function filterByScore(items, min, max, scoreField = 'score') {
  if (min === undefined && max === undefined) {
    return items;
  }

  const minScore = min !== undefined ? min : 0;
  const maxScore = max !== undefined ? max : 100;

  return items.filter(item => {
    const score = item[scoreField];
    if (score === undefined || score === null) return false;

    return score >= minScore && score <= maxScore;
  });
}

/**
 * 根据时间范围过滤
 * @param {Array} items - 数据项数组
 * @param {string} range - 时间范围（'7d', '30d', 'all'）
 * @returns {Array} 过滤后的数据项
 */
export function filterByDateRange(items, range) {
  if (!range || range === 'all') {
    return items;
  }

  const now = new Date();
  let daysAgo;

  switch (range) {
    case '7d':
      daysAgo = 7;
      break;
    case '30d':
      daysAgo = 30;
      break;
    case '90d':
      daysAgo = 90;
      break;
    default:
      return items;
  }

  const cutoffDate = new Date(now.getTime() - daysAgo * 24 * 60 * 60 * 1000);

  return items.filter(item => {
    if (!item.timestamp) return false;

    const itemDate = new Date(item.timestamp);
    return itemDate >= cutoffDate;
  });
}

/**
 * 组合多个过滤条件
 * @param {Array} items - 数据项数组
 * @param {Object} filters - 过滤条件对象
 * @returns {Array} 过滤后的数据项
 */
export function combineFilters(items, filters) {
  let result = items;

  // 关键词搜索
  if (filters.keyword && filters.searchFields) {
    result = filterByKeyword(result, filters.keyword, filters.searchFields);
  }

  // 来源过滤
  if (filters.sources && filters.sources.length > 0) {
    result = filterBySource(result, filters.sources);
  }

  // 标签过滤
  if (filters.tags && filters.tags.length > 0) {
    result = filterByTags(result, filters.tags);
  }

  // 评分过滤
  if (filters.minScore !== undefined || filters.maxScore !== undefined) {
    result = filterByScore(
      result,
      filters.minScore,
      filters.maxScore,
      filters.scoreField
    );
  }

  // 时间范围过滤
  if (filters.dateRange) {
    result = filterByDateRange(result, filters.dateRange);
  }

  return result;
}

/**
 * 从数据项中提取所有可用的数据来源
 * @param {Array} items - 数据项数组
 * @returns {Array<string>} 去重后的数据来源数组
 */
export function getAvailableSources(items) {
  const sources = new Set();

  items.forEach(item => {
    if (item.source) {
      sources.add(item.source);
    }
  });

  return Array.from(sources).sort();
}

/**
 * 从数据项中提取所有可用的标签
 * @param {Array} items - 数据项数组
 * @param {number} limit - 限制返回的标签数量（默认50）
 * @returns {Array<{tag: string, count: number}>} 按频率排序的标签数组
 */
export function getAvailableTags(items, limit = 50) {
  const tagCounts = new Map();

  items.forEach(item => {
    if (item.tags && Array.isArray(item.tags)) {
      item.tags.forEach(tag => {
        tagCounts.set(tag, (tagCounts.get(tag) || 0) + 1);
      });
    }
  });

  // 转换为数组并按频率排序
  const sortedTags = Array.from(tagCounts.entries())
    .map(([tag, count]) => ({ tag, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, limit);

  return sortedTags;
}

/**
 * 根据定价模式过滤（专门用于 Tools）
 * @param {Array} items - 数据项数组
 * @param {Array<string>} pricingModels - 选中的定价模式
 * @returns {Array} 过滤后的数据项
 */
export function filterByPricingModel(items, pricingModels) {
  if (!pricingModels || pricingModels.length === 0) {
    return items;
  }

  return items.filter(item => {
    if (!item.pricing_model) return false;
    return pricingModels.includes(item.pricing_model);
  });
}

/**
 * 获取所有可用的定价模式
 * @param {Array} items - 数据项数组
 * @returns {Array<string>} 定价模式数组
 */
export function getAvailablePricingModels(items) {
  const models = new Set();

  items.forEach(item => {
    if (item.pricing_model) {
      models.add(item.pricing_model);
    }
  });

  return Array.from(models).sort();
}
