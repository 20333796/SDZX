<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import {
  ChevronDown,
  ChevronRight,
  Menu,
  Sparkles,
  X
} from '@lucide/vue'
import { fallbackPortalConfig } from '@/config/portal'
import { destinationForTarget } from '@/config/destinations'
import { buildGeoChatAgentUrl } from '@/config/geochat'
import type { PortalConfig, PortalNavigationLink } from '@/types'
import { router } from '@/router'
import { session } from '@/session'
import AccountEntry from '@/features/account/AccountEntry.vue'
import AssistantWorkspace from '@/features/chat/AssistantWorkspace.vue'
import FloatingAssistant from '@/features/chat/FloatingAssistant.vue'
import MajorAtlas from '@/features/home/MajorAtlas.vue'

const menuOpen = ref(false)
const headerCondensed = ref(false)
const portalConfig = ref<PortalConfig>(fallbackPortalConfig)
const deck = ref<HTMLElement | null>(null)
const activeSlide = ref('slide-home')

// The drawer carries the account entry on phones, since the condensed bar hides the header chip.
const isAuthenticated = session.isAuthenticated
const displayName = session.displayName

function goSignIn() {
  menuOpen.value = false
  void router.push({ name: 'sign-in' })
}

function signOut() {
  menuOpen.value = false
  session.signOut()
}

// The first screen is the assistant itself; the two atlases follow as their own screens.
const slides = [
  { id: 'slide-home', label: '智慧问答' },
  { id: 'slide-course', label: '课程图谱' },
  { id: 'slide-ability', label: '能力图谱' }
]

