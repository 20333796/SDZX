<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { ChevronDown, LogOut, UserRound } from '@lucide/vue'
import { useRouter } from 'vue-router'
import { session } from '@/session'
import { buildGeoChatLoginUrl } from '@/config/geochat'

// The account chip in the header, in both of its states. Before this, the homepage header and the column
// header each hard-coded their own 访客 chip — two copies of an account menu for an account nobody could
// have. Now the signed-out state is the 登录 / 注册 entry and the chip only appears once there is a
// principal behind it; both headers render this one component, so the two cannot drift apart again.
const router = useRouter()
const open = ref(false)
const root = ref<HTMLElement | null>(null)

const isAuthenticated = session.isAuthenticated
const displayName = session.displayName
const initial = session.initial
const roleLabel = session.roleLabel

function goSignIn() {
  open.value = false
  const from = router.currentRoute.value
  // Remember where the user was so the login page can hand them back. Nothing to remember when we are
  // already standing on it — that would just make the redirect bounce off the guard.
  const redirect = from.name === 'sign-in' || from.fullPath === '/' ? undefined : from.fullPath
  // 兜底落平台首页而非站点根 `/`：站点根现在是郭网页落地页，登录后应回到平台里。
  window.location.assign(buildGeoChatLoginUrl(redirect || '/platform/'))
}

function signOut() {
  open.value = false
  session.signOut()
}

// The chip is a real menu, so it has to close the way menus do: click anywhere else, or press Escape.
// Watching `pointerdown` rather than `click` keeps it from reopening on the same press that dismisses it.
function onPointerDown(event: PointerEvent) {
  if (!open.value) return
  if (root.value && !root.value.contains(event.target as Node)) open.value = false
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') open.value = false
}

onMounted(() => {
  document.addEventListener('pointerdown', onPointerDown)
  document.addEventListener('keydown', onKeydown)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', onPointerDown)
  document.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <div ref="root" class="account-entry">
    <button v-if="!isAuthenticated" class="account-signin" @click="goSignIn">
      <UserRound :size="18" /><span>登录 / 注册</span>
    </button>
    <template v-else>
      <button class="account-profile" :aria-expanded="open" aria-haspopup="true" aria-label="打开用户菜单" @click="open = !open">
        <span class="account-avatar">{{ initial }}</span>
        <span class="account-name">{{ displayName }}</span>
        <ChevronDown class="account-caret" :class="{ 'is-open': open }" :size="18" />
      </button>
      <Transition name="account-pop">
        <div v-if="open" class="account-menu" role="menu">
          <div class="account-identity"><strong>{{ displayName }}</strong><span>{{ roleLabel }}</span></div>
          <button role="menuitem" @click="signOut"><LogOut :size="16" />退出登录</button>
        </div>
      </Transition>
    </template>
  </div>
</template>

<style scoped>
/* 61px because the header aligns its children to the top, not to their centres: the brand block is 61px
   tall and the nav 78px, so a 46px chip sat 7.5px above the brand's midline. The condensed header already
   pinned this element to 61px (`.site-header.is-condensed .site-profile`), which is what made the
   mismatch visible only in the un-condensed state. Fixing the height here centres the 46px control inside
   a row that matches the brand. */
.account-entry { position: relative; display: inline-flex; align-items: center; height: 61px; margin-left: auto; }
.account-signin,
.account-profile {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  height: 46px;
  color: #fff;
  background: transparent;
  font-size: 18px;
  font-weight: 800;
  white-space: nowrap;
  transition: background 180ms ease, transform 180ms ease;
}
.account-signin { padding: 0 20px; border: 1px solid rgba(197, 222, 249, .55); border-radius: 26px; }
.account-signin svg { color: #cfe8ff; }
.account-signin:hover { background: rgba(255, 255, 255, .16); transform: translateY(-2px); }
.account-profile { padding: 0; border: 0; }
.account-profile:hover { transform: translateY(-2px); }
.account-avatar {
  display: grid;
  place-items: center;
  width: 39px;
  height: 39px;
  color: #d9f5ff;
  background: radial-gradient(circle at 60% 28%, #cde9fd 0 8%, transparent 9%), linear-gradient(145deg, #6da7ce, #164f81 72%);
  border-radius: 50%;
  font-size: 15px;
  font-weight: 800;
}
.account-caret { width: 23px; height: 23px; padding: 3px; border: 1px solid rgba(255, 255, 255, .78); border-radius: 50%; transition: transform 200ms ease; }
.account-caret.is-open { transform: rotate(180deg); }
/* Sits above the header's own surface. The header condenses to a translucent bar once the page moves, so
   the panel gets an opaque enough ground of its own to stay legible over whatever scrolls under it. */
.account-menu {
  position: absolute;
  z-index: 40;
  top: calc(100% + 10px);
  right: 0;
  display: grid;
  gap: 2px;
  min-width: 178px;
  padding: 8px;
  background: rgba(4, 66, 137, .97);
  border: 1px solid rgba(212, 239, 255, .35);
  border-radius: 10px;
  box-shadow: 0 20px 38px rgba(0, 23, 66, .36);
}
.account-identity { display: grid; gap: 4px; padding: 8px 10px 10px; border-bottom: 1px solid rgba(212, 239, 255, .18); }
.account-identity strong { font-size: 15px; }
.account-identity span { color: rgba(222, 241, 255, .72); font-size: 12px; font-weight: 700; }
.account-menu button { display: inline-flex; align-items: center; gap: 8px; padding: 8px 10px; color: #e9f7ff; background: transparent; border: 0; border-radius: 6px; font-size: 14px; font-weight: 700; text-align: left; }
.account-menu button:hover { color: #fff; background: rgba(115, 190, 255, .28); }
.account-pop-enter-active, .account-pop-leave-active { transition: opacity 160ms ease, transform 160ms ease; }
.account-pop-enter-from, .account-pop-leave-to { opacity: 0; transform: translateY(-6px); }
/* On phones both headers drop the chip from the bar itself and carry the entry inside the menu drawer, so
   the condensed bar keeps its single 34px toggle. */
@media (max-width: 760px) {
  .account-entry { display: none; }
}
</style>
