<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Menu, X } from '@lucide/vue'
import { fallbackPortalConfig } from '@/config/portal'
import { destinationForTarget, groupOf } from '@/config/destinations'
import { session } from '@/session'
import AccountEntry from '@/features/account/AccountEntry.vue'
import FloatingAssistant from '@/features/chat/FloatingAssistant.vue'
import type { PortalNavigationLink } from '@/types'

// The chrome every portal column shares: header + mobile navigation, the hero band, the footer and the
// floating assistant. Each column is a real page of its own (see router.ts) and renders inside this
// layout, so no column has to re-declare the navigation — which is what let the old single page drift
// away from the homepage header in the first place.
const route = useRoute()
const router = useRouter()
const menuOpen = ref(false)
// The bar is part of the page's colour band until the page moves: at the top there is no background at
// all, so the hero's gradient runs up behind it and the two read as one surface; once the page scrolls
// it has to separate from the light content sliding under it, and only then does it get a surface of
// its own. This is the same idea as the homepage header condensing over its deck.
const scrolled = ref(false)

function syncScroll() {
  scrolled.value = window.scrollY > 12
}

onMounted(() => {
  syncScroll()
  window.addEventListener('scroll', syncScroll, { passive: true })
})

onBeforeUnmount(() => window.removeEventListener('scroll', syncScroll))

const current = computed(() => destinationForTarget(String(route.meta.target ?? '')))
const currentGroup = computed(() => (current.value ? groupOf(current.value) : null))

function isGroupActive(item: (typeof fallbackPortalConfig.navigation)[number]) {
  if (item.links.some((link) => link.target === current.value?.target)) return true
  // 能力大图谱 is a page of its own but has no entry in the portal navigation (it is reached from the
  // capability panel and from the homepage), so fall back to the group the current page belongs to —
  // otherwise standing on that page highlights no group at all.
  return currentGroup.value?.label === item.title
}

function isLinkSelected(link: PortalNavigationLink) {
  return link.target === current.value?.target
}

function openColumn(link: PortalNavigationLink) {
  menuOpen.value = false
  const destination = destinationForTarget(link.target)
  // An unknown target means the portal config lists a column this build has no page for. Stay put and
  // say so, rather than guessing the page from the id's spelling — that guess is exactly what used to
  // send 成长画像 into the 智能研学 page.
  if (!destination) {
    console.warn('[portal] 未配置的栏目:', link.target)
    return
  }
  void router.push({ path: destination.path, query: link.category ? { category: link.category } : undefined })
}

// The 深地智学 group is the homepage deck itself rather than a column: its three entries are the deck's
// screens, reached by scrolling the deck to the matching slide id on the home route.
const screens = [
  { id: 'slide-home', label: '智慧问答' },
  { id: 'slide-course', label: '课程图谱' },
  { id: 'slide-ability', label: '能力图谱' }
]

function goToScreen(id: string) {
  menuOpen.value = false
  void router.push({ name: 'home', hash: `#${id}` })
}

function goHome() {
  menuOpen.value = false
  void router.push({ name: 'home' })
}

// Same account entry as the homepage header, and the same two states — the drawer carries it on phones
// because the bar drops the chip below 760px.
const isAuthenticated = session.isAuthenticated
const displayName = session.displayName

function goSignIn() {
  menuOpen.value = false
  void router.push({ name: 'sign-in', query: { redirect: route.fullPath } })
}

function signOut() {
  menuOpen.value = false
  session.signOut()
}
</script>

