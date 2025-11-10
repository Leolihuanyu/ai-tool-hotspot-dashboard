import { useEffect, useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  Target,
  Lightbulb,
  Wrench,
  TrendingUp,
  ExternalLink,
  Star,
  Tag,
  Calendar,
  BarChart3
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { loadDashboardData, enrichOpportunities, getLocalizedField } from '../services/dataService';
import { cn, truncate, formatDate, formatNumber } from '../lib/utils';
import SearchBar from '../components/SearchBar';
import { combineFilters, getAvailableSources, getAvailableTags } from '../utils/filterUtils';
import { useDebounce } from '../hooks/useDebounce';

/**
 * 机会榜页面
 */
export default function Opportunities() {
  const { t, i18n } = useTranslation();
  const currentLang = i18n.language;
  const [opportunities, setOpportunities] = useState([]);
  const [filteredOpportunities, setFilteredOpportunities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({});

  // 使用防抖来优化过滤性能
  const debouncedFilters = useDebounce(filters, 300);

  // 加载数据
  useEffect(() => {
    async function fetchData() {
      try {
        const rawData = await loadDashboardData();
        const enrichedData = enrichOpportunities(rawData);
        // 按评分降序排序
        const sorted = (enrichedData.opportunities || []).sort((a, b) =>
          (b.opportunity_score || 0) - (a.opportunity_score || 0)
        );
        setOpportunities(sorted);
        setFilteredOpportunities(sorted);
      } catch (error) {
        console.error(t('common.loadError'), error);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  // 提取可用的过滤选项（从pain_points中提取，因为机会是基于痛点的）
  const availableSources = (() => {
    const sources = new Set();
    opportunities.forEach(opp => {
      const painPoints = opp.related_pain_points || [];
      painPoints.forEach(pp => {
        if (pp.source) sources.add(pp.source);
      });
    });
    return Array.from(sources).sort();
  })();

  const availableTags = (() => {
    const tagCounts = new Map();
    opportunities.forEach(opp => {
      const tags = opp.tags || [];
      tags.forEach(tag => {
        tagCounts.set(tag, (tagCounts.get(tag) || 0) + 1);
      });
    });
    return Array.from(tagCounts.entries())
      .map(([tag, count]) => ({ tag, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 50);
  })();

  // 应用过滤
  useEffect(() => {
    let filtered = opportunities;

    // 关键词搜索：搜索痛点文本、MVP建议、关键词、标签
    if (debouncedFilters.keyword) {
      const keyword = debouncedFilters.keyword.toLowerCase();
      filtered = filtered.filter(opp => {
        // 搜索痛点文本
        const painText = (opp.related_pain_points || [])
          .map(pp => pp.original_text || pp.pain_point_text || '')
          .join(' ')
          .toLowerCase();

        // 搜索MVP建议
        const mvp = (opp.mvp_suggestion_cn || '').toLowerCase();

        // 搜索关键词
        const keywords = (opp.related_pain_points || [])
          .flatMap(pp => pp.extracted_keywords || pp.pain_point_keywords || [])
          .join(' ')
          .toLowerCase();

        // 搜索标签
        const tags = (opp.tags || []).join(' ').toLowerCase();

        return painText.includes(keyword) ||
               mvp.includes(keyword) ||
               keywords.includes(keyword) ||
               tags.includes(keyword);
      });
    }

    // 来源过滤：基于关联痛点的来源
    if (debouncedFilters.sources && debouncedFilters.sources.length > 0) {
      filtered = filtered.filter(opp => {
        const painPoints = opp.related_pain_points || [];
        return painPoints.some(pp =>
          debouncedFilters.sources.some(source =>
            (pp.source || '').toLowerCase().includes(source.toLowerCase())
          )
        );
      });
    }

    // 标签过滤
    if (debouncedFilters.tags && debouncedFilters.tags.length > 0) {
      filtered = filtered.filter(opp => {
        const oppTags = opp.tags || [];
        return debouncedFilters.tags.some(tag =>
          oppTags.some(oppTag => oppTag.toLowerCase() === tag.toLowerCase())
        );
      });
    }


    // 时间范围过滤
    if (debouncedFilters.dateRange && debouncedFilters.dateRange !== 'all') {
      const now = new Date();
      let daysAgo;
      switch (debouncedFilters.dateRange) {
        case '7d': daysAgo = 7; break;
        case '30d': daysAgo = 30; break;
        case '90d': daysAgo = 90; break;
        default: daysAgo = 0;
      }
      if (daysAgo > 0) {
        const cutoffDate = new Date(now.getTime() - daysAgo * 24 * 60 * 60 * 1000);
        filtered = filtered.filter(opp => {
          if (!opp.timestamp) return false;
          const oppDate = new Date(opp.timestamp);
          return oppDate >= cutoffDate;
        });
      }
    }

    // 按评分排序
    filtered.sort((a, b) => (b.opportunity_score || 0) - (a.opportunity_score || 0));

    setFilteredOpportunities(filtered);
  }, [opportunities, debouncedFilters]);

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
        <h1 className="text-4xl font-bold mb-2">{t('opportunities.title')}</h1>
        <p className="text-slate-400">{t('opportunities.subtitle')}</p>
      </div>

      {/* 搜索和过滤 */}
      <SearchBar
        searchPlaceholder={t('opportunities.search')}
        availableSources={availableSources}
        availableTags={availableTags}
        showDateFilter={true}
        onFilterChange={setFilters}
        resultCount={filteredOpportunities.length}
      />

      {/* 机会列表 */}
      <div className="space-y-6">
        {filteredOpportunities.slice(0, 20).map((opp, idx) => (
          <OpportunityCard key={opp.id || idx} opportunity={opp} rank={idx + 1} currentLang={currentLang} />
        ))}
      </div>

      {/* 空状态 */}
      {filteredOpportunities.length === 0 && (
        <div className="text-center py-12 text-slate-400">
          {t('opportunities.noResults')}
        </div>
      )}
    </div>
  );
}

// ========== 子组件 ==========

/**
 * 机会卡片 - 完整版
 */
function OpportunityCard({ opportunity, rank, currentLang }) {
  const { t } = useTranslation();
  const [expandedSections, setExpandedSections] = useState({
    mvp: true,  // MVP建议默认展开
    resources: false,
    scores: false
  });

  // 提取数据
  const score = opportunity.opportunity_score || 0;
  const painPoints = opportunity.related_pain_points || [];
  const tools = opportunity.related_tools || [];
  const topics = opportunity.related_topics || [];
  const tags = opportunity.tags || [];
  const mvpSuggestion = getLocalizedField(opportunity, 'mvp_suggestion', currentLang);
  const scores = opportunity.scores || null;
  const dataQuality = opportunity.data_quality_score || 0;
  const timestamp = opportunity.timestamp || '';

  // 痛点信息（从第一个关联痛点获取）
  const painPoint = painPoints[0] || {};
  const painText = painPoint.original_text || painPoint.pain_point_text || '';
  const painContext = painPoint.context_title || painPoint.pain_point_context || '';
  const painKeywords = painPoint.extracted_keywords || painPoint.pain_point_keywords || [];
  const painConfidence = painPoint.confidence_score || painPoint.pain_point_confidence || 0;

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  // 排名徽章
  const getRankBadge = () => {
    if (rank <= 3) {
      return (
        <div className="flex-shrink-0 w-14 h-14 rounded-xl bg-gradient-to-br from-yellow-500 to-orange-500 flex flex-col items-center justify-center font-bold shadow-lg">
          <span className="text-2xl">🏆</span>
          <span className="text-xs">Top {rank}</span>
        </div>
      );
    }
    return (
      <div className="flex-shrink-0 w-14 h-14 rounded-xl bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center font-bold text-xl">
        #{rank}
      </div>
    );
  };

  return (
    <div className="glass-card overflow-hidden hover-lift">
      {/* 头部 - 排名 + 评分 */}
      <div className="p-6 border-b border-white/10">
        <div className="flex items-start gap-4">
          {getRankBadge()}

          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <Target className="w-6 h-6 text-primary-400" />
              <h3 className="text-2xl font-bold">{t('opportunities.opportunity')} #{rank}</h3>
            </div>
            <div className="flex items-center gap-2">
              <Star className="w-5 h-5 text-yellow-500" />
              <span className="text-lg font-semibold text-primary-400">
                {t('common.score')} {score.toFixed(1)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 痛点信息区 */}
      {painText && (
        <div className="p-6 border-b border-white/10 bg-gradient-to-r from-red-500/5 to-orange-500/5">
          <div className="flex items-center gap-2 mb-3">
            <Lightbulb className="w-5 h-5 text-red-400" />
            <h4 className="font-bold text-lg">{t('opportunities.painPoint.title')}</h4>
          </div>

          <p className="text-white mb-3 leading-relaxed">{painText}</p>

          {painContext && (
            <div className="mb-3">
              <span className="text-sm text-slate-400">{t('opportunities.painPoint.context')} </span>
              <span className="text-sm text-slate-300">{painContext}</span>
            </div>
          )}

          {painKeywords.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-3">
              {painKeywords.map((keyword, idx) => (
                <span
                  key={idx}
                  className="px-2 py-1 text-xs rounded-full bg-red-500/20 text-red-300 border border-red-500/30"
                >
                  {keyword}
                </span>
              ))}
            </div>
          )}

          {painConfidence > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-400">{t('opportunities.painPoint.confidence')}</span>
              <div className="flex-1 max-w-xs h-2 bg-white/10 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-red-500 to-orange-500 rounded-full transition-all"
                  style={{ width: `${painConfidence * 100}%` }}
                />
              </div>
              <span className="text-sm font-semibold text-red-400">
                {(painConfidence * 100).toFixed(0)}%
              </span>
            </div>
          )}
        </div>
      )}

      {/* MVP建议区 */}
      {mvpSuggestion && (
        <CollapsibleSection
          title={t('opportunities.mvp.title')}
          icon={<Target className="w-5 h-5" />}
          isExpanded={expandedSections.mvp}
          onToggle={() => toggleSection('mvp')}
          colorClass="text-primary-400"
        >
          <div className="space-y-4">
            <div className="p-4 rounded-lg bg-primary-500/10 border border-primary-500/30">
              <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-line">{mvpSuggestion}</p>
            </div>
          </div>
        </CollapsibleSection>
      )}

      {/* 相关资源区 */}
      {(tools.length > 0 || topics.length > 0) && (
        <CollapsibleSection
          title={t('opportunities.related.title')}
          icon={<Wrench className="w-5 h-5" />}
          isExpanded={expandedSections.resources}
          onToggle={() => toggleSection('resources')}
          colorClass="text-blue-400"
        >
          <div className="space-y-6">
            {/* 相关工具 */}
            {tools.length > 0 && (
              <div>
                <h5 className="font-semibold mb-3 flex items-center gap-2">
                  <Wrench className="w-4 h-4" />
                  {t('opportunities.related.tools')} ({tools.slice(0, 5).length})
                </h5>
                <div className="space-y-3">
                  {tools.slice(0, 5).map((tool, idx) => (
                    <div key={tool.id || idx} className="p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors">
                      <div className="flex items-start justify-between mb-2">
                        <h6 className="font-semibold text-white">{tool.name || tool.title}</h6>
                        {tool.url && (
                          <a
                            href={tool.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary-400 hover:text-primary-300 transition-colors"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <ExternalLink className="w-4 h-4" />
                          </a>
                        )}
                      </div>
                      <p className="text-sm text-slate-400 mb-2">
                        {truncate(tool.description || getLocalizedField(tool, 'summary', currentLang) || '', 100)}
                      </p>
                      <div className="flex items-center gap-2 flex-wrap">
                        {tool.pricing_model && (
                          <span className="text-xs px-2 py-1 rounded-full bg-green-500/20 text-green-400">
                            {tool.pricing_model}
                          </span>
                        )}
                        {tool.source && (
                          <span className="text-xs text-slate-500">来源: {tool.source}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 相关热点 */}
            {topics.length > 0 && (
              <div>
                <h5 className="font-semibold mb-3 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" />
                  {t('opportunities.related.trends')} ({topics.slice(0, 5).length})
                </h5>
                <div className="space-y-3">
                  {topics.slice(0, 5).map((topic, idx) => (
                    <div key={topic.id || idx} className="p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors">
                      <div className="flex items-start justify-between mb-2">
                        <h6 className="font-semibold text-white">{topic.title}</h6>
                        {topic.url && (
                          <a
                            href={topic.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary-400 hover:text-primary-300 transition-colors"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <ExternalLink className="w-4 h-4" />
                          </a>
                        )}
                      </div>
                      {topic.heat_score && (
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-xs text-slate-400">热度:</span>
                          <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-orange-500 to-red-500 rounded-full"
                              style={{ width: `${Math.min(topic.heat_score, 100)}%` }}
                            />
                          </div>
                          <span className="text-xs font-semibold text-orange-400">
                            {topic.heat_score.toFixed(0)}
                          </span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </CollapsibleSection>
      )}

      {/* 评分详情区 */}
      {scores && Object.keys(scores).length > 0 && (
        <CollapsibleSection
          title={t('opportunities.scoreDetails')}
          icon={<BarChart3 className="w-5 h-5" />}
          isExpanded={expandedSections.scores}
          onToggle={() => toggleSection('scores')}
          colorClass="text-purple-400"
        >
          <div className="space-y-3">
            {Object.entries(scores).map(([key, value]) => (
              <div key={key} className="p-3 rounded-lg bg-white/5">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-semibold text-slate-300">{key}</span>
                  <span className="text-sm font-bold text-purple-400">{value.toFixed(1)}</span>
                </div>
                <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full transition-all"
                    style={{ width: `${(value / 100) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </CollapsibleSection>
      )}

      {/* 标签区 */}
      {tags.length > 0 && (
        <div className="px-6 py-4 border-t border-white/10">
          <div className="flex items-center gap-2 mb-3">
            <Tag className="w-4 h-4 text-slate-400" />
            <span className="text-sm font-semibold text-slate-400">标签</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {tags.slice(0, 8).map((tag, idx) => (
              <span
                key={idx}
                className="px-3 py-1 text-xs rounded-full bg-primary-500/20 text-primary-300 border border-primary-500/30"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 底部信息 */}
      <div className="px-6 py-4 bg-white/5 border-t border-white/10">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-4">
            {dataQuality > 0 && (
              <div className="flex items-center gap-2">
                <Star className="w-4 h-4 text-yellow-500" />
                <span className="text-slate-400">{t('opportunities.dataQuality')}</span>
                <span className="font-semibold text-yellow-400">
                  {(dataQuality * 100).toFixed(0)}%
                </span>
              </div>
            )}
            {timestamp && (
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-slate-400" />
                <span className="text-slate-500">{formatDate(timestamp)}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * 可折叠区块组件
 */
function CollapsibleSection({ title, icon, children, isExpanded, onToggle, colorClass = "text-primary-400" }) {
  return (
    <div className="border-t border-white/10">
      <button
        onClick={onToggle}
        className="w-full px-6 py-4 flex items-center justify-between hover:bg-white/5 transition-colors"
      >
        <div className={cn("flex items-center gap-2 font-semibold", colorClass)}>
          {icon}
          <span>{title}</span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-5 h-5 text-slate-400" />
        ) : (
          <ChevronDown className="w-5 h-5 text-slate-400" />
        )}
      </button>
      {isExpanded && (
        <div className="px-6 pb-6 animate-slide-down">
          {children}
        </div>
      )}
    </div>
  );
}
