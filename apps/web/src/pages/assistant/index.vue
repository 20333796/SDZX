<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, ArrowRight, Bot, BookOpen, BrainCircuit, Check, ChevronDown, Globe2, LibraryBig, Link2, Mic, MoreHorizontal, Plus, Search, SendHorizontal, Sparkles, UserRoundSearch } from '@lucide/vue'
import type { ChatResourceReference, Citation } from '@/types'

type Message = { role: 'assistant' | 'user'; content: string; citations?: Citation[]; resources?: ChatResourceReference[] }
type Mode = 'conversation' | 'search' | 'inquiry'

const route = useRoute()
const router = useRouter()
const prompt = ref('')
const mode = ref<Mode>('conversation')
const loading = ref(false)
const planning = ref(false)
const sidebarCollapsed = ref(false)
const activeNavigation = ref('“深地·智学”智能体')
const messages = ref<Message[]>([])
const answerScroll = ref<HTMLElement | null>(null)
const showSources = ref(true)
const activeResource = ref<ChatResourceReference | null>(null)
const currentPrompt = computed(() => typeof route.query.q === 'string' ? route.query.q : '')
const navigation = [
  { label: '新对话', icon: Plus }, { label: '智能体广场', icon: Bot }, { label: '“深地·智学”智能体', icon: Sparkles },
  { label: 'AI知识库', icon: LibraryBig }, { label: '知识生产中心', icon: BrainCircuit }
]
const quickActions = [
  { label: '学习知识', icon: BookOpen, value: '油气成藏需要哪些关键地质条件？' },
  { label: '导师查找', icon: UserRoundSearch, value: '地质资源与地质工程方向有哪些研究专题？' },
  { label: '研究方向查找', icon: Search, value: '储层表征与建模有哪些常见研究方法？' },
  { label: '人才培养', icon: BrainCircuit, value: '地质资源与地质工程学科的核心课程如何衔接？' }
]

const resourceLabels: Record<ChatResourceReference['category'], string> = {
  courses: '课程', practice: '虚拟仿真', mentor: '导师图谱'
}

function openResource(resource: ChatResourceReference) {
  if (resource.route?.startsWith('/')) {
    void router.push(resource.route)
    return
  }
  activeResource.value = resource
}

function openExternal(resource: ChatResourceReference) {
  if (resource.url) window.open(resource.url, '_blank', 'noopener,noreferrer')
}

async function scrollAnswers() {
  await nextTick()
  answerScroll.value?.scrollTo({ top: answerScroll.value.scrollHeight, behavior: 'smooth' })
}

function newConversation() {
  messages.value = []
  prompt.value = ''
  activeNavigation.value = '新对话'
  void router.replace({ name: 'assistant' })
}

function selectNavigation(label: string) {
  activeNavigation.value = label
  if (label === '新对话') newConversation()
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    void sendQuestion()
  }
}

async function sendQuestion(text = prompt.value) {
  const question = text.trim()
  if (!question || loading.value) return
  messages.value.push({ role: 'user', content: question })
  prompt.value = ''
  loading.value = true
  planning.value = true
  const answer: Message = { role: 'assistant', content: '' }
  messages.value.push(answer)
  await scrollAnswers()
  try {
    const response = await fetch('/api/v1/chat/stream', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ mode: mode.value, message: question })
    })
    if (!response.ok || !response.body) throw new Error('Chat API unavailable')
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const events = buffer.split('\n\n')
      buffer = events.pop() ?? ''
      for (const event of events) {
        const dataLine = event.split('\n').find((line) => line.startsWith('data: '))
        if (!dataLine) continue
        const eventName = event.split('\n').find((line) => line.startsWith('event: '))?.slice(7)
        const payload = JSON.parse(dataLine.slice(6)) as { content?: string; citations?: Citation[]; resources?: ChatResourceReference[] }
        if (payload.content) answer.content += payload.content
        if (eventName === 'sources' && payload.citations) answer.citations = payload.citations
        if (eventName === 'resources' && payload.resources) answer.resources = payload.resources
      }
      void scrollAnswers()
    }
  } catch {
    answer.content = '地质知识服务正在连接中。你可以先从油矿地质学、测井解释或油气田勘探资源开始。'
  } finally {
    loading.value = false
    planning.value = false
    void scrollAnswers()
  }
}

onMounted(() => {
  const initialMode = route.query.mode
  if (initialMode === 'search' || initialMode === 'inquiry') mode.value = initialMode
  if (currentPrompt.value) void sendQuestion(currentPrompt.value)
})
</script>