<template>
  <main class="layer-page" :class="{ 'nav-open': menuOpen }">
    <header class="module-header" :class="{ 'is-scrolled': scrolled }">
      <button class="module-brand" @click="goHome"><img class="module-university-logo" src="/cupb-logo.png" alt="中国石油大学（北京）" /><span class="module-product">深地智学</span></button>
      <nav class="module-nav" aria-label="平台层级">
        <div class="module-layer-group">
          <button @click="goHome"><b>深地智学</b></button>
          <div class="module-inline-links" aria-label="首页栏目"><button v-for="screen in screens" :key="screen.id" @click="goToScreen(screen.id)">{{ screen.label }}</button></div>
          <div class="module-dropdown" aria-label="深地智学栏目"><button v-for="screen in screens" :key="screen.id" @click="goToScreen(screen.id)">{{ screen.label }}</button></div>
        </div>
        <div v-for="item in fallbackPortalConfig.navigation" :key="item.title" class="module-layer-group" :class="{ active: isGroupActive(item) }">
          <button @click="openColumn(item.links[0])"><b>{{ item.title }}</b></button>
          <div class="module-inline-links" :aria-label="`${item.title}栏目`"><button v-for="link in item.links" :key="link.label" :class="{ selected: isLinkSelected(link) }" @click="openColumn(link)">{{ link.label }}</button></div>
          <div class="module-dropdown" :aria-label="`${item.title}栏目`"><button v-for="link in item.links" :key="link.label" :class="{ selected: isLinkSelected(link) }" @click="openColumn(link)">{{ link.label }}</button></div>
        </div>
      </nav>
      <AccountEntry class="module-profile" />
      <button class="module-mobile-toggle" :aria-expanded="menuOpen" aria-controls="module-mobile-navigation" :aria-label="menuOpen ? '收起平台导航' : '展开平台导航'" @click="menuOpen = !menuOpen"><X v-if="menuOpen" :size="21" /><Menu v-else :size="21" /></button>
    </header>

    <nav v-if="menuOpen" id="module-mobile-navigation" class="module-mobile-navigation" aria-label="移动端平台导航">
      <section>
        <strong>深地智学</strong>
        <button v-for="screen in screens" :key="screen.id" @click="goToScreen(screen.id)">{{ screen.label }}</button>
      </section>
      <section v-for="item in fallbackPortalConfig.navigation" :key="item.title">
        <strong>{{ item.title }}</strong>
        <button v-for="link in item.links" :key="link.label" @click="openColumn(link)">{{ link.label }}</button>
      </section>
      <section>
        <strong>账号</strong>
        <button v-if="!isAuthenticated" @click="goSignIn">登录 / 注册</button>
        <button v-else @click="signOut">退出登录（{{ displayName }}）</button>
      </section>
    </nav>

    <section v-if="current && currentGroup" class="layer-hero">
      <component :is="currentGroup.icon" :size="28" />
      <p>{{ currentGroup.label }}</p>
      <h1>{{ current.title }}</h1>
      <span>{{ current.intro }}</span>
    </section>

    <section class="layer-content section-shell">
      <router-view />
    </section>

    <footer class="module-footer">
      <div class="footer-copy"><strong>深地智学</strong><span>中国石油大学（北京）地质资源与地质工程学科教育大模型</span></div>
      <button @click="goHome">返回首页</button>
    </footer>
    <FloatingAssistant />
  </main>
</template>

