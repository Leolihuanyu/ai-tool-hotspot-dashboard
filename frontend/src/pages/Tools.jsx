import { useEffect, useState } from 'react';
import { ExternalLink, Star, Tag, DollarSign, Sparkles, Calendar } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { loadDashboardData, getLocalizedField } from '../services/dataService';
import { cn, formatNumber, truncate, formatDate } from '../lib/utils';
import SearchBar from '../components/SearchBar';
import { combineFilters, getAvailableSources, getAvailableTags, getAvailablePricingModels } from '../utils/filterUtils';
import { useDebounce } from '../hooks/useDebounce';

/**
 * AI 工具榜页面
 */
export default function Tools() {
  const { t, i18n } = useTranslation();
  const currentLang = i18n.language;
  const [tools, setTools] = useState([]);
  const [filteredTools, setFilteredTools] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({});
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 30;

  // 使用防抖来优化过滤性能
  const debouncedFilters = useDebounce(filters, 300);

  // 加载数据
  useEffect(() => {
    async function fetchData() {
      try {
        const data = await loadDashboardData();
        setTools(data.ai_tools || []);
        setFilteredTools(data.ai_tools || []);
      } catch (error) {
        console.error(t('common.loadError'), error);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  // 提取可用的过滤选项
  const availableSources = getAvailableSources(tools);
  const availableTags = getAvailableTags(tools);
  const availablePricingModels = getAvailablePricingModels(tools);

  // 应用过滤
  useEffect(() => {
    const filtered = combineFilters(tools, {
      keyword: debouncedFilters.keyword,
      searchFields: ['name', 'title', 'description', 'summary_cn', 'summary_ja', 'summary_en', 'tags', 'features'],
      sources: debouncedFilters.sources,
      tags: debouncedFilters.tags,
      dateRange: debouncedFilters.dateRange
    });

    // 定价模式过滤（使用专门的过滤函数）
    let result = filtered;
    if (debouncedFilters.pricingModels && debouncedFilters.pricingModels.length > 0) {
      result = result.filter(tool =>
        debouncedFilters.pricingModels.includes(tool.pricing_model)
      );
    }

    setFilteredTools(result);
    setCurrentPage(1); // 重置到第一页
  }, [tools, debouncedFilters]);

  // 分页
  const totalPages = Math.ceil(filteredTools.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedTools = filteredTools.slice(startIndex, startIndex + itemsPerPage);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-400">{t('common.loading')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-2">{t('tools.title')}</h1>
        <p className="text-slate-400">{t('tools.subtitle')}</p>
      </div>

      {/* 搜索和过滤 */}
      <SearchBar
        searchPlaceholder={t('tools.search')}
        availableSources={availableSources}
        availableTags={availableTags}
        showScoreFilter={false}
        showDateFilter={true}
        showPricingFilter={true}
        availablePricingModels={availablePricingModels}
        onFilterChange={setFilters}
        resultCount={filteredTools.length}
      />

      {/* 工具网格 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {paginatedTools.map((tool, idx) => (
          <ToolCard key={tool.id || idx} tool={tool} currentLang={currentLang} />
        ))}
      </div>

      {/* 空状态 */}
      {filteredTools.length === 0 && (
        <div className="text-center py-12 text-slate-400">
          {t('tools.noResults')}
        </div>
      )}

      {/* 分页 */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2">
          <button
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className={cn(
              "px-4 py-2 rounded-lg transition-colors",
              currentPage === 1
                ? "bg-white/5 text-slate-600 cursor-not-allowed"
                : "bg-white/10 hover:bg-white/20 text-white"
            )}
          >
            {t('common.prev')}
          </button>
          <span className="px-4 py-2 text-slate-400">
            {t('common.page')} {currentPage} {t('common.of')} {totalPages}
          </span>
          <button
            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            className={cn(
              "px-4 py-2 rounded-lg transition-colors",
              currentPage === totalPages
                ? "bg-white/5 text-slate-600 cursor-not-allowed"
                : "bg-white/10 hover:bg-white/20 text-white"
            )}
          >
            {t('common.next')}
          </button>
        </div>
      )}
    </div>
  );
}

// ========== 子组件 ==========

/**
 * 工具卡片 - 完整版
 */
function ToolCard({ tool, currentLang }) {
  const { t } = useTranslation();
  const name = tool.name || tool.title || t('tools.unnamed');
  const description = tool.description || '';
  const summary = getLocalizedField(tool, 'summary', currentLang);
  const url = tool.url || tool.link || '#';
  const tags = tool.tags || [];
  const features = tool.features || [];
  const pricingModel = tool.pricing_model || '';
  const dataQuality = tool.data_quality_score || 0;
  const source = tool.source || '';
  const timestamp = tool.timestamp || '';

  // 定价模式的颜色映射
  const getPricingColor = (model) => {
    const colors = {
      'free': 'bg-green-500/20 text-green-400 border-green-500/30',
      'freemium': 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      'paid': 'bg-orange-500/20 text-orange-400 border-orange-500/30',
      'trial': 'bg-purple-500/20 text-purple-400 border-purple-500/30'
    };
    return colors[model] || 'bg-slate-500/20 text-slate-400 border-slate-500/30';
  };

  return (
    <div className="glass-card flex flex-col h-full hover-lift">
      {/* 头部 */}
      <div className="p-5 border-b border-white/10">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <h3 className="text-lg font-bold text-white mb-2 group-hover:text-primary-400 transition-colors line-clamp-2">
              {name}
            </h3>
            <div className="flex flex-wrap items-center gap-2">
              {source && (
                <span className="text-xs px-2 py-1 rounded-full bg-primary-500/20 text-primary-400 border border-primary-500/30">
                  {source}
                </span>
              )}
              {pricingModel && (
                <span className={cn(
                  "text-xs px-2 py-1 rounded-full border flex items-center gap-1",
                  getPricingColor(pricingModel)
                )}>
                  <DollarSign className="w-3 h-3" />
                  {pricingModel}
                </span>
              )}
            </div>
          </div>
          {url !== '#' && (
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="ml-2 text-slate-400 hover:text-primary-400 transition-colors"
              onClick={(e) => e.stopPropagation()}
            >
              <ExternalLink className="w-5 h-5" />
            </a>
          )}
        </div>

        {/* 英文描述 */}
        {description && (
          <p className="text-sm text-slate-400 line-clamp-3 mb-3">
            {description}
          </p>
        )}

        {/* 功能特性 */}
        {features.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-3">
            {features.slice(0, 3).map((feature, idx) => (
              <span
                key={idx}
                className="text-xs px-2 py-0.5 rounded bg-accent-500/20 text-accent-300 flex items-center gap-1"
              >
                <Sparkles className="w-3 h-3" />
                {feature}
              </span>
            ))}
            {features.length > 3 && (
              <span className="text-xs px-2 py-0.5 text-slate-500">
                +{features.length - 3}
              </span>
            )}
          </div>
        )}
      </div>

      {/* 摘要 */}
      {summary && (
        <div className="p-4 bg-white/5 border-b border-white/10">
          <p className="text-sm text-slate-300 leading-relaxed line-clamp-4">
            {summary}
          </p>
        </div>
      )}

      {/* 标签 */}
      {tags.length > 0 && (
        <div className="p-4 border-b border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <Tag className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-xs font-semibold text-slate-400">{t('tools.tags')}</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {tags.slice(0, 5).map((tag, idx) => (
              <span
                key={idx}
                className="text-xs px-2 py-1 rounded-full bg-slate-500/20 text-slate-300 border border-slate-500/30"
              >
                {tag}
              </span>
            ))}
            {tags.length > 5 && (
              <span className="text-xs px-2 py-1 text-slate-500">
                +{tags.length - 5}
              </span>
            )}
          </div>
        </div>
      )}

      {/* 底部信息 */}
      <div className="mt-auto p-4 bg-white/5">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-3">
            {dataQuality > 0 && (
              <div className="flex items-center gap-1.5">
                <Star className="w-3.5 h-3.5 text-yellow-500" />
                <span className="text-slate-400">{t('common.quality')}</span>
                <span className={cn(
                  "font-semibold",
                  dataQuality >= 0.8 ? "text-green-400" :
                  dataQuality >= 0.6 ? "text-yellow-400" : "text-orange-400"
                )}>
                  {(dataQuality * 100).toFixed(0)}%
                </span>
              </div>
            )}
            {timestamp && (
              <div className="flex items-center gap-1.5 text-slate-500">
                <Calendar className="w-3.5 h-3.5" />
                <span>{formatDate(timestamp)}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
