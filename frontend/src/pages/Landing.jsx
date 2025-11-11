import { useState, useEffect } from 'react';
import {
  Sparkles, TrendingUp, Target, Zap, Shield, Clock,
  Check, ArrowRight, Mail, Github, Twitter, ChevronDown
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import PreviewDashboard from '../components/PreviewDashboard';

/**
 * Landing Page - 产品首页
 * 展示产品功能、定价和FAQ
 */
export default function Landing() {
  const [openFaq, setOpenFaq] = useState(null);
  const navigate = useNavigate();

  // 检测URL中的token参数，如果存在则重定向到Dashboard
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.has('token') && params.has('email')) {
      // 保留所有URL参数并重定向到Dashboard
      navigate(`/dashboard?${params.toString()}`, { replace: true });
    }
  }, [navigate]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Hero 区域 */}
      <HeroSection />

      {/* Dashboard 预览 */}
      <DashboardPreviewSection />

      {/* 功能亮点 */}
      <FeaturesSection />

      {/* 定价简表 */}
      <PricingSection />

      {/* 社会证明 */}
      <StatsSection />

      {/* FAQ */}
      <FAQSection openFaq={openFaq} setOpenFaq={setOpenFaq} />

      {/* Footer */}
      <Footer />
    </div>
  );
}

/**
 * Hero 区域组件
 */
function HeroSection() {
  const { t } = useTranslation();

  return (
    <section className="pt-20 pb-32 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto text-center">
        {/* 徽章 */}
        <div className="inline-flex items-center gap-2 bg-purple-500/20 border border-purple-500/50 rounded-full px-4 py-2 mb-8">
          <Sparkles className="w-4 h-4 text-yellow-400" />
          <span className="text-purple-200 text-sm font-medium">
            {t('landing.badge')}
          </span>
        </div>

        {/* 主标题 */}
        <h1 className="text-5xl md:text-7xl font-extrabold text-white mb-6 leading-tight">
          {t('landing.hero.title1')}
          <span className="bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
            {' '}{t('landing.hero.title2')}
          </span>
        </h1>

        <p className="text-xl md:text-2xl text-gray-300 mb-12 max-w-3xl mx-auto leading-relaxed">
          {t('landing.hero.subtitle')}
        </p>

        {/* CTA 按钮 */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <Link
            to="/pricing"
            className="group bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-8 py-4 rounded-xl font-bold text-lg transition-all duration-200 shadow-2xl hover:shadow-purple-500/50 flex items-center gap-2"
          >
            {t('landing.hero.ctaPrimary')}
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Link>

          <Link
            to="/invite-register"
            className="bg-white/10 hover:bg-white/20 backdrop-blur-lg border border-white/30 text-white px-8 py-4 rounded-xl font-bold text-lg transition-all duration-200"
          >
            {t('landing.hero.ctaSecondary')}
          </Link>
        </div>
      </div>
    </section>
  );
}

/**
 * Dashboard 预览区域 - 浏览器窗口预览效果
 */
function DashboardPreviewSection() {
  const { t } = useTranslation();

  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8" id="preview">
      {/* 紧凑的预览容器 */}
      <div className="max-w-5xl mx-auto">
        {/* 浏览器窗口预览框 */}
        <div className="browser-window-preview">
          {/* 浏览器标题栏 */}
          <div className="browser-header">
            {/* Mac风格三色圆点 */}
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-red-500/80"></span>
              <span className="w-3 h-3 rounded-full bg-yellow-500/80"></span>
              <span className="w-3 h-3 rounded-full bg-green-500/80"></span>
            </div>
            {/* 标题文字 */}
            <div className="flex-1 text-center">
              <span className="text-sm text-slate-400 font-medium">
                {t('landing.preview.browserTitle')}
              </span>
            </div>
            {/* 右侧占位，保持对称 */}
            <div className="w-[52px]"></div>
          </div>

          {/* Dashboard内容区域 */}
          <div className="browser-content">
            <PreviewDashboard />
          </div>
        </div>
      </div>
    </section>
  );
}

/**
 * 功能亮点区域
 */
