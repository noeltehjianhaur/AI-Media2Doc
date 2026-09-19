import { describe, expect, it } from 'vitest'
import { isHtmlRecord, outputDownloadName, prepareHtmlPreview } from './outputRecord'

describe('output record helpers', () => {
    it('detects explicit HTML records', () => {
        expect(isHtmlRecord('html', '<h1>Record</h1>')).toBe(true)
        expect(isHtmlRecord('markdown', '# Record')).toBe(false)
    })

    it('uses the content-derived output filename', () => {
        expect(outputDownloadName('records/audio/2026/09/useful-title_20260916-010203.md', 4, 'markdown'))
            .toBe('useful-title_20260916-010203.md')
    })

    it('inlines the packaged SVG diagram in the standalone preview', () => {
        const preview = prepareHtmlPreview(
            '<img src="diagram.svg" alt="Process flowchart">',
            'records/audio-video/2026/09/demo/index.html',
            { 'records/audio-video/2026/09/demo/diagram.svg': '<svg><text>Flow</text></svg>' }
        )

        expect(preview).toContain('src="data:image/svg+xml;charset=utf-8,')
        expect(preview).not.toContain('src="diagram.svg"')
    })
})