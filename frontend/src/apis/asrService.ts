import httpService from './http'
import { APIResponse, SubmitAsrTaskResponse, QueryASRTaskResponse, AudioTaskResult, ProcessingMode, TaskStatus } from './types'

/**
 * 提交音频处理任务
 * @param audioFileName 音频文件名
 * @returns 任务ID
 */
export const submitAsrTask = async (
  filename: string,
  processingMode: ProcessingMode = 'audio',
  originalName?: string,
  keepSourceMedia = false
): Promise<string> => {
  try {
    const response = await httpService.request<APIResponse<SubmitAsrTaskResponse>>({
      url: '/api/v1/audio/transcription-tasks',
      method: 'POST',
      data: {
        filename,
        processing_mode: processingMode,
        original_name: originalName,
        keep_source_media: keepSourceMedia
      }
    })

    if (!response.success) {
      throw new Error(response.error?.message || '提交音频任务失败')
    }

    return response.data?.task_id || ''
  } catch (error) {
    console.error('提交音频任务失败:', error)
    throw error
  }
}

/**
 * 查询音频处理任务状态
 * @param taskId 任务ID
 * @returns 任务结果和状态
 */
export const queryAsrTask = async (taskId: string): Promise<AudioTaskResult> => {
  try {
    const response = await httpService.request<APIResponse<QueryASRTaskResponse>>({
      url: `/api/v1/audio/transcription-tasks/${taskId}`,
      method: 'GET'
    })

    if (!response.success) {
      throw new Error(response.error?.message || '查询音频任务失败')
    }

    const status = response.data?.status as TaskStatus || 'running'
    let text: Array<Record<string, any>> | null = null
    // 如果任务完成且有结果，拼接所有文本
    if (status === 'finished' && response.data?.result) {
      text = response.data.result
    }

    return {
      text,
      status,
      details: response.data
    }
  } catch (error) {
    console.error('查询音频任务失败:', error)
    throw error
  }
}

export const pollAsrTaskDetails = async (
  taskId: string,
  maxAttempts?: number,
  interval = 3000
): Promise<QueryASRTaskResponse> => {
  const actualMaxAttempts = maxAttempts || getMaxPollingAttempts()
  for (let attempts = 0; attempts < actualMaxAttempts; attempts++) {
    const result = await queryAsrTask(taskId)
    if (result.status === 'finished') return result.details as QueryASRTaskResponse
    if (result.status === 'failed') {
      throw new Error(result.details?.error || 'Transcription failed')
    }
    await new Promise(resolve => setTimeout(resolve, interval))
  }
  throw new Error(`Transcription timed out after ${actualMaxAttempts} attempts`)
}

/**
 * 获取本地存储的最大轮询次数
 * @returns 最大轮询次数
 */
const getMaxPollingAttempts = (): number => {
  try {
    const v = localStorage.getItem('maxPollingAttempts')
    if (v) {
      const n = parseInt(v)
      if (!isNaN(n) && n >= 10) return n
    }
  } catch { }
  return 180 // 默认值：允许 Gemini 暂时繁忙时的后台重试
}

/**
 * 轮询音频处理任务直到完成
 * @param taskId 任务ID
 * @param onProgress 进度回调
 * @param maxAttempts 最大尝试次数，如果不传则从localStorage读取
 * @param interval 轮询间隔(ms)
 * @returns 处理结果文本
 */
export const pollAsrTask = async (
  taskId: string,
  maxAttempts?: number,
  interval = 3000
): Promise<Array<Record<string, any>> | null> => {
  const result = await pollAsrTaskDetails(taskId, maxAttempts, interval)
  return result.result
}
