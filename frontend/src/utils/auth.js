/**
 * 前端认证工具模块
 * 用于处理Dashboard访问Token的验证和管理
 */

// 使用环境变量配置API基础URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

const TOKEN_STORAGE_KEY = 'access_token';
const EMAIL_STORAGE_KEY = 'user_email';
const SUBSCRIPTION_TYPE_STORAGE_KEY = 'subscription_type';
const TOKEN_EXPIRY_STORAGE_KEY = 'token_expiry';

/**
 * 从URL参数中提取token和email
 * @returns {{ token: string | null, email: string | null }}
 */
export function getTokenFromURL() {
  const params = new URLSearchParams(window.location.search);
  return {
    token: params.get('token'),
    email: params.get('email')
  };
}

/**
 * 将token保存到localStorage
 * @param {string} token - 访问token
 * @param {string} email - 用户邮箱
 * @param {string} subscriptionType - 订阅类型（beta/paid）
 */
export function saveToken(token, email, subscriptionType = 'beta') {
  // 计算24小时后的过期时间
  const expiry = Date.now() + 24 * 60 * 60 * 1000;

  localStorage.setItem(TOKEN_STORAGE_KEY, token);
  localStorage.setItem(EMAIL_STORAGE_KEY, email);
  localStorage.setItem(SUBSCRIPTION_TYPE_STORAGE_KEY, subscriptionType);
  localStorage.setItem(TOKEN_EXPIRY_STORAGE_KEY, expiry.toString());

  console.log('✅ Token已保存至localStorage', {
    email,
    subscriptionType,
    expiresAt: new Date(expiry).toLocaleString()
  });
}

/**
 * 从localStorage获取token
 * @returns {{ token: string | null, email: string | null, subscriptionType: string | null, expiry: number | null }}
 */
export function getStoredToken() {
  return {
    token: localStorage.getItem(TOKEN_STORAGE_KEY),
    email: localStorage.getItem(EMAIL_STORAGE_KEY),
    subscriptionType: localStorage.getItem(SUBSCRIPTION_TYPE_STORAGE_KEY),
    expiry: parseInt(localStorage.getItem(TOKEN_EXPIRY_STORAGE_KEY) || '0', 10)
  };
}

/**
 * 检查localStorage中的token是否仍然有效（未过期）
 * @returns {boolean}
 */
export function isTokenValid() {
  const { token, expiry } = getStoredToken();

  if (!token || !expiry) {
    return false;
  }

  // 检查是否过期
  const isExpired = Date.now() >= expiry;

  if (isExpired) {
    console.warn('⚠️  LocalStorage中的token已过期');
    clearToken();
    return false;
  }

  return true;
}

/**
 * 获取当前的访问token（用于API请求）
 * @returns {string | null} - 返回token字符串，如果不存在或已过期返回null
 */
export function getAuthToken() {
  const { token } = getStoredToken();

  if (!token || !isTokenValid()) {
    return null;
  }

  return token;
}

/**
 * 清除localStorage中的token和用户信息
 */
export function clearToken() {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
  localStorage.removeItem(EMAIL_STORAGE_KEY);
  localStorage.removeItem(SUBSCRIPTION_TYPE_STORAGE_KEY);
  localStorage.removeItem(TOKEN_EXPIRY_STORAGE_KEY);
  console.log('🧹 Token已清除');
}

/**
 * 调用后端API验证token的有效性
 * @param {string} token - 待验证的token
 * @param {string} email - 用户邮箱（用于数据库token验证）
 * @returns {Promise<{ valid: boolean, email?: string, subscription_type?: string, error?: string }>}
 */
export async function verifyToken(token, email) {
  try {
    // 构建查询参数（同时传递token和email）
    const params = new URLSearchParams({ token });
    if (email) {
      params.append('email', email);
    }

    const response = await fetch(`${API_BASE_URL}/verify-token?${params.toString()}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include'
    });

    if (!response.ok) {
      throw new Error(`HTTP错误: ${response.status}`);
    }

    const result = await response.json();
    return result;
  } catch (error) {
    console.error('❌ Token验证失败:', error);
    return {
      valid: false,
      error: `Token验证请求失败: ${error.message}`
    };
  }
}

/**
 * 检查用户是否已认证（优先检查localStorage，避免每次都请求后端）
 * @returns {boolean}
 */
export function isAuthenticated() {
  return isTokenValid();
}

/**
 * 获取当前用户信息
 * @returns {{ email: string | null, subscriptionType: string | null }}
 */
export function getCurrentUser() {
  const { email, subscriptionType } = getStoredToken();
  return { email, subscriptionType };
}

/**
 * 完整的认证流程：从URL提取token -> 验证 -> 保存
 * @returns {Promise<{ success: boolean, error?: string, email?: string }>}
 */
export async function handleAuthFlow() {
  // 1. 从URL提取token和email
  const { token, email } = getTokenFromURL();

  if (!token || !email) {
    console.log('ℹ️  URL中未找到token和email参数');
    return { success: false, error: '未提供访问token' };
  }

  console.log('🔍 发现URL中的token，开始验证...', { email });

  // 2. 验证token（传递email用于数据库token验证）
  const verifyResult = await verifyToken(token, email);

  if (!verifyResult.valid) {
    console.error('❌ Token验证失败:', verifyResult.error);
    return {
      success: false,
      error: verifyResult.error || 'Token无效'
    };
  }

  // 3. 保存token到localStorage
  saveToken(
    token,
    verifyResult.email || email,
    verifyResult.subscription_type || 'beta'
  );

  console.log('✅ 认证成功！', {
    email: verifyResult.email,
    subscriptionType: verifyResult.subscription_type
  });

  return {
    success: true,
    email: verifyResult.email
  };
}
