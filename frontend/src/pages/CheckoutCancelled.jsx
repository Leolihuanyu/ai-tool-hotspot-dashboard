import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

/**
 * 支付取消页面
 * 显示用户取消支付后的信息
 */
export default function CheckoutCancelled() {
  const { t } = useTranslation();
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center">
        {/* 取消图标 */}
        <div className="mb-6">
          <div className="mx-auto w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center">
            <svg
              className="w-8 h-8 text-yellow-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
        </div>

        {/* 标题 */}
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          {t('checkoutCancelled.title')}
        </h1>

        {/* 描述 */}
        <p className="text-gray-600 mb-6">
          {t('checkoutCancelled.message')}
          <br />
          {t('checkoutCancelled.comeback')}
        </p>

        {/* 提示信息 */}
        <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-start space-x-3">
            <svg
              className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0"
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
              <p className="text-sm font-medium text-yellow-900 mb-1">
                {t('checkoutCancelled.why.title')}
              </p>
              <ul className="text-sm text-yellow-800 space-y-1">
                <li>• {t('checkoutCancelled.why.reason1')}</li>
                <li>• {t('checkoutCancelled.why.reason2')}</li>
                <li>• {t('checkoutCancelled.why.reason3')}</li>
                <li>• {t('checkoutCancelled.why.reason4')}</li>
              </ul>
            </div>
          </div>
        </div>

        {/* 按钮组 */}
        <div className="space-y-3">
          <Link
            to="/pricing"
            className="block w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold py-3 px-6 rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 shadow-lg hover:shadow-xl"
          >
            {t('checkoutCancelled.actions.pricing')}
          </Link>

          <Link
            to="/"
            className="block w-full bg-gray-100 text-gray-700 font-semibold py-3 px-6 rounded-lg hover:bg-gray-200 transition-all duration-200"
          >
            {t('checkoutCancelled.actions.home')}
          </Link>

          <a
            href="mailto:leolihuanyu@gmail.com"
            className="block w-full text-gray-600 font-medium py-2 hover:text-gray-800 transition-colors duration-200"
          >
            {t('checkoutCancelled.actions.support')}
          </a>
        </div>

        {/* 底部提示 */}
        <p className="mt-8 text-xs text-gray-400">
          {t('checkoutCancelled.welcome')}
        </p>
      </div>
    </div>
  );
}
