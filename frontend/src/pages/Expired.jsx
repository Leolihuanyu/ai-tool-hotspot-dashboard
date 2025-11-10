import { useSearchParams } from 'react-router-dom';
import { AlertCircle, Clock, Shield, Mail, ArrowRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';

/**
 * 访问过期/无效提示页面
 * 根据错误类型显示不同的提示信息
 */
export default function Expired() {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const error = searchParams.get('error') || t('expired.title');

  // 根据错误信息判断类型并选择合适的图标和提示
  let icon, title, suggestion, iconColor;

  if (error.includes('过期') || error.includes('expired')) {
    icon = <Clock className="w-20 h-20" />;
    iconColor = 'text-orange-500';
    title = t('expired.errors.expired.title');
    suggestion = t('expired.errors.expired.message');
  } else if (error.includes('IP') || error.includes('转发')) {
    icon = <Shield className="w-20 h-20" />;
    iconColor = 'text-red-500';
    title = t('expired.errors.ipMismatch.title');
    suggestion = t('expired.errors.ipMismatch.message');
  } else if (error.includes('未提供') || error.includes('未找到')) {
    icon = <AlertCircle className="w-20 h-20" />;
    iconColor = 'text-gray-500';
    title = t('expired.errors.noToken.title');
    suggestion = t('expired.errors.noToken.message');
  } else {
    icon = <AlertCircle className="w-20 h-20" />;
    iconColor = 'text-gray-500';
    title = t('expired.errors.invalid.title');
    suggestion = t('expired.errors.invalid.message');
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-gray-100 to-gray-200 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {/* 主卡片 */}
        <div className="bg-white rounded-2xl shadow-2xl p-8 text-center">
          {/* 图标 */}
          <div className={`flex justify-center mb-6 ${iconColor}`}>
            {icon}
          </div>

          {/* 标题 */}
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            {title}
          </h1>

          {/* 建议 */}
          <p className="text-gray-600 mb-6 text-lg leading-relaxed">
            {suggestion}
          </p>

          {/* 错误详情（可折叠） */}
          <details className="mb-6">
            <summary className="text-sm text-gray-500 cursor-pointer hover:text-gray-700 transition">
              {t('expired.actions.showDetails')}
            </summary>
            <div className="mt-3 p-4 bg-gray-50 rounded-lg text-left">
              <p className="text-sm font-mono text-gray-700 break-words">
                {error}
              </p>
            </div>
          </details>

          {/* 操作按钮 */}
          <div className="space-y-3">
            {/* 使用邀请码注册 */}
            <a
              href="/invite-register"
              className="flex items-center justify-center gap-2 w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 px-6 rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl font-medium"
            >
              {t('expired.actions.useInviteCode')}
              <ArrowRight className="w-5 h-5" />
            </a>

            {/* 联系支持 */}
            <a
              href="mailto:support@your-dashboard.com?subject=访问链接问题&body=错误信息：%0A%0A{error}"
              className="flex items-center justify-center gap-2 w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 transition-all duration-200 shadow-lg hover:shadow-xl font-medium"
            >
              <Mail className="w-5 h-5" />
              {t('common.contactSupport')}
            </a>

            {/* 立即订阅 */}
            <a
              href="/subscribe"
              className="flex items-center justify-center gap-2 w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white py-3 px-6 rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all duration-200 shadow-lg hover:shadow-xl font-medium"
            >
              {t('expired.actions.subscribe')}
              <ArrowRight className="w-5 h-5" />
            </a>

            {/* 返回首页 */}
            <button
              onClick={() => window.location.href = '/'}
              className="w-full bg-gray-100 text-gray-700 py-3 px-6 rounded-lg hover:bg-gray-200 transition-all duration-200 font-medium"
            >
              {t('common.backHome')}
            </button>
          </div>
        </div>

        {/* 底部提示 */}
        <div className="mt-6 text-center">
          <p className="text-gray-500 text-sm">
            {t('expired.tip')}
          </p>
        </div>

        {/* 帮助信息卡片 */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">
            {t('expired.help.title')}
          </h3>
          <ul className="space-y-2 text-blue-800 text-sm">
            <li className="flex items-start gap-2">
              <span className="text-blue-600 font-bold">1.</span>
              <span>{t('expired.help.step1')}</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 font-bold">2.</span>
              <span>{t('expired.help.step2')}</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 font-bold">3.</span>
              <span>{t('expired.help.step3')}</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 font-bold">4.</span>
              <span>{t('expired.help.step4')}</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
