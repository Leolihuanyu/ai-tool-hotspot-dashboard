import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Ticket, ArrowRight, AlertCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';

/**
 * 邀请码输入页面
 * 用户输入邀请码后跳转到注册页面
 */
export default function InviteCodeInput() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [inviteCode, setInviteCode] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();

    // 验证邀请码格式
    const code = inviteCode.trim().toUpperCase();

    if (!code) {
      setError(t('inviteInput.errors.required'));
      return;
    }

    if (code.length < 6) {
      setError(t('inviteInput.errors.invalid'));
      return;
    }

    // 跳转到邀请注册页面
    navigate(`/invite?code=${code}`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 flex items-center justify-center p-4 text-gray-900">
      <div className="max-w-md w-full">
        {/* 主卡片 */}
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          {/* 图标 */}
          <div className="flex justify-center mb-6">
            <div className="bg-blue-100 p-4 rounded-full">
              <Ticket className="w-12 h-12 text-blue-600" />
            </div>
          </div>

          {/* 标题 */}
          <h1 className="text-3xl font-bold text-gray-900 mb-2 text-center">
            {t('inviteInput.title')}
          </h1>
          <p className="text-gray-600 mb-6 text-center">
            {t('inviteInput.subtitle')}
          </p>

          {/* 表单 */}
          <form onSubmit={handleSubmit}>
            <div className="mb-6">
              <label htmlFor="inviteCode" className="block text-sm font-medium text-gray-700 mb-2">
                {t('inviteInput.codeLabel')}
              </label>
              <input
                type="text"
                id="inviteCode"
                value={inviteCode}
                onChange={(e) => {
                  setInviteCode(e.target.value.toUpperCase());
                  setError('');
                }}
                placeholder={t('inviteInput.placeholder')}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-lg text-center uppercase"
                autoFocus
              />
              <p className="mt-2 text-sm text-gray-500">
                {t('inviteInput.hint')}
              </p>
            </div>

            {/* 错误提示 */}
            {error && (
              <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            {/* 提交按钮 */}
            <button
              type="submit"
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 px-6 rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 font-medium shadow-lg hover:shadow-xl flex items-center justify-center gap-2"
            >
              {t('inviteInput.submit')}
              <ArrowRight className="w-5 h-5" />
            </button>
          </form>
        </div>

        {/* 帮助信息 */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">
            {t('inviteInput.help.title')}
          </h3>
          <ul className="space-y-2 text-blue-800 text-sm">
            <li className="flex items-start gap-2">
              <span className="text-blue-600 font-bold">1.</span>
              <span>{t('inviteInput.help.tip1')}</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 font-bold">2.</span>
              <span>{t('inviteInput.help.tip2')}</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 font-bold">3.</span>
              <span>{t('inviteInput.help.tip3')}</span>
            </li>
          </ul>
        </div>

        {/* 底部链接 */}
        <div className="mt-6 text-center">
          <p className="text-gray-600 text-sm">
            {t('inviteInput.noCode.title')}
            <a href="mailto:support@your-dashboard.com" className="text-blue-600 hover:underline ml-1">
              {t('inviteInput.noCode.cta')}
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
