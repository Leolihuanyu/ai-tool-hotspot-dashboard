import { useState, useEffect } from 'react';
import { Search, Filter, X, ChevronDown, ChevronUp, SlidersHorizontal } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { cn } from '../lib/utils';

/**
 * 通用搜索和过滤组件
 *
 * @param {Object} props
 * @param {string} props.searchPlaceholder - 搜索框占位符
 * @param {Array<string>} props.availableSources - 可用的数据来源列表
 * @param {Array<{tag: string, count: number}>} props.availableTags - 可用的标签列表
 * @param {boolean} props.showDateFilter - 是否显示时间范围过滤器
 * @param {boolean} props.showPricingFilter - 是否显示定价模式过滤器（仅用于Tools）
 * @param {Array<string>} props.availablePricingModels - 可用的定价模式
 * @param {Function} props.onFilterChange - 过滤条件改变时的回调
 * @param {number} props.resultCount - 结果数量
 */
export default function SearchBar({
  searchPlaceholder,
  availableSources = [],
  availableTags = [],
  showDateFilter = true,
  showPricingFilter = false,
  availablePricingModels = [],
  onFilterChange,
  resultCount = 0
}) {
  const { t } = useTranslation();
  // 过滤器状态
  const [keyword, setKeyword] = useState('');
  const [selectedSources, setSelectedSources] = useState([]);
  const [selectedTags, setSelectedTags] = useState([]);
  const [selectedPricingModels, setSelectedPricingModels] = useState([]);
  const [dateRange, setDateRange] = useState('all');

  // UI 状态
  const [showFilters, setShowFilters] = useState(false);
  const [showSourceDropdown, setShowSourceDropdown] = useState(false);
  const [showTagDropdown, setShowTagDropdown] = useState(false);

  // 当过滤条件改变时，通知父组件
  useEffect(() => {
    if (onFilterChange) {
      onFilterChange({
        keyword,
        sources: selectedSources,
        tags: selectedTags,
        pricingModels: selectedPricingModels,
        dateRange
      });
    }
  }, [keyword, selectedSources, selectedTags, selectedPricingModels, dateRange]);

  // 清除所有过滤条件
  const handleClearFilters = () => {
    setKeyword('');
    setSelectedSources([]);
    setSelectedTags([]);
    setSelectedPricingModels([]);
    setDateRange('all');
  };

  // 切换来源选择
  const toggleSource = (source) => {
    setSelectedSources(prev =>
      prev.includes(source)
        ? prev.filter(s => s !== source)
        : [...prev, source]
    );
  };

  // 切换标签选择
  const toggleTag = (tag) => {
    setSelectedTags(prev =>
      prev.includes(tag)
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    );
  };

  // 切换定价模式选择
  const togglePricingModel = (model) => {
    setSelectedPricingModels(prev =>
      prev.includes(model)
        ? prev.filter(m => m !== model)
        : [...prev, model]
    );
  };

  // 检查是否有活跃的过滤条件
  const hasActiveFilters = keyword || selectedSources.length > 0 ||
    selectedTags.length > 0 || selectedPricingModels.length > 0 || dateRange !== 'all';

  return (
    <div className="glass-card p-4 space-y-4">
      {/* 第一行：搜索框和过滤按钮 */}
      <div className="flex flex-col md:flex-row gap-3">
        {/* 搜索框 */}
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none" />
          <input
            type="text"
            placeholder={searchPlaceholder || t('search.placeholder')}
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            className="w-full pl-10 pr-10 py-2.5 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all"
          />
          {keyword && (
            <button
              onClick={() => setKeyword('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* 过滤按钮（移动端） */}
        <div className="flex gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={cn(
              "flex items-center gap-2 px-4 py-2.5 rounded-lg border transition-all min-h-[44px]",
              showFilters || hasActiveFilters
                ? "bg-primary-500/20 border-primary-500/50 text-primary-400"
                : "bg-white/5 border-white/10 text-slate-400 hover:border-white/20"
            )}
          >
            <SlidersHorizontal className="w-5 h-5" />
            <span className="hidden sm:inline">{t('common.filters')}</span>
            {hasActiveFilters && (
              <span className="w-2 h-2 bg-primary-400 rounded-full"></span>
            )}
            {showFilters ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {/* 清除按钮 */}
          {hasActiveFilters && (
            <button
              onClick={handleClearFilters}
              className="flex items-center gap-2 px-4 py-2.5 bg-red-500/20 border border-red-500/50 text-red-400 rounded-lg hover:bg-red-500/30 transition-all min-h-[44px]"
            >
              <X className="w-5 h-5" />
              <span className="hidden sm:inline">{t('common.clear')}</span>
            </button>
          )}
        </div>
      </div>

      {/* 展开的过滤器 */}
      {showFilters && (
        <div className="space-y-4 pt-2 border-t border-white/10 animate-slide-down">
          {/* 数据来源过滤 */}
          {availableSources.length > 0 && (
            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-2">
                {t('search.filters.source')}
              </label>
              <div className="flex flex-wrap gap-2">
                {availableSources.map(source => (
                  <button
                    key={source}
                    onClick={() => toggleSource(source)}
                    className={cn(
                      "px-3 py-1.5 text-sm rounded-full border transition-all min-h-[36px]",
                      selectedSources.includes(source)
                        ? "bg-primary-500/30 border-primary-500/50 text-primary-300"
                        : "bg-white/5 border-white/10 text-slate-400 hover:border-white/20"
                    )}
                  >
                    {source}
                  </button>
                ))}
              </div>
              {selectedSources.length > 0 && (
                <p className="mt-2 text-xs text-slate-500">
                  {t('common.selected')} {selectedSources.length} {t('search.filters.sourcesCount')}
                </p>
              )}
            </div>
          )}

          {/* 标签过滤 */}
          {availableTags.length > 0 && (
            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-2">
                {t('search.filters.tags')} <span className="text-slate-500">{t('search.filters.tagsHint')}</span>
              </label>
              <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto">
                {availableTags.slice(0, 20).map(({ tag, count }) => (
                  <button
                    key={tag}
                    onClick={() => toggleTag(tag)}
                    className={cn(
                      "px-3 py-1.5 text-sm rounded-full border transition-all flex items-center gap-1.5 min-h-[36px]",
                      selectedTags.includes(tag)
                        ? "bg-accent-500/30 border-accent-500/50 text-accent-300"
                        : "bg-white/5 border-white/10 text-slate-400 hover:border-white/20"
                    )}
                  >
                    {tag}
                    <span className="text-xs opacity-60">({count})</span>
                  </button>
                ))}
              </div>
              {selectedTags.length > 0 && (
                <p className="mt-2 text-xs text-slate-500">
                  {t('common.selected')} {selectedTags.length} {t('search.filters.tagsCount')}
                </p>
              )}
            </div>
          )}

          {/* 定价模式过滤（仅用于Tools页面） */}
          {showPricingFilter && availablePricingModels.length > 0 && (
            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-2">
                {t('search.filters.pricing')}
              </label>
              <div className="flex flex-wrap gap-2">
                {availablePricingModels.map(model => (
                  <button
                    key={model}
                    onClick={() => togglePricingModel(model)}
                    className={cn(
                      "px-3 py-1.5 text-sm rounded-full border transition-all min-h-[36px]",
                      selectedPricingModels.includes(model)
                        ? "bg-blue-500/30 border-blue-500/50 text-blue-300"
                        : "bg-white/5 border-white/10 text-slate-400 hover:border-white/20"
                    )}
                  >
                    {model}
                  </button>
                ))}
              </div>
            </div>
          )}


          {/* 时间范围过滤 */}
          {showDateFilter && (
            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-2">
                {t('search.filters.timeRange')}
              </label>
              <div className="flex flex-wrap gap-2">
                {[
                  { value: 'all', label: t('search.filters.timeRanges.all') },
                  { value: '7d', label: t('search.filters.timeRanges.7days') },
                  { value: '30d', label: t('search.filters.timeRanges.30days') },
                  { value: '90d', label: t('search.filters.timeRanges.90days') }
                ].map(({ value, label }) => (
                  <button
                    key={value}
                    onClick={() => setDateRange(value)}
                    className={cn(
                      "px-4 py-2 text-sm rounded-lg border transition-all min-h-[36px]",
                      dateRange === value
                        ? "bg-primary-500/30 border-primary-500/50 text-primary-300"
                        : "bg-white/5 border-white/10 text-slate-400 hover:border-white/20"
                    )}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 结果统计 */}
      <div className="flex items-center justify-between text-sm pt-2 border-t border-white/10">
        <p className="text-slate-400">
          {t('common.found')} <span className="font-semibold text-white">{resultCount}</span> {t('common.results')}
        </p>
        {hasActiveFilters && (
          <p className="text-xs text-primary-400">
            {t('common.filtersActive')}
          </p>
        )}
      </div>
    </div>
  );
}
