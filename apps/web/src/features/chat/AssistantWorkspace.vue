<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { ChevronDown, Compass, Layers3, LoaderCircle, Search, SendHorizontal, Sparkles } from '@lucide/vue'
import type { ChatResourceReference, Citation } from '@/types'
import { buildGeoChatWorkbenchUrl } from '@/config/geochat'

type ChatMode = 'conversation' | 'search' | 'inquiry'
type ChatMessage = { role: 'assistant' | 'user'; content: string; citations?: Citation[]; resources?: ChatResourceReference[] }

const props = withDefaults(defineProps<{
  landing?: boolean
  standalone?: boolean
  initialPrompt?: string
  initialMode?: ChatMode
}>(), {
  landing: false,
  standalone: false,
  initialPrompt: '',
  initialMode: 'conversation'
})

const mode = ref<ChatMode>(props.initialMode)
const prompt = ref('')
const loading = ref(false)
const focused = ref(false)
const showSources = ref(false)
const messages = ref<ChatMessage[]>([])
const answerScroll = ref<HTMLElement | null>(null)

const modeOptions: Array<{ id: ChatMode; label: string; prompt: string; icon: typeof Search }> = [
  { id: 'conversation', label: '问地质', prompt: '油气成藏需要哪些关键地质条件？', icon: Sparkles },
  { id: 'search', label: '查课程', prompt: '推荐油矿地质学的学习资源。', icon: Search },
  { id: 'inquiry', label: '做探究', prompt: '帮我设计一个测井曲线储层判识的学习任务。', icon: Compass }
]

const statusText = computed(() => {
  if (!loading.value) return ''
  return mode.value === 'search' ? '正在检索课程资料' : mode.value === 'inquiry' ? '正在组织探究路径' : '正在分析地质问题'
})

function chooseMode(option: typeof modeOptions[number]) {
  mode.value = option.id
  prompt.value = option.prompt
}

function onComposerKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    void sendQuestion()
  }
}

async function scrollAnswers() {
  await nextTick()
  answerScroll.value?.scrollTo({ top: answerScroll.value.scrollHeight, behavior: 'smooth' })
}

async function sendQuestion() {
  const question = prompt.value.trim()
  if (!question || loading.value) return

  if (props.landing) {
    window.location.assign(buildGeoChatWorkbenchUrl(question))
    return
  }

  messages.value.push({ role: 'user', content: question })
  prompt.value = ''
  loading.value = true
  const answer: ChatMessage = { role: 'assistant', content: '' }
  messages.value.push(answer)
  await scrollAnswers()

  try {
    const response = await fetch('/api/v1/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode: mode.value, message: question })
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
      events.forEach((event) => {
        const dataLine = event.split('\n').find((line) => line.startsWith('data: '))
        if (!dataLine) return
        const eventName = event.split('\n').find((line) => line.startsWith('event: '))?.slice(7)
        const payload = JSON.parse(dataLine.slice(6)) as { content?: string; citations?: Citation[]; resources?: ChatResourceReference[] }
        if (payload.content) answer.content += payload.content
        if (eventName === 'sources' && payload.citations) answer.citations = payload.citations
        if (eventName === 'resources' && payload.resources) answer.resources = payload.resources
      })
      void scrollAnswers()
    }
  } catch {
    answer.content = '地质知识服务正在连接中。你可以先从油矿地质学、测井解释或油气田勘探资源开始。'
  } finally {
    loading.value = false
    void scrollAnswers()
  }
}

onMounted(() => {
  if (!props.initialPrompt) return
  prompt.value = props.initialPrompt
  void sendQuestion()
})
</script>

<template>
  <section :class="['assistant-workspace', { landing, 'has-messages': messages.length, standalone }]" aria-label="深地智学匿名问答">
    <div class="assistant-intro">
      <div class="assistant-avatar" aria-hidden="true"><span></span><Layers3 :size="31" /></div>
      <div><h2>Hi，<span>我是地智——你的地质资源与地质工程学科 AI 学习助手，欢迎随时向我提问！</span></h2></div>
    </div>

    <div class="assistant-tools" role="tablist" aria-label="问答能力">
      <button v-for="option in modeOptions" :key="option.id" :class="{ active: mode === option.id }" role="tab" :aria-selected="mode === option.id" @click="chooseMode(option)">
        <component :is="option.icon" :size="17" />{{ option.label }}
      </button>
    </div>

    <div ref="answerScroll" class="assistant-answer-area" aria-live="polite">
      <template v-if="messages.length">
        <article v-for="(message, index) in messages" :key="index" :class="['assistant-message', message.role]">
          <p v-if="message.content">{{ message.content }}</p>
          <div v-else-if="message.role === 'assistant' && loading" class="assistant-thinking"><LoaderCircle :size="16" />{{ statusText }}<span class="typing-dots"></span></div>
          <button v-if="message.citations?.length" class="sources-toggle" @click="showSources = !showSources">来源 {{ message.citations.length }} <ChevronDown :size="14" :class="{ flipped: showSources }" /></button>
          <ul v-if="showSources && message.citations?.length" class="assistant-sources">
            <li v-for="citation in message.citations" :key="`${citation.document_id}-${citation.source_locator}`">{{ citation.title }}{{ citation.source_locator ? ` · ${citation.source_locator}` : '' }}</li>
          </ul>
          <ul v-if="message.resources?.length" class="assistant-resources">
            <li v-for="resource in message.resources" :key="resource.id">
              <a v-if="resource.url" :href="resource.url" target="_blank" rel="noopener noreferrer">{{ resource.title }}</a>
              <a v-else-if="resource.route" :href="resource.route">{{ resource.title }}</a>
              <span v-else>{{ resource.title }}</span>
              <small>{{ resource.url || '暂无可用访问地址' }}</small>
            </li>
          </ul>
        </article>
      </template>
    </div>

    <div :class="['assistant-composer', { focused }]">
      <textarea v-model="prompt" aria-label="输入地质学问题" placeholder="输入你想了解的地质问题" rows="2" :disabled="loading" @focus="focused = true" @blur="focused = false" @keydown="onComposerKeydown"></textarea>
      <div class="composer-footer">
        <span>Enter 发送 · Shift + Enter 换行</span>
        <button :disabled="loading || !prompt.trim()" @click="sendQuestion"><SendHorizontal :size="17" />发送</button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.assistant-workspace { position: relative; width: min(886px, 100%); height: 298px; padding: 22px 29px 26px; color: #fff; background: rgba(14, 58, 107, .74); border: 1px solid rgba(225, 240, 255, .28); border-radius: 48px; box-shadow: 0 24px 70px rgba(1, 13, 38, .24); backdrop-filter: blur(11px); }
.assistant-intro { display: flex; align-items: center; justify-content: center; min-height: 50px; padding-left: 68px; }.assistant-avatar { position: absolute; top: -29px; left: 60px; display: grid; place-items: center; width: 74px; height: 74px; color: #d9f7ff; background: linear-gradient(145deg, #0b9bea, #0562c8); border: 2px solid rgba(228, 249, 255, .75); border-radius: 48% 52% 45% 55%; box-shadow: 0 12px 24px rgba(1, 28, 88, .34); animation: avatar-float 4s ease-in-out infinite; }.assistant-intro h2 { margin: 0; color: #fff; font-family: "Microsoft YaHei", sans-serif; font-size: clamp(17px, 1.8vw, 24px); line-height: 1.35; }.assistant-intro h2 span { font-size: .76em; font-weight: 500; }
.assistant-tools { position: absolute; z-index: 2; bottom: 47px; left: 49px; display: flex; flex-wrap: wrap; gap: 10px; }.assistant-tools button { display: inline-flex; align-items: center; gap: 5px; padding: 7px 12px; color: #9ba8b5; background: rgba(247, 249, 252, .72); border: 0; border-radius: 16px; font-size: 12px; font-weight: 700; transition: color .18s ease, background .18s ease, transform .18s ease; }.assistant-tools button:hover, .assistant-tools button.active { color: #1573f4; background: #e6f4ff; transform: translateY(-1px); }.assistant-tools button.active { box-shadow: 0 4px 12px rgba(10, 104, 255, .15); }
.assistant-answer-area { min-height: 0; max-height: 120px; margin: 0 10px 7px; padding: 0 6px; overflow: auto; scrollbar-width: thin; }.assistant-workspace:not(.has-messages) .assistant-answer-area { display: none; }.assistant-message { width: fit-content; max-width: 87%; margin: 0 0 10px; padding: 9px 13px; border-radius: 12px; font-size: 13px; line-height: 1.65; animation: message-in .24s ease-out both; }.assistant-message p { margin: 0; white-space: pre-wrap; }.assistant-message.assistant { color: #22324a; background: #eff7ff; border-bottom-left-radius: 4px; }.assistant-message.user { margin-left: auto; color: #fff; background: #1674ef; border-bottom-right-radius: 4px; font-weight: 600; }.assistant-thinking { display: inline-flex; align-items: center; gap: 7px; color: #dbeeff; }.assistant-thinking svg { animation: spin .8s linear infinite; }.typing-dots::after { content: "..."; display: inline-block; width: 16px; overflow: hidden; vertical-align: bottom; animation: dots 1.2s steps(4, end) infinite; }
.sources-toggle { display: inline-flex; align-items: center; gap: 3px; margin-top: 9px; padding: 0; color: #095a9c; background: transparent; border: 0; font-size: 12px; }.sources-toggle svg { transition: transform .2s ease; }.sources-toggle svg.flipped { transform: rotate(180deg); }.assistant-sources { display: grid; gap: 5px; margin: 9px 0 0; padding: 9px 0 0 17px; color: #5f6170; border-top: 1px solid #d9e9f6; font-size: 12px; }
.assistant-resources { display: grid; gap: 5px; margin: 9px 0 0; padding: 9px 0 0 17px; color: #31546c; border-top: 1px solid #d9e9f6; font-size: 12px; }.assistant-resources li { display: flex; align-items: center; gap: 7px; }.assistant-resources a { color: #0871ba; font-weight: 700; text-decoration: none; }.assistant-resources small { color: #7a8d9c; }
.assistant-composer { min-height: 178px; padding: 21px 22px 18px; background: #fff; border: 0; border-radius: 33px; transition: box-shadow .2s ease, transform .2s ease; }.assistant-workspace:not(.has-messages) .assistant-composer { position: absolute; right: 29px; bottom: 28px; left: 29px; }.assistant-composer.focused { box-shadow: 0 0 0 3px rgba(121, 193, 255, .54), 0 12px 28px rgba(2, 21, 66, .18); transform: translateY(-2px); }.assistant-composer textarea { display: block; width: 100%; min-height: 72px; padding: 0; resize: none; color: #26384e; background: transparent; border: 0; outline: 0; font: inherit; font-size: 18px; line-height: 1.6; }.assistant-composer textarea::placeholder { color: #a4a9b1; }.composer-footer { display: flex; align-items: center; justify-content: flex-end; gap: 12px; color: #9899a2; font-size: 11px; }.composer-footer > span { display: none; }.composer-footer button { display: inline-flex; align-items: center; gap: 7px; padding: 15px 29px; color: #fff; background: #1477f5; border: 0; border-radius: 28px; font-size: 17px; font-weight: 700; transition: transform .16s ease, opacity .16s ease, background .16s ease; }.composer-footer button:not(:disabled):hover { background: #0563dc; transform: translateY(-2px); }.composer-footer button:disabled { opacity: .45; cursor: not-allowed; }
.assistant-workspace.has-messages .assistant-tools { display: none; }.assistant-workspace.has-messages .assistant-answer-area { position: absolute; top: 74px; right: 29px; bottom: 142px; left: 29px; max-height: none; margin: 0; }.assistant-workspace.has-messages .assistant-composer { position: absolute; right: 29px; bottom: 20px; left: 29px; min-height: 112px; padding: 12px 16px; border-radius: 24px; }.assistant-workspace.has-messages .assistant-composer textarea { min-height: 44px; font-size: 14px; }.assistant-workspace.has-messages .composer-footer button { padding: 9px 18px; font-size: 14px; }
.assistant-workspace.standalone { min-height: 560px; height: min(70vh, 720px); background: rgba(8, 46, 94, .84); }.assistant-workspace.standalone .assistant-intro { justify-content: flex-start; padding-left: 110px; }.assistant-workspace.standalone .assistant-avatar { left: 48px; }.assistant-workspace.standalone.has-messages .assistant-answer-area { top: 104px; bottom: 190px; }.assistant-workspace.standalone.has-messages .assistant-composer { bottom: 30px; min-height: 142px; padding: 17px 20px; }.assistant-workspace.standalone.has-messages .assistant-composer textarea { min-height: 62px; font-size: 16px; }.assistant-workspace.standalone.has-messages .composer-footer button { padding: 12px 22px; font-size: 15px; }
.assistant-workspace.landing { background: rgba(5, 63, 137, .52); border-color: rgba(177, 221, 255, .25); box-shadow: none; backdrop-filter: none; }.assistant-workspace.landing .assistant-avatar { top: -30px; left: 42px; width: 132px; height: 78px; color: #eaf9ff; background: linear-gradient(164deg, #6cddff 0 12%, #0879d7 13% 30%, #e9f8ff 31% 39%, #196fca 40% 56%, #bdefff 57% 64%, #0659b6 65% 82%, #0f4f98 83%); border: 2px solid rgba(230, 250, 255, .82); border-radius: 58% 42% 49% 51% / 64% 61% 39% 36%; box-shadow: 0 13px 25px rgba(1, 28, 88, .34), inset 0 0 0 4px rgba(0, 65, 142, .12); }.assistant-workspace.landing .assistant-avatar::before { content: ""; position: absolute; top: 10px; right: 17px; width: 27px; height: 27px; background: rgba(255,255,255,.86); border-radius: 50%; box-shadow: 0 0 0 7px rgba(197, 244, 255, .22); }.assistant-workspace.landing .assistant-avatar span { position: absolute; right: 0; bottom: -5px; left: 0; height: 22px; background: repeating-radial-gradient(ellipse at 50% 150%, transparent 0 8px, rgba(193, 240, 255, .9) 9px 10px, transparent 11px 18px); opacity: .9; }.assistant-workspace.landing .assistant-avatar svg { position: relative; z-index: 1; width: 38px; height: 38px; margin-left: -35px; filter: drop-shadow(0 2px 2px rgba(0, 42, 100, .28)); }.assistant-workspace.landing .assistant-intro { min-height: 48px; padding-left: 116px; }.assistant-workspace.landing .assistant-intro h2 { font-size: 25px; font-weight: 800; }.assistant-workspace.landing .assistant-intro h2 span { font-size: 18px; font-weight: 500; }.assistant-workspace.landing .assistant-composer { border-radius: 31px; }.assistant-workspace.landing .assistant-tools { bottom: 46px; left: 58px; gap: 13px; }.assistant-workspace.landing .assistant-tools button { padding: 6px 10px; color: rgba(138, 148, 161, .62); background: rgba(246, 247, 249, .56); font-size: 12px; }.assistant-workspace.landing .assistant-tools button.active { color: #1477f5; background: #edf7ff; box-shadow: 0 4px 12px rgba(10, 104, 255, .15); }.assistant-workspace.landing .composer-footer button { min-width: 136px; padding: 16px 27px; background: #2178f6; }.assistant-workspace.landing .composer-footer button:disabled { opacity: 1; color: rgba(255,255,255,.97); background: #2178f6; }
@keyframes avatar-float { 0%, 100% { transform: translateY(0) rotate(-2deg); } 50% { transform: translateY(-5px) rotate(2deg); } } @keyframes message-in { from { opacity: 0; transform: translateY(8px) scale(.98); } to { opacity: 1; transform: translateY(0) scale(1); } } @keyframes spin { to { transform: rotate(360deg); } } @keyframes dots { to { width: 0; } }
@media (max-width: 760px) { .assistant-workspace { height: auto; min-height: 0; padding: 17px; border-radius: 28px; }.assistant-intro { justify-content: flex-start; min-height: 42px; padding-left: 51px; }.assistant-avatar { top: 12px; left: 17px; width: 42px; height: 42px; }.assistant-intro h2 { font-size: 16px; }.assistant-answer-area { max-height: 150px; margin-top: 13px; }.assistant-tools { position: static; margin: 17px 0 12px; gap: 6px; }.assistant-tools button { padding: 7px 9px; font-size: 11px; }.assistant-workspace:not(.has-messages) .assistant-composer { position: static; }.assistant-composer { min-height: 136px; padding: 16px; border-radius: 22px; }.assistant-composer textarea { min-height: 50px; font-size: 14px; }.composer-footer button { padding: 10px 17px; font-size: 14px; } }
@media (max-width: 760px) {
  /* 手机端首页问答卡：占满内容区并居中（.qa-stage 自带 margin auto），字号回到可读尺寸。
     旧版把整卡压成 190x76、字号 4-6px，用户明确要求"居中且占主要内容"。 */
  .assistant-workspace.landing { width: 100%; height: auto; min-height: 0; padding: 16px 16px 18px; border-radius: 22px; border-color: rgba(177, 221, 255, .36); }
  .assistant-workspace.landing .assistant-intro { min-height: 0; padding-left: 58px; justify-content: flex-start; align-items: center; }
  .assistant-workspace.landing .assistant-avatar { top: 16px; left: 14px; width: 40px; height: 40px; border-width: 1.5px; }
  .assistant-workspace.landing .assistant-avatar::before, .assistant-workspace.landing .assistant-avatar span { display: none; }
  .assistant-workspace.landing .assistant-avatar svg { width: 18px; height: 18px; margin: 0; }
  .assistant-workspace.landing .assistant-intro h2 { font-size: 14px; line-height: 1.5; white-space: normal; }
  .assistant-workspace.landing .assistant-intro h2 span { font-size: 11px; }
  .assistant-workspace.landing .assistant-tools { position: static; gap: 7px; margin: 13px 0 11px; }
  .assistant-workspace.landing .assistant-tools button { gap: 4px; padding: 6px 10px; border-radius: 10px; font-size: 11px; }
  .assistant-workspace.landing .assistant-tools button svg { width: 12px; height: 12px; }
  .assistant-workspace.landing .assistant-composer, .assistant-workspace.landing:not(.has-messages) .assistant-composer { position: static; min-height: 96px; padding: 12px 13px 10px; border-radius: 16px; }
  .assistant-workspace.landing .assistant-composer textarea { min-height: 40px; font-size: 13px; line-height: 1.5; }
  .assistant-workspace.landing .composer-footer { position: static; margin-top: 4px; }
  .assistant-workspace.landing .composer-footer button { min-width: 0; padding: 8px 16px; border-radius: 12px; font-size: 13px; }
  .assistant-workspace.landing .composer-footer button svg { width: 14px; height: 14px; }
}
</style>
