<template>
  <aside class="retrieval-panel">
    <!-- 列表视图 -->
    <template v-if="!browsingUrl">
      <div class="retrieval-panel__header">
        <span class="retrieval-panel__title">最近检索</span>
        <button
          type="button"
          class="retrieval-panel__close"
          title="关闭"
          aria-label="关闭最近检索面板"
          @click.stop="emit('close')"
        >
          <X :size="14" />
        </button>
      </div>

      <div class="retrieval-panel__body">
        <!-- 最近检索（仅网络搜索） -->
        <section class="retrieval-section">
          <div v-if="!records.length" class="retrieval-empty">暂无检索记录</div>
          <div v-else class="record-list">
            <article v-for="record in records" :key="record.key" class="record-card">
              <div class="record-card__head">
                <span class="record-card__kind">{{ record.kindLabel }}</span>
                <span v-if="record.timeText" class="record-card__time">{{ record.timeText }}</span>
              </div>
              <div class="record-card__query" :title="record.title">{{ record.title }}</div>
              <div v-if="record.hits.length" class="record-card__hits">
                <button
                  v-for="hit in record.hits"
                  :key="hit.key"
                  type="button"
                  class="record-hit"
                  :title="hit.summary || hit.label"
                  @click="openHit(hit)"
                >
                  <span class="record-hit__title">
                    <Globe :size="12" class="record-hit__icon" />
                    <span class="record-hit__label">{{ hit.label }}</span>
                  </span>
                  <span v-if="hit.summary" class="record-hit__summary">{{ hit.summary }}</span>
                </button>
                <span v-if="record.extraCount > 0" class="record-hit record-hit--more">
                  +{{ record.extraCount }}
                </span>
              </div>
            </article>
          </div>
        </section>
      </div>
    </template>

    <!-- 内嵌浏览视图 -->
    <template v-else>
      <div class="retrieval-panel__header browse-header">
        <button
          type="button"
          class="retrieval-panel__close"
          title="关闭网页，返回列表"
          aria-label="关闭内嵌网页"
          @click.stop="closeBrowse"
        >
          <X :size="14" />
        </button>
        <span class="browse-title" :title="browsingTitle || browsingUrl">
          {{ browsingTitle || browsingUrl }}
        </span>
        <button
          type="button"
          class="retrieval-panel__close"
          title="在新窗口打开"
          aria-label="在新窗口打开网页"
          @click.stop="openInNewWindow"
        >
          <ExternalLink :size="14" />
        </button>
      </div>
      <div class="browse-body">
        <div v-if="iframeLoading" class="browse-loading">
          <span class="browse-loading__spinner"></span>
          <span>正在加载页面…</span>
        </div>
        <div v-if="frameBlocked" class="browse-blocked">
          <span class="browse-blocked__text">该站点禁止内嵌或加载受限</span>
          <button type="button" class="browse-blocked__btn" @click="openInNewWindow">
            在新窗口打开
          </button>
        </div>
        <iframe
          ref="frameRef"
          :key="iframeKey"
          class="browse-frame"
          :src="browsingUrl"
          :title="browsingTitle || '内嵌网页'"
          referrerpolicy="no-referrer"
          @load="handleFrameLoad"
        ></iframe>
      </div>
    </template>
  </aside>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ExternalLink, Globe, X } from '@lucide/vue'

const props = defineProps({
  /** 当前对话的检索记录列表（由 AgentChatComponent 从本线程消息中提取，不含跨对话缓存） */
  records: {
    type: Array,
    default: () => []
  },
  /** 外部请求面板内嵌打开的链接（来自消息正文点击，AgentChatComponent 下发） */
  pendingLink: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'browsing-change'])

// 内嵌浏览状态
const frameRef = ref(null)
const browsingUrl = ref('')
const browsingTitle = ref('')
const iframeLoading = ref(false)
const iframeKey = ref(0)
const frameBlocked = ref(false)
let blockedCheckTimer = null

// 浏览状态上报给父组件，由父组件统一控制面板宽度（避免与父级样式优先级打架）
watch(browsingUrl, (value) => emit('browsing-change', Boolean(value)))

// 消息正文链接 → 面板内嵌打开
watch(
  () => props.pendingLink,
  (link) => {
    if (link?.url) openHit({ url: link.url, label: link.title || '' })
  }
)

