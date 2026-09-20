<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { buildGeoChatLoginUrl, buildGeoChatRegistrationUrl } from '@/config/geochat'

const router = useRouter()
const route = useRoute()

const redirect = computed(() => {
  const raw = route.query.redirect
  const value = Array.isArray(raw) ? raw[0] : raw
  // 兜底落平台首页而非站点根 `/`：站点根现在是郭网页落地页，登录后应回到平台里。
  return typeof value === 'string' && value.startsWith('/') && !value.startsWith('//') ? value : '/platform/'
})

function openGeoChatLogin() {
  window.location.assign(buildGeoChatLoginUrl(redirect.value))
}

function openGeoChatRegistration() {
  window.location.assign(buildGeoChatRegistrationUrl(redirect.value))
}
</script>

<template>
  <main class="auth-page">
    <div class="auth-strata" aria-hidden="true"></div>

    <button class="auth-brand" @click="router.push({ name: 'home' })">
      <img class="auth-university-logo" src="/cupb-emblem-red.png" alt="中国石油大学（北京）" />
      <strong>深地智学</strong>
    </button>

    <section class="auth-card">
      <header class="auth-heading">
        <p>地质资源与地质工程学科教育大模型</p>
        <h1>进入深地智学</h1>
      </header>

      <p class="auth-note">使用一个账户即可访问智能问答与校内学习功能。</p>
      <button class="auth-submit" type="button" @click="openGeoChatLogin">统一登录</button>
      <button class="auth-register" type="button" @click="openGeoChatRegistration">注册账户</button>
    </section>

    <p class="auth-footnote">
      登录后可直接进入智能问答和校内学习功能。
      <button @click="router.push({ name: 'home' })">返回首页</button>
    </p>
  </main>
</template>

<style scoped>
/* A pale blue wash rather than the deep radial gradient this started as. The homepage is dark blue because
   it is a full-bleed hero; a sign-in form is not, and a saturated gradient behind a white card reads as
   decoration for its own sake. The lighter ground also puts the card *on* the page instead of floating it
   over the page, and keeps this screen in the same family as the portal's #f7f8fc content ground. Every
   text colour below had to move with it — the brand line and the footnote were white, and white on a pale
   blue is nothing at all. */
