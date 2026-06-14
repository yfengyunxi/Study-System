import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'

const md = new MarkdownIt({
  html: false,
  breaks: false,
  linkify: true,
  typographer: false
})

// Allow links to open safely
DOMPurify.addHook('afterSanitizeAttributes', (node) => {
  if (node.tagName === 'A') {
    node.setAttribute('target', '_blank')
    node.setAttribute('rel', 'noopener noreferrer')
  }
})

export function renderMarkdown(source) {
  if (!source || typeof source !== 'string') return ''
  const html = md.render(source)
  return DOMPurify.sanitize(html)
}

export default renderMarkdown