const openHit = (hit) => {
  if (!hit?.url) return
  if (shouldPreferExternal(hit.url)) {
    window.open(hit.url, '_blank', 'noopener,noreferrer')
    return
  }
  browsingUrl.value = hit.url
  browsingTitle.value = hit.label || ''
  iframeLoading.value = true
  frameBlocked.value = false
  iframeKey.value += 1
  armBlockedFallback()
}

// 明确返回 X-Frame-Options: SAMEORIGIN 的学校官网不能被工作台跨站嵌入。
// 这类链接直接新窗口打开，其余站点仍先尝试内嵌。
const shouldPreferExternal = (url) => {
  try {
    const parsed = new URL(url)
    return parsed.hostname === 'www.cup.edu.cn'
  } catch {
    return false
  }
}

const closeBrowse = () => {
  browsingUrl.value = ''
  browsingTitle.value = ''
  iframeLoading.value = false
  frameBlocked.value = false
  if (blockedCheckTimer) {
    clearTimeout(blockedCheckTimer)
    blockedCheckTimer = null
  }
}

const openInNewWindow = () => {
  if (!browsingUrl.value) return
  window.open(browsingUrl.value, '_blank', 'noopener,noreferrer')
}

// load 迟迟不来（网络不通/极慢）时的兜底引导
const armBlockedFallback = () => {
  if (blockedCheckTimer) clearTimeout(blockedCheckTimer)
  blockedCheckTimer = setTimeout(() => {
    blockedCheckTimer = null
    if (browsingUrl.value) frameBlocked.value = true
  }, 8000)
}

// 拦截提示的可用信号有限（实测 Chromium 对 XFO/CSP 拒绝的 frame：contentDocument
// 为 null 且 load 正常触发，与正常跨域页完全不可区分）：
// 1) load 迟迟不来 → 8s 兜底（网络不通/极慢）；
// 2) 同源空白文档（href 为 ''/about:blank 且无子元素）→ 200ms + 800ms 双检。
// 更多站点级拒绝（X-Frame-Options 等）无法在前端可靠感知，交给工具条上的「在新窗口打开」。
const checkFrameBlank = () => {
  try {
    const doc = frameRef.value?.contentDocument
    const href = doc?.location?.href || ''
    if (doc && (href === '' || href === 'about:blank') && !doc.body?.childElementCount) {
      frameBlocked.value = true
    }
  } catch {
    /* 正常跨域页面：不可访问即未被拦截 */
  }
}

const handleFrameLoad = () => {
  iframeLoading.value = false
  if (blockedCheckTimer) clearTimeout(blockedCheckTimer)
  frameBlocked.value = false
  blockedCheckTimer = setTimeout(() => {
    blockedCheckTimer = null
    checkFrameBlank()
    if (!frameBlocked.value && !blockedCheckTimer) {
      blockedCheckTimer = setTimeout(() => {
        blockedCheckTimer = null
        checkFrameBlank()
      }, 800)
    }
  }, 200)
}
</script>

