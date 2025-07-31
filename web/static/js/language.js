/**
 * 语言切换和多语言相关的工具函数
 * Language switching and i18n utility functions
 */

/**
 * 处理语言切换
 */
async function handleLanguageChange(newLanguage) {
    try {
        // 显示加载状态
        const languageSelect = document.getElementById('languageSelect');
        if (languageSelect) {
            languageSelect.disabled = true;
        }

        // 切换语言
        await window.i18n.setLanguage(newLanguage);
        
        // 更新语言选择器的值
        updateLanguageSelector(newLanguage);
        
        // 触发其他需要响应语言变化的功能
        onLanguageChanged(newLanguage);

    } catch (error) {
        console.error('Language switch failed:', error);
        showError(window.i18n ? window.i18n.t('messages.error_occurred') : 'An error occurred');
    } finally {
        // 恢复语言选择器
        const languageSelect = document.getElementById('languageSelect');
        if (languageSelect) {
            languageSelect.disabled = false;
        }
    }
}

/**
 * 更新语言选择器的当前值
 */
function updateLanguageSelector(language) {
    const languageSelect = document.getElementById('languageSelect');
    if (languageSelect && languageSelect.value !== language) {
        languageSelect.value = language;
    }
}

/**
 * 语言变化时的回调处理
 */
function onLanguageChanged(newLanguage) {
    // 更新动态生成的内容
    updateDynamicContent();
    
    // 更新select选项的翻译
    updateSelectOptions();
    
    // 重新渲染clips如果已经加载
    if (window.clips && window.clips.length > 0) {
        renderClips(window.clips);
    }
    
    // 触发自定义事件，让其他模块监听
    document.dispatchEvent(new CustomEvent('app:languageChanged', {
        detail: { language: newLanguage }
    }));
}

/**
 * 更新select选项的翻译
 */
function updateSelectOptions() {
    // 更新类型过滤器
    const typeFilter = document.getElementById('typeFilter');
    if (typeFilter) {
        const options = typeFilter.querySelectorAll('option');
        options.forEach(option => {
            const i18nKey = option.getAttribute('data-i18n');
            if (i18nKey) {
                option.textContent = window.i18n.t(i18nKey);
            }
        });
    }

    // 更新排序过滤器
    const sortFilter = document.getElementById('sortFilter');
    if (sortFilter) {
        const options = sortFilter.querySelectorAll('option');
        options.forEach(option => {
            const i18nKey = option.getAttribute('data-i18n');
            if (i18nKey) {
                option.textContent = window.i18n.t(i18nKey);
            }
        });
    }
}

/**
 * 更新动态生成的内容
 */
function updateDynamicContent() {
    // 更新模态框标题（如果正在显示）
    const modal = document.getElementById('clipModal');
    if (modal && modal.style.display !== 'none') {
        const modalTitle = document.getElementById('modalTitle');
        if (modalTitle) {
            const isEdit = modalTitle.getAttribute('data-editing') === 'true';
            const titleKey = isEdit ? 'modal.edit_title' : 'modal.create_title';
            modalTitle.textContent = window.i18n.t(titleKey);
        }
    }

    // 更新用户信息显示
    updateUserInfoDisplay();
}

/**
 * 更新用户信息显示
 */
function updateUserInfoDisplay() {
    const userInfo = document.getElementById('userInfo');
    if (userInfo && window.currentUser) {
        const userName = userInfo.querySelector('.user-name');
        const userStatus = userInfo.querySelector('.user-status');
        
        if (userName && userStatus) {
            if (window.isAnonymous || !window.currentUser.username) {
                userName.textContent = window.i18n.t('user.anonymous');
                userStatus.textContent = window.i18n.t('user.limited_features');
            } else {
                userName.textContent = window.currentUser.full_name || window.currentUser.username;
                userStatus.textContent = window.currentUser.email || '';
            }
        }
    }
}

/**
 * 初始化语言选择器
 */
function initializeLanguageSelector() {
    const languageSelect = document.getElementById('languageSelect');
    if (languageSelect) {
        // 设置当前语言
        const currentLanguage = window.i18n ? window.i18n.getCurrentLanguage() : 'en';
        languageSelect.value = currentLanguage;
        
        // 监听语言变化事件
        window.addEventListener('languageChanged', (event) => {
            updateLanguageSelector(event.detail.language);
        });
    }
}

/**
 * 获取本地化的时间格式
 */
function getLocalizedTimeFormat(date) {
    if (!window.i18n) return new Date(date).toLocaleDateString();
    return window.i18n.formatDate(date);
}

/**
 * 获取本地化的时间差显示
 */
function getLocalizedTimeAgo(date) {
    if (!window.i18n) return 'some time ago';
    return window.i18n.formatTimeAgo(date);
}

/**
 * 获取本地化的文件大小显示
 */
function getLocalizedFileSize(bytes) {
    if (!window.i18n) return `${bytes} B`;
    return window.i18n.formatFileSize(bytes);
}

/**
 * 获取本地化的数字格式
 */
function getLocalizedNumber(number) {
    if (!window.i18n) return number.toString();
    return window.i18n.formatNumber(number);
}

/**
 * 显示本地化的确认对话框
 */
function showLocalizedConfirm(messageKey, interpolations = {}) {
    const message = window.i18n ? window.i18n.t(messageKey, interpolations) : messageKey;
    return confirm(message);
}

/**
 * 显示本地化的提示消息
 */
function showLocalizedAlert(messageKey, interpolations = {}) {
    const message = window.i18n ? window.i18n.t(messageKey, interpolations) : messageKey;
    alert(message);
}

/**
 * 在DOM加载完成后初始化语言相关功能
 */
document.addEventListener('DOMContentLoaded', function() {
    // 等待i18n初始化完成后再初始化语言选择器
    if (window.i18n) {
        initializeLanguageSelector();
    } else {
        // 如果i18n还没有初始化，等待一下
        setTimeout(() => {
            if (window.i18n) {
                initializeLanguageSelector();
            }
        }, 100);
    }
}); 