.auth-page {
  position: relative;
  display: grid;
  align-content: center;
  justify-items: center;
  gap: 26px;
  min-height: 100svh;
  padding: 96px 24px 64px;
  color: #142d45;
  background: linear-gradient(180deg, #f5f9fd 0%, #e4edf9 100%);
  overflow: hidden;
  isolation: isolate;
}
.auth-strata { position: absolute; inset: auto 0 0; z-index: -1; height: 46%; background: linear-gradient(180deg, transparent, rgba(176, 206, 238, .46)); }
.auth-strata::before {
  content: "";
  position: absolute;
  right: -12vw;
  bottom: -22vw;
  width: min(58vw, 720px);
  height: min(58vw, 720px);
  border: 1px solid rgba(120, 170, 220, .3);
  border-radius: 50%;
  box-shadow: 0 0 0 48px rgba(120, 170, 220, .07), 0 0 0 96px rgba(120, 170, 220, .05);
}
.auth-brand { position: absolute; top: 40px; left: 5.5vw; display: inline-flex; align-items: center; gap: 11px; padding: 0; color: #164f81; background: transparent; border: 0; font-size: 20px; font-weight: 800; }
.auth-university-logo { display: block; width: auto; height: 36px; object-fit: contain; }
.auth-brand svg { color: #2f7cc4; }
.auth-brand i { width: 1px; height: 20px; background: rgba(22, 79, 129, .22); }
.auth-card { width: min(452px, 100%); padding: 36px 38px 30px; color: #142d45; background: #fff; border: 1px solid #e2ecf7; border-radius: 14px; box-shadow: 0 16px 40px rgba(21, 60, 110, .13); }
.auth-heading { display: grid; gap: 6px; }
.auth-heading p { margin: 0; color: #6d7f95; font-size: 13px; font-weight: 700; letter-spacing: .04em; }
.auth-heading h1 { margin: 0; font-family: "Microsoft YaHei", "PingFang SC", sans-serif; font-size: 26px; font-weight: 900; letter-spacing: .02em; }
.auth-tabs { display: grid; grid-template-columns: repeat(2, 1fr); gap: 4px; margin: 22px 0 24px; padding: 4px; background: #eef3fa; border-radius: 10px; }
.auth-tabs button { padding: 10px 0; color: #5c6d84; background: transparent; border: 0; border-radius: 7px; font-size: 15px; font-weight: 800; transition: color 160ms ease, background 160ms ease; }
.auth-tabs button.active { color: #164f81; background: #fff; box-shadow: 0 4px 12px rgba(23, 60, 110, .12); }
.auth-form { display: grid; gap: 16px; }
.auth-form label { display: grid; gap: 7px; }
.auth-form label > span { color: #3c526c; font-size: 13px; font-weight: 800; }
.auth-form input { width: 100%; height: 46px; padding: 0 14px; color: #142d45; background: #f7fafd; border: 1px solid #d8e3ef; border-radius: 8px; font-size: 15px; transition: border-color 160ms ease, background 160ms ease; }
.auth-form input:focus { background: #fff; border-color: #5b9bdc; outline: none; }
.auth-roles { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
.auth-roles button { height: 42px; color: #43586f; background: #f7fafd; border: 1px solid #d8e3ef; border-radius: 8px; font-size: 14px; font-weight: 800; transition: color 160ms ease, background 160ms ease, border-color 160ms ease; }
.auth-roles button.active { color: #164f81; background: #e8f2fd; border-color: #8fbdec; }
.auth-error { margin: 0; padding: 10px 12px; color: #a3322c; background: #fdf1f0; border: 1px solid #f3d2cf; border-radius: 8px; font-size: 13px; font-weight: 700; }
/* The `width: 100%` is load-bearing: the button used to live inside `.auth-form` (a grid, so its
   children stretch to the column), and when it moved up into the card's block flow it shrank to its
   own text — "统一登录" wrapped onto two lines inside a 60px chip. `margin-top` likewise: the note
   above it only carries a top margin for the heading, so the button was sitting flush under the text. */
.auth-submit { width: 100%; height: 48px; margin-top: 18px; color: #fff; background: linear-gradient(135deg, #2f7cc4, #164f81); border: 0; border-radius: 8px; font-size: 16px; font-weight: 800; box-shadow: 0 12px 26px rgba(22, 79, 129, .28); transition: transform 160ms ease, box-shadow 160ms ease; }
.auth-submit:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 16px 30px rgba(22, 79, 129, .34); }
.auth-submit:disabled { opacity: .72; cursor: default; }
.auth-register { display: block; width: 100%; margin-top: 10px; padding: 8px; color: #2f7cc4; background: transparent; border: 0; font-size: 14px; font-weight: 800; }
.auth-register:hover { text-decoration: underline; }
/* Left-aligned like the heading above it. `text-align: center` came from when this line was a
   "还没有账号？立即注册" prompt; as a plain sentence under a left-aligned title it just looked loose. */
.auth-note { margin: 20px 0 0; color: #6d7f95; font-size: 13px; }
.auth-note button { padding: 0; color: #2f7cc4; background: transparent; border: 0; font-size: 13px; font-weight: 800; }
.auth-note button:hover { text-decoration: underline; }
/* 560px so the sentence and the 返回首页 link fit on one line at 12px; at 460px it broke mid-word
   ("…本机浏览 / 器。 返回首页"). `text-wrap: balance` keeps the phone's two lines even. */
.auth-footnote { max-width: 560px; margin: 0; color: #6d7f95; font-size: 12px; line-height: 1.7; text-align: center; text-wrap: balance; }
.auth-footnote button { padding: 0; color: #2f7cc4; background: transparent; border: 0; font-size: 12px; font-weight: 800; }
.auth-footnote button:hover { text-decoration: underline; }

@media (max-width: 760px) {
  .auth-page { gap: 20px; padding: 88px 18px 48px; }
  .auth-brand { top: 26px; left: 18px; font-size: 17px; }
  .auth-university-logo { height: 30px; }
  .auth-school { display: none; }
  .auth-brand i { display: none; }
  .auth-card { padding: 28px 22px 24px; }
  .auth-heading h1 { font-size: 22px; }
}
</style>
