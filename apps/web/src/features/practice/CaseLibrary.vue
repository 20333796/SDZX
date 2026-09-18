<script setup lang="ts">
import { useRouter } from 'vue-router'
import { FolderOpen, ScanSearch, Gavel } from '@lucide/vue'
import { pathTo, WELL_LOG_LAB_PATH } from '@/config/destinations'
import DestinationView from '@/features/portal/DestinationView.vue'
import DestinationNote from '@/features/portal/DestinationNote.vue'

const router = useRouter()

// A case is read in three passes; that reading order is the interface. The cases themselves are still
// being reviewed by the course team, so the columns show what each pass will contain.
const passes = [
  { name: '资料', detail: '井位与曲线、录井与岩心描述、区域地质背景。', icon: FolderOpen },
  { name: '解释', detail: '把曲线特征翻译成岩性与流体判断，并标出不确定的地方。', icon: ScanSearch },
  { name: '判断', detail: '给出结论、适用条件与需要补充的资料，形成可复核的案例结论。', icon: Gavel }
]
</script>

<template>
  <DestinationView eyebrow="工程案例" title="按「资料 — 解释 — 判断」读案例" intro="案例库按课程审核流程建设，先公开案例的阅读结构。">
    <div class="case-columns">
      <article v-for="item in passes" :key="item.name">
        <div class="card-head"><span class="icon-chip"><component :is="item.icon" :size="20" /></span></div>
        <strong>{{ item.name }}</strong>
        <p>{{ item.detail }}</p>
      </article>
    </div>
    <DestinationNote title="案例内容正在按课程审核流程建设">每个案例需经任课教师与资料提供方确认后发布，当前页面只公开阅读顺序，不放未经审核的资料。</DestinationNote>
    <div class="case-actions"><button @click="router.push(pathTo('resources'))">浏览课程资源</button><button class="is-quiet" @click="router.push(WELL_LOG_LAB_PATH)">体验测井教学实验</button></div>
  </DestinationView>
</template>

<style scoped>
.case-columns { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 20px; }
.case-columns article { display: flex; flex-direction: column; gap: 8px; padding: 22px 24px 20px; background: #fff; border: 1px solid #e6ecf2; border-radius: 14px; box-shadow: 0 1px 2px rgba(16, 52, 84, .05); transition: transform .22s ease, box-shadow .22s ease, border-color .22s ease; }
.case-columns article:hover { transform: translateY(-4px); border-color: #d4e3ef; box-shadow: 0 14px 28px rgba(7, 94, 163, .13); }
.card-head { margin-bottom: 14px; }
.icon-chip { display: inline-flex; align-items: center; justify-content: center; width: 44px; height: 44px; border-radius: 12px; background: #e8f4fc; color: #0870bc; }
.case-columns strong { color: #17384d; font-size: 17px; }
.case-columns p { margin: 0; color: #5f7487; line-height: 1.8; }
.case-actions { display: flex; flex-wrap: wrap; gap: 12px; }
.case-actions button { padding: 11px 18px; color: #fff; background: #0870bc; border: 0; border-radius: 4px; font-weight: 800; transition: transform 180ms ease; }
.case-actions button.is-quiet { color: #075a9d; background: #e8f4fc; }
.case-actions button:hover { transform: translateY(-2px); }
@media (prefers-reduced-motion: no-preference) {
  .case-columns article { animation: cardIn 360ms ease both; }
}
@keyframes cardIn { from { opacity: 0; } to { opacity: 1; } }
</style>
