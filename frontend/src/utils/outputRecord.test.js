import { describe, expect, it } from 'vitest'
import { isHtmlRecord, outputDownloadName } from './outputRecord'

describe('output record helpers', () => {
    it('detects explicit HTML records', () => {
        expect(isHtmlRecord('html', '<h1>Record</h1>')).toBe(true)
        expect(isHtmlRecord('markdown', '# Record')).toBe(false)
    })

    it('uses the content-derived output filename', () => {
        expect(outputDownloadName('records/audio/2026/09/useful-title_20260916-010203.md', 4, 'markdown'))
            .toBe('useful-title_20260916-010203.md')
    })
})