function goToSlide(target: string) {
  menuOpen.value = false
  document.getElementById(target)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function openGeoChat() {
  window.location.assign(buildGeoChatAgentUrl())
}

function navigate(link: PortalNavigationLink) {
  menuOpen.value = false
  // Each column is its own page now, so the header just asks the destination table where it lives.
  // The old version inferred the layer from the id's spelling here as well as on the layers page;
  // the table is the only place that mapping exists.
  const destination = destinationForTarget(link.target)
  if (!destination) {
    console.warn('[portal] 未配置的栏目:', link.target)
    return
  }
  void router.push({ path: destination.path, query: link.category ? { category: link.category } : undefined })
}

async function loadPortalConfig() {
  try {
    const response = await fetch('/api/v1/portal-config')
    if (!response.ok) throw new Error('Portal API unavailable')
    portalConfig.value = await response.json() as PortalConfig
  } catch {
    portalConfig.value = fallbackPortalConfig
  }
}

// The deck is the scroll container, so the header and the pager follow its offset.
function syncDeck() {
  const container = deck.value
  if (!container) return
  headerCondensed.value = container.scrollTop > 86
  const anchor = container.getBoundingClientRect().top
  let current = slides[0].id
  for (const slide of slides) {
    const node = document.getElementById(slide.id)
    if (!node) continue
    if (node.getBoundingClientRect().top - anchor <= container.clientHeight * 0.45) current = slide.id
  }
  activeSlide.value = current
}

onMounted(() => {
  void loadPortalConfig()
  syncDeck()
  deck.value?.addEventListener('scroll', syncDeck, { passive: true })
  window.addEventListener('resize', syncDeck, { passive: true })
  // A `#slide-*` hash means "open the deck on this screen" — that is how the portal header's three
  // entries (智慧问答 / 课程图谱 / 能力图谱) reach these screens from another route, e.g. the header on
  // /layers. The deck is the scroll container and the route transition can land before layout settles,
  // so scroll on the next frame rather than in the same tick.
  const target = window.location.hash.slice(1)
  if (slides.some((slide) => slide.id === target)) {
    requestAnimationFrame(() => {
      document.getElementById(target)?.scrollIntoView({ block: 'start' })
    })
  }
})

onBeforeUnmount(() => {
  deck.value?.removeEventListener('scroll', syncDeck)
  window.removeEventListener('resize', syncDeck)
})
</script>

<template>
  <main>
    <div ref="deck" class="deck">
      <section id="slide-home" class="deck-slide hero-shell" aria-label="首页 · 智慧问答">
        <!-- 实景地质剖面图（深海钻井/三维地层块）：压在全部绘制层之下作hero底图，
             蓝调渐变罩负责与品牌色融合、保证文字可读（见 styles.css .hero-photo）。 -->
        <div class="hero-photo" aria-hidden="true"></div>
        <div class="topographic-lines" aria-hidden="true"></div>
        <!-- Drawn scene layers (see styles.css "The hero scene is drawn, not photographed"): the two
             aurora blobs drift behind the contour rings to keep the hero alive without a photo. -->
        <div class="hero-aurora aurora-west" aria-hidden="true"></div>
        <div class="hero-aurora aurora-east" aria-hidden="true"></div>
        <!-- 深部地层剖面：四条层界带自下而上堆叠、越深越暗、错拍缓移——地质语言是"深地"的
             层序剖面（向下分层），不是地表山川。 -->
        <div class="geo-stratum stratum-d1" aria-hidden="true"></div>
        <div class="geo-stratum stratum-d2" aria-hidden="true"></div>
        <div class="geo-stratum stratum-d3" aria-hidden="true"></div>
        <div class="geo-stratum stratum-d4" aria-hidden="true"></div>
        <!-- 高感知动效层：六组跃动微粒（沉积颗粒/矿物晶体在层带间断续起跳、悬停、落回，
             粒径/密度/时长/相位/跳跃幅度彼此错开，配合明暗闪烁）。原先的"全幅斜向扫光 +
             层界左→右掠光"按用户要求移除，横向扫掠一律取消，运动感改由粒子的纵向跃动承担。 -->
        <div class="geo-motes motes-a" aria-hidden="true"></div>
        <div class="geo-motes motes-b" aria-hidden="true"></div>
        <div class="geo-motes motes-c" aria-hidden="true"></div>
        <div class="geo-motes motes-d" aria-hidden="true"></div>
        <div class="geo-motes motes-e" aria-hidden="true"></div>
        <div class="geo-motes motes-f" aria-hidden="true"></div>

        <header :class="['site-header', { 'is-condensed': headerCondensed }]">
          <a class="brand" href="#top" aria-label="返回首页">
            <img class="brand-university-logo" src="/cupb-logo.png" alt="中国石油大学（北京）" />
            <span class="brand-product">深地智学</span>
          </a>
          <nav class="main-nav" aria-label="平台导航">
            <div class="nav-group">
              <button class="nav-group-primary" @click="goToSlide(slides[0].id)">
                <span>深地智学</span>
              </button>
              <div class="nav-inline-links" aria-label="首页栏目">
                <button v-for="screen in slides" :key="screen.id" @click="goToSlide(screen.id)">{{ screen.label }}</button>
              </div>
              <div class="nav-submenu" aria-label="深地智学栏目">
                <button v-for="screen in slides" :key="screen.id" @click="goToSlide(screen.id)">{{ screen.label }}</button>
              </div>
            </div>
            <div v-for="item in portalConfig.navigation" :key="item.title" class="nav-group">
              <button class="nav-group-primary" @click="navigate(item.links[0])">
                <span>{{ item.title }}</span>
              </button>
              <div class="nav-inline-links" :aria-label="`${item.title}栏目`">
                <button v-for="link in item.links" :key="link.label" @click="navigate(link)">{{ link.label }}</button>
              </div>
              <div class="nav-submenu" :aria-label="`${item.title}栏目`">
                <button v-for="link in item.links" :key="link.label" @click="navigate(link)">{{ link.label }}</button>
              </div>
            </div>
          </nav>
          <!-- Signed out this is the 登录 / 注册 entry; signed in it is the account chip. It used to be a
               hard-coded 访客 chip with a dropdown arrow, i.e. an account menu for an account that could not
               exist yet. Both headers render this one component so the two cannot disagree about who is here. -->
          <AccountEntry class="site-profile" />
          <button class="mobile-menu-toggle" :aria-expanded="menuOpen" aria-controls="mobile-navigation" aria-label="展开平台导航" @click="menuOpen = !menuOpen">
            <X v-if="menuOpen" :size="22" /><Menu v-else :size="22" />
          </button>
        </header>

        <nav v-if="menuOpen" id="mobile-navigation" class="mobile-navigation" aria-label="移动端平台导航">
          <section>
            <strong>深地智学</strong>
            <button v-for="screen in slides" :key="screen.id" @click="goToSlide(screen.id)">{{ screen.label }}</button>
          </section>
          <section v-for="item in portalConfig.navigation" :key="item.title">
            <strong>{{ item.title }}</strong>
            <button v-for="link in item.links" :key="link.label" @click="navigate(link)">{{ link.label }}</button>
          </section>
          <!-- The bar hides the account chip below 760px, so the drawer is where the account lives on a phone. -->
          <section>
            <strong>账号</strong>
            <button v-if="!isAuthenticated" @click="goSignIn">登录 / 注册</button>
            <button v-else @click="signOut">退出登录（{{ displayName }}）</button>
          </section>
        </nav>

        <div id="top" class="hero-content">
          <span class="hero-laurel hero-laurel-left" aria-hidden="true"></span>
          <span class="hero-laurel hero-laurel-right" aria-hidden="true"></span>
          <div class="hero-identification" aria-label="中国石油大学北京校区">
            <span aria-hidden="true"></span>
            <small>CHINA UNIVERSITY OF PETROLEUM, BEIJING</small>
          </div>
          <h1>智赋深地</h1>
          <p class="hero-subtitle">地质资源与地质工程学科教育大模型</p>

          <div class="qa-stage">
            <AssistantWorkspace landing />
          </div>
        </div>

        <aside class="hero-stats" aria-label="平台状态">
          <div v-for="stat in portalConfig.stats" :key="stat.label"><span>{{ stat.value }}</span><strong>{{ stat.label }}</strong></div>
        </aside>

        <button class="deck-scroll-hint" @click="goToSlide('slide-course')">向下浏览 <ChevronDown :size="19" /></button>
      </section>

      <MajorAtlas />

      <footer class="site-footer">
        <div><strong>深地智学</strong><span>中国石油大学（北京）地质资源与地质工程学科教育大模型</span></div>
        <span>课程资源保留原平台版权与访问规则</span>
      </footer>
    </div>

    <!-- Bottom-left corner entry, framing the page against the floating assistant at bottom-right. It sits
         here, outside the deck and outside .hero-content, for a reason: .hero-content carries a transform
         (matrix(1,0,0,1,0,0) from its entrance animation), and a transformed ancestor becomes the
         containing block for `position: fixed` descendants — inside the hero the button was measured at
         x=294 at 1440 instead of 24, and it scrolled away with the deck (-190 after one screen).
         It belongs to the 智慧问答 screen only: the rest of the deck scrolls *inside* .deck, so a fixed
         chip would otherwise hang over 课程图谱 and 能力图谱 too. `activeSlide` is the very value the
         right-hand pager follows, so the two appear and disappear together. -->
    <Transition name="corner-entry">
      <button v-if="activeSlide === 'slide-home'" class="ai-center-entry" @click="openGeoChat"><Sparkles :size="18" />AI应用中心 <ChevronRight :size="18" /></button>
    </Transition>

    <nav class="deck-nav" aria-label="首页分页">
      <button v-for="slide in slides" :key="slide.id" :class="{ active: activeSlide === slide.id }" :aria-current="activeSlide === slide.id ? 'true' : undefined" @click="goToSlide(slide.id)">
        <i aria-hidden="true"></i><span>{{ slide.label }}</span>
      </button>
    </nav>

    <FloatingAssistant />
  </main>
</template>

<style scoped>
.deck-scroll-hint { position: absolute; bottom: 30px; left: 50%; display: inline-flex; align-items: center; gap: 8px; padding: 10px 20px; color: rgba(255, 255, 255, .92); background: rgba(4, 44, 92, .34); border: 1px solid rgba(206, 233, 255, .32); border-radius: 30px; font-size: 14px; font-weight: 700; transform: translateX(-50%); animation: hint-bob 2.4s ease-in-out infinite; transition: background .2s ease; }
.deck-scroll-hint:hover { background: rgba(9, 66, 132, .6); }

.qa-stage { position: relative; width: min(920px, 100%); margin: 0 auto; text-align: left; }
.hero-content .hero-subtitle { margin-bottom: 30px; }
.qa-stage :deep(.assistant-workspace) { border-radius: 18px; box-shadow: 0 22px 54px rgba(6, 30, 70, .22); }
/* The entry belongs in the bottom-left corner of the viewport, framing the page against the floating
   assistant in the bottom-right — on the reference site the two corner entries sit at the same inset.
   It used to be `position: static` inside the hero's centred column, which left it trailing the prompt
   box at 290px from the left edge, neither centred nor at the corner. The inset matches the floating
   assistant's 24px so the two read as a pair. It has to stay a direct child of <main>: a transformed
   ancestor (the hero carries one) becomes the containing block for `position: fixed`, which is exactly
   how it ended up 294px from the left and scrolling away with the deck. */
.ai-center-entry { position: fixed; z-index: 30; left: 24px; bottom: 24px; display: inline-flex; align-items: center; justify-content: center; gap: 7px; min-width: 208px; height: 54px; color: #fff; background: rgba(34, 112, 194, .78); border: 1px solid rgba(202, 232, 255, .34); border-radius: 30px; font-size: 16px; font-weight: 800; backdrop-filter: blur(8px); transition: transform .2s ease, background .2s ease; }
.ai-center-entry:hover { background: rgba(51, 141, 226, .95); transform: translateY(-2px); }
/* The chip leaves with the 智慧问答 screen instead of popping out mid-scroll. Declared after
   .ai-center-entry on purpose: same specificity, so the later transition wins while entering/leaving. */
.corner-entry-enter-active, .corner-entry-leave-active { transition: opacity .22s ease, transform .22s ease; }
.corner-entry-enter-from, .corner-entry-leave-to { opacity: 0; transform: translateY(10px); }

.deck-nav { position: fixed; z-index: 30; top: 50%; right: 24px; display: grid; gap: 14px; transform: translateY(-50%); }
.deck-nav button { display: inline-flex; align-items: center; gap: 9px; padding: 6px 12px 6px 6px; color: #6c6e85; background: rgba(255, 255, 255, .82); border: 1px solid #e3e3ef; border-radius: 30px; font-size: 12px; font-weight: 700; backdrop-filter: blur(8px); transition: color .2s ease, background .2s ease, border-color .2s ease; }
.deck-nav button i { width: 9px; height: 9px; background: #c8c9dc; border-radius: 50%; transition: background .2s ease, transform .2s ease; }
.deck-nav button span { max-width: 0; overflow: hidden; white-space: nowrap; transition: max-width .28s ease; }
.deck-nav button:hover span, .deck-nav button.active span { max-width: 92px; }
.deck-nav button:hover { color: #4c37d8; border-color: #d3cbff; }
.deck-nav button.active { color: #4c37d8; background: #fff; border-color: #d3cbff; box-shadow: 0 8px 20px rgba(76, 55, 216, .12); }
.deck-nav button.active i { background: #5f4ae8; transform: scale(1.35); }

@keyframes hint-bob { 50% { transform: translate(-50%, 7px); } }

@media (max-width: 1120px) { .deck-nav { right: 12px; gap: 10px; } .deck-nav button span { display: none; } .deck-nav button { padding: 6px; } }
/* On phones the entry keeps the corner rather than going back into the flow (the flow position no longer
   exists — it is outside the deck now), so it shrinks to a compact chip. */
@media (max-width: 760px) { .deck-nav { display: none; } .ai-center-entry { left: 16px; bottom: 16px; min-width: 0; height: 46px; padding: 0 16px; font-size: 14px; backdrop-filter: none; } /* 手机端问答卡改为全宽后，右侧悬挂的统计列必然重叠（绝对定位旧方案）；
   改为回到文档流：横向一排居中放在问答卡正下方，同时填补卡片下方的大片空白 */ .deck-slide .hero-stats { position: static; display: flex; justify-content: center; gap: 38px; margin: 22px auto 0; text-align: center; } .deck-slide .hero-stats span { font-size: 22px; } .deck-slide .hero-stats strong { font-size: 11px; } }
/* The hint is centred and only 125px wide, so it starts at (100vw - 125px) / 2: below ~500px that lands
   inside the corner entry's 16..171px span, and once the hero screen is a full viewport tall again the
   two sit in the same bottom strip (both ~16px off the floor).    Lift the hint above the entry rather than
   dropping either one. Declared with three classes on purpose — the global sheet sets this at
   `.deck .deck-scroll-hint` (0,2,0), and `max-height: 870px` reaches phones too. (The stats column was
   previously lifted here too, but on phones it is now hidden entirely — see the 760px block.) */
@media (max-width: 500px) {
  .deck-slide .deck-scroll-hint { bottom: 78px; }
}
</style>
