import { NavLink } from 'react-router-dom';
import { Home, Wrench, TrendingUp, Target, ArrowUp } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { cn } from '../lib/utils';

/**
 * 移动端底部导航栏
 * 只在小屏幕（<768px）显示
 */
export default function MobileNav() {
  const [showScrollTop, setShowScrollTop] = useState(false);
  const { t } = useTranslation();

  // 监听滚动位置，决定是否显示返回顶部按钮
  useEffect(() => {
    const handleScroll = () => {
      setShowScrollTop(window.scrollY > 500);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // 返回顶部
  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  };

  const navItems = [
    {
      path: '/dashboard',
      icon: Home,
      label: t('mobile.home')
    },
    {
      path: '/dashboard/tools',
      icon: Wrench,
      label: t('mobile.tools')
    },
    {
      path: '/dashboard/trends',
      icon: TrendingUp,
      label: t('mobile.trends')
    },
    {
      path: '/dashboard/opportunities',
      icon: Target,
      label: t('mobile.opportunities')
    }
  ];

  return (
    <>
      {/* 移动端底部导航栏 */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-slate-900/95 backdrop-blur-lg border-t border-white/10 safe-area-inset-bottom">
        <div className="flex items-center justify-around px-2 py-2">
          {navItems.map(({ path, icon: Icon, label }) => (
            <NavLink
              key={path}
              to={path}
              className={({ isActive }) =>
                cn(
                  "flex flex-col items-center justify-center gap-1 px-3 py-2 rounded-lg transition-all touch-target touch-feedback",
                  isActive
                    ? "text-primary-400 bg-primary-500/20"
                    : "text-slate-400 hover:text-slate-300"
                )
              }
            >
              {({ isActive }) => (
                <>
                  <Icon className={cn("w-5 h-5", isActive && "text-primary-400")} />
                  <span className="text-xs font-medium">{label}</span>
                </>
              )}
            </NavLink>
          ))}
        </div>
      </nav>

      {/* 返回顶部按钮（移动端和桌面端都显示） */}
      {showScrollTop && (
        <button
          onClick={scrollToTop}
          className="fixed bottom-20 md:bottom-8 right-4 z-40 p-3 bg-primary-500/90 hover:bg-primary-600/90 text-white rounded-full shadow-lg transition-all touch-target touch-feedback"
          aria-label={t('mobile.backToTop')}
        >
          <ArrowUp className="w-5 h-5" />
        </button>
      )}

      {/* 为底部导航栏预留空间（仅移动端） */}
      <div className="md:hidden h-16" aria-hidden="true"></div>
    </>
  );
}
