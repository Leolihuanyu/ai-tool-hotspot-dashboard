import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { TrendingUp, Sparkles, Target, ArrowRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { loadDashboardData, getStats } from '../services/dataService';
import { formatNumber } from '../lib/utils';

/**
 * 首页组件 - Dashboard 概览
 */
export default function Home() {
  const { t } = useTranslation();
  const [stats, setStats] = useState({ tools: 0, topics: 0, opportunities: 0 });
  const [loading, setLoading] = useState(true);
  const [recentTools, setRecentTools] = useState([]);
  const [recentTopics, setRecentTopics] = useState([]);

  useEffect(() => {
    async function fetchData() {
      try {
        const data = await loadDashboardData();
        setStats(getStats(data));
        setRecentTools((data.ai_tools || []).slice(0, 5));
        setRecentTopics((data.trending_topics || []).slice(0, 5));
      } catch (error) {
        console.error(t('common.loadError'), error);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-400">{t('common.loading')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Hero 区域 */}
      <section className="text-center py-12">
        <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent">
          {t('home.title')}
        </h1>
        <p className="text-xl text-slate-400 max-w-2xl mx-auto">
          {t('home.subtitle')}
        </p>
      </section>

      {/* 统计卡片 */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard
          icon={<Sparkles className="w-8 h-8" />}
          title={t('home.stats.tools')}
          value={formatNumber(stats.tools)}
          subtitle={t('home.stats.toolsCount')}
          link="/tools"
          color="from-blue-500 to-cyan-500"
        />
        <StatCard
          icon={<TrendingUp className="w-8 h-8" />}
          title={t('home.stats.topics')}
          value={formatNumber(stats.topics)}
          subtitle={t('home.stats.topicsCount')}
          link="/trends"
          color="from-purple-500 to-pink-500"
        />
        <StatCard
          icon={<Target className="w-8 h-8" />}
          title={t('home.stats.opportunities')}
          value={formatNumber(stats.opportunities)}
          subtitle={t('home.stats.opportunitiesCount')}
          link="/opportunities"
          color="from-orange-500 to-red-500"
        />
      </section>

      {/* 最新工具 */}
      <section className="glass-card p-6 animate-slide-up">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold">{t('home.sections.latestTools')}</h2>
          <Link
            to="/tools"
            className="flex items-center gap-2 text-primary-400 hover:text-primary-300 transition-colors"
          >
            {t('common.viewAll')} <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
        <div className="space-y-4">
          {recentTools.map((tool, idx) => (
            <ToolItem key={tool.id || idx} tool={tool} />
          ))}
        </div>
      </section>

      {/* 最新话题 */}
      <section className="glass-card p-6 animate-slide-up" style={{ animationDelay: '0.1s' }}>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold">{t('home.sections.latestTopics')}</h2>
          <Link
            to="/trends"
            className="flex items-center gap-2 text-primary-400 hover:text-primary-300 transition-colors"
          >
            {t('common.viewAll')} <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
        <div className="space-y-4">
          {recentTopics.map((topic, idx) => (
            <TopicItem key={topic.id || idx} topic={topic} />
          ))}
        </div>
      </section>
    </div>
  );
}

// ========== 子组件 ==========

/**
 * 统计卡片组件
 */
function StatCard({ icon, title, value, subtitle, link, color }) {
  return (
    <Link to={link} className="block">
      <div className="glass-card p-6 hover-lift cursor-pointer group">
        <div className="flex items-center gap-4">
          <div className={`bg-gradient-to-br ${color} p-3 rounded-lg group-hover:scale-110 transition-transform`}>
            {icon}
          </div>
          <div className="flex-1">
            <p className="text-slate-400 text-sm mb-1">{title}</p>
            <p className="text-3xl font-bold">{value}</p>
            <p className="text-slate-500 text-sm">{subtitle}</p>
          </div>
        </div>
      </div>
    </Link>
  );
}

/**
 * 工具列表项
 */
function ToolItem({ tool }) {
  const { t } = useTranslation();

  return (
    <div className="flex items-center gap-4 p-4 rounded-lg bg-white/5 hover:bg-white/10 transition-colors">
      <div className="flex-1">
        <h3 className="font-semibold text-white mb-1">{tool.name || t('home.placeholders.unnamed')}</h3>
        <p className="text-sm text-slate-400 line-clamp-1">
          {tool.description || tool.title || t('home.placeholders.noDescription')}
        </p>
      </div>
      <div className="text-xs text-slate-500">{tool.source || ''}</div>
    </div>
  );
}

/**
 * 话题列表项
 */
function TopicItem({ topic }) {
  const { t } = useTranslation();

  return (
    <div className="flex items-center gap-4 p-4 rounded-lg bg-white/5 hover:bg-white/10 transition-colors">
      <div className="flex-1">
        <h3 className="font-semibold text-white mb-1">{topic.title || t('home.placeholders.unnamedTopic')}</h3>
        <p className="text-sm text-slate-400 line-clamp-1">
          {topic.description || topic.summary || t('home.placeholders.noDescription')}
        </p>
      </div>
      {topic.engagement && (
        <div className="text-right">
          <p className="text-sm font-semibold text-primary-400">{formatNumber(topic.engagement)}</p>
          <p className="text-xs text-slate-500">{t('home.placeholders.engagement')}</p>
        </div>
      )}
    </div>
  );
}
