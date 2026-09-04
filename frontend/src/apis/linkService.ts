import httpService from './http'
import { APIResponse } from './types'

export interface LinkTaskResponse {
    task_id: string
    filename: string
}

/**
 * 通过视频/网页链接提交转写任务
 * @param url 视频或网页链接
 * @returns 任务ID与生成的音频文件名
 */
export const submitLinkTask = async (url: string): Promise<LinkTaskResponse> => {
    const response = await httpService.request<APIResponse<LinkTaskResponse>>({
        url: '/api/v1/link/transcription-tasks',
        method: 'POST',
        data: { url }
    })

    if (!response.success || !response.data) {
        throw new Error(response.error?.message || 'Failed to transcribe link')
    }

    return response.data
}
