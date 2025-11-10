import { useState } from 'react';
import { Check, Loader2, Sparkles, TrendingUp, Zap, Shield, ArrowRight } from 'lucide-react';
import { redirectToCheckout } from '../services/paymentService';
import { useTranslation } from 'react-i18next';

/**
 * 定价页面
 * 显示月付和年付订阅选项
 */
export default function Pricing() {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(null); // 'monthly' | 'yearly' | null
  const [error, setError] = useState('');

  // 处理订阅按钮点击
  const handleSubscribe = async (priceType) => {
    try {
      setLoading(priceType);
      setError('');

      // 重定向到Stripe Checkout
      await redirectToCheckout(priceType);
    } catch (err) {
      console.error('订阅失败:', err);
      setError(err.message || t('pricing.error') + err.message);
      setLoading(null);
    }
  };

  // 功能列表
  const features = [
    { icon: TrendingUp, text: t('pricing.monthly.feature1') },
    { icon: Zap, text: t('pricing.monthly.feature2') },
    { icon: Sparkles, text: t('pricing.monthly.feature3') },
    { icon: Shield, text: t('pricing.monthly.feature4') },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* 页面标题 */}
        <div className="text-center mb-16">
          <h1 className="text-5xl md:text-6xl font-extrabold text-white mb-6">
            {t('pricing.title')}
          </h1>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto">
            {t('pricing.subtitle')}
          </p>
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="max-w-2xl mx-auto mb-8 bg-red-500/10 border border-red-500/50 rounded-lg p-4 text-red-200">
            <p className="text-center">{error}</p>
          </div>
        )}

        {/* 定价卡片 */}
        <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
          {/* 月付计划 */}
          <PricingCard
            title={t('pricing.monthly.title')}
            price="$5"
            period="/月"
            description={t('pricing.monthly.desc')}
            features={features}
            onSubscribe={() => handleSubscribe('monthly')}
            loading={loading === 'monthly'}
            buttonText={t('pricing.monthly.cta')}
            popular={false}
          />

          {/* 年付计划 */}
          <PricingCard
            title={t('pricing.yearly.title')}
            price="$48"
            period="/年"
            description={t('pricing.yearly.desc')}
            features={features}
            onSubscribe={() => handleSubscribe('yearly')}
            loading={loading === 'yearly'}
            buttonText={t('pricing.yearly.cta')}
            popular={true}
            badge={t('pricing.yearly.badge')}
          />
        </div>

        {/* 底部说明 */}
        <div className="mt-16 text-center text-gray-400">
          <p className="mb-4">{t('pricing.features.allFeatures')}</p>
          <p className="text-sm">{t('pricing.features.securePayment')}</p>
        </div>
      </div>
    </div>
  );
}

/**
 * 定价卡片组件
 */
function PricingCard({
  title,
  price,
  period,
  description,
  features,
  onSubscribe,
  loading,
  buttonText,
  popular,
  badge
}) {
  const { t } = useTranslation();
  return (
    <div className={`
      relative rounded-2xl p-8
      ${popular
        ? 'bg-gradient-to-br from-purple-600 to-blue-600 shadow-2xl scale-105'
        : 'bg-white/10 backdrop-blur-lg border border-white/20'
      }
      transition-all duration-300 hover:scale-105
    `}>
      {/* 推荐徽章 */}
      {badge && (
        <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
          <span className="bg-gradient-to-r from-yellow-400 to-orange-500 text-white px-4 py-1 rounded-full text-sm font-bold shadow-lg">
            {badge}
          </span>
        </div>
      )}

      {/* 卡片头部 */}
      <div className="text-center mb-8">
        <h3 className="text-2xl font-bold text-white mb-2">{title}</h3>
        <p className="text-gray-300 text-sm mb-6">{description}</p>

        <div className="flex items-baseline justify-center">
          <span className="text-5xl font-extrabold text-white">{price}</span>
          <span className="text-xl text-gray-300 ml-2">{period}</span>
        </div>
      </div>

      {/* 功能列表 */}
      <div className="space-y-4 mb-8">
        {features.map((feature, index) => {
          const Icon = feature.icon;
          return (
            <div key={index} className="flex items-center text-white">
              <Icon className="w-5 h-5 mr-3 flex-shrink-0" />
              <span>{feature.text}</span>
            </div>
          );
        })}
      </div>

      {/* 订阅按钮 */}
      <button
        onClick={onSubscribe}
        disabled={loading}
        className={`
          w-full py-4 px-6 rounded-xl font-bold text-lg
          transition-all duration-200
          flex items-center justify-center gap-2
          ${popular
            ? 'bg-white text-purple-600 hover:bg-gray-100'
            : 'bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:from-purple-700 hover:to-blue-700'
          }
          ${loading ? 'opacity-50 cursor-not-allowed' : 'hover:shadow-xl'}
        `}
      >
        {loading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            <span>{t('common.processing')}</span>
          </>
        ) : (
          <>
            <span>{buttonText}</span>
            <ArrowRight className="w-5 h-5" />
          </>
        )}
      </button>

      {/* 底部提示 */}
      <p className="text-center text-sm text-gray-300 mt-4">
        {t('pricing.features.cancelAnytime')}
      </p>
    </div>
  );
}
