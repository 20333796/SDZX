<script setup lang="ts">
import { useRouter } from 'vue-router'
import { BookOpen, FlaskConical, UserCheck } from '@lucide/vue'
import { pathTo, WELL_LOG_LAB_PATH } from '@/config/destinations'
import DestinationView from '@/features/portal/DestinationView.vue'
import DestinationNote from '@/features/portal/DestinationNote.vue'

const router = useRouter()

// Assessment here is deliberately not a separate exam: evidence comes from the tasks and experiments
// that already exist, which is why grading, history and personal records all need campus sign-on.
const sources = [
  { name: '课程任务', detail: '智能研学任务的结论与引用，判断依据是否可复核。', icon: BookOpen },
  { name: '实验记录', detail: '测井智能解释等教学实验的操作与判识结果。', icon: FlaskConical },
  { name: '教师评价', detail: '教师对任务与实验的批注与结论确认。', icon: UserCheck }
]
</script>

<template>
  <DestinationView eyebrow="独立能力测评" title="从课程任务形成可复核的能力证据" intro="测评不另设考试，而是把课程任务、实验记录与教师评价折算成能力证据。">
    <ul class="assessment-sources">
      <li v-for="source in sources" :key="source.name">
        <div class="card-head"><span class="icon-chip"><component :is="source.icon" :size="20" /></span></div>
        <strong>{{ source.name }}</strong>
        <span>{{ source.detail }}</span>
      </li>
    </ul>
    <DestinationNote tone="auth" title="测评与历史记录需要校内登录">评分、历史结果与个人数据不会向匿名用户开放；当前可以先体验教学实验，了解判识依据的组织方式。</DestinationNote>
    <div class="assessment-actions">
      <button @click="router.push(WELL_LOG_LAB_PATH)">体验测井教学实验</button>
      <button class="is-quiet" @click="router.push(pathTo('ability-map'))">查看能力大图谱</button>
    </div>
  </DestinationView>
</template>

<style scoped>
.assessment-sources { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 20px; margin: 0; padding: 0; list-style: none; }
.assessment-sources li { display: flex; flex-direction: column; gap: 8px; padding: 22px 24px 20px; background: #fff; border: 1px solid #e6ecf2; border-radius: 14px; box-shadow: 0 1px 2px rgba(16, 52, 84, .05); transition: transform .22s ease, box-shadow .22s ease, border-color .22s ease; }
.assessment-sources li:hover { transform: translateY(-4px); border-color: #d4e3ef; box-shadow: 0 14px 28px rgba(7, 94, 163, .13); }
.card-head { margin-bottom: 14px; }
.icon-chip { display: inline-flex; align-items: center; justify-content: center; width: 44px; height: 44px; border-radius: 12px; background: #e8f4fc; color: #0870bc; }
.assessment-sources strong { color: #17384d; font-size: 17px; }
.assessment-sources span { color: #5f7487; line-height: 1.8; }
.assessment-actions { display: flex; flex-wrap: wrap; gap: 12px; }
.assessment-actions button { padding: 11px 18px; color: #fff; background: #0870bc; border: 0; border-radius: 4px; font-weight: 800; transition: transform 180ms ease; }
.assessment-actions button.is-quiet { color: #075a9d; background: #e8f4fc; }
.assessment-actions button:hover { transform: translateY(-2px); }
@media (prefers-reduced-motion: no-preference) {
  .assessment-sources li { animation: cardIn 360ms ease both; }
}
@keyframes cardIn { from { opacity: 0; } to { opacity: 1; } }
</style>
