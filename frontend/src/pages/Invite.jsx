import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { CheckCircle, XCircle, Mail, Loader2, UserPlus, Gift, Clock } from 'lucide-react';
import { useTranslation } from 'react-i18next';

// 使用环境变量配置API基础URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

/**
 * 邀请注册页面
 * 用户通过邀请码注册Beta账号
 */
export default function Invite() {
  const { t, i18n } = useTranslation();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const inviteCode = searchParams.get('code');

  // 页面状态
  const [step, setStep] = useState('validating'); // validating, valid, invalid, submitting, success, error
  const [email, setEmail] = useState('');
  const [codeInfo, setCodeInfo] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // 验证邀请码
  useEffect(() => {
    if (!inviteCode) {
      setStep('invalid');
      setErrorMessage(t('invite.invalid.reason4'));
      return;
    }

    validateInviteCode(inviteCode);
  }, [inviteCode, t]);

  // 验证邀请码的API调用
  const validateInviteCode = async (code) => {
    try {
      const response = await fetch(`${API_BASE_URL}/invite/validate?code=${encodeURIComponent(code)}`);
      const data = await response.json();

      if (data.valid) {
        setCodeInfo(data.code_info);
        setStep('valid');
      } else {
        setStep('invalid');
        setErrorMessage(data.reason || t('invite.invalid.title'));
      }
    } catch (error) {
      console.error('验证邀请码失败:', error);
      setStep('invalid');
      setErrorMessage(t('invite.invalid.title'));
    }
  };

  // 提交注册表单
  const handleSubmit = async (e) => {
    e.preventDefault();

    // 验证邮箱格式
    if (!email || !email.includes('@')) {
      setErrorMessage(t('inviteInput.errors.required'));
      return;
    }

    setStep('submitting');
    setErrorMessage('');

    try {
      const response = await fetch(`${API_BASE_URL}/invite/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email,
          invite_code: inviteCode,
          language: i18n.language, // 传递当前界面语言
        }),
      });

      const data = await response.json();

      if (data.success) {
        setStep('success');
        setSuccessMessage(
          t('checkoutSuccess.message') + ' ' + t('checkoutSuccess.emailSent')
        );
      } else {
        setStep('error');
        setErrorMessage(data.message || t('pricing.error'));
      }
    } catch (error) {
      console.error('注册失败:', error);
      setStep('error');
      setErrorMessage(t('pricing.error'));
    }
  };

  // 渲染不同状态的内容
  const renderContent = () => {
    // 验证中
    if (step === 'validating') {
      return (
        <div className="text-center py-12">
          <Loader2 className="w-16 h-16 text-blue-500 animate-spin mx-auto mb-4" />
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">
            {t('invite.validating.title')}
          </h2>
          <p className="text-gray-600">
            {t('invite.validating.message')}
          </p>
        </div>
      );
    }

    // 邀请码无效
    if (step === 'invalid') {
      return (
        <div className="text-center">
          <XCircle className="w-20 h-20 text-red-500 mx-auto mb-6" />
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            {t('invite.invalid.title')}
          </h2>
          <p className="text-gray-600 text-lg mb-6">
            {errorMessage}
          </p>
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-left">
            <h3 className="font-semibold text-red-900 mb-3">
              {t('invite.invalid.reasons')}
            </h3>
            <ul className="space-y-2 text-red-800 text-sm">
              <li>• {t('invite.invalid.reason1')}</li>
              <li>• {t('invite.invalid.reason2')}</li>
              <li>• {t('invite.invalid.reason3')}</li>
              <li>• {t('invite.invalid.reason4')}</li>
            </ul>
          </div>
          <button
            onClick={() => window.location.href = 'mailto:support@your-dashboard.com'}
            className="mt-6 w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 transition font-medium"
          >
            {t('common.contactSupport')}
          </button>
        </div>
      );
    }

    // 注册成功
    if (step === 'success') {
      return (
        <div className="text-center">
          <CheckCircle className="w-20 h-20 text-green-500 mx-auto mb-6" />
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            {t('invite.success.title')}
          </h2>
          <p className="text-gray-600 text-lg mb-6">
            {successMessage}
          </p>
          <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-left mb-6">
            <h3 className="font-semibold text-green-900 mb-3">
              {t('invite.success.nextSteps')}
            </h3>
            <ul className="space-y-2 text-green-800 text-sm">
              <li className="flex items-start gap-2">
                <span className="text-green-600 font-bold">1.</span>
                <span>{t('invite.success.step1')} <strong>{email}</strong></span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-600 font-bold">2.</span>
                <span>{t('invite.success.step2')}</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-600 font-bold">3.</span>
                <span>{t('invite.success.step3')}</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-600 font-bold">4.</span>
                <span>{t('invite.success.step4')}</span>
              </li>
            </ul>
          </div>
        </div>
      );
    }

    // 注册表单（邀请码有效）
    return (
      <div>
        {/* 欢迎信息 */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="bg-green-100 p-4 rounded-full">
              <CheckCircle className="w-12 h-12 text-green-600" />
            </div>
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            {t('invite.form.title')}
          </h2>
          <p className="text-gray-600 text-lg">
            {t('invite.form.subtitle')}
          </p>
        </div>

        {/* 邀请码信息 */}
        {codeInfo && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
            <h3 className="font-semibold text-blue-900 mb-3 flex items-center gap-2">
              <Gift className="w-5 h-5" />
              {t('invite.form.codeLabel')}
            </h3>
            <div className="space-y-2 text-sm text-blue-800">
              <div className="flex justify-between">
                <span>{t('invite.form.codeLabel')}</span>
                <span className="font-mono font-bold">{codeInfo.code}</span>
              </div>
              <div className="flex justify-between">
                <span>{t('invite.form.typeLabel')}</span>
                <span className="font-semibold">
                  {codeInfo.code_type === 'beta' ? t('invite.form.types.beta') :
                   codeInfo.code_type === 'partner' ? t('invite.form.types.partner') : t('invite.form.types.referral')}
                </span>
              </div>
              {codeInfo.expires_at && (
                <div className="flex justify-between items-center">
                  <span>{t('invite.form.expiresLabel')}</span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    {new Date(codeInfo.expires_at).toLocaleDateString('zh-CN')}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 注册表单 */}
        <form onSubmit={handleSubmit}>
          <div className="mb-6">
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
              {t('invite.form.emailLabel')}
            </label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your-email@example.com"
              required
              disabled={step === 'submitting'}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
            <p className="mt-2 text-sm text-gray-500">
              {t('invite.form.emailHelp')}
            </p>
          </div>

          {/* 错误提示 */}
          {errorMessage && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
              <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-800">{errorMessage}</p>
            </div>
          )}

          {/* 提交按钮 */}
          <button
            type="submit"
            disabled={step === 'submitting'}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 px-6 rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg hover:shadow-xl"
          >
            {step === 'submitting' ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                {t('invite.form.submitting')}
              </>
            ) : (
              <>
                <UserPlus className="w-5 h-5" />
                {t('invite.form.submit')}
              </>
            )}
          </button>
        </form>

        {/* 隐私说明 */}
        <div className="mt-6 text-center text-xs text-gray-500">
          <p>
            {t('invite.form.terms')}
          </p>
          <p className="mt-1">
            {t('invite.form.privacy')}
          </p>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 flex items-center justify-center p-4 text-gray-900">
      <div className="max-w-md w-full">
        {/* 主卡片 */}
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          {renderContent()}
        </div>

        {/* 底部提示 */}
        <div className="mt-6 text-center">
          <p className="text-gray-600 text-sm">
            {t('invite.form.hasAccount')}<a href="mailto:support@your-dashboard.com" className="text-blue-600 hover:underline">{t('common.contactSupport')}</a>
          </p>
        </div>
      </div>
    </div>
  );
}
