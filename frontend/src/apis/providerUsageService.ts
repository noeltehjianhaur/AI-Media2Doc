import { ref } from 'vue'
import httpService from './http'
import type { APIResponse, ProviderUsageData } from './types'

export const providerUsage = ref<ProviderUsageData | null>(null)
export const providerUsageLoading = ref(false)
export const providerUsageError = ref('')
export const modelCapabilities = ref<Record<string, Array<{ provider: string; model: string; role: string }>>>({})

let pendingRefresh: Promise<ProviderUsageData> | null = null

export const refreshProviderUsage = (force = false): Promise<ProviderUsageData> => {
    if (pendingRefresh) return pendingRefresh
    providerUsageLoading.value = true
    providerUsageError.value = ''
    pendingRefresh = httpService.request<APIResponse<ProviderUsageData>>({
        url: force ? '/api/v1/provider-usage/refresh' : '/api/v1/provider-usage',
        method: force ? 'POST' : 'GET'
    }).then(response => {
        if (!response.success || !response.data) throw new Error(response.error?.message || 'Provider usage unavailable')
        providerUsage.value = response.data
        return response.data
    }).catch(error => {
        providerUsageError.value = error.message || 'Provider usage unavailable'
        throw error
    }).finally(() => {
        providerUsageLoading.value = false
        pendingRefresh = null
    })
    return pendingRefresh
}

export const refreshModelCapabilities = async () => {
    const response = await httpService.request<APIResponse<Record<string, Array<{ provider: string; model: string; role: string }>>>>({
        url: '/api/v1/provider-usage/models',
        method: 'GET'
    })
    if (response.success && response.data) modelCapabilities.value = response.data
    return modelCapabilities.value
}