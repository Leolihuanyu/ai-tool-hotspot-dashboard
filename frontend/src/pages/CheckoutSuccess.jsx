import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

/**
 * 支付成功页面
 * 显示支付完成后的成功信息
 */
export default function CheckoutSuccess() {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get('session_id');
  const [countdown, setCountdown] = useState(5);

  useEffect(() => {
    // 倒计时5秒后自动跳转到首页
    const timer = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          window.location.href = '/';
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center">
        {/* 成功图标 */}
        <div className="mb-6">
          <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
            <svg
              className="w-8 h-8 text-green-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>
        </div>

        {/* 标题 */}
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          {t('checkoutSuccess.title')}
        </h1>

        {/* 描述 */}
        <p className="text-gray-600 mb-6">
          {t('checkoutSuccess.message')}
          <br />
          {t('checkoutSuccess.emailSent')}
        </p>

        {/* Session ID */}
        {sessionId && (
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500 mb-2">{t('checkoutSuccess.orderId')}</p>
            <p className="text-xs font-mono text-gray-700 break-all">
              {sessionId}
            </p>
          </div>
        )}

        {/* 提示信息 */}
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start space-x-3">
            <svg
              className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                clipRule="evenodd"
              />
            </svg>
            <div className="text-left">
              <p className="text-sm font-medium text-blue-900 mb-1">
                {t('checkoutSuccess.nextSteps.title')}
              </p>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• {t('checkoutSuccess.nextSteps.step1')}</li>
                <li>• {t('checkoutSuccess.nextSteps.step2')}</li>
                <li>• {t('checkoutSuccess.nextSteps.step3')}</li>
              </ul>
            </div>
          </div>
        </div>

        {/* 倒计时提示 */}
        <p className="text-sm text-gray-500 mb-4">
          {countdown} {t('common.seconds')}
        </p>

        {/* 按钮组 */}
        <div className="space-y-3">
          <Link
            to="/"
            className="block w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold py-3 px-6 rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 shadow-lg hover:shadow-xl"
          >
            {t('checkoutSuccess.cta')}
          </Link>

          <a
            href="mailto:leolihuanyu@gmail.com"
            className="block w-full bg-gray-100 text-gray-700 font-semibold py-3 px-6 rounded-lg hover:bg-gray-200 transition-all duration-200"
          >
            {t('checkoutSuccess.support.title')}
          </a>
        </div>

        {/* 底部提示 */}
        <p className="mt-8 text-xs text-gray-400">
          {t('checkoutSuccess.support.message')}
        </p>
      </div>
    </div>
  );
}
