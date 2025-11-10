import { Outlet } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Navbar from './Navbar';
import MobileNav from './MobileNav';

/**
 * 布局组件 - 包含导航栏和页面内容
 */
export default function Layout() {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen relative">
      {/* 背景装饰 */}
      <div className="fixed inset-0 -z-10 overflow-hidden">
        {/* 渐变球体 */}
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary-500/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-accent-500/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>

        {/* 网格背景 */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>
      </div>

      {/* 导航栏 */}
      <Navbar />

      {/* 主要内容 */}
      <main className="container mx-auto px-4 py-8 pb-20 md:pb-8">
        <Outlet />
      </main>

      {/* 页脚 */}
      <footer className="border-t border-white/10 mt-16 py-8 mb-16 md:mb-0">
        <div className="container mx-auto px-4 text-center text-slate-500 text-sm">
          <p>{t('landing.footer.copyright')}</p>
        </div>
      </footer>

      {/* 移动端底部导航栏 */}
      <MobileNav />
    </div>
  );
}
