import { createI18n } from 'vue-i18n'
import en from './en'
import zh from './zh'

export const SUPPORTED_LOCALES = [
    { value: 'zh', label: '简体中文' },
    { value: 'en', label: 'English' }
]

const STORAGE_KEY = 'displayLanguage'

export const getStoredLocale = () => {
    try {
        const stored = localStorage.getItem(STORAGE_KEY)
        if (stored && SUPPORTED_LOCALES.some(item => item.value === stored)) return stored
    } catch { }
    return navigator.language?.toLowerCase().startsWith('zh') ? 'zh' : 'en'
}

const i18n = createI18n({
    legacy: false,
    globalInjection: true,
    locale: getStoredLocale(),
    fallbackLocale: 'en',
    messages: { en, zh }
})

export const setLocale = (locale) => {
    i18n.global.locale.value = locale
    try {
        localStorage.setItem(STORAGE_KEY, locale)
    } catch { }
    document.documentElement.lang = locale === 'zh' ? 'zh-CN' : 'en'
}

setLocale(i18n.global.locale.value)

// Allows non-component modules (API services) to translate messages.
export const t = (key, params) => i18n.global.t(key, params)

export default i18n
