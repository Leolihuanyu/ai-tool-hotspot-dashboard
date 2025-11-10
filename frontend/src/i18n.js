import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import enTranslation from './locales/en/translation.json';
import jaTranslation from './locales/ja/translation.json';
import zhTranslation from './locales/zh/translation.json';

// 语言资源
const resources = {
  en: {
    translation: enTranslation
  },
  ja: {
    translation: jaTranslation
  },
  zh: {
    translation: zhTranslation
  }
};

// 从URL参数获取语言
const getLanguageFromURL = () => {
  const params = new URLSearchParams(window.location.search);
  const langParam = params.get('lang');
  if (langParam && ['en', 'ja', 'zh'].includes(langParam)) {
    return langParam;
  }
  return null;
};

// 从localStorage获取语言
const getLanguageFromStorage = () => {
  return localStorage.getItem('language');
};

// 保存语言到localStorage
const saveLanguageToStorage = (lang) => {
  localStorage.setItem('language', lang);
};

// 确定初始语言（优先级：URL参数 > localStorage > 浏览器语言 > 默认英文）
const getInitialLanguage = () => {
  // 1. 优先使用URL参数
  const urlLang = getLanguageFromURL();
  if (urlLang) {
    saveLanguageToStorage(urlLang);
    return urlLang;
  }

  // 2. 使用localStorage中保存的语言
  const storedLang = getLanguageFromStorage();
  if (storedLang) {
    return storedLang;
  }

  // 3. 使用浏览器语言（降级）
  const browserLang = navigator.language || navigator.userLanguage;
  if (browserLang) {
    if (browserLang.startsWith('zh')) return 'zh';
    if (browserLang.startsWith('ja')) return 'ja';
    if (browserLang.startsWith('en')) return 'en';
  }

  // 4. 默认英文
  return 'en';
};

i18n
  // 加载语言检测插件
  .use(LanguageDetector)
  // 传递i18n实例给react-i18next
  .use(initReactI18next)
  // 初始化i18next
  .init({
    resources,
    lng: getInitialLanguage(), // 初始语言
    fallbackLng: 'en', // 降级语言
    load: 'languageOnly', // 只加载语言代码，不加载区域代码（如 'en' 而非 'en-US'）

    // 语言检测配置
    detection: {
      order: ['querystring', 'localStorage', 'navigator'],
      lookupQuerystring: 'lang',
      lookupLocalStorage: 'language',
      caches: ['localStorage'],
    },

    interpolation: {
      escapeValue: false, // React已经处理了XSS
    },

    react: {
      useSuspense: false, // 禁用Suspense以避免加载问题
    },
  });

// 监听语言变化，同步到localStorage和URL
i18n.on('languageChanged', (lng) => {
  saveLanguageToStorage(lng);

  // 更新URL参数（但不刷新页面）
  const url = new URL(window.location);
  url.searchParams.set('lang', lng);
  window.history.replaceState({}, '', url);
});

export default i18n;
