import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { useEffect } from 'react';
import Layout from './components/Layout';
import Home from './pages/Home';
import Tools from './pages/Tools';
import Trends from './pages/Trends';
import Opportunities from './pages/Opportunities';
import Expired from './pages/Expired';
import Invite from './pages/Invite';
import InviteCodeInput from './pages/InviteCodeInput';
import Pricing from './pages/Pricing';
import Landing from './pages/Landing';
import CheckoutSuccess from './pages/CheckoutSuccess';
import CheckoutCancelled from './pages/CheckoutCancelled';
import { handleAuthFlow, isAuthenticated } from './utils/auth';

/**
 * 认证包装组件 - 处理token验证逻辑
 */
function AuthWrapper({ children }) {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const checkAuth = async () => {
      // 检查URL中是否有token参数
      const urlParams = new URLSearchParams(location.search);
      const hasTokenInUrl = urlParams.has('token') && urlParams.has('email');

      if (hasTokenInUrl) {
        // URL中有token，执行认证流程
        console.log('🔐 执行认证流程...');
        const result = await handleAuthFlow();

        if (!result.success) {
          // 认证失败，跳转到过期页面
          console.error('❌ 认证失败，跳转到过期页面');
          navigate(`/access-expired?error=${encodeURIComponent(result.error || '认证失败')}`);
          return;
        }

        // 认证成功，清除URL中的token参数（避免token泄露在浏览器历史中）
        console.log('✅ 认证成功，清除URL参数');
        urlParams.delete('token');
        urlParams.delete('email');
        const newUrl = `${location.pathname}${urlParams.toString() ? '?' + urlParams.toString() : ''}`;
        navigate(newUrl, { replace: true });
      } else {
        // URL中没有token，检查localStorage中是否有有效token
        if (!isAuthenticated()) {
          // 没有有效token，跳转到过期页面
          console.warn('⚠️  未找到有效的访问token，跳转到过期页面');
          navigate('/access-expired?error=' + encodeURIComponent('未提供访问token或token已过期'));
        } else {
          // 有有效token，允许访问
          console.log('✅ 发现有效token，允许访问');
        }
      }
    };

    // 只在非过期页面、非邀请页面、非定价页面、非支付页面和非Landing页面执行认证检查
    const publicPaths = ['/access-expired', '/invite', '/invite-register', '/pricing', '/checkout/success', '/checkout/cancelled', '/'];
    if (!publicPaths.includes(location.pathname)) {
      checkAuth();
    }
  }, [location, navigate]);

  return children;
}

/**
 * 应用主组件 - 配置路由和认证
 */
function App() {
  return (
    <BrowserRouter>
      <AuthWrapper>
        <Routes>
          {/* Landing Page - 公开首页 */}
          <Route path="/" element={<Landing />} />

          {/* Dashboard - 需要认证 */}
          <Route path="/dashboard" element={<Layout />}>
            <Route index element={<Home />} />
            <Route path="tools" element={<Tools />} />
            <Route path="trends" element={<Trends />} />
            <Route path="opportunities" element={<Opportunities />} />
          </Route>

          {/* 访问过期/无效提示页面（不需要Layout包裹） */}
          <Route path="/access-expired" element={<Expired />} />
          {/* 邀请码输入页面（不需要Layout包裹） */}
          <Route path="/invite-register" element={<InviteCodeInput />} />
          {/* 邀请注册页面（不需要Layout包裹） */}
          <Route path="/invite" element={<Invite />} />
          {/* 定价页面（不需要认证） */}
          <Route path="/pricing" element={<Pricing />} />
          {/* 支付成功页面（不需要认证） */}
          <Route path="/checkout/success" element={<CheckoutSuccess />} />
          {/* 支付取消页面（不需要认证） */}
          <Route path="/checkout/cancelled" element={<CheckoutCancelled />} />

          {/* 重定向旧路径到新路径 */}
          <Route path="/tools" element={<Navigate to="/dashboard/tools" replace />} />
          <Route path="/trends" element={<Navigate to="/dashboard/trends" replace />} />
          <Route path="/opportunities" element={<Navigate to="/dashboard/opportunities" replace />} />
        </Routes>
      </AuthWrapper>
    </BrowserRouter>
  );
}

export default App;
