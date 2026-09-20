import assert from 'node:assert/strict'
import test from 'node:test'

import {
  extractPageSummary,
  formatWebResourceTitle
} from '../../src/utils/retrievalExtract.js'

test('formats known sources without exposing raw URLs', () => {
  assert.equal(
    formatWebResourceTitle('https://www.cae.cn/cae/html/main/col248/column_248_1.html'),
    '中国工程院网页'
  )
})

test('decodes search queries into readable titles', () => {
  assert.equal(
    formatWebResourceTitle('https://m.bing.com/search?q=%E9%99%A2%E5%A3%AB%E5%90%8D%E5%8D%95'),
    '必应搜索：院士名单'
  )
})

test('keeps a parsed page title ahead of the URL fallback', () => {
  assert.equal(formatWebResourceTitle('https://example.com/a', '院士馆'), '院士馆')
})

test('removes execution metadata from page summaries', () => {
  assert.equal(extractPageSummary('size 34996 CTX: 中国工程院 | 院士名单'), '中国工程院 | 院士名单')
})