<style scoped lang="less">
.retrieval-panel {
  flex: 0 0 320px;
  width: 320px;
  min-width: 0;
  align-self: stretch;
  display: flex;
  flex-direction: column;
  background: var(--gray-0);
  border-left: 1px solid var(--gray-150);
  overflow: hidden;
  // 加宽由父组件 .retrieval-side-panel.is-browsing 控制
  transition:
    flex-basis 0.24s cubic-bezier(0.16, 1, 0.3, 1),
    width 0.24s cubic-bezier(0.16, 1, 0.3, 1);

  .retrieval-panel__header {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 10px 12px;
    border-bottom: 1px solid var(--gray-150);

    .retrieval-panel__title {
      font-size: 13px;
      font-weight: 600;
      color: var(--gray-800);
    }

    .retrieval-panel__close {
      flex-shrink: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      width: 22px;
      height: 22px;
      border: none;
      border-radius: 6px;
      background: transparent;
      color: var(--gray-600);
      cursor: pointer;
      transition: all 0.15s ease;

      &:hover {
        background: var(--gray-25);
        color: var(--gray-800);
      }
    }
  }

  .retrieval-panel__body {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .retrieval-section {
    .retrieval-section__title {
      font-size: 12px;
      font-weight: 600;
      color: var(--gray-600);
      padding-bottom: 6px;
      margin-bottom: 8px;
      border-bottom: 1px solid var(--gray-100);
    }
  }

  .retrieval-empty {
    border: 1px dashed var(--gray-150);
    border-radius: 8px;
    padding: 12px 10px;
    font-size: 12px;
    color: var(--gray-500);
    text-align: center;
  }

  .record-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .record-card {
    border: 1px solid var(--gray-150);
    border-radius: 8px;
    padding: 8px 10px;
    transition: background 0.15s ease;

    &:hover {
      background: var(--gray-25);
    }

    .record-card__head {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 4px;

      .record-card__kind {
        font-size: 11px;
        color: var(--gray-600);
        background: var(--gray-25);
        border-radius: 4px;
        padding: 1px 6px;
      }

      .record-card__time {
        margin-left: auto;
        font-size: 11px;
        color: var(--gray-500);
        white-space: nowrap;
      }
    }

    .record-card__query {
      font-size: 13px;
      color: var(--gray-800);
      line-height: 1.4;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
      word-break: break-word;
      margin-bottom: 6px;
    }

    .record-card__hits {
      display: flex;
      flex-direction: column;
      align-items: stretch;
      gap: 4px;
    }
  }

  // 单条命中：标题行（可点开网页）+ 内容概述两行
  .record-hit {
    display: block;
    width: 100%;
    text-align: left;
    border: 1px solid var(--gray-150);
    border-radius: 6px;
    background: var(--gray-0);
    padding: 4px 8px;
    cursor: pointer;
    transition: all 0.15s ease;

    .record-hit__title {
      display: flex;
      align-items: center;
      gap: 4px;
      min-width: 0;
    }

    .record-hit__icon {
      flex-shrink: 0;
      color: var(--gray-500);
    }

    .record-hit__label {
      min-width: 0;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      font-size: 12px;
      color: var(--gray-700);
    }

    .record-hit__summary {
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
      margin-top: 2px;
      font-size: 11px;
      line-height: 1.4;
      color: var(--gray-500);
      word-break: break-word;
    }

    &:hover {
      border-color: var(--gray-300);
      background: var(--gray-25);
    }

    &.record-hit--more {
      align-self: flex-start;
      width: auto;
      cursor: default;
      font-size: 12px;
      color: var(--gray-500);
      background: transparent;
      border-style: dashed;

      &:hover {
        border-color: var(--gray-150);
        background: transparent;
      }
    }
  }

  // 内嵌浏览视图
  .browse-header {
    .browse-title {
      flex: 1;
      min-width: 0;
      font-size: 12px;
      color: var(--gray-700);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }

  .browse-body {
    flex: 1;
    min-height: 0;
    position: relative;
    background: var(--gray-0);

    .browse-frame {
      display: block;
      width: 100%;
      height: 100%;
      border: none;
      background: var(--gray-0);
    }

    .browse-loading {
      position: absolute;
      inset: 0;
      z-index: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      font-size: 12px;
      color: var(--gray-500);
      background: var(--gray-0);

      .browse-loading__spinner {
        width: 14px;
        height: 14px;
        border: 2px solid var(--gray-150);
        border-top-color: var(--gray-500);
        border-radius: 50%;
        animation: browseSpin 0.8s linear infinite;
      }
    }

    .browse-blocked {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      z-index: 2;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      padding: 6px 10px;
      background: var(--gray-25);
      border-bottom: 1px solid var(--gray-150);

      .browse-blocked__text {
        font-size: 12px;
        color: var(--gray-700);
      }

      .browse-blocked__btn {
        flex-shrink: 0;
        border: 1px solid var(--gray-150);
        border-radius: 6px;
        background: var(--gray-0);
        padding: 2px 8px;
        font-size: 12px;
        color: var(--gray-700);
        cursor: pointer;
        transition: all 0.15s ease;

        &:hover {
          background: var(--gray-25);
          border-color: var(--gray-300);
        }
      }
    }
  }
}

@keyframes browseSpin {
  to {
    transform: rotate(360deg);
  }
}
</style>
