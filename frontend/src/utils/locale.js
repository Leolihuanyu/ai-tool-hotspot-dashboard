/**
 * 语言和时区检测工具函数
 */

/**
 * 获取用户浏览器的真实时区
 * @returns {string} IANA时区名称，例如 'Asia/Shanghai', 'America/New_York'
 */
export function getUserTimezone() {
  try {
    // 使用 Intl API 获取浏览器的时区设置
    return Intl.DateTimeFormat().resolvedOptions().timeZone;
  } catch (error) {
    console.warn('无法获取用户时区，使用默认值 UTC:', error);
    return 'UTC';
  }
}

/**
 * 获取当前界面语言
 * 注意：此函数应该在组件中使用 i18n.language，这里提供备用方案
 * @returns {string} 语言代码，例如 'zh', 'en', 'ja'
 */
export function getCurrentLanguage() {
  try {
    // 优先从 localStorage 读取 i18next 保存的语言
    const savedLanguage = localStorage.getItem('i18nextLng');
    if (savedLanguage) {
      return savedLanguage;
    }

    // 降级到浏览器语言
    const browserLang = navigator.language.split('-')[0];
    return browserLang || 'en';
  } catch (error) {
    console.warn('无法获取用户语言，使用默认值 en:', error);
    return 'en';
  }
}

/**
 * 根据语言推断默认时区（降级方案）
 * @param {string} language - 语言代码
 * @returns {string} IANA时区名称
 */
export function inferTimezoneFromLanguage(language) {
  const timezoneMap = {
    'zh': 'Asia/Shanghai',
    'ja': 'Asia/Tokyo',
    'en': 'UTC'
  };
  return timezoneMap[language] || 'UTC';
}