function FeaturesSection() {
  const { t } = useTranslation();

  const features = [
    {
      icon: TrendingUp,
      titleKey: 'landing.features.multiSource.title',
      descKey: 'landing.features.multiSource.desc'
    },
    {
      icon: Zap,
      titleKey: 'landing.features.llmFilter.title',
      descKey: 'landing.features.llmFilter.desc'
    },
    {
      icon: Target,
      titleKey: 'landing.features.smartMatch.title',
      descKey: 'landing.features.smartMatch.desc'
    },
    {
      icon: Clock,
      titleKey: 'landing.features.autoUpdate.title',
      descKey: 'landing.features.autoUpdate.desc'
    }
  ];

  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8 bg-black/20">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
            {t('landing.features.title')}
          </h2>
          <p className="text-xl text-gray-300">
            {t('landing.features.subtitle')}
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <div
                key={index}
                className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-2xl p-6 hover:bg-white/10 transition-all duration-300 hover:scale-105"
              >
                <div className="bg-gradient-to-br from-purple-500 to-pink-500 w-14 h-14 rounded-xl flex items-center justify-center mb-4">
                  <Icon className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-xl font-bold text-white mb-2">
                  {t(feature.titleKey)}
                </h3>
                <p className="text-gray-300">
                  {t(feature.descKey)}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

/**
 * 定价区域（简化版）
 */
function PricingSection() {
  const { t } = useTranslation();

  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
            {t('landing.pricing.title')}
          </h2>
          <p className="text-xl text-gray-300">
            {t('landing.pricing.subtitle')}
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {/* 月付 */}
          <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-2xl p-8 hover:border-purple-500/50 transition-all">
            <h3 className="text-2xl font-bold text-white mb-2">{t('landing.pricing.monthly.title')}</h3>
            <p className="text-gray-400 mb-6">{t('landing.pricing.monthly.desc')}</p>
            <div className="flex items-baseline mb-6">
              <span className="text-5xl font-extrabold text-white">$5</span>
              <span className="text-gray-400 ml-2">/月</span>
            </div>
            <ul className="space-y-3 mb-8">
              <PricingFeature text={t('landing.pricing.monthly.feature1')} />
              <PricingFeature text={t('landing.pricing.monthly.feature2')} />
              <PricingFeature text={t('landing.pricing.monthly.feature3')} />
              <PricingFeature text={t('landing.pricing.monthly.feature4')} />
            </ul>
            <Link
              to="/pricing"
              className="block w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white py-3 rounded-xl font-bold text-center transition-all"
            >
              {t('landing.pricing.monthly.cta')}
            </Link>
          </div>

          {/* 年付 */}
          <div className="bg-gradient-to-br from-purple-600 to-pink-600 rounded-2xl p-8 relative transform scale-105 shadow-2xl">
            <div className="absolute -top-4 right-8 bg-yellow-400 text-purple-900 px-4 py-1 rounded-full text-sm font-bold">
              {t('landing.pricing.yearly.badge')}
            </div>
            <h3 className="text-2xl font-bold text-white mb-2">{t('landing.pricing.yearly.title')}</h3>
            <p className="text-purple-100 mb-6">{t('landing.pricing.yearly.desc')}</p>
            <div className="flex items-baseline mb-6">
              <span className="text-5xl font-extrabold text-white">$48</span>
              <span className="text-purple-100 ml-2">/年</span>
            </div>
            <ul className="space-y-3 mb-8">
              <PricingFeature text={t('landing.pricing.monthly.feature1')} white />
              <PricingFeature text={t('landing.pricing.monthly.feature2')} white />
              <PricingFeature text={t('landing.pricing.monthly.feature3')} white />
              <PricingFeature text={t('landing.pricing.monthly.feature4')} white />
              <PricingFeature text={t('landing.pricing.yearly.feature4')} white />
            </ul>
            <Link
              to="/pricing"
              className="block w-full bg-white text-purple-600 hover:bg-gray-100 py-3 rounded-xl font-bold text-center transition-all"
            >
              {t('landing.pricing.yearly.cta')}
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}

/**
 * 定价功能项
 */
function PricingFeature({ text, white = false }) {
  return (
    <li className="flex items-center">
      <Check className={`w-5 h-5 mr-2 ${white ? 'text-white' : 'text-purple-400'}`} />
      <span className={white ? 'text-white' : 'text-gray-300'}>{text}</span>
    </li>
  );
}

/**
 * 统计数据区域
 */
function StatsSection() {
  const { t } = useTranslation();

  const stats = [
    { number: '10+', labelKey: 'landing.stats.sources' },
    { number: '100+', labelKey: 'landing.stats.opportunities' },
    { number: '70%+', labelKey: 'landing.stats.quality' },
    { number: '24/7', labelKey: 'landing.stats.updates' }
  ];

  return (
    <section className="py-16 px-4 sm:px-6 lg:px-8 bg-black/20">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((stat, index) => (
            <div key={index} className="text-center">
              <div className="text-4xl md:text-5xl font-extrabold text-white mb-2">
                {stat.number}
              </div>
              <div className="text-gray-400 text-lg">
                {t(stat.labelKey)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/**
 * FAQ区域
 */
function FAQSection({ openFaq, setOpenFaq }) {
  const { t } = useTranslation();

  const faqs = [
    { questionKey: 'landing.faq.q1.q', answerKey: 'landing.faq.q1.a' },
    { questionKey: 'landing.faq.q2.q', answerKey: 'landing.faq.q2.a' },
    { questionKey: 'landing.faq.q3.q', answerKey: 'landing.faq.q3.a' },
    { questionKey: 'landing.faq.q4.q', answerKey: 'landing.faq.q4.a' },
    { questionKey: 'landing.faq.q5.q', answerKey: 'landing.faq.q5.a' }
  ];

  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
            {t('landing.faq.title')}
          </h2>
        </div>

        <div className="space-y-4">
          {faqs.map((faq, index) => (
            <div
              key={index}
              className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-xl overflow-hidden"
            >
              <button
                onClick={() => setOpenFaq(openFaq === index ? null : index)}
                className="w-full px-6 py-4 text-left flex items-center justify-between hover:bg-white/5 transition-all"
              >
                <span className="text-lg font-semibold text-white">
                  {t(faq.questionKey)}
                </span>
                <ChevronDown
                  className={`w-5 h-5 text-gray-400 transition-transform ${
                    openFaq === index ? 'rotate-180' : ''
                  }`}
                />
              </button>
              {openFaq === index && (
                <div className="px-6 pb-4 text-gray-300">
                  {t(faq.answerKey)}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/**
 * Footer 组件
 */
function Footer() {
  const { t } = useTranslation();

  return (
    <footer className="py-12 px-4 sm:px-6 lg:px-8 border-t border-white/10">
      <div className="max-w-7xl mx-auto">
        <div className="grid md:grid-cols-3 gap-8 mb-8">
          {/* 品牌信息 */}
          <div>
            <h3 className="text-xl font-bold text-white mb-4">
              {t('landing.footer.title')}
            </h3>
            <p className="text-gray-400">
              {t('landing.footer.subtitle')}
            </p>
          </div>

          {/* 快速链接 */}
          <div>
            <h4 className="text-lg font-semibold text-white mb-4">
              {t('landing.footer.links.title')}
            </h4>
            <ul className="space-y-2">
              <li>
                <Link to="/pricing" className="text-gray-400 hover:text-white transition-colors">
                  {t('landing.footer.links.pricing')}
                </Link>
              </li>
              <li>
                <Link to="/invite-register" className="text-gray-400 hover:text-white transition-colors">
                  {t('landing.footer.links.beta')}
                </Link>
              </li>
            </ul>
          </div>

          {/* 联系方式 */}
          <div>
            <h4 className="text-lg font-semibold text-white mb-4">
              {t('landing.footer.links.contact')}
            </h4>
            <div className="flex gap-4">
              <a href="mailto:support@example.com" className="text-gray-400 hover:text-white transition-colors">
                <Mail className="w-6 h-6" />
              </a>
              <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-white transition-colors">
                <Github className="w-6 h-6" />
              </a>
              <a href="https://twitter.com" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-white transition-colors">
                <Twitter className="w-6 h-6" />
              </a>
            </div>
          </div>
        </div>

        {/* 版权信息 */}
        <div className="pt-8 border-t border-white/10 text-center text-gray-400">
          <p>{t('landing.footer.copyright')}</p>
          <p className="mt-2 text-sm">
            Powered by Stripe · Secure Payments
          </p>
        </div>
      </div>
    </footer>
  );
}
