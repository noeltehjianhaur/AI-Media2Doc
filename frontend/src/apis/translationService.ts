import httpService from './http'
import { APIResponse } from './types'

export const TARGET_LANGUAGES = [
    { value: '', labelKey: 'settings.language.original' },
    { value: 'English', labelKey: 'settings.language.english' },
    { value: 'Simplified Chinese', labelKey: 'settings.language.chinese' },
    { value: 'Traditional Chinese', labelKey: 'settings.language.traditionalChinese' },
    { value: 'Malay', labelKey: 'settings.language.malay' },
    { value: 'Japanese', labelKey: 'settings.language.japanese' },
    { value: 'Korean', labelKey: 'settings.language.korean' },
    { value: 'Spanish', labelKey: 'settings.language.spanish' },
    { value: 'French', labelKey: 'settings.language.french' },
    { value: 'German', labelKey: 'settings.language.german' }
]

/**
 * 读取用户设置的目标输出语言，空字符串表示保持原始语言
 */
export const getTargetLanguage = (): string => {
    try {
        return localStorage.getItem('targetLanguage') || ''
    } catch {
        return ''
    }
}

export const setTargetLanguage = (value: string): void => {
    try {
        localStorage.setItem('targetLanguage', value)
    } catch { }
}

/**
 * 将转写文本翻译为目标语言
 */
export const translateText = async (
    text: string,
    targetLanguage: string,
    timeout = 120,
    maxTokens = 8192
): Promise<string> => {
    const response = await httpService.request<APIResponse<{ text: string }>>({
        url: '/api/v1/llm/translation',
        method: 'POST',
        data: {
            text,
            target_language: targetLanguage,
            timeout,
            max_tokens: maxTokens
        }
    })

    if (!response.success || !response.data) {
        throw new Error(response.error?.message || 'Translation failed')
    }

    return response.data.text
}
