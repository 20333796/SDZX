// 跨线程的检索记录本地缓存：切换线程/新开对话后「最近检索」仍有内容。
// 只在浏览器本地存储，上限 100 条，FIFO 淘汰。
const STORAGE_KEY = 'agent-retrieval-records-v1'
const RETRIEVAL_CACHE_LIMIT = 100

export const loadCachedRetrievalRecords = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    const list = raw ? JSON.parse(raw) : []
    return Array.isArray(list) ? list : []
  } catch {
    return []
  }
}

export const saveCachedRetrievalRecords = (records) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(records.slice(0, RETRIEVAL_CACHE_LIMIT)))
  } catch {
    /* 存储满/不可用时静默放弃，缓存仅是增强功能 */
  }
}

/**
 * 把当前线程提取到的检索记录合并进缓存（按 key 去重，新记录带时间戳）。
 * @param {Array} records 当前线程的检索记录（key 唯一）
 * @param {{threadId: string, threadTitle: string}} context 线程上下文
 * @returns {Array} 合并后的缓存列表（savedAt 降序，已截断）
 */
export const mergeRetrievalRecordsIntoCache = (records, { threadId, threadTitle }) => {
  const byKey = new Map(loadCachedRetrievalRecords().map((rec) => [rec.key, rec]))
  for (const rec of [...(records || [])].reverse()) {
    if (!rec?.key || byKey.has(rec.key)) continue
    byKey.set(rec.key, {
      ...rec,
      threadId: threadId || '',
      threadTitle: threadTitle || '',
      savedAt: Date.now()
    })
  }
  const next = [...byKey.values()]
    .sort((a, b) => (b.savedAt || 0) - (a.savedAt || 0))
    .slice(0, RETRIEVAL_CACHE_LIMIT)
  saveCachedRetrievalRecords(next)
  return next
}
