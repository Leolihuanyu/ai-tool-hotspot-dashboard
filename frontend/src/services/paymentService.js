/**
 * 支付服务 - Stripe支付相关API调用
 */

import { getAuthToken } from '../utils/auth';

// 使用环境变量配置API基础URL
// 开发环境: 通过 Vite proxy 代理到本地 Flask (http://127.0.0.1:8010)
// 生产环境: 直接请求 Render.com 后端
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

/**
 * 创建Stripe Checkout Session
 * @param {string} priceType - 价格类型 ('monthly' | 'yearly')
 * @param {string} email - 用户邮箱（可选，用于预填充）
 * @returns {Promise<Object>} Checkout session信息
 */
export async function createCheckoutSession(priceType = 'monthly', email = null) {
  try {
    const token = getAuthToken();

    // 构建请求头（如果有token则附加，没有则不附加）
    const headers = {
      'Content-Type': 'application/json'
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    // 构建请求体
    const body = { price_type: priceType };
    if (email) {
      body.email = email;
    }

    const response = await fetch(`${API_BASE_URL}/create-checkout-session`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body)
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || '创建支付会话失败');
    }

    return data;
  } catch (error) {
    console.error('创建Checkout Session失败:', error);
    throw error;
  }
}

/**
 * 查询订阅状态（需要认证）
 * @returns {Promise<Object>} 订阅信息
 */
export async function getSubscriptionStatus() {
  try {
    const token = getAuthToken();
    if (!token) {
      return {
        success: false,
        error: '未登录，无法查询订阅状态'
      };
    }

    const response = await fetch(`${API_BASE_URL}/subscription-status`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || '查询订阅状态失败');
    }

    return data;
  } catch (error) {
    console.error('查询订阅状态失败:', error);
    throw error;
  }
}

/**
 * 取消订阅
 * @param {boolean} immediately - 是否立即取消
 * @returns {Promise<Object>} 取消结果
 */
export async function cancelSubscription(immediately = false) {
  try {
    const token = getAuthToken();
    if (!token) {
      throw new Error('未找到认证token');
    }

    const response = await fetch(`${API_BASE_URL}/cancel-subscription`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ immediately })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || '取消订阅失败');
    }

    return data;
  } catch (error) {
    console.error('取消订阅失败:', error);
    throw error;
  }
}

/**
 * 创建客户门户会话
 * @returns {Promise<Object>} 门户会话信息
 */
export async function createPortalSession() {
  try {
    const token = getAuthToken();
    if (!token) {
      throw new Error('未找到认证token');
    }

    const response = await fetch(`${API_BASE_URL}/portal-session`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || '创建门户会话失败');
    }

    return data;
  } catch (error) {
    console.error('创建门户会话失败:', error);
    throw error;
  }
}

/**
 * 重定向到Stripe Checkout
 * @param {string} priceType - 价格类型
 */
export async function redirectToCheckout(priceType) {
  try {
    const session = await createCheckoutSession(priceType);
    if (session.url) {
      window.location.href = session.url;
    } else {
      throw new Error('未收到Checkout URL');
    }
  } catch (error) {
    console.error('跳转到支付页面失败:', error);
    throw error;
  }
}

/**
 * 重定向到Stripe客户门户
 */
export async function redirectToPortal() {
  try {
    const portalSession = await createPortalSession();
    if (portalSession.url) {
      window.location.href = portalSession.url;
    } else {
      throw new Error('未收到Portal URL');
    }
  } catch (error) {
    console.error('跳转到客户门户失败:', error);
    throw error;
  }
}
