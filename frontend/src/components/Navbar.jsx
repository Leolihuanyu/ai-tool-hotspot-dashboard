import { Link, useLocation } from 'react-router-dom';
import { Home, Sparkles, TrendingUp, Target } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { cn } from '../lib/utils';
import LanguageSwitcher from './LanguageSwitcher';

/**
 * 导航栏组件
 */
export default function Navbar() {
  const location = useLocation();
  const { t } = useTranslation();

  const navItems = [
    { path: '/dashboard', label: t('nav.home'), icon: Home },
    { path: '/dashboard/tools', label: t('nav.tools'), icon: Sparkles },
    { path: '/dashboard/trends', label: t('nav.trends'), icon: TrendingUp },
    { path: '/dashboard/opportunities', label: t('nav.opportunities'), icon: Target },
  ];

  // 判断是否在 Dashboard 内
  const isDashboard = location.pathname.startsWith('/dashboard');
  const logoPath = isDashboard ? '/dashboard' : '/';

  return (
    <nav className="sticky top-0 z-50 glass-card border-b border-white/10">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to={logoPath} className="flex items-center gap-2 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center group-hover:scale-110 transition-transform">
              <Sparkles className="w-5 h-5" />
            </div>
            <span className="font-bold text-xl hidden sm:block">{t('nav.brand')}</span>
          </Link>

          {/* 导航链接 */}
          <div className="flex items-center gap-1">
            {navItems.map(item => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;

              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={cn(
                    "flex items-center gap-2 px-4 py-2 rounded-lg transition-all",
                    isActive
                      ? "bg-gradient-to-r from-primary-500/20 to-accent-500/20 text-white"
                      : "text-slate-400 hover:text-white hover:bg-white/5"
                  )}
                >
                  <Icon className="w-4 h-4" />
                  <span className="hidden sm:inline">{item.label}</span>
                </Link>
              );
            })}

            {/* 语言切换器 */}
            <LanguageSwitcher />
          </div>
        </div>
      </div>
    </nav>
  );
}