<template>
  <main :class="['workbench-page', { 'is-sidebar-collapsed': sidebarCollapsed, 'is-sources-closed': !showSources }]">
    <aside class="workbench-sidebar">
      <button class="back-home" aria-label="返回深地智学首页" @click="router.push({ name: 'home' })"><ArrowLeft :size="23" /></button>
      <button class="sidebar-collapse" :aria-label="sidebarCollapsed ? '展开侧栏' : '收起侧栏'" @click="sidebarCollapsed = !sidebarCollapsed"><span></span><span></span></button>
      <nav aria-label="AI工作台功能">
        <button v-for="item in navigation" :key="item.label" :class="{ selected: item.label === activeNavigation }" :title="item.label" @click="selectNavigation(item.label)"><component :is="item.icon" :size="20" /><span>{{ item.label }}</span></button>
      </nav>
      <section class="chat-history" aria-label="历史对话">
        <p>历史对话</p>
        <button v-for="(message, index) in messages.filter((message) => message.role === 'user').slice(-5)" :key="`${message.content}-${index}`" @click="prompt = message.content">{{ message.content }}</button>
        <button v-if="!messages.length" @click="prompt = '油气成藏需要哪些关键地质条件？'">油气成藏需要哪些关键地质条件？</button>
      </section>
    </aside>

    <section class="workbench-main">
      <header class="assistant-topbar"><button class="assistant-platform" aria-label="返回深地智学首页" @click="router.push({ name: 'home' })"><img src="/cupb-emblem-red.png" alt="中国石油大学（北京）" /><span>深地智学</span></button><i></i><span class="assistant-avatar"><Sparkles :size="17" /></span><strong>地智 · 地质资源与地质工程学科 AI 学习助手</strong></header>
      <div ref="answerScroll" class="conversation-scroll" aria-live="polite">
        <section v-if="!messages.length" class="empty-conversation">
          <div class="assistant-welcome"><div class="empty-orbit"><Sparkles :size="22" /></div><div><h1>Hi，我是地智！</h1><p>你的地质资源与地质工程学科 AI 学习助手，欢迎随时向我提问！</p><p>请提出你的问题吧！</p></div></div>
          <strong class="interest-title">你也许感兴趣？</strong>
          <div class="interest-list"><button @click="sendQuestion('什么是储层的有效孔隙度？')"><span></span>什么是储层的有效孔隙度？<ArrowRight :size="15" /></button><button @click="sendQuestion('如何用测井曲线识别砂岩储层？')"><span></span>如何用测井曲线识别砂岩储层？<ArrowRight :size="15" /></button><button @click="sendQuestion('油气成藏需要哪些关键地质条件？')"><span></span>油气成藏需要哪些关键地质条件？<ArrowRight :size="15" /></button></div>
        </section>
        <article v-for="(message, index) in messages" :key="index" :class="['conversation-item', message.role]">
          <div v-if="message.role === 'assistant'" class="answer-label"><span class="assistant-avatar"><Sparkles :size="15" /></span>地智</div>
          <div class="bubble"><p v-if="message.content">{{ message.content }}</p><p v-else class="thinking"><span></span>正在组织地质学习依据</p></div>
          <button v-if="message.role === 'assistant' && (message.citations?.length || message.resources?.length)" class="source-button" @click="showSources = !showSources">查看参考来源 <ArrowRight :size="14" /></button>
        </article>
        <section v-if="planning" class="planning-card" aria-label="回答规划过程">
          <button class="planning-summary" type="button"><span class="planning-orbit"><Sparkles :size="15" /></span><strong>规划过程</strong><small>正在为本次问题组织学习路径</small><ChevronDown :size="17" /></button>
          <div class="planning-steps">
            <p><span><Check :size="12" /></span>识别问题中的课程与知识点</p>
            <p><span class="is-active"></span>检索课程资源与知识库依据</p>
            <p><span></span>整理可追溯的学习建议</p>
          </div>
        </section>
      </div>
      <div class="workbench-bottom">
        <div class="quick-actions"><button v-for="action in quickActions" :key="action.label" @click="sendQuestion(action.value)"><component :is="action.icon" :size="16" />{{ action.label }}</button></div>
        <div class="workbench-composer">
          <textarea v-model="prompt" rows="3" placeholder="试着输入您想了解的问题吧。&#10;输入 Shift+Enter 是换行哦～" :disabled="loading" @keydown="onKeydown"></textarea>
          <div class="composer-actions">
            <button :class="{ active: mode === 'conversation' }" @click="mode = 'conversation'"><BrainCircuit :size="15" />深度思考(R1)</button>
            <button :class="{ active: mode === 'search' }" @click="mode = 'search'"><Globe2 :size="15" />联网搜索</button>
            <span></span><button aria-label="添加资料"><Link2 :size="19" /></button><button aria-label="语音输入"><Mic :size="18" /></button><button class="submit-message" :disabled="loading || !prompt.trim()" aria-label="发送问题" @click="sendQuestion()"><SendHorizontal :size="18" /></button>
          </div>
        </div>
        <p>以上内容由 AI 大模型生成，请结合课程资料与教师指导进行判断。</p>
      </div>
    </section>

    <aside :class="['sources-panel', { 'is-closed': !showSources }]">
      <header><strong>地学指令</strong><button :aria-label="showSources ? '关闭参考来源' : '展开参考来源'" @click="showSources = !showSources"><span v-if="showSources">×</span><ArrowRight v-else :size="20" /></button></header>
      <div v-if="showSources" class="sources-content">
        <p>基于当前问答，为您整理了可追溯的知识与门户资源</p><h2>知识库依据</h2>
        <template v-if="messages.at(-1)?.citations?.length">
          <a v-for="citation in messages.at(-1)?.citations" :key="`${citation.document_id}-${citation.source_locator}`" href="#sources"><span>{{ citation.title }}</span><b>{{ citation.course_name || '课程知识库' }}</b><small>{{ citation.excerpt }}</small></a>
        </template>
        <template v-if="messages.at(-1)?.resources?.length">
          <h2 class="resource-heading">可直接打开</h2>
          <article v-for="resource in messages.at(-1)?.resources" :key="resource.id" class="resource-item">
            <button class="resource-main" type="button" @click="openResource(resource)">
              <span class="resource-kind">{{ resourceLabels[resource.category] }}</span>
              <b>{{ resource.title }}</b>
              <small>{{ resource.provider }} · {{ resource.description }}</small>
            </button>
            <a v-if="resource.url" class="resource-address" :href="resource.url" target="_blank" rel="noopener noreferrer" @click.stop>
              <Globe2 :size="15" /><span>访问地址</span><small>{{ resource.url }}</small>
            </a>
            <button v-else class="resource-external" type="button" disabled aria-label="暂无访问地址" title="暂无访问地址"><Globe2 :size="16" /></button>
          </article>
        </template>
        <template v-else>
          <a href="#source"><span>油矿地质学</span><b>课程知识图谱</b><small>油气成藏、储层与圈闭的基础学习资料。</small></a>
          <a href="#source"><span>地球物理测井</span><b>教学知识库</b><small>GR、RT 与孔隙度曲线的基础判识依据。</small></a>
          <a href="#source"><span>油气田勘探</span><b>课程资源</b><small>从构造背景到风险评价的课程资源。</small></a>
        </template>
      </div>
      <div v-else class="sources-closed"><MoreHorizontal :size="24" /><span>参考来源已收起</span></div>
    </aside>
    <div v-if="activeResource" class="resource-modal" role="dialog" aria-modal="true" :aria-label="activeResource.title">
      <div class="resource-modal-backdrop" @click="activeResource = null"></div>
      <section class="resource-modal-panel">
        <header><div><strong>{{ activeResource.title }}</strong><small>{{ activeResource.provider }}</small></div><button type="button" aria-label="关闭预览" @click="activeResource = null">×</button></header>
        <iframe v-if="activeResource.embedded_url" :src="activeResource.embedded_url" :title="activeResource.title" loading="lazy"></iframe>
        <div v-else class="resource-modal-empty">该资源不允许内嵌，请使用新窗口打开。</div>
        <footer><button type="button" @click="openExternal(activeResource)">新窗口打开 <Globe2 :size="15" /></button></footer>
      </section>
    </div>
  </main>
