import { describe, expect, it } from 'vitest'
import { renderMarkdown } from './renderMarkdown'

describe('renderMarkdown', () => {
  it('renders bold text', () => {
    const html = renderMarkdown('**bold**')
    expect(html).toContain('<strong>bold</strong>')
  })

  it('renders lists', () => {
    const html = renderMarkdown('- item')
    expect(html).toContain('<li>item</li>')
  })

  it('renders inline code', () => {
    const html = renderMarkdown('`code`')
    expect(html).toContain('<code>code</code>')
  })

  it('escapes script tags', () => {
    const html = renderMarkdown('<script>alert("xss")</script>')
    // raw HTML is escaped by markdown-it (html:false), safe by design
    expect(html).not.toContain('<script>')
    expect(html).toContain('&lt;script&gt;')
  })

  it('escapes img onerror handler', () => {
    const html = renderMarkdown('<img src=x onerror="alert(1)">')
    expect(html).not.toContain('<img ')
    expect(html).toContain('&lt;img')
  })

  it('blocks javascript: links', () => {
    // markdown-it does not recognise javascript: as a valid link scheme
    const html = renderMarkdown('[click](javascript:alert(1))')
    expect(html).not.toContain('href')
  })

  it('removes iframe', () => {
    const html = renderMarkdown('<iframe src="http://evil.com"></iframe>')
    expect(html).not.toContain('<iframe>')
  })

  it('removes style injection', () => {
    const html = renderMarkdown('<style>body{display:none}</style>')
    expect(html).not.toContain('<style>')
  })

  it('adds target and rel to safe external links', () => {
    const html = renderMarkdown('[safe](https://example.com)')
    expect(html).toContain('target="_blank"')
    expect(html).toContain('rel="noopener noreferrer"')
  })

  it('handles empty input', () => {
    expect(renderMarkdown('')).toBe('')
    expect(renderMarkdown(null)).toBe('')
  })
})