<style scoped>
.layer-page { min-height: 100svh; color: #183d5c; background: #f4f6fc; }/* Fixed rather than sticky: the hero below carries the bar's own height as padding, so its background
   starts at the very top of the page and runs up behind the bar. With no background of its own the bar
   is invisible against that band until the page moves. */
.module-header { position: fixed; top: 0; right: 0; left: 0; z-index: 20; display: flex; align-items: flex-start; height: 124px; padding: 47px 4.1vw 0; color: #fff; background: transparent; box-shadow: none; transition: background 220ms ease, box-shadow 220ms ease; }.module-header.is-scrolled { background: rgba(35, 53, 84, .78); box-shadow: 0 10px 24px rgba(6, 24, 51, .18); backdrop-filter: blur(16px); }.module-brand { display: inline-flex; align-items: center; gap: 11px; height: 61px; padding: 0 31px 0 0; color: #fff; background: transparent; border: 0; border-right: 1px solid rgba(255,255,255,.18); font-size: 20px; font-weight: 800; white-space: nowrap; }.module-brand svg { color: #dff5ff; }.module-product { color: #fff; }.module-nav { display: flex; flex: 1; height: 72px; }.module-layer-group { position: relative; flex: 1; border-left: 1px solid rgba(255,255,255,.14); }.module-layer-group > button { width: 100%; padding: 1px 16px 0; color: #fff; background: transparent; border: 0; text-align: center; }.module-layer-group b { display: block; font-size: 25px; line-height: 1.25; }.module-layer-group small { display: block; min-height: 28px; margin-top: 12px; color: rgba(226, 241, 255, .8); font-size: 15px; font-weight: 700; line-height: 1.55; }.module-layer-group.active b { text-shadow: 0 3px 14px rgba(0, 25, 72, .45); }.module-profile { display: inline-flex; align-items: center; gap: 10px; height: 61px; padding: 0; color: #fff; background: transparent; border: 0; font-size: 18px; font-weight: 800; white-space: nowrap; }.module-mobile-toggle, .module-mobile-navigation { display: none; }
.layer-hero { display: grid; justify-items: center; gap: 13px; padding: 198px 24px 88px; color: #fff; text-align: center; background: radial-gradient(ellipse at 50% 110%, rgba(103, 189, 242, .34), transparent 57%), linear-gradient(130deg, #0755a0, #0874bc 55%, #064b90); }.layer-hero p { margin: 4px 0 0; color: #caebff; font-size: 14px; font-weight: 800; letter-spacing: .12em; }.layer-hero h1 { margin: 0; font-size: clamp(36px, 4.2vw, 58px); letter-spacing: .05em; }.layer-hero span { max-width: 620px; color: rgba(236, 248, 255, .85); line-height: 1.8; }.layer-content { padding-bottom: 90px; }
@media (max-width: 760px) { .module-header { height: 72px; align-items: center; padding: 0 18px; }.module-brand { height: auto; padding: 0; border: 0; font-size: 17px; }.module-brand .module-school { display: none; }.module-brand .module-product { display: inline; }.module-nav, .module-profile { display: none; }.module-mobile-toggle { display: grid; place-items: center; width: 34px; height: 34px; margin-left: auto; color: #fff; background: transparent; border: 1px solid rgba(222, 244, 255, .66); border-radius: 3px; }.module-mobile-navigation { position: fixed; z-index: 19; top: 72px; right: 0; left: 0; display: grid; gap: 1px; padding: 14px 18px 18px; background: rgba(4, 65, 136, .98); border-bottom: 1px solid rgba(222, 244, 255, .25); box-shadow: 0 18px 32px rgba(0, 13, 30, .3); }.module-mobile-navigation section { display: grid; grid-template-columns: 88px repeat(3, minmax(0, 1fr)); align-items: center; gap: 4px; padding: 10px 0; border-bottom: 1px solid rgba(226, 240, 240, .16); }.module-mobile-navigation section:last-child { border-bottom: 0; }.module-mobile-navigation strong { color: #cfe8ff; font-size: 13px; }.module-mobile-navigation button { min-width: 0; padding: 6px 2px; color: #e9f7ff; background: transparent; border: 0; font-size: 12px; text-align: left; }.layer-hero { padding: 54px 22px 62px; }.layer-hero h1 { font-size: 34px; }.layer-content { width: min(100% - 30px, 1180px); } }

.module-brand, .module-layer-group > button, .module-profile { transition: background 180ms ease, color 180ms ease, transform 180ms ease; }
.module-brand:hover { transform: translateY(-2px); }.module-layer-group > button:hover { background: rgba(255,255,255,.06); }.module-layer-group.active > button::after { content: ""; display: block; width: 34px; height: 3px; margin: 10px auto 0; background: #bce8ff; border-radius: 3px; animation: active-line 300ms ease both; }
.layer-hero { position: relative; overflow: hidden; isolation: isolate; }.layer-hero::after { content: ""; position: absolute; z-index: -1; width: 520px; height: 520px; right: 12%; bottom: -390px; border: 1px solid rgba(210, 240, 255, .3); border-radius: 50%; box-shadow: 0 0 0 34px rgba(210, 240, 255, .05), 0 0 0 72px rgba(210, 240, 255, .035); animation: hero-drift 9s ease-in-out infinite; }.layer-hero > * { animation: layer-reveal 440ms cubic-bezier(.2, .8, .2, 1) both; }.layer-hero p { animation-delay: 70ms; }.layer-hero h1 { animation-delay: 130ms; }.layer-hero span { animation-delay: 190ms; }
.module-footer { display: flex; align-items: center; justify-content: space-between; gap: 24px; padding: 34px max(6.25vw, 24px); color: rgba(227, 243, 255, .82); background: #123b66; }.module-footer div { display: flex; align-items: baseline; gap: 15px; }.module-footer strong { color: #fff; font-size: 18px; }.module-footer span { font-size: 13px; }.module-footer button { padding: 8px 0; color: #d9f1ff; background: transparent; border: 0; font-weight: 800; }.module-footer button:hover { color: #fff; text-decoration: underline; }
@media (max-width: 760px) { .module-footer { align-items: start; flex-direction: column; gap: 8px; padding: 28px 22px; }.module-footer div { align-items: start; flex-direction: column; gap: 5px; } }
@keyframes layer-reveal { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
@keyframes active-line { from { transform: scaleX(.35); opacity: .2; } to { transform: scaleX(1); opacity: 1; } }
@keyframes hero-drift { 50% { transform: translate(-26px, -16px); } }

/* Secondary routes retain the portal navigation, then move into a light work area. */
@media (min-width: 761px) {
  .layer-page { background: #f5f6fb; }
  /* The bar takes its surface from .module-header.is-scrolled, so this block only keeps the geometry. */
  .module-header { height: 124px; padding-top: 47px; color: #fff; }
  /* 深地智学 is the first group's title on desktop, so the brand keeps only the school name — the rule
     styles.css already applies to the homepage brand. Without it both rendered and the two names ran
     together: "...（北京）| 深地智学" followed immediately by the 深地智学 group. */
  .module-brand .module-product { display: none; }
  .module-brand { color: #fff; border-right-color: rgba(255,255,255,.18); }.module-brand svg { color: #dff5ff; }.module-product { color: #fff; }
  .module-nav { height: 72px; }.module-layer-group { border-left-color: rgba(255,255,255,.14); }.module-layer-group > button { color: #fff; }.module-layer-group small { color: rgba(226, 241, 255, .8); }.module-layer-group.active > button::after { background: #bce8ff; }.module-layer-group.active b { text-shadow: 0 3px 14px rgba(0, 25, 72, .45); }
  .module-brand:hover, .module-profile:hover { color: #fff; }.module-layer-group > button:hover { color: #fff; background: rgba(255,255,255,.06); }
  .module-profile { color: #fff; }
  .layer-hero { display: grid; justify-items: center; min-height: 258px; padding: 178px 24px 62px; color: #fff; text-align: center; background: radial-gradient(ellipse at 50% 110%, rgba(103, 189, 242, .34), transparent 57%), linear-gradient(130deg, #0755a0, #0874bc 55%, #064b90); }.layer-hero::after { display: block; }.layer-hero > svg, .layer-hero > p { display: block; }.layer-hero h1 { width: auto; max-width: 920px; color: #fff; font-family: "Alibaba PuHuiTi", "Microsoft YaHei", sans-serif; font-size: clamp(38px, 3.25vw, 52px); font-weight: 800; line-height: 1.18; letter-spacing: .04em; }.layer-hero span { display: block; width: auto; max-width: 620px; margin-top: 0; color: rgba(236, 248, 255, .85); font-size: 15px; }
  .layer-content { padding-bottom: 100px; }.module-footer { color: #d2e4fa; background: #0b3a63; }.module-footer strong { color: #fff; }.module-footer button { color: #d9ecfa; }
}
@media (max-width: 760px) {
  .layer-page { background: #f5f6fb; }
  /* This block used to redefine the header as a 38px bar carrying 4px brand text, 7px nav titles and
     3px sub-links, force the desktop nav visible and hide the hamburger — the same "micro header"
     pathology already removed from styles.css. Sitting below the `max-width: 760px` block above, it won
     on source order, so the layers page showed an unreadable smear of 4px Chinese while the homepage
     showed a 72px bar with a working hamburger: two navigations for one product. The header now keeps
     the upper block values and matches the homepage — flat #1b5fa7, 深地智学 at 20px beside the mark,
     school name dropped on phones, desktop nav hidden in favour of the hamburger. */
  .module-header { position: fixed; height: 72px; align-items: center; padding: 0 18px; background: transparent; box-shadow: none; }
  .module-header.is-scrolled { background: rgba(35, 53, 84, .78); box-shadow: 0 10px 24px rgba(6, 24, 51, .18); backdrop-filter: blur(16px); }
  .module-brand { height: auto; padding: 0; border: 0; font-size: 20px; }
  .module-brand .module-school, .module-nav, .module-profile { display: none; }
  .module-brand .module-product { display: inline; }
  .module-mobile-toggle { display: grid; }
  .layer-hero { display: grid; justify-items: center; min-height: 232px; padding: 117px 22px 48px; color: #fff; text-align: center; background: radial-gradient(ellipse at 50% 110%, rgba(103, 189, 242, .34), transparent 57%), linear-gradient(130deg, #0755a0, #0874bc 55%, #064b90); }.layer-hero::after, .layer-hero > svg, .layer-hero > p { display: block; }.layer-hero h1 { width: auto; max-width: 310px; color: #fff; font-size: 31px; line-height: 1.18; letter-spacing: .03em; }.layer-hero span { display: block; width: auto; max-width: 310px; margin-top: 0; color: rgba(236, 248, 255, .85); font-size: 12px; line-height: 1.65; }.layer-content { width: calc(100% - 30px); padding-bottom: 62px; }.module-footer { align-items: start; flex-direction: column; gap: 8px; padding: 28px 22px; color: #d2e4fa; background: #0b3a63; }.module-footer div { align-items: start; flex-direction: column; gap: 5px; }.module-footer strong { color: #fff; }.module-footer button { color: #d9ecfa; }
}

@media (min-width: 761px) {
  .module-layer-group { display: grid; grid-template-rows: 36px auto; align-content: start; }
  .module-layer-group > button { padding: 0 12px; }
  .module-inline-links { display: flex; align-items: start; justify-content: center; gap: clamp(7px, .62vw, 12px); padding: 8px 10px 0; }
  .module-inline-links button { padding: 0; color: rgba(226, 241, 255, .8); background: transparent; border: 0; font-size: clamp(11px, .72vw, 14px); font-weight: 700; line-height: 1.55; white-space: nowrap; transition: color 180ms ease, transform 180ms ease; }
  .module-inline-links button:hover, .module-inline-links button.selected { color: #fff; transform: translateY(-1px); }
}
@media (min-width: 761px) { .module-layer-group b { font-size: clamp(18px, 1.3vw, 25px); }.module-layer-group small { font-size: clamp(11px, .78vw, 15px); }.module-layer-group > button { padding-right: clamp(7px, .8vw, 16px); padding-left: clamp(7px, .8vw, 16px); } }

/* Five groups carrying three labels each do not fit every window, so the header degrades in symmetric
   steps — the same ladder styles.css solves for the homepage header (>=1540 three labels, >=1360 two,
   >=1100 titles only, below that the brand drops the school name). This header had no ladder at all,
   which is why it overflowed: at 1440px the profile chip measured right=1476 against a 1425px viewport,
   a 51px horizontal scroll on every column page, with the chip clipped at the edge. */
@media (min-width: 761px) and (max-width: 1539px) {
  .module-inline-links button:nth-child(n + 3) { display: none; }
  /* ...except the column you are standing on. Dropping the third chip removes exactly 导师图谱 from
     因材智教 and 成长画像 from 能力智验, so on those two pages the header would list the neighbouring
     columns and hide the current one — the one entry a visitor most needs to see. Same specificity as
     the rule above, so it wins by coming later. */
  .module-inline-links button.selected { display: block; }
}
@media (min-width: 761px) and (max-width: 1359px) {
  .module-inline-links { display: none; }
  .module-layer-group { grid-template-rows: auto; align-content: center; }
}
@media (min-width: 761px) and (max-width: 1099px) {
  .module-brand .module-school { display: none; }
  .module-layer-group > button { padding-right: 8px; padding-left: 8px; }
  .module-layer-group b { font-size: clamp(14px, 1.6vw, 20px); }
}

/* The ladder above hides chips as the window narrows — but hiding is not reaching: at the scaled sizes
   the dropped chips (导师图谱 / 成长画像 ...) simply stop existing in the bar. Give the ladder a hover
   floor: pointing at any group drops a panel listing ALL of its entries, so nothing becomes unreachable
   just because the window got smaller. Full width (>=1540) already shows every chip inline and needs no
   dropdown; below 761px the hamburger drawer carries the same list. The panel starts exactly at the
   group's bottom edge (no gap) so the pointer never leaves hover while travelling into it, and
   :focus-within keeps it open for keyboard users — visibility:hidden also takes the closed panel's
   buttons out of the tab order. The card sizes to its widest entry (min-width keeps it at least as wide
   as the group) and centres on the group like the centred title does: pinning it to the group's box
   with nowrap entries wider than a narrow group made the text paint past the card's edge. */
.module-dropdown { display: none; }
@media (min-width: 761px) and (max-width: 1539px) {
  .module-dropdown { position: absolute; z-index: 30; top: 100%; left: 50%; display: grid; gap: 2px; padding: 10px 12px; width: max-content; min-width: 100%; max-width: calc(100vw - 32px); background: #fff; border: 1px solid rgba(8, 85, 141, .14); border-radius: 6px; box-shadow: 0 18px 34px rgba(6, 24, 51, .2); opacity: 0; visibility: hidden; transform: translate(-50%, -6px); transition: opacity 160ms ease, transform 160ms ease, visibility 160ms; }
  .module-layer-group:hover > .module-dropdown, .module-layer-group:focus-within > .module-dropdown { opacity: 1; visibility: visible; transform: translate(-50%, 0); }
  .module-dropdown button { padding: 8px 10px; color: #164f81; background: transparent; border: 0; border-radius: 4px; font-size: 14px; font-weight: 700; text-align: left; white-space: nowrap; cursor: pointer; transition: background 160ms ease, color 160ms ease; }
  .module-dropdown button:hover { color: #075a9d; background: #e8f4fc; }
  .module-dropdown button.selected { color: #075a9d; background: #e7f4fc; box-shadow: inset 3px 0 #0870bc; }
}

/* Keep every tool surface on the secondary pages in the same cool academic palette. */
.layer-page :deep(.eyebrow), .layer-page :deep(.resource-catalog header p), .layer-page :deep(.resource-catalog article > div), .layer-page :deep(.resource-catalog article a), .layer-page :deep(.learning-steps > div), .layer-page :deep(.learning-steps span) { color: #0870bc; }.layer-page :deep(.resource-catalog nav button.active) { background: #0870bc; }.layer-page :deep(.resource-catalog nav button), .layer-page :deep(.map-inspector button.selected) { transition: background 180ms ease, color 180ms ease, box-shadow 180ms ease; }.layer-page :deep(.resource-catalog nav button:hover) { color: #075a9d; background: #e8f4fc; }.layer-page :deep(.resource-catalog article:hover) { box-shadow: 0 14px 28px rgba(7, 94, 163, .13); }.layer-page :deep(.graph-selection) { border-left-color: #0870bc; }.layer-page :deep(.graph-selection span), .layer-page :deep(.map-inspector span) { color: #0870bc; }.layer-page :deep(.map-inspector button.selected) { background: #e7f4fc; box-shadow: inset 3px 0 #0870bc; }.layer-page :deep(.analysis-button) { background: #0870bc; border-color: #0870bc; }.layer-page :deep(.upload-button) { color: #075a9d; background: #e8f4fc; }.layer-page :deep(.task-action) { color: #0870bc; }.layer-page :deep(.task-item) { transition: background 180ms ease, padding 180ms ease; }.layer-page :deep(.task-item:hover) { padding-right: 18px; padding-left: 18px; background: #f8fcff; }
.layer-page :deep(.knowledge-graph), .layer-page :deep(.geo-data), .layer-page :deep(.well-log-lab) { border-top-color: #d5e5ed; }
.layer-page :deep(.graph-canvas), .layer-page :deep(.map-canvas), .layer-page :deep(.lab-workspace) { background: #f7fbff; border-color: #c8dfeb; }
.layer-page :deep(.graph-selection) { border-left-color: #0870bc; }.layer-page :deep(.graph-selection span), .layer-page :deep(.map-inspector span) { color: #0870bc; }
.layer-page :deep(.map-workspace) { border-color: #c8dfeb; }.layer-page :deep(.map-inspector) { background: #f7fbff; border-left-color: #c8dfeb; }.layer-page :deep(.map-inspector > p), .layer-page :deep(.map-inspector button) { border-bottom-color: #d8e8f0; }.layer-page :deep(.map-inspector button.selected) { background: #e7f4fc; box-shadow: inset 3px 0 #0870bc; }
.layer-page :deep(.curve-header), .layer-page :deep(.curve-legend) { color: #59788b; }.layer-page :deep(.grid-line line) { stroke: #d6e7ef; }.layer-page :deep(.analysis-result) { color: #145b66; background: #e5f4f3; }.layer-page :deep(.evidence-list) { color: #496b7c; background: #e8f3f7; }
.layer-page :deep([id]) { scroll-margin-top: 148px; }
@media (max-width: 760px) { .layer-page :deep([id]) { scroll-margin-top: 88px; } }
/* 汉堡菜单展开时收起右下角的 AI 悬浮球：菜单是 fixed 面板而悬浮球 z-index 更高，
   会盖在菜单和页面内容上（手机截图实测），且此时它无处可去。 */
.layer-page.nav-open :deep(.floating-ai) { display: none; }
.module-university-logo { display: block; width: auto; height: 48px; object-fit: contain; }
@media (max-width: 760px) { .module-university-logo { height: 30px; } }
</style>
