/**
 * 轻量级国际化引擎
 * Lightweight i18n engine for CLIP.LRU
 */
class I18n {
    constructor() {
        this.currentLanguage = 'en';
        this.translations = {};
        this.supportedLanguages = ['en', 'zh-CN'];
        this.fallbackLanguage = 'en';
        
        // 初始化
        this.init();
    }

    async init() {
        // 检测语言偏好
        const preferredLanguage = this.detectLanguage();
        await this.setLanguage(preferredLanguage);
        
        // 更新页面语言属性
        document.documentElement.lang = this.currentLanguage;
    }

    /**
     * 检测用户首选语言
     */
    detectLanguage() {
        // 1. 检查本地存储
        const storedLanguage = localStorage.getItem('preferred_language');
        if (storedLanguage && this.supportedLanguages.includes(storedLanguage)) {
            return storedLanguage;
        }

        // 2. 检查浏览器语言设置
        const browserLanguage = navigator.language || navigator.userLanguage;
        
        // 直接匹配
        if (this.supportedLanguages.includes(browserLanguage)) {
            return browserLanguage;
        }

        // 匹配语言代码（忽略地区）
        const languageCode = browserLanguage.split('-')[0];
        const matchedLanguage = this.supportedLanguages.find(lang => 
            lang.startsWith(languageCode)
        );
        
        if (matchedLanguage) {
            return matchedLanguage;
        }

        // 3. 中文检测特殊处理
        if (browserLanguage.toLowerCase().includes('zh')) {
            return 'zh-CN';
        }

        // 4. 默认返回英文
        return this.fallbackLanguage;
    }

    /**
     * 加载翻译文件
     */
    async loadTranslations(language) {
        try {
            const response = await fetch(`/static/locales/${language}.json`);
            if (!response.ok) {
                throw new Error(`Failed to load translations for ${language}`);
            }
            
            const translations = await response.json();
            this.translations[language] = translations;
            return translations;
        } catch (error) {
            console.warn(`Failed to load translations for ${language}:`, error);
            
            // 如果加载失败且不是fallback语言，尝试加载fallback
            if (language !== this.fallbackLanguage) {
                return await this.loadTranslations(this.fallbackLanguage);
            }
            
            // 返回空对象作为最后的fallback
            return {};
        }
    }

    /**
     * 设置语言
     */
    async setLanguage(language) {
        if (!this.supportedLanguages.includes(language)) {
            console.warn(`Unsupported language: ${language}, fallback to ${this.fallbackLanguage}`);
            language = this.fallbackLanguage;
        }

        // 加载翻译文件（如果还没有加载）
        if (!this.translations[language]) {
            await this.loadTranslations(language);
        }

        this.currentLanguage = language;
        
        // 保存到本地存储
        localStorage.setItem('preferred_language', language);
        
        // 更新HTML lang属性
        document.documentElement.lang = language;
        
        // 触发语言变更事件
        this.onLanguageChange();
    }

    /**
     * 获取翻译文本
     */
    t(key, interpolations = {}) {
        const keys = key.split('.');
        let translation = this.translations[this.currentLanguage];
        
        // 遍历嵌套的key
        for (const k of keys) {
            if (translation && typeof translation === 'object' && k in translation) {
                translation = translation[k];
            } else {
                // 如果当前语言没有找到，尝试fallback语言
                if (this.currentLanguage !== this.fallbackLanguage) {
                    return this.getFallbackTranslation(key, interpolations);
                }
                
                // 最终fallback：返回key本身
                console.warn(`Missing translation for key: ${key}`);
                return key;
            }
        }

        // 如果translation不是字符串，返回key
        if (typeof translation !== 'string') {
            console.warn(`Invalid translation type for key: ${key}`);
            return key;
        }

        // 处理插值
        return this.interpolate(translation, interpolations);
    }

    /**
     * 获取fallback翻译
     */
    getFallbackTranslation(key, interpolations = {}) {
        const keys = key.split('.');
        let translation = this.translations[this.fallbackLanguage];
        
        for (const k of keys) {
            if (translation && typeof translation === 'object' && k in translation) {
                translation = translation[k];
            } else {
                console.warn(`Missing translation for key: ${key} in fallback language`);
                return key;
            }
        }

        if (typeof translation !== 'string') {
            return key;
        }

        return this.interpolate(translation, interpolations);
    }

