import { useEffect, useState } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  ExternalLink,
  Star,
  Tag,
  Calendar,
  Flame,
  Zap
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { loadDashboardData, getLocalizedField } from '../services/dataService';
import { cn, formatNumber, truncate, formatDate } from '../lib/utils';
import SearchBar from '../components/SearchBar';
import { combineFilters, getAvailableSources, getAvailableTags } from '../utils/filterUtils';
import { useDebounce } from '../hooks/useDebounce';

/**
 * 热点榜页面
 */
export default function Trends() {
  const { t, i18n } = useTranslation();
  const currentLang = i18n.language;
  const [topics, setTopics] = useState([]);
  const [filteredTopics, setFilteredTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({});
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;

  // 使用防抖来优化过滤性能
  const debouncedFilters = useDebounce(filters, 300);

  // 加载数据
  useEffect(() => {
    async function fetchData() {
      try {
        const data = await loadDashboardData();
        const sorted = (data.trending_topics || []).sort((a, b) =>
          (b.heat_score || 0) - (a.heat_score || 0)
        );
        setTopics(sorted);
        setFilteredTopics(sorted);
      } catch (error) {
        console.error(t('common.loadError'), error);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  // 提取可用的过滤选项
  const availableSources = getAvailableSources(topics);
  const availableTags = getAvailableTags(topics);

  // 应用过滤
  useEffect(() => {
    const filtered = combineFilters(topics, {
      keyword: debouncedFilters.keyword,
      searchFields: ['title', 'description', 'summary_cn', 'summary_ja', 'summary_en', 'tags'],
      sources: debouncedFilters.sources,
      tags: debouncedFilters.tags,
      dateRange: debouncedFilters.dateRange
    });

    // 按热度评分排序（默认降序）
    const sorted = filtered.sort((a, b) =>
      (b.heat_score || 0) - (a.heat_score || 0)
    );

    setFilteredTopics(sorted);
    setCurrentPage(1);
  }, [topics, debouncedFilters]);

  // 分页
  const totalPages = Math.ceil(filteredTopics.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedTopics = filteredTopics.slice(startIndex, startIndex + itemsPerPage);

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
        <h1 className="text-4xl font-bold mb-2">{t('trends.title')}</h1>
        <p className="text-slate-400">{t('trends.subtitle')}</p>
      </div>

      {/* 搜索和过滤 */}
      <SearchBar
        searchPlaceholder={t('trends.search')}
        availableSources={availableSources}
        availableTags={availableTags}
        showDateFilter={true}
        onFilterChange={setFilters}
        resultCount={filteredTopics.length}
      />

      {/* 热点列表 */}
      <div className="space-y-4">
        {paginatedTopics.map((topic, idx) => (
          <TopicCard key={topic.id || idx} topic={topic} rank={startIndex + idx + 1} currentLang={currentLang} />
        ))}
      </div>

      {/* 空状态 */}
      {filteredTopics.length === 0 && (
        <div className="text-center py-12 text-slate-400">
          {t('trends.noResults')}
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
 * 话题卡片 - 完整版
 */
function TopicCard({ topic, rank, currentLang }) {
  const { t } = useTranslation();
  const title = topic.title || t('trends.unnamedTopic');
  const description = topic.description || '';
  const summary = getLocalizedField(topic, 'summary', currentLang);
  const url = topic.url || topic.link || '#';
  const heatScore = topic.heat_score || 0;
  const trendDirection = topic.trend_direction || 'stable';
  const trendVelocity = topic.trend_velocity || null;
  const tags = topic.tags || [];
  const platforms = topic.platforms || [];
  const dataQuality = topic.data_quality_score || 0;
  const source = topic.source || '';
  const timestamp = topic.timestamp || '';

  // 趋势方向配置
  const getTrendConfig = (direction) => {
    const configs = {
      rising: {
        icon: TrendingUp,
        label: t('trends.direction.rising'),
        emoji: '📈',
        color: 'text-green-400',
        bgColor: 'bg-green-500/20',
        borderColor: 'border-green-500/30'
      },
      falling: {
        icon: TrendingDown,
        label: t('trends.direction.falling'),
        emoji: '📉',
        color: 'text-slate-400',
        bgColor: 'bg-slate-500/20',
        borderColor: 'border-slate-500/30'
      },
      stable: {
        icon: Minus,
        label: t('trends.direction.stable'),
        emoji: '➡️',
        color: 'text-blue-400',
        bgColor: 'bg-blue-500/20',
        borderColor: 'border-blue-500/30'
      }
    };
    return configs[direction] || configs.stable;
  };

  const trendConfig = getTrendConfig(trendDirection);
  const TrendIcon = trendConfig.icon;

  // 热度颜色（根据分数）
  const getHeatColor = (score) => {
    if (score >= 80) return 'from-red-500 to-orange-500';
    if (score >= 60) return 'from-orange-500 to-yellow-500';
    if (score >= 40) return 'from-yellow-500 to-green-500';
    return 'from-green-500 to-blue-500';
  };

  return (
    <div className="glass-card hover-lift animate-slide-up">
      <div className="p-6">
        {/* 头部：排名 + 标题 + 热度 */}
        <div className="flex gap-4 mb-4">
          {/* 排名徽章 */}
          <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center font-bold text-lg">
            #{rank}
          </div>

          {/* 标题和元信息 */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between mb-2">
              <h3 className="text-xl font-bold text-white leading-tight flex-1">
                {title}
              </h3>
              {url !== '#' && (
                <a
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="ml-2 text-slate-400 hover:text-primary-400 transition-colors flex-shrink-0"
                  onClick={(e) => e.stopPropagation()}
                >
                  <ExternalLink className="w-5 h-5" />
                </a>
              )}
            </div>

            {/* 热度和趋势指示器 */}
            <div className="flex flex-wrap items-center gap-3 mb-3">
              {/* 热度分数 */}
              <div className="flex items-center gap-2">
                <Flame className="w-5 h-5 text-orange-500" />
                <span className="text-lg font-bold text-orange-400">
                  {heatScore.toFixed(0)}
                </span>
                <span className="text-xs text-slate-500">{t('trends.metrics.heat')}</span>
              </div>

              {/* 趋势方向 */}
              <div className={cn(
                "flex items-center gap-1.5 px-2.5 py-1 rounded-full border",
                trendConfig.bgColor,
                trendConfig.borderColor,
                trendConfig.color
              )}>
                <span className="text-sm">{trendConfig.emoji}</span>
                <TrendIcon className="w-4 h-4" />
                <span className="text-xs font-semibold">{trendConfig.label}</span>
              </div>

              {/* 趋势速度 */}
              {trendVelocity !== null && (
                <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-purple-500/20 border border-purple-500/30 text-purple-400">
                  <Zap className="w-4 h-4" />
                  <span className="text-xs font-semibold">
                    {(trendVelocity * 100).toFixed(0)}% {t('trends.metrics.velocity')}
                  </span>
                </div>
              )}

              {/* 来源 */}
              {source && (
                <span className="text-xs px-2 py-1 rounded-full bg-primary-500/20 text-primary-400 border border-primary-500/30">
                  {source}
                </span>
              )}
            </div>

            {/* 热度进度条 */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-500">{t('trends.metrics.heatIndicator')}</span>
                <span className="text-slate-400 font-semibold">
                  {heatScore.toFixed(1)} / 100
                </span>
              </div>
              <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                <div
                  className={cn(
                    "h-full rounded-full transition-all duration-500 bg-gradient-to-r",
                    getHeatColor(heatScore)
                  )}
                  style={{ width: `${Math.min(heatScore, 100)}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* 描述 */}
        {description && (
          <p className="text-sm text-slate-400 mb-4 leading-relaxed">
            {truncate(description, 200)}
          </p>
        )}

        {/* 摘要 */}
        {summary && (
          <div className="p-4 rounded-lg bg-white/5 border border-white/10 mb-4">
            <p className="text-sm text-slate-200 leading-relaxed">
              {summary}
            </p>
          </div>
        )}

        {/* 标签和平台 */}
        <div className="flex flex-wrap gap-4 mb-4">
          {/* 标签 */}
          {tags.length > 0 && (
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <Tag className="w-3.5 h-3.5 text-slate-400" />
                <span className="text-xs font-semibold text-slate-400">{t('trends.labels.tags')}</span>
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

          {/* 平台 */}
          {platforms && platforms.length > 0 && (
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs font-semibold text-slate-400">📱 {t('trends.labels.platforms')}</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {platforms.map((platform, idx) => (
                  <span
                    key={idx}
                    className="text-xs px-2 py-1 rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/30"
                  >
                    {platform}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 底部信息 */}
        <div className="flex items-center justify-between pt-4 border-t border-white/10 text-xs">
          <div className="flex items-center gap-4">
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
