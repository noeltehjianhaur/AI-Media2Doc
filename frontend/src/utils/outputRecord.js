export const isHtmlRecord = (format, content) =>
    format === 'html' || /^\s*<!doctype html/i.test(content || '')

export const outputDownloadName = (outputPath, taskId, format) => {
    const pathName = String(outputPath || '').split('/').filter(Boolean).pop()
    if (pathName) return pathName
    return `record_${taskId}.${format === 'html' ? 'html' : 'md'}`
}

export const prepareHtmlPreview = (html, outputPath, outputFiles) => {
    let preview = html || ''
    const outputDirectory = String(outputPath || '').split('/').slice(0, -1).join('/')
    if (!outputDirectory) return preview

    for (const [path, value] of Object.entries(outputFiles || {})) {
        if (!path.startsWith(`${outputDirectory}/`)) continue
        const relativePath = path.slice(outputDirectory.length + 1)
        if (typeof value === 'object' && value.encoding === 'base64') {
            const extension = path.toLowerCase().endsWith('.png') ? 'png' : 'jpeg'
            preview = preview.replaceAll(
                `src="${relativePath}"`,
                `src="data:image/${extension};base64,${value.content}"`
            )
        } else if (path.toLowerCase().endsWith('.svg')) {
            const dataUri = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(String(value))}`
            preview = preview.replaceAll(`src="${relativePath}"`, `src="${dataUri}"`)
        }
    }
    return preview
}