import React, { useEffect, useState } from 'react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001';

/**
 * 支付成功页面
 * 显示支付完成后的成功信息，自动获取访问token并跳转到Dashboard
 */
export default function CheckoutSuccess() {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const sessionId = searchParams.get('session_id');
  const [countdown, setCountdown] = useState(5);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dashboardUrl, setDashboardUrl] = useState(null);
  const [email, setEmail] = useState(null);

  // 获取访问token
  useEffect(() => {
    const fetchAccessToken = async () => {
      if (!sessionId) {
        setError('缺少支付会话ID');
        setLoading(false);
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/get-session-info`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ session_id: sessionId }),
        });

        const data = await response.json();

        if (data.success) {
          setEmail(data.email);
          setDashboardUrl(data.dashboard_url);
          setLoading(false);
        } else {
          setError(data.error || '获取访问信息失败');
          setLoading(false);
        }
      } catch (err) {
        console.error('获取访问token失败:', err);
        setError('网络错误，请稍后重试');
        setLoading(false);
      }
    };

    fetchAccessToken();
  }, [sessionId]);

  // 倒计时自动跳转
  useEffect(() => {
    if (!loading && dashboardUrl) {
      const timer = setInterval(() => {
        setCountdown(prev => {
          if (prev <= 1) {
            clearInterval(timer);
            window.location.href = dashboardUrl;
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      return () => clearInterval(timer);
    }
  }, [loading, dashboardUrl]);

  // 显示加载状态
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center px-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center">
          <div className="mb-6">
            <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
              <svg className="animate-spin h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">正在准备您的Dashboard...</h1>
          <p className="text-gray-600">请稍候，我们正在为您生成访问凭证</p>
        </div>
      </div>
    );
  }

  // 显示错误状态
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center px-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center">
          <div className="mb-6">
            <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-4">出现问题</h1>
          <p className="text-gray-600 mb-6">{error}</p>
          <div className="space-y-3">
            <Link
              to="/"
              className="block w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold py-3 px-6 rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all duration-200"
            >
              返回首页
            </Link>
            <a
              href="mailto:support@jereo.co.jp"
              className="block w-full bg-gray-100 text-gray-700 font-semibold py-3 px-6 rounded-lg hover:bg-gray-200 transition-all duration-200"
            >
              联系客服
            </a>
          </div>
        </div>
      </div>
    );
  }

  // 显示成功状态
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
        <p className="text-gray-600 mb-2">
          {t('checkoutSuccess.message')}
        </p>
        {email && (
          <p className="text-sm text-gray-500 mb-6">
            订阅邮箱: <span className="font-medium text-gray-700">{email}</span>
          </p>
        )}

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
              <p className="text-sm font-medium text-blue-900 mb-2">
                即将自动跳转到Dashboard，或者：
              </p>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• 点击下方"立即访问"按钮</li>
                <li>• 访问链接也已发送至您的邮箱作为备用</li>
                <li>• 链接有效期为24小时</li>
              </ul>
            </div>
          </div>
        </div>

        {/* 倒计时提示 */}
        <p className="text-sm text-gray-500 mb-4">
          {countdown} 秒后自动跳转...
        </p>

        {/* 按钮组 */}
        <div className="space-y-3">
          {dashboardUrl && (
            <a
              href={dashboardUrl}
              className="block w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold py-3 px-6 rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 shadow-lg hover:shadow-xl"
            >
              立即访问Dashboard
            </a>
          )}

          <a
            href="mailto:support@jereo.co.jp"
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