    /**
     * 字符串插值
     */
    interpolate(template, values = {}) {
        return template.replace(/\{\{(\w+)\}\}/g, (match, key) => {
            return values.hasOwnProperty(key) ? values[key] : match;
        });
    }

    /**
     * 格式化相对时间
     */
    formatTimeAgo(date) {
        const now = new Date();
        const diff = now - new Date(date);
        const minutes = Math.floor(diff / (1000 * 60));
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));

        if (days > 0) {
            return this.t('clips.time_ago.days', { count: days });
        } else if (hours > 0) {
            return this.t('clips.time_ago.hours', { count: hours });
        } else {
            return this.t('clips.time_ago.minutes', { count: Math.max(1, minutes) });
        }
    }

    /**
     * 格式化日期
     */
    formatDate(date) {
        const dateObj = new Date(date);
        return new Intl.DateTimeFormat(this.currentLanguage, {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(dateObj);
    }

    /**
     * 格式化数字
     */
    formatNumber(number) {
        return new Intl.NumberFormat(this.currentLanguage).format(number);
    }

    /**
     * 格式化文件大小
     */
    formatFileSize(bytes) {
        const units = this.currentLanguage === 'zh-CN' 
            ? ['字节', 'KB', 'MB', 'GB'] 
            : ['B', 'KB', 'MB', 'GB'];
        
        let size = bytes;
        let unitIndex = 0;
        
        while (size >= 1024 && unitIndex < units.length - 1) {
            size /= 1024;
            unitIndex++;
        }
        
        const formattedSize = unitIndex === 0 
            ? size.toString() 
            : size.toFixed(1);
            
        return `${formattedSize} ${units[unitIndex]}`;
    }

    /**
     * 语言变更回调
     */
    onLanguageChange() {
        // 更新所有带有 data-i18n 属性的元素
        this.updatePageTranslations();
        
        // 触发自定义事件
        window.dispatchEvent(new CustomEvent('languageChanged', {
            detail: { 
                language: this.currentLanguage,
                translations: this.translations[this.currentLanguage]
            }
        }));
    }

    /**
     * 更新页面翻译
     */
    updatePageTranslations() {
        // 更新所有具有 data-i18n 属性的元素
        const elements = document.querySelectorAll('[data-i18n]');
        elements.forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.t(key);
            
            // 更新文本内容
            if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                if (element.hasAttribute('placeholder')) {
                    element.placeholder = translation;
                } else {
                    element.value = translation;
                }
            } else {
                element.textContent = translation;
            }
        });

        // 更新所有具有 data-i18n-attr 属性的元素
        const attrElements = document.querySelectorAll('[data-i18n-attr]');
        attrElements.forEach(element => {
            const attrConfig = element.getAttribute('data-i18n-attr');
            try {
                const config = JSON.parse(attrConfig);
                Object.entries(config).forEach(([attr, key]) => {
                    element.setAttribute(attr, this.t(key));
                });
            } catch (error) {
                console.warn('Invalid data-i18n-attr format:', attrConfig);
            }
        });
    }

    /**
     * 获取当前语言
     */
    getCurrentLanguage() {
        return this.currentLanguage;
    }

    /**
     * 获取支持的语言列表
     */
    getSupportedLanguages() {
        return this.supportedLanguages;
    }

    /**
     * 检查是否为RTL语言
     */
    isRTL() {
        const rtlLanguages = ['ar', 'he', 'fa'];
        return rtlLanguages.some(lang => this.currentLanguage.startsWith(lang));
    }
}

// 创建全局i18n实例
window.i18n = new I18n();

// 导出常用方法到全局作用域（为了向后兼容）
window.t = (key, interpolations) => window.i18n.t(key, interpolations);
window.setLanguage = (language) => window.i18n.setLanguage(language);
window.getCurrentLanguage = () => window.i18n.getCurrentLanguage();

// 当DOM加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        // DOM已加载，i18n会在构造函数中自动初始化
    });
} else {
    // DOM已经加载完成
    // i18n会在构造函数中自动初始化
} 