</template>

<style scoped>
.workbench-page { display: grid; grid-template-columns: 320px minmax(0, 1fr) 460px; min-height: 100svh; color: #20222d; background: #f7f8ff; }.workbench-sidebar { display: grid; grid-template-columns: 1fr; align-content: start; gap: 22px; padding: 30px 28px; background: #f2f3fa; }.back-home { position: absolute; top: 32px; left: 30px; display: grid; place-items: center; color: #2c3141; background: transparent; border: 0; }.sidebar-collapse { justify-self: end; display: grid; grid-template-columns: repeat(2, 5px); gap: 2px; padding: 0; color: #34394d; background: transparent; border: 0; }.sidebar-collapse span { display: block; width: 5px; height: 22px; border: 1px solid currentColor; border-radius: 2px; }.workbench-sidebar nav { display: grid; gap: 8px; margin-top: 44px; }.workbench-sidebar nav button { display: flex; align-items: center; gap: 14px; padding: 11px 15px; color: #1f2532; background: transparent; border: 0; border-radius: 8px; font-weight: 700; text-align: left; }.workbench-sidebar nav button.selected { color: #5946fa; background: #e9e7ff; }.chat-history { display: grid; gap: 7px; margin-top: 44px; }.chat-history p { margin: 0 0 5px; color: #898ea0; font-size: 14px; }.chat-history button { overflow: hidden; padding: 10px 12px; color: #596075; background: #fff; border: 0; border-radius: 10px; font-size: 14px; text-align: left; text-overflow: ellipsis; white-space: nowrap; }.workbench-main { display: grid; grid-template-rows: 74px minmax(0, 1fr) auto; min-height: 0; background: #fff; }.assistant-topbar { display: flex; align-items: center; gap: 9px; padding: 0 42px; border-bottom: 1px solid #efeff4; font-size: 18px; }.assistant-avatar { display: grid; place-items: center; width: 28px; height: 28px; color: #fff; background: linear-gradient(135deg, #8c77ff, #4d48ef); border-radius: 50%; }.conversation-scroll { min-height: 0; padding: 28px 10%; overflow-y: auto; }.empty-conversation { display: grid; justify-items: center; align-content: center; min-height: 100%; color: #73788a; text-align: center; }.empty-orbit { display: grid; place-items: center; width: 76px; height: 76px; color: #5c4df4; background: #f1efff; border: 1px solid #dedbff; border-radius: 50%; box-shadow: 0 0 0 15px #faf9ff; }.empty-conversation h1 { margin: 28px 0 9px; color: #2a2d3b; font-family: "Microsoft YaHei", sans-serif; font-size: 27px; letter-spacing: 0; text-shadow: none; }.empty-conversation p { margin: 0; font-size: 14px; }.conversation-item { position: relative; margin-bottom: 25px; }.conversation-item.user { display: flex; justify-content: flex-end; }.answer-label { display: flex; align-items: center; gap: 8px; margin-bottom: 9px; color: #333747; font-size: 14px; font-weight: 800; }.answer-label .assistant-avatar { width: 24px; height: 24px; }.bubble { width: fit-content; max-width: min(100%, 760px); padding: 17px 19px; color: #3f4655; background: #f7f7fb; border: 1px solid #ececf3; border-radius: 10px; line-height: 1.8; }.conversation-item.user .bubble { color: #fff; background: #6454f5; border-color: #6454f5; }.bubble p { margin: 0; white-space: pre-wrap; }.thinking { display: flex; align-items: center; gap: 8px; color: #778097; }.thinking span { width: 9px; height: 9px; background: #6554f5; border-radius: 50%; animation: thinking-pulse 1s ease-in-out infinite; }.source-button { display: inline-flex; align-items: center; gap: 5px; margin-top: 10px; padding: 7px 10px; color: #5a49ed; background: #f1efff; border: 0; border-radius: 6px; font-weight: 700; }.workbench-bottom { padding: 13px 10% 11px; }.quick-actions { display: flex; gap: 9px; margin-bottom: 11px; overflow-x: auto; }.quick-actions button { display: inline-flex; align-items: center; gap: 6px; padding: 7px 10px; color: #32394f; background: #f7f7fa; border: 0; border-radius: 7px; white-space: nowrap; }.workbench-composer { padding: 13px 16px 12px; border: 2px solid #6b57fd; border-radius: 20px; box-shadow: 0 5px 15px rgba(100, 80, 248, .1); }.workbench-composer textarea { display: block; width: 100%; min-height: 59px; padding: 0; resize: none; color: #34384a; background: transparent; border: 0; outline: 0; font: inherit; line-height: 1.55; }.workbench-composer textarea::placeholder { color: #a6a9b5; }.composer-actions { display: flex; align-items: center; gap: 8px; }.composer-actions button { display: inline-flex; align-items: center; gap: 5px; height: 33px; padding: 0 10px; color: #5d6372; background: #f6f6f8; border: 0; border-radius: 8px; }.composer-actions button.active { color: #4d54ee; background: #f0efff; border: 1px solid #a59dff; }.composer-actions span { flex: 1; }.composer-actions .submit-message { display: grid; place-items: center; width: 36px; padding: 0; color: #fff; background: #20222c; border-radius: 50%; }.composer-actions .submit-message:disabled { opacity: .45; }.workbench-bottom > p { margin: 7px 0 0; color: #a1a5b3; font-size: 11px; text-align: center; }.sources-panel { display: grid; grid-template-rows: auto 1fr; overflow: hidden; background: #fff; border-left: 1px solid #ececf2; box-shadow: -10px 0 25px rgba(34, 32, 70, .035); }.sources-panel header { display: flex; align-items: center; justify-content: space-between; height: 74px; padding: 0 27px; border-bottom: 1px solid #efeff4; }.sources-panel header strong { align-self: stretch; display: flex; align-items: center; color: #5a49f4; border-bottom: 3px solid #5a49f4; font-size: 18px; }.sources-panel header button { color: #a4a8b4; background: transparent; border: 0; font-size: 31px; font-weight: 200; }.sources-content { padding: 25px 30px; overflow: auto; }.sources-content > p { margin: 0 0 26px; color: #959aaa; font-size: 14px; }.sources-content h2 { margin: 0 0 20px; color: #2d3140; font-family: "Microsoft YaHei", sans-serif; font-size: 19px; }.sources-content a { display: grid; gap: 7px; padding: 0 0 21px; margin-bottom: 20px; color: inherit; border-bottom: 1px solid #f0f0f4; text-decoration: none; }.sources-content a span { overflow: hidden; color: #5a49f4; font-size: 14px; text-overflow: ellipsis; white-space: nowrap; }.sources-content a b { overflow: hidden; color: #282c39; font-size: 15px; text-overflow: ellipsis; white-space: nowrap; }.sources-content a small { display: -webkit-box; overflow: hidden; color: #969baa; line-height: 1.6; -webkit-box-orient: vertical; -webkit-line-clamp: 2; }.sources-closed { display: grid; place-content: center; justify-items: center; gap: 10px; color: #9aa0b0; }
@keyframes thinking-pulse { 50% { transform: scale(.55); opacity: .45; } }
@media (max-width: 1180px) { .workbench-page { grid-template-columns: 250px minmax(0, 1fr) 330px; }.workbench-sidebar { padding: 26px 18px; }.workbench-bottom, .conversation-scroll { padding-right: 7%; padding-left: 7%; } }
@media (max-width: 880px) { .workbench-page { grid-template-columns: 72px minmax(0, 1fr); }.workbench-sidebar { padding: 22px 12px; }.back-home { position: static; justify-self: center; }.sidebar-collapse, .workbench-sidebar nav button { justify-self: center; font-size: 0; }.workbench-sidebar nav button { padding: 12px; }.workbench-sidebar nav button svg { width: 21px; height: 21px; }.chat-history, .sources-panel { display: none; } }
@media (max-width: 620px) { .workbench-page { display: block; }.workbench-sidebar { display: flex; align-items: center; justify-content: space-between; min-height: 56px; padding: 9px 14px; }.back-home { display: inline-grid; }.sidebar-collapse, .chat-history { display: none; }.workbench-sidebar nav { display: flex; gap: 2px; margin: 0; }.workbench-sidebar nav button { padding: 8px; }.workbench-main { min-height: calc(100svh - 56px); grid-template-rows: 57px minmax(0, 1fr) auto; }.assistant-topbar { padding: 0 18px; font-size: 16px; }.conversation-scroll, .workbench-bottom { padding-right: 16px; padding-left: 16px; }.quick-actions button { font-size: 12px; }.composer-actions button { padding: 0 7px; font-size: 11px; }.composer-actions button[aria-label] { width: 28px; padding: 0; justify-content: center; }.empty-conversation h1 { font-size: 22px; }.bubble { font-size: 14px; } }

/* Workbench state motion follows the reference's calm, progressive feedback. */
.workbench-page { transition: grid-template-columns 260ms cubic-bezier(.2, .8, .2, 1); }
.workbench-page.is-sidebar-collapsed { grid-template-columns: 86px minmax(0, 1fr) 460px; }
.workbench-page.is-sidebar-collapsed .workbench-sidebar { padding-right: 12px; padding-left: 12px; }
.workbench-page.is-sidebar-collapsed .workbench-sidebar nav button { justify-content: center; padding-right: 8px; padding-left: 8px; font-size: 0; }
.workbench-page.is-sidebar-collapsed .workbench-sidebar nav button span,
.workbench-page.is-sidebar-collapsed .chat-history { display: none; }
.workbench-page.is-sidebar-collapsed .sidebar-collapse { transform: rotate(180deg); }
.sidebar-collapse { transition: transform 220ms ease, color 180ms ease; }
.sidebar-collapse:hover { color: #5a49f4; }
.workbench-sidebar nav button { position: relative; transition: color 180ms ease, background 180ms ease, transform 180ms ease; }
.workbench-sidebar nav button::before { content: ""; position: absolute; left: 0; width: 3px; height: 0; background: #5a49f4; border-radius: 0 4px 4px 0; transition: height 180ms ease; }
.workbench-sidebar nav button:hover { color: #5546ea; background: rgba(101, 84, 245, .06); transform: translateX(2px); }
.workbench-sidebar nav button.selected::before { height: 52%; }
.conversation-item { animation: conversation-in 280ms cubic-bezier(.2, .8, .2, 1) both; }
.conversation-item.assistant { animation-delay: 70ms; }
.bubble { transition: box-shadow 180ms ease, border-color 180ms ease; }
.conversation-item.assistant .bubble:hover { border-color: #dfdcff; box-shadow: 0 10px 24px rgba(54, 46, 129, .06); }
.source-button, .quick-actions button, .composer-actions button, .sources-content a { transition: transform 180ms ease, background 180ms ease, color 180ms ease, box-shadow 180ms ease; }
.resource-address { grid-column: 1 / -1; display: flex; flex: 1; align-items: center; flex-wrap: wrap; gap: 6px; min-width: 0; padding: 13px 10px; color: #0871ba; background: #f2f6f9; border-radius: 10px; font-size: 13px; font-weight: 700; text-decoration: none; }
.resource-address small { overflow: hidden; color: #6e8297; font-size: 11px; font-weight: 400; text-overflow: ellipsis; white-space: nowrap; }
.resource-external:disabled { opacity: .35; cursor: not-allowed; }
.source-button:hover, .quick-actions button:hover, .composer-actions button:hover { transform: translateY(-2px); box-shadow: 0 7px 15px rgba(53, 45, 121, .1); }
.workbench-composer { transition: border-color 180ms ease, box-shadow 180ms ease, transform 180ms ease; }
.workbench-composer:focus-within { border-color: #5645f2; box-shadow: 0 10px 28px rgba(93, 74, 243, .16); transform: translateY(-2px); }
.submit-message:not(:disabled):hover { transform: translateY(-2px) rotate(-8deg); box-shadow: 0 8px 18px rgba(32, 34, 44, .23); }
.planning-card { overflow: hidden; margin: -4px 0 25px; border: 1px solid #e5e3fb; border-radius: 12px; background: linear-gradient(115deg, #faf9ff, #f5f5ff); box-shadow: 0 12px 28px rgba(79, 67, 172, .07); animation: planning-in 280ms cubic-bezier(.2, .8, .2, 1) both; }
.planning-summary { display: grid; grid-template-columns: auto auto 1fr auto; align-items: center; gap: 9px; width: 100%; padding: 14px 16px; color: #38334e; background: transparent; border: 0; text-align: left; }
.planning-summary strong { font-size: 14px; }.planning-summary small { color: #9290a1; font-size: 12px; }.planning-summary svg:last-child { color: #8b86a2; }
.planning-orbit { display: grid; place-items: center; width: 28px; height: 28px; color: #5948f4; background: #eae8ff; border-radius: 50%; animation: orbit-pulse 1.7s ease-in-out infinite; }
.planning-steps { display: grid; gap: 11px; padding: 1px 18px 17px 29px; border-top: 1px solid #ebe9f7; }
.planning-steps p { display: flex; align-items: center; gap: 9px; margin: 0; color: #777489; font-size: 13px; }.planning-steps span { display: grid; place-items: center; flex: 0 0 auto; width: 16px; height: 16px; border: 1px solid #d3d0e4; border-radius: 50%; color: #fff; }.planning-steps span:empty { width: 8px; height: 8px; margin: 0 4px; background: #d5d1e4; border: 0; }.planning-steps span.is-active { background: #6454f5; box-shadow: 0 0 0 4px rgba(100, 84, 245, .14); animation: active-step 1.1s ease-in-out infinite; }
.sources-panel { transition: width 240ms cubic-bezier(.2, .8, .2, 1), background 180ms ease; }.sources-panel header button { display: grid; place-items: center; width: 34px; height: 34px; border-radius: 50%; transition: color 180ms ease, background 180ms ease, transform 180ms ease; }.sources-panel header button:hover { color: #5a49f4; background: #f1efff; transform: rotate(8deg); }.sources-panel.is-closed { background: #fafaff; }.sources-content a:hover { padding-left: 8px; color: #4334d1; }.sources-content a:hover b { color: #4334d1; }
@keyframes conversation-in { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@keyframes planning-in { from { opacity: 0; transform: translateY(8px) scale(.985); } to { opacity: 1; transform: translateY(0) scale(1); } }
@keyframes orbit-pulse { 50% { color: #fff; background: #6554f5; box-shadow: 0 0 0 6px rgba(101, 84, 245, .1); } }
@keyframes active-step { 50% { transform: scale(.72); opacity: .65; } }
@media (max-width: 1180px) { .workbench-page.is-sidebar-collapsed { grid-template-columns: 76px minmax(0, 1fr) 330px; } }
@media (max-width: 880px) { .workbench-page.is-sidebar-collapsed { grid-template-columns: 72px minmax(0, 1fr); }.workbench-sidebar nav button span { display: none; } }
@media (max-width: 620px) { .workbench-sidebar nav button.selected::before { display: none; }.workbench-sidebar nav button:hover { transform: none; }.planning-summary { grid-template-columns: auto 1fr auto; }.planning-summary small { display: none; }.planning-steps { padding-left: 18px; }.workbench-composer:focus-within { transform: none; } }

/* Keep the destination workbench in the same blue portal family as the homepage. */
.workbench-page { color: #183d5c; background: #eef5fb; }.workbench-sidebar { background: #e8f2fb; }.back-home, .sidebar-collapse, .workbench-sidebar nav button { color: #183d5c; }.workbench-sidebar nav button.selected { color: #0768b4; background: #d3eaff; }.chat-history button { color: #49677d; background: rgba(255,255,255,.82); }.assistant-topbar { color: #1d5279; border-bottom-color: #dbe8f1; }.assistant-avatar { background: linear-gradient(135deg, #0b84ca, #0755a0); }.empty-conversation { color: #718a9e; }.empty-orbit { color: #0873ba; background: #e8f5fc; border-color: #c8e7f8; box-shadow: 0 0 0 15px #f5fbff; }.empty-conversation h1 { color: #183d5c; }.bubble { color: #31546c; background: #f1f7fb; border-color: #dceaf3; }.conversation-item.user .bubble { background: #0871ba; border-color: #0871ba; }.thinking { color: #6d8497; }.thinking span { background: #0871ba; }.source-button { color: #0766ad; background: #e3f2fc; }.workbench-composer { border-color: #137dc1; box-shadow: 0 5px 15px rgba(8, 104, 180, .12); }.composer-actions button.active { color: #0768b4; background: #e7f3fc; border-color: #9ed0ee; }.sources-panel { border-left-color: #dbe8f1; }.sources-panel header { border-bottom-color: #dbe8f1; }.sources-panel header strong, .sources-content a span { color: #0871ba; border-bottom-color: #0871ba; }.sources-content a { border-bottom-color: #e4edf3; }.sources-content a b { color: #183d5c; }.planning-orbit { color: #0871ba; background: #e4f3fc; }
.sidebar-collapse:hover, .workbench-sidebar nav button:hover { color: #0768b4; }.workbench-sidebar nav button::before, .planning-steps span.is-active { background: #0871ba; }.conversation-item.assistant .bubble:hover { border-color: #cde5f4; box-shadow: 0 10px 24px rgba(6, 92, 157, .08); }.source-button:hover, .quick-actions button:hover, .composer-actions button:hover { box-shadow: 0 7px 15px rgba(6, 92, 157, .12); }.workbench-composer:focus-within { border-color: #0871ba; box-shadow: 0 10px 28px rgba(8, 104, 180, .16); }.planning-card { border-color: #d5e7f4; background: linear-gradient(115deg, #f8fcff, #eef7fc); box-shadow: 0 12px 28px rgba(6, 92, 157, .08); }.planning-summary { color: #264c67; }.planning-steps { border-top-color: #dcebf4; }.sources-panel header button:hover { color: #0871ba; background: #e7f3fc; }.sources-content a:hover { color: #075a9d; }.sources-content a:hover b { color: #075a9d; }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { scroll-behavior: auto !important; animation-duration: 1ms !important; animation-iteration-count: 1 !important; transition-duration: 1ms !important; } }

/* Keep the assistant destination connected to the portal identity. */
.assistant-platform { display: inline-flex; align-items: center; gap: 7px; padding: 0; color: #1d5279; background: transparent; border: 0; font-size: 14px; font-weight: 800; }
.assistant-platform img { display: block; width: 20px; height: 20px; object-fit: contain; }
.assistant-platform:hover { color: #0871ba; }
.assistant-topbar > i { width: 1px; height: 20px; margin: 0 4px; background: #d7e6ef; }
@media (max-width: 620px) { .assistant-platform span, .assistant-topbar > i { display: none; } }

/* The assistant route follows the target workbench's neutral command-center surface. */
.workbench-page { color: #20222d; background: #f7f8ff; }.workbench-sidebar { background: #f2f3fa; }.back-home, .sidebar-collapse, .workbench-sidebar nav button { color: #2c3141; }.workbench-sidebar nav button.selected { color: #5946fa; background: #e9e7ff; }.chat-history button { color: #596075; background: #fff; }.assistant-topbar { color: #20222d; border-bottom-color: #efeff4; }.assistant-topbar > * { display: none; }.assistant-avatar { background: linear-gradient(135deg, #8c77ff, #4d48ef); }.empty-conversation { color: #73788a; }.empty-orbit { color: #5c4df4; background: #f1efff; border-color: #dedbff; box-shadow: 0 0 0 15px #faf9ff; }.empty-conversation h1 { color: #2a2d3b; }.bubble { color: #3f4655; background: #f7f7fb; border-color: #ececf3; }.conversation-item.user .bubble { background: #6454f5; border-color: #6454f5; }.thinking { color: #778097; }.thinking span { background: #6554f5; }.source-button { color: #5a49ed; background: #f1efff; }.workbench-composer { border-color: #6b57fd; box-shadow: 0 5px 15px rgba(100, 80, 248, .1); }.composer-actions button.active { color: #4d54ee; background: #f0efff; border-color: #a59dff; }.sources-panel { background: #fff; border-left-color: #ececf2; }.sources-panel header { border-bottom-color: #efeff4; }.sources-panel header strong { color: #5a49f4; border-bottom-color: #5a49f4; }.sources-content a { padding: 16px 17px 18px; margin-bottom: 14px; background: #f7f8fa; border-bottom: 0; border-radius: 13px; }.sources-content a span { color: #5a49f4; }.sources-content a b { color: #282c39; }.sources-content a small { color: #969baa; }.planning-card { border-color: #e5e3fb; background: linear-gradient(115deg, #faf9ff, #f5f5ff); }.planning-orbit { color: #5948f4; background: #eae8ff; }.planning-steps { border-top-color: #ebe9f7; }.planning-steps span.is-active { background: #6454f5; }.sidebar-collapse:hover, .workbench-sidebar nav button:hover { color: #5546ea; }.workbench-sidebar nav button::before { background: #5a49f4; }.sources-panel header button:hover { color: #5a49f4; background: #f1efff; }
.empty-conversation { justify-items: start; align-content: start; min-height: 100%; padding-top: 0; text-align: left; }.assistant-welcome { display: flex; align-items: flex-start; gap: 25px; }.assistant-welcome .empty-orbit { flex: 0 0 auto; width: 45px; height: 45px; box-shadow: none; }.assistant-welcome h1 { margin: 0 0 14px; font-size: 24px; font-weight: 800; }.assistant-welcome p { margin: 0 0 4px; font-size: 18px; line-height: 1.35; }.interest-title { display: block; margin: 50px 0 20px 76px; color: #20222d; font-size: 20px; }.interest-list { display: grid; gap: 13px; width: min(700px, 100%); margin-left: 76px; }.interest-list button { display: flex; align-items: center; gap: 12px; padding: 11px 12px; color: #4a4e5c; background: #f7f7fb; border: 0; border-radius: 10px; font-size: 17px; text-align: left; }.interest-list button span { width: 8px; height: 8px; flex: 0 0 auto; background: #6354f6; border-radius: 50%; }.interest-list button svg { margin-left: auto; color: #8d91a1; }.interest-list button:hover { color: #5a49f4; background: #f1efff; }
.workbench-bottom { padding-bottom: 27px; }.workbench-composer { min-height: 170px; }.workbench-bottom { padding-right: 8.4%; }.workbench-main { grid-template-rows: 28px minmax(0, 1fr) auto; }.assistant-topbar { height: 28px; border-bottom: 0; }.interest-title { margin-top: 14px; }.interest-list { justify-items: start; }.interest-list button { width: max-content; max-width: 100%; }.sources-panel header { padding-right: 20px; padding-left: 20px; }.sources-content { padding-right: 20px; padding-left: 20px; }
@media (max-width: 620px) { .empty-conversation { padding-top: 6px; }.assistant-welcome { gap: 12px; }.assistant-welcome .empty-orbit { width: 36px; height: 36px; }.assistant-welcome h1 { margin-bottom: 7px; font-size: 18px; }.assistant-welcome p { font-size: 13px; }.interest-title { margin: 32px 0 13px 48px; font-size: 16px; }.interest-list { gap: 8px; margin-left: 48px; }.interest-list button { padding: 9px 10px; font-size: 13px; }.workbench-bottom { padding-right: 16px; padding-bottom: 11px; }.workbench-composer { min-height: 136px; } }
@media (max-width: 620px) { .workbench-main { grid-template-rows: 57px minmax(0, 1fr) auto; }.assistant-topbar { height: auto; border-bottom: 1px solid #efeff4; } }

.resource-heading { margin-top: 28px !important; padding-top: 19px; border-top: 1px solid #edf0f4; }
.resource-item { display: flex; align-items: stretch; gap: 6px; margin-bottom: 10px; }
.resource-main { display: grid; flex: 1; gap: 5px; padding: 13px 14px; color: inherit; background: #f7f8fa; border: 0; border-radius: 11px; text-align: left; transition: background 180ms ease, transform 180ms ease; }
.resource-main:hover { background: #edf5fb; transform: translateY(-1px); }
.resource-kind { color: #0871ba; font-size: 11px; font-weight: 800; letter-spacing: .03em; }
.resource-main b { color: #183d5c; font-size: 14px; line-height: 1.45; }
.resource-main small { color: #7f8d99; line-height: 1.5; }
.resource-external { display: grid; place-items: center; width: 38px; color: #5b7690; background: #f2f6f9; border: 0; border-radius: 10px; transition: color 180ms ease, background 180ms ease; }
.resource-external:hover { color: #0871ba; background: #e5f2fa; }
.resource-modal { position: fixed; z-index: 20; inset: 0; display: grid; place-items: center; padding: 4vh 5vw; }
.resource-modal-backdrop { position: absolute; inset: 0; background: rgba(16, 30, 43, .46); backdrop-filter: blur(3px); }
.resource-modal-panel { position: relative; z-index: 1; display: grid; grid-template-rows: auto minmax(0, 1fr) auto; width: min(1120px, 100%); height: min(86vh, 820px); overflow: hidden; background: #fff; border: 1px solid #d9e6ee; border-radius: 16px; box-shadow: 0 28px 80px rgba(11, 35, 55, .25); }
.resource-modal-panel header { display: flex; align-items: center; justify-content: space-between; gap: 18px; padding: 14px 18px; border-bottom: 1px solid #e5edf2; }
.resource-modal-panel header div { display: grid; gap: 3px; min-width: 0; }
.resource-modal-panel header strong { overflow: hidden; color: #183d5c; font-size: 16px; text-overflow: ellipsis; white-space: nowrap; }
.resource-modal-panel header small { overflow: hidden; color: #7b8e9d; text-overflow: ellipsis; white-space: nowrap; }
.resource-modal-panel header button { width: 32px; height: 32px; color: #688095; background: transparent; border: 0; border-radius: 50%; font-size: 25px; line-height: 1; }
.resource-modal-panel header button:hover { color: #0871ba; background: #edf5fa; }
.resource-modal-panel iframe { width: 100%; height: 100%; border: 0; background: #f4f7f9; }
.resource-modal-empty { display: grid; place-items: center; color: #657b8c; background: #f8fafb; }
.resource-modal-panel footer { display: flex; justify-content: flex-end; padding: 10px 14px; border-top: 1px solid #e5edf2; }
.resource-modal-panel footer button { display: inline-flex; align-items: center; gap: 6px; padding: 8px 12px; color: #fff; background: #0871ba; border: 0; border-radius: 7px; font-weight: 700; }
@media (max-width: 620px) { .resource-modal { padding: 0; }.resource-modal-panel { width: 100%; height: 100%; border-radius: 0; } }
</style>
