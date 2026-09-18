import httpService from './http'
import type { APIResponse, ProcessingMode } from './types'

export interface OutputRecordResponse {
    title: string
    output_path: string
    files: Record<string, string>
    manifest: Record<string, any>
    publication: Record<string, any> | null
}

export const createOutputRecord = async (payload: {
    processingMode: ProcessingMode
    transcript: any
    generatedContent: string
    metadata: Record<string, any>
    visualAnalysis?: Record<string, any> | null
    screenshots?: Array<{ timestamp: number; data_url: string }>
    publish?: boolean
}): Promise<OutputRecordResponse> => {
    const response = await httpService.request<APIResponse<OutputRecordResponse>>({
        url: '/api/v1/records',
        method: 'POST',
        data: {
            processing_mode: payload.processingMode,
            transcript: payload.transcript,
            generated_content: payload.generatedContent,
            metadata: payload.metadata,
            visual_analysis: payload.visualAnalysis,
            screenshots: payload.screenshots || [],
            publish: payload.publish || false
        }
    })
    if (!response.success || !response.data) {
        throw new Error(response.error?.message || 'Failed to create output record')
    }
    return response.data
}

export const publishOutputRecord = async (title: string, files: Record<string, any>) => {
    const response = await httpService.request<APIResponse<Record<string, any>>>({
        url: '/api/v1/records/publish',
        method: 'POST',
        data: { title, files }
    })
    if (!response.success || !response.data) throw new Error(response.error?.message || 'Publication failed')
    return response.data
}