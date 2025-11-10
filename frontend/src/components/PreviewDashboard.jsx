import { useEffect, useState } from 'react';
import { Sparkles, TrendingUp, Target, ArrowRight, ExternalLink, Flame, DollarSign, Star } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { loadDashboardData, getStats, getLocalizedField } from '../services/dataService';
import { formatNumber, cn } from '../lib/utils';

/**
 * Landing页面的Dashboard预览组件
 * 展示每日精选内容，包括统计数据、热门工具、热点趋势和精选机会
 */
export default function PreviewDashboard() {
  const { t, i18n } = useTranslation();
  const currentLang = i18n.language;
  const [data, setData] = useState(null);
  const [stats, setStats] = useState({ tools: 0, topics: 0, opportunities: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const dashboardData = await loadDashboardData();
        setData(dashboardData);
        setStats(getStats(dashboardData));
      } catch (error) {
        console.error('加载Dashboard预览数据失败:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="py-16 text-center">
        <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-slate-400">{t('landing.preview.loading')}</p>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  // 精选数据
  const topTools = (data.ai_tools || [])
    .filter(tool => tool.pricing_model === 'freemium' || tool.data_quality_score >= 0.9)
    .sort((a, b) => (b.data_quality_score || 0) - (a.data_quality_score || 0))
    .slice(0, 3);

  const topTrends = (data.trending_topics || [])
    .sort((a, b) => (b.heat_score || 0) - (a.heat_score || 0))
    .slice(0, 3);

  const topOpportunity = (data.opportunities || [])
    .sort((a, b) => (b.opportunity_score || 0) - (a.opportunity_score || 0))[0];

  return (
    <div className="space-y-12">
      {/* 标题 */}
      <div className="text-center">
        <h2 className="text-3xl md:text-4xl font-bold mb-3 bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent">
          {t('landing.preview.title')}
        </h2>
        <p className="text-slate-400 text-lg">
          {t('landing.preview.subtitle')}
        </p>
      </div>

      {/* 统计数字板 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-slide-up">
        <PreviewStatCard
          icon={<Sparkles className="w-7 h-7" />}
          title={t('landing.preview.stats.tools')}
          value={formatNumber(stats.tools)}
          color="from-blue-500 to-cyan-500"
        />
        <PreviewStatCard
          icon={<TrendingUp className="w-7 h-7" />}
          title={t('landing.preview.stats.trends')}
          value={formatNumber(stats.topics)}
          color="from-purple-500 to-pink-500"
        />
        <PreviewStatCard
          icon={<Target className="w-7 h-7" />}
          title={t('landing.preview.stats.opportunities')}
          value={formatNumber(stats.opportunities)}
          color="from-orange-500 to-red-500"
        />
      </div>

      {/* 热门AI工具 */}
      {topTools.length > 0 && (
        <section className="animate-slide-up" style={{ animationDelay: '0.1s' }}>
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-2xl font-bold flex items-center gap-2">
              <Sparkles className="w-6 h-6 text-primary-400" />
              {t('landing.preview.sections.topTools')}
            </h3>
            <div className="flex items-center gap-2 text-xs px-3 py-1.5 rounded-full bg-green-500/20 text-green-400 border border-green-500/30">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
              </span>
              <span className="font-semibold">{t('landing.preview.live')}</span>
            </div>
          </div>
          <div className="overflow-x-auto pb-4 -mx-4 px-4">
            <div className="flex gap-4 md:grid md:grid-cols-2 lg:grid-cols-3">
              {topTools.map((tool, idx) => (
                <PreviewToolCard key={tool.id || idx} tool={tool} currentLang={currentLang} />
              ))}
            </div>
          </div>
        </section>
      )}

      {/* 热点趋势 Top3 */}
      {topTrends.length > 0 && (
        <section className="animate-slide-up" style={{ animationDelay: '0.2s' }}>
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-2xl font-bold flex items-center gap-2">
              <Flame className="w-6 h-6 text-orange-500" />
              {t('landing.preview.sections.topTrends')}
            </h3>
          </div>
          <div className="space-y-4">
            {topTrends.map((topic, idx) => (
              <PreviewTrendCard
                key={topic.id || idx}
                topic={topic}
                rank={idx + 1}
                currentLang={currentLang}
              />
            ))}
          </div>
        </section>
      )}

      {/* 精选创业机会 */}
      {topOpportunity && (
        <section className="animate-slide-up" style={{ animationDelay: '0.3s' }}>
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-2xl font-bold flex items-center gap-2">
              <Target className="w-6 h-6 text-accent-400" />
              {t('landing.preview.sections.topOpportunity')}
            </h3>
          </div>
          <PreviewOpportunityCard opportunity={topOpportunity} currentLang={currentLang} />
        </section>
      )}

      {/* CTA 按钮 */}
      <div className="text-center pt-8">
        <a
          href="pricing"
          className="inline-flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-primary-500 to-accent-500 rounded-xl font-semibold text-lg hover:shadow-2xl hover:shadow-primary-500/50 transition-all hover-lift"
        >
          {t('landing.preview.cta')}
          <ArrowRight className="w-5 h-5" />
        </a>
        <p className="text-slate-500 text-sm mt-4">
          {t('landing.preview.ctaSubtext')}
        </p>
      </div>
    </div>
  );
}

// ========== 子组件 ==========

/**
 * 预览统计卡片 - 简化版
 */
function PreviewStatCard({ icon, title, value, color }) {
  return (
    <div className="glass-card p-6 hover-lift">
      <div className="flex items-center gap-4">
        <div className={`bg-gradient-to-br ${color} p-3 rounded-lg flex-shrink-0`}>
          {icon}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-slate-400 text-sm mb-1">{title}</p>
          <p className="text-4xl font-bold">{value}</p>
        </div>
      </div>
    </div>
  );
}

/**
 * 预览工具卡片 - 紧凑版
 */
function PreviewToolCard({ tool, currentLang }) {
  const { t } = useTranslation();
  const name = tool.name || tool.title || t('tools.unnamed');
  const summary = getLocalizedField(tool, 'summary', currentLang);
  const url = tool.url || tool.link || '#';
  const pricingModel = tool.pricing_model || '';
  const dataQuality = tool.data_quality_score || 0;
  const features = tool.features || [];

  const getPricingColor = (model) => {
    const colors = {
      'free': 'bg-green-500/20 text-green-400 border-green-500/30',
      'freemium': 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      'paid': 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    };
    return colors[model] || 'bg-slate-500/20 text-slate-400 border-slate-500/30';
  };

  return (
    <div className="glass-card flex flex-col min-w-[280px] md:min-w-0 hover-lift group">
      {/* 头部 */}
      <div className="p-5 flex-1">
        <div className="flex items-start justify-between mb-3">
          <h4 className="text-lg font-bold text-white line-clamp-1 flex-1 group-hover:text-primary-400 transition-colors">
            {name}
          </h4>
          {url !== '#' && (
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="ml-2 text-slate-400 hover:text-primary-400 transition-colors flex-shrink-0"
            >
              <ExternalLink className="w-4 h-4" />
            </a>
          )}
        </div>

        {/* 定价 */}
        {pricingModel && (
          <div className="mb-3">
            <span className={cn(
              "text-xs px-2 py-1 rounded-full border inline-flex items-center gap-1",
              getPricingColor(pricingModel)
            )}>
              <DollarSign className="w-3 h-3" />
              {pricingModel}
            </span>
          </div>
        )}

        {/* 摘要 */}
        {summary && (
          <p className="text-sm text-slate-300 line-clamp-3 mb-3 leading-relaxed">
            {summary}
          </p>
        )}

        {/* 功能特性 */}
        {features.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {features.slice(0, 2).map((feature, idx) => (
              <span
                key={idx}
                className="text-xs px-2 py-0.5 rounded bg-accent-500/20 text-accent-300"
              >
                {feature}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* 底部 */}
      <div className="px-5 py-3 bg-white/5 border-t border-white/10">
        <div className="flex items-center gap-2">
          <Star className="w-3.5 h-3.5 text-yellow-500" />
          <span className="text-xs text-slate-400">{t('common.quality')}</span>
          <span className={cn(
            "text-xs font-semibold ml-auto",
            dataQuality >= 0.8 ? "text-green-400" :
            dataQuality >= 0.6 ? "text-yellow-400" : "text-orange-400"
          )}>
            {(dataQuality * 100).toFixed(0)}%
          </span>
        </div>
      </div>
    </div>
  );
}

/**
 * 预览趋势卡片 - 紧凑版
 */
function PreviewTrendCard({ topic, rank, currentLang }) {
  const { t } = useTranslation();
  const title = topic.title || t('trends.unnamedTopic');
  const summary = getLocalizedField(topic, 'summary', currentLang);
  const heatScore = topic.heat_score || 0;
  const url = topic.url || topic.link || '#';

  const getHeatColor = (score) => {
    if (score >= 80) return 'from-red-500 to-orange-500';
    if (score >= 60) return 'from-orange-500 to-yellow-500';
    return 'from-yellow-500 to-green-500';
  };

  const getRankColor = (rank) => {
    if (rank === 1) return 'from-yellow-500 to-orange-500';
    if (rank === 2) return 'from-slate-400 to-slate-500';
    return 'from-amber-600 to-amber-700';
  };

  return (
    <div className="glass-card p-5 hover-lift group">
      <div className="flex gap-4">
        {/* 排名徽章 */}
        <div className={cn(
          "flex-shrink-0 w-10 h-10 rounded-lg bg-gradient-to-br flex items-center justify-center font-bold text-white",
          getRankColor(rank)
        )}>
          #{rank}
        </div>

        {/* 内容 */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between mb-2">
            <h4 className="text-lg font-bold text-white line-clamp-1 flex-1 group-hover:text-primary-400 transition-colors">
              {title}
            </h4>
            {url !== '#' && (
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="ml-2 text-slate-400 hover:text-primary-400 transition-colors flex-shrink-0"
              >
                <ExternalLink className="w-4 h-4" />
              </a>
            )}
          </div>

          {/* 热度指示器 */}
          <div className="flex items-center gap-3 mb-3">
            <div className="flex items-center gap-1.5">
              <Flame className="w-4 h-4 text-orange-500" />
              <span className="text-lg font-bold text-orange-400">
                {heatScore.toFixed(0)}
              </span>
            </div>
            <div className="flex-1">
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

          {/* 摘要 */}
          {summary && (
            <p className="text-sm text-slate-300 line-clamp-2 leading-relaxed">
              {summary}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * 预览机会卡片
 */
function PreviewOpportunityCard({ opportunity, currentLang }) {
  const { t } = useTranslation();
  const mvpSuggestion = getLocalizedField(opportunity, 'mvp_suggestion', currentLang);
  const score = opportunity.opportunity_score || 0;

  return (
    <div className="glass-card p-6 hover-lift bg-gradient-to-br from-primary-500/10 to-accent-500/10 border-2 border-primary-500/30">
      <div className="flex items-start gap-4 mb-4">
        <div className="flex-shrink-0 w-16 h-16 rounded-xl bg-gradient-to-br from-accent-500 to-primary-500 flex items-center justify-center">
          <Target className="w-8 h-8 text-white" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h4 className="text-xl font-bold text-white">
              {t('landing.preview.opportunityTitle')}
            </h4>
            <div className="px-3 py-1 rounded-full bg-gradient-to-r from-green-500/20 to-emerald-500/20 border border-green-500/30">
              <span className="text-sm font-bold text-green-400">
                {t('landing.preview.score')}: {(score * 100).toFixed(0)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {mvpSuggestion && (
        <div className="p-4 rounded-lg bg-white/5 border border-white/10">
          <p className="text-slate-200 leading-relaxed">
            {mvpSuggestion}
          </p>
        </div>
      )}

      <div className="mt-4 flex items-center gap-2 text-xs text-slate-400">
        <Star className="w-4 h-4 text-yellow-500" />
        <span>{t('landing.preview.aiGenerated')}</span>
      </div>
    </div>
  );
}
