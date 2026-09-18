<script setup lang="ts">
import { useRouter } from 'vue-router'
import { pathTo } from '@/config/destinations'
import DestinationView from '@/features/portal/DestinationView.vue'
import DestinationNote from '@/features/portal/DestinationNote.vue'

const router = useRouter()

// Fieldwork is organised as a route -> stops -> notes chain; the three stages are the interface this
// column will have. The 3D scene and the mobile recording view are not connected yet, so the page
// describes the stages and hands the visitor to the task flow that does exist.
const stages = [
  { name: '地层路线', detail: '按野外路线组织时间与站位，记录起点、终点与交通方式。' },
  { name: '观察点', detail: '每个观察点记录岩性、产状与照片，并与课程知识点对应。' },
  { name: '任务记录', detail: '把观察结论写成可复核的依据，交给教师批注后进入能力证据。' }
]
</script>

<template>
  <DestinationView eyebrow="野外实训" title="从路线到观察点，再落到任务记录" intro="野外实训按「路线 — 观察点 — 任务记录」三段组织，三维场景接口已预留。">
    <ol class="field-stages">
      <li v-for="(stage, index) in stages" :key="stage.name">
        <div class="field-marker"><span>{{ index + 1 }}</span></div>
        <div class="field-body"><strong>{{ stage.name }}</strong><p>{{ stage.detail }}</p></div>
      </li>
    </ol>
    <DestinationNote title="三维场景与移动端记录尚未接入">路线建模与现场记录依赖校内三维场景服务，接入前教师可先用研学任务发布野外观察作业。</DestinationNote>
    <div class="field-actions">
      <button @click="router.push(pathTo('learning-tasks'))">进入研学任务</button>
      <button class="is-quiet" @click="router.push(pathTo('case-library'))">看工程案例</button>
    </div>
  </DestinationView>
</template>

<style scoped>
.field-stages { position: relative; display: grid; gap: 4px; margin: 0; padding: 0 0 0 4px; list-style: none; }
.field-stages li { display: flex; align-items: flex-start; gap: 18px; padding-bottom: 22px; }
.field-stages li::before { content: ""; position: absolute; left: 17px; width: 1px; height: 100%; background: #d5e4ee; }
.field-stages li:last-child::before { display: none; }
.field-marker { position: relative; z-index: 1; display: grid; place-items: center; flex: 0 0 auto; width: 34px; height: 34px; color: #0870bc; background: #fff; border: 1px solid #bcd7e8; border-radius: 50%; font-weight: 800; }
.field-body strong { display: block; color: #17384d; font-size: 16px; }
.field-body p { margin: 6px 0 0; color: #5f7487; line-height: 1.8; }
.field-actions { display: flex; flex-wrap: wrap; gap: 12px; }
.field-actions button { padding: 11px 18px; color: #fff; background: #0870bc; border: 0; border-radius: 4px; font-weight: 800; transition: transform 180ms ease; }
.field-actions button.is-quiet { color: #075a9d; background: #e8f4fc; }
.field-actions button:hover { transform: translateY(-2px); }
</style>
