export const isHtmlRecord = (format, content) =>
    format === 'html' || /^\s*<!doctype html/i.test(content || '')

export const outputDownloadName = (outputPath, taskId, format) => {
    const pathName = String(outputPath || '').split('/').filter(Boolean).pop()
    if (pathName) return pathName
    return `record_${taskId}.${format === 'html' ? 'html' : 'md'}`
}