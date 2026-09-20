<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { MessageCircleMore, SendHorizontal, Sparkles, X } from '@lucide/vue'
import { useRouter } from 'vue-router'
import { pathTo } from '@/config/destinations'
import { buildGeoChatWorkbenchUrl } from '@/config/geochat'

const router = useRouter()
const open = ref(false)
const prompt = ref('')
const focused = ref(false)
const greeting = ref('')
// 「地质资源」后显式换行：这行的自然宽度 ~14em，而气泡可用宽度曾只有 ~13.6em，浏览器只能把
// 放不下的「助手」甩成孤行（用户截图的错误换行）。断点写进文本里，任何视口、任何字体回退下
// 都不会漂移；配合下方 15.2vw 的宽度给两行各留出余量。
const greetingText = 'Hi，我是地智——你的地质资源\n与地质工程学科 AI 学习助手。\n想从哪里开始？'
let greetingDelay: number | undefined
let greetingTimer: number | undefined

const placeholder = computed(() => focused.value ? '输入地质学习问题，Enter 发送' : '问问课程、知识图谱或学习资源')

function navigate(target: 'resources' | 'knowledge-graph' | 'geo-data') {
  const category = target === 'resources' ? 'courses' : undefined
  void router.push({ path: pathTo(target), query: category ? { category } : undefined })
  open.value = false
}

function ask() {
  const question = prompt.value.trim()
  if (!question) return
  const url = buildGeoChatWorkbenchUrl(question)
  window.location.assign(url)
  open.value = false
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    ask()
  }
}

function clearGreetingTimers() {
  if (greetingDelay !== undefined) window.clearTimeout(greetingDelay)
  if (greetingTimer !== undefined) window.clearInterval(greetingTimer)
  greetingDelay = undefined
  greetingTimer = undefined
}

watch(open, (isOpen) => {
  clearGreetingTimers()
  greeting.value = ''
  if (!isOpen) return
  greetingDelay = window.setTimeout(() => {
    let index = 0
    greetingTimer = window.setInterval(() => {
      greeting.value = greetingText.slice(0, index + 1)
      index += 1
      if (index >= greetingText.length) clearGreetingTimers()
    }, 38)
  }, 300)
})

onBeforeUnmount(clearGreetingTimers)
</script>

<template>
  <aside class="floating-ai" aria-label="地质 AI 助手">
    <section :class="['floating-ai-dialog', { 'is-open': open }]" aria-live="polite">
      <button class="floating-ai-close" aria-label="收起 AI 助手" @click="open = false"><X :size="17" /></button>
      <div class="floating-ai-guidance">
        <span class="floating-ai-avatar"><Sparkles :size="22" /></span>
        <p>{{ greeting }}</p>
      </div>
      <div class="floating-ai-functions">
        <button @click="navigate('resources')">查课程</button>
        <button @click="navigate('knowledge-graph')">查知识</button>
        <button @click="navigate('geo-data')">查资料</button>
      </div>
      <div class="floating-ai-suggestions">
        <p>猜你感兴趣</p>
        <button @click="prompt = '油气成藏需要哪些关键地质条件？'">油气成藏需要哪些关键地质条件？</button>
        <button @click="prompt = '储层表征与建模有哪些常见方法？'">储层表征与建模有哪些常见方法？</button>
      </div>
      <form class="floating-ai-composer" @submit.prevent="ask">
        <textarea v-model="prompt" :placeholder="placeholder" rows="2" @focus="focused = true" @blur="focused = false" @keydown="onKeydown"></textarea>
        <button :disabled="!prompt.trim()" aria-label="发送问题" type="submit"><SendHorizontal :size="18" /></button>
      </form>
    </section>
    <button v-show="!open" :class="['floating-ai-helper', { 'is-open': open }]" :aria-expanded="open" aria-label="打开 AI 助手" @click="open = !open">
      <span class="floating-ai-message"><b>Hi，我是地智</b><small>陪你探索地质知识</small></span>
      <span class="floating-ai-helper-avatar"><MessageCircleMore :size="24" /></span>
    </button>
  </aside>
</template>

<style scoped>
/* The launcher and the dialog it opens share one corner, so both use the same fixed inset: the dialog is
   anchored to this box's bottom-right and grows from it (`transform-origin: 100% 100%`), which only lines up
   with the button when the two insets match. These were two different vw values (2.60417vw vs 2.08333vw/1.25vw),
   so the panel grew out of a point the button was not on. */
.floating-ai { position: fixed; z-index: 1010; right: 24px; bottom: 24px; width: 25vw; font-family: "Alibaba PuHuiTi", "Microsoft YaHei", sans-serif; }
/* `grid-template-columns: minmax(0, 1fr)` is not decoration here. Only the rows were declared, so the
   implicit column was `auto`, which sizes to the widest item's MAX-CONTENT — and the 查课程/查知识/查资料
   row is three fixed `6.82292vw` buttons plus gaps, i.e. 357.7px, wider than the panel's 310px content
   box (360px panel minus 2x24px padding minus 2px border). The column therefore grew to 357.7px and every
   sibling grew with it, so the suggestion cards ran 47px past the content box and 23px past the panel
   itself. `minmax(0, 1fr)` lets the track go below its content's min-content size, which is exactly the
   fix already applied to the atlas slide in styles.css for the same failure. */
.floating-ai-dialog { position: absolute; right: 0; bottom: 0; display: grid; grid-template-rows: auto auto 1fr; grid-template-columns: minmax(0, 1fr); gap: 1.25vw; width: 100%; height: 75vh; max-height: 75vh; padding: 4.42708vw 1.66667vw 8.85417vw; opacity: 0; pointer-events: none; background: linear-gradient(180deg, rgba(206, 210, 255, .7), rgba(255, 255, 255, .7) 20%); border: .10417vw solid #fff; border-radius: 1.25vw; box-shadow: 0 0 1.04167vw rgba(0, 0, 0, .1); transform: scale3d(0, 0, 0); transform-origin: 100% 100%; transition: transform 300ms cubic-bezier(.2, .8, .2, 1), opacity 220ms ease; backdrop-filter: blur(1.04167vw); }
.floating-ai-dialog.is-open { opacity: 1; pointer-events: auto; transform: scale(1); }
.floating-ai-close { position: absolute; top: -1.25vw; right: 0; display: grid; place-items: center; width: 2.5vw; height: 2.5vw; color: #30415c; background: #fff; border: 0; border-radius: 50%; box-shadow: 1px 1px .52083vw rgba(0, 0, 0, .1); transition: transform 180ms ease; }.floating-ai-close:hover { transform: rotate(90deg); }
/* Anchor the welcome row to the panel's right edge so a wider bubble grows left into free space.
   The explicit newlines remain authoritative and keep Chinese phrases such as “地质资源” intact. */
.floating-ai-guidance { position: absolute; top: -2.08333vw; right: 0; display: flex; align-items: center; gap: .625vw; }.floating-ai-guidance p { box-sizing: border-box; width: clamp(300px, 18vw, 360px); min-height: 3.95833vw; margin: 0; padding: .83333vw; color: #1e1e28; background: #fff; border: .10417vw solid #fff; border-radius: .83333vw; box-shadow: 1px 1px .52083vw rgba(0, 0, 0, .1); font-size: .9375vw; font-weight: 700; line-height: 1.6; white-space: pre-line; word-break: keep-all; overflow-wrap: normal; }.floating-ai-avatar, .floating-ai-helper-avatar { display: grid; place-items: center; flex: 0 0 auto; color: #fff; background: linear-gradient(135deg, #5c70ff, #0666ff); border-radius: 50%; box-shadow: 0 6px 14px rgba(42, 62, 173, .25); }.floating-ai-avatar { width: clamp(52px, 4.2vw, 56px); height: clamp(52px, 4.2vw, 56px); }
/* `flex: 1` instead of a fixed `6.82292vw`: the three buttons were sized against the viewport while the
   panel is only 25vw wide, so their combined max-content (357.7px) exceeded the panel's 310px content box.
   Letting them fill the row also fixes the phone block, which overrides every property EXCEPT `width` —
   at 390px that fixed value resolved to 26.6px and the two-character labels had nowhere to go. */
.floating-ai-functions { display: flex; align-items: center; justify-content: center; gap: .52083vw; margin-bottom: 1.66667vw; padding: 0 1.66667vw; }.floating-ai-functions button { flex: 1; min-width: 0; padding: .9375vw; color: #fff; background-color: #06f; border: .10417vw solid #fff; border-radius: 1.25vw; font-family: "Alibaba PuHuiTi", "Microsoft YaHei", sans-serif; font-size: 1.14583vw; font-weight: 800; line-height: 1; transition: opacity 180ms ease, transform 180ms ease; }.floating-ai-functions button:hover { opacity: .8; transform: translateY(-2px); }
.floating-ai-suggestions { display: grid; gap: .41667vw; align-content: start; overflow: auto; }.floating-ai-suggestions p { margin: 0; color: #303345; font-size: .83333vw; font-weight: 800; }.floating-ai-suggestions button { position: relative; overflow: hidden; padding: .46875vw .57292vw .46875vw 1.19792vw; color: #4c5264; background: #f5f7ff; border: 1px solid rgba(0, 102, 255, .1); border-radius: .41667vw; text-align: left; font-size: .78125vw; transition: background 180ms ease, color 180ms ease; }.floating-ai-suggestions button::before { content: ""; position: absolute; top: 50%; left: .57292vw; width: .41667vw; height: .41667vw; background: rgba(0, 102, 255, .5); border-radius: .20833vw; transform: translateY(-50%); }.floating-ai-suggestions button:hover { color: #0666ff; background: #fff; font-weight: 900; text-decoration: underline; }
.floating-ai-composer { position: absolute; right: .83333vw; bottom: .83333vw; left: .83333vw; display: flex; align-items: end; gap: .41667vw; padding: .625vw .52083vw .625vw .67708vw; background: #fff; border: .10417vw solid #fff; border-radius: 1.25vw; box-shadow: 0 0 1.04167vw rgba(0, 0, 0, .1); }.floating-ai-composer:focus-within { border-color: rgba(23, 104, 177, .5); box-shadow: 0 .20833vw .20833vw rgba(23, 104, 177, .25); }.floating-ai-composer textarea { flex: 1; min-height: 2.70833vw; padding: .15625vw 0; color: #1e1e28; resize: none; background: transparent; border: 0; outline: 0; font: inherit; font-size: .9375vw; line-height: 1.5; }.floating-ai-composer textarea::placeholder { color: #7d8192; }.floating-ai-composer button { display: grid; place-items: center; width: 2.70833vw; height: 2.70833vw; color: #fff; background: #0666ff; border: 0; border-radius: 50%; transition: transform 180ms ease, opacity 180ms ease; }.floating-ai-composer button:hover:not(:disabled) { transform: rotate(-12deg) scale(1.06); }.floating-ai-composer button:disabled { opacity: .48; }
/* The launcher was `width: 4.16667vw; height: 5.72917vw` — two different lengths — with `border-radius: 50%`,
   which is what turned it into a vertical egg: 53x73 at 1280, 60x83 at 1440, 80x110 at 1920 (h/w = 1.375 at
   every width). A 26px icon centred in a 110px-tall oval reads as a small logo drowning in a big blob.
   `border-radius: 50%` only draws a circle on a square box, so the height must equal the width; the size is
   now capped at the phone value (56px, see the max-width:760px block below) so no desktop screen grows a
   launcher bigger than the one it uses on a phone, and the icon drops to 24px to keep the 43% icon-to-diameter
   ratio Material uses (26px in a 50px circle was half the diameter). */
.floating-ai-helper { position: fixed; right: 24px; bottom: 24px; display: flex; align-items: center; gap: 12px; height: auto; padding: 0; color: #1c2435; background: transparent; border: 0; }.floating-ai-helper-avatar { width: clamp(50px, 3.3vw, 56px); height: clamp(50px, 3.3vw, 56px); transition: transform 220ms cubic-bezier(.2, .8, .2, 1), box-shadow 220ms ease; }.floating-ai-message { display: none; flex-direction: column; justify-content: center; gap: .20833vw; color: #111827; background: #ebedff; border-radius: 1.25vw; }.floating-ai-message b { width: 13.2292vw; padding: .83333vw .83333vw .20833vw; font-size: .9375vw; font-weight: 600; line-height: 1.25; white-space: nowrap; }.floating-ai-message small { padding: 0 .83333vw .52083vw; font-size: .83333vw; font-weight: 400; line-height: 1.25; white-space: nowrap; }.floating-ai-helper:hover .floating-ai-message, .floating-ai-helper:focus-visible .floating-ai-message { display: flex; animation: helper-message 180ms ease both; }.floating-ai-helper:hover .floating-ai-helper-avatar, .floating-ai-helper.is-open .floating-ai-helper-avatar { box-shadow: 0 10px 22px rgba(42, 62, 173, .34); transform: translateY(-3px) scale(1.04); }
@keyframes helper-message { from { opacity: 0; transform: translateX(8px); } to { opacity: 1; transform: translateX(0); } }
@media (max-width: 760px) { .floating-ai { right: 16px; bottom: 16px; width: min(360px, calc(100vw - 28px)); }.floating-ai-dialog { position: fixed; inset: 12px; width: auto; height: auto; max-height: none; gap: 16px; padding: 26px 18px 104px; border-width: 2px; border-radius: 20px; backdrop-filter: blur(12px); }.floating-ai-close { top: 16px; right: 16px; width: 40px; height: 40px; }.floating-ai-guidance { position: static; margin: 0 56px 6px 0; gap: 10px; }.floating-ai-guidance p { flex: 1; width: auto; padding: 13px 16px; border-width: 2px; border-radius: 16px; font-size: 12px; }.floating-ai-avatar { width: 54px; height: 54px; }.floating-ai-functions { gap: 10px; margin-bottom: 16px; padding: 0; }.floating-ai-functions button { min-height: 58px; padding: 10px 5px; border-width: 2px; border-radius: 16px; font-size: 14px; }.floating-ai-suggestions { gap: 8px; }.floating-ai-suggestions p { font-size: 13px; }.floating-ai-suggestions button { padding: 9px 11px 9px 23px; border-radius: 8px; font-size: 13px; }.floating-ai-suggestions button::before { left: 11px; width: 6px; height: 6px; }.floating-ai-composer { right: 12px; bottom: 12px; left: 12px; gap: 8px; padding: 9px 10px 9px 13px; border-width: 2px; border-radius: 20px; }.floating-ai-composer textarea { min-height: 42px; padding: 3px 0; font-size: 14px; }.floating-ai-composer button { width: 40px; height: 40px; }.floating-ai-helper { right: 16px; bottom: 16px; gap: 12px; height: auto; }.floating-ai-helper-avatar { width: 56px; height: 56px; }.floating-ai-message { display: none !important; } }
</style>
