<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { buildGeoChatWorkbenchUrl } from '@/config/geochat'

const route = useRoute()

onMounted(() => {
  const question = typeof route.query.q === 'string' ? route.query.q : ''
  window.location.replace(buildGeoChatWorkbenchUrl(question))
})
</script>

<template>
  <main class="assistant-bridge" aria-live="polite">
    <div>
      <span class="assistant-bridge-mark" aria-hidden="true"></span>
      <strong>正在打开深地智学 AI 工作台</strong>
      <p>GeoChat 服务启动后会自动进入智能体工作区。</p>
    </div>
  </main>
</template>

<style scoped>
.assistant-bridge { display: grid; place-items: center; min-height: 100svh; color: #173f67; background: #f4f7fb; text-align: center; }
.assistant-bridge > div { display: grid; justify-items: center; gap: 12px; padding: 32px; }
.assistant-bridge-mark { width: 42px; height: 42px; border: 4px solid #b8dff6; border-top-color: #176fba; border-radius: 50%; animation: bridge-spin .9s linear infinite; }
.assistant-bridge strong { font-size: 20px; }
.assistant-bridge p { margin: 0; color: #6c8195; font-size: 14px; }
@keyframes bridge-spin { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .assistant-bridge-mark { animation: none; } }
</style>
