// 「最近检索」面板的网页标题/内容概述提取工具。
// 数据源是工具执行结果（tool_call_result.content）：
// - 网络搜索类结果条目：不同引擎字段名不一（content/snippet/digest/...），pickSearchSummary 兜底。
// - 网页访问类（execute/curl 抓取）：原始 HTML/文本输出，extractPageTitle / extractPageSummary 解析。

const SCRIPT_STYLE_RE = /<(script|style|noscript|svg)\b[^>]*>[\s\S]*?<\/\1>/gi
const COMMENT_RE = /<!--[\s\S]*?-->/g
const BODY_RE = /<body[^>]*>([\s\S]*?)<\/body>/i
const TAG_RE = /<[^>]+>/g
// 块级标签转换为空格（防止文字粘连）；行内标签（b/i/span/a…）直接删除
const BLOCK_TAG_RE =
  /<\/?(?:p|div|li|ul|ol|dl|dd|dt|h[1-6]|tr|td|th|table|thead|tbody|section|article|header|footer|nav|aside|blockquote|pre|br|hr|form|option)\b[^>]*>/gi
const ENTITY_MAP = {
  amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ',
  '#39': "'", '#x27': "'",
  ldquo: '“', rdquo: '”', lsquo: '‘', rsquo: '’',
  mdash: '—', ndash: '–', hellip: '…', middot: '·', bull: '•',
  laquo: '«', raquo: '»', times: '×', deg: '°', plusmn: '±',
  copy: '©', reg: '®', trade: '™'
}
const ENTITY_RE = /&(amp|lt|gt|quot|apos|nbsp|#39|#x27|ldquo|rdquo|lsquo|rsquo|mdash|ndash|hellip|middot|bull|laquo|raquo|times|deg|plusmn|copy|reg|trade);/gi

const decodeEntities = (text) =>
  text.replace(ENTITY_RE, (_, name) => ENTITY_MAP[name.toLowerCase()] ?? ' ')

const clip = (text, maxLen) => (text.length > maxLen ? `${text.slice(0, maxLen)}…` : text)

const SOURCE_NAMES = [
  [/^(?:www\.)?cae\.cn$/i, '中国工程院'],
  [/^(?:www\.|m\.)?bing\.com$/i, '必应'],
  [/^(?:html\.)?duckduckgo\.com$/i, 'DuckDuckGo'],
  [/^(?:www\.)?baidu\.com$/i, '百度'],
  [/^(?:www\.)?google\.[a-z.]+$/i, 'Google']
]

const cleanExecutionPrefix = (text) =>
  text
    .replace(/^\s*size\s+\d+\s+CTX:\s*/i, '')
    .replace(/^\s*(?:stdout|output|content):\s*/i, '')
    .trim()

/** 标题缺失时生成用户可读名称，避免把完整 URL 和编码查询串当标题。 */
export const formatWebResourceTitle = (url, pageTitle = '') => {
  const normalizedTitle = cleanExecutionPrefix(String(pageTitle || '')).trim()
  if (normalizedTitle && !/^https?:\/\//i.test(normalizedTitle)) return clip(normalizedTitle, 80)

  try {
    const parsed = new URL(url)
    const hostname = parsed.hostname.replace(/^www\./i, '')
    const sourceName = SOURCE_NAMES.find(([pattern]) => pattern.test(parsed.hostname))?.[1] || hostname
    const query = parsed.searchParams.get('q')?.replace(/\s+/g, ' ').trim()
    if (query) return clip(`${sourceName}搜索：${query}`, 80)
    return `${sourceName}网页`
  } catch {
    return '外部网页'
  }
}

/** HTML → 正文文本：剥 script/style/注释，块级标签转空格、行内标签删除，实体解码后压缩空白 */
const stripHtml = (html) =>
  decodeEntities(
    html.replace(SCRIPT_STYLE_RE, ' ').replace(COMMENT_RE, ' ').replace(BLOCK_TAG_RE, ' ').replace(TAG_RE, '')
  )
    .replace(/\s+/g, ' ')
    .trim()

/** 去掉标签/实体后压缩空白，得到正文文本 */
export const extractPageText = (content) => {
  if (typeof content !== 'string' || !content) return ''
  return stripHtml(content)
}

/** 网页标题：优先 <title>，退回 <h1>（script 内出现的伪标签已先剥离）；
// 都取不到返回空串（调用方退回 URL 展示） */
export const extractPageTitle = (content) => {
  if (typeof content !== 'string' || !content) return ''
  const cleaned = content.replace(SCRIPT_STYLE_RE, ' ')
  const patterns = [/<title[^>]*>([\s\S]*?)<\/title>/i, /<h1[^>]*>([\s\S]*?)<\/h1>/i]
  for (const re of patterns) {
    const matched = cleaned.match(re)?.[1]
    if (!matched) continue
    const text = stripHtml(matched)
    if (text) return text
  }
  return ''
}

/** 内容概述：优先取 <body> 内文本（剔除 curl 进度行等 body 外噪音），正文截断 */
export const extractPageSummary = (content, maxLen = 120) => {
  if (typeof content !== 'string' || !content) return ''
  const bodyMatch = content.match(BODY_RE)
  const text = cleanExecutionPrefix(stripHtml(bodyMatch?.[1] ?? content))
  return text ? clip(text, maxLen) : ''
}

/** 网络搜索结果条目的概述：按常见字段名兜底取值 */
export const pickSearchSummary = (item, maxLen = 120) => {
  if (!item || typeof item !== 'object') return ''
  for (const key of ['content', 'snippet', 'digest', 'description', 'summary', 'abstract']) {
    const val = item[key]
    if (typeof val === 'string' && val.trim()) {
      const text = stripHtml(val)
      if (text) return clip(text, maxLen)
    }
  }
  return ''
}

/** execute 类工具结果 content 归一化为文本（JSON 包装时拆常见输出字段） */
export const toolResultContentText = (content) => {
  if (typeof content === 'string') return content
  if (content && typeof content === 'object') {
    for (const key of ['output', 'content', 'text', 'result', 'stdout', 'data']) {
      const val = content[key]
      if (typeof val === 'string' && val) return val
    }
  }
  return ''
}
