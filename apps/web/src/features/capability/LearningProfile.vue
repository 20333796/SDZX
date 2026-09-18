<script setup lang="ts">
import { useRouter } from 'vue-router'
import { GraduationCap, FlaskConical, BadgeCheck } from '@lucide/vue'
import { pathTo } from '@/config/destinations'
import DestinationView from '@/features/portal/DestinationView.vue'
import DestinationNote from '@/features/portal/DestinationNote.vue'

const router = useRouter()

// Was the column that rendered the 智能研学 task list: the header's id-based layer inference put
// `learning-profile` (a 能力智验 column) under the 因材智教 layer, where every section that was not
// explicitly handled fell through to <LearningTasks>. It is now its own page.
const tracks = [
  { name: '学习', detail: '课程学习与任务完成情况，按学期与课程归集。', icon: GraduationCap },
  { name: '实践', detail: '虚拟仿真与野外实训的记录，含实验名称与完成状态。', icon: FlaskConical },
  { name: '评价', detail: '教师批注、任务结论与能力证据的确认记录。', icon: BadgeCheck }
]
</script>

<template>
  <DestinationView eyebrow="成长画像" title="学习、实践与评价汇聚成成长轨迹" intro="按时间轴聚合课程学习、实验实践与评价记录，呈现可追溯的成长过程。">
    <div class="profile-tracks">
      <article v-for="track in tracks" :key="track.name">
        <div class="card-head"><span class="icon-chip"><component :is="track.icon" :size="20" /></span></div>
        <strong>{{ track.name }}</strong>
        <p>{{ track.detail }}</p>
      </article>
    </div>
    <DestinationNote tone="auth" title="画像数据需校内登录后查看">成长画像由个人学习与实践记录聚合而成，属校内数据，需在统一认证接入后启用。</DestinationNote>
    <div class="profile-actions">
      <button @click="router.push(pathTo('ability-map'))">查看能力大图谱</button>
      <button class="is-quiet" @click="router.push(pathTo('learning-diagnosis'))">了解学情诊断</button>
    </div>
  </DestinationView>
</template>

<style scoped>
.profile-tracks { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 20px; }
.profile-tracks article { display: flex; flex-direction: column; gap: 8px; padding: 22px 24px 20px; background: #fff; border: 1px solid #e6ecf2; border-radius: 14px; box-shadow: 0 1px 2px rgba(16, 52, 84, .05); transition: transform .22s ease, box-shadow .22s ease, border-color .22s ease; }
.profile-tracks article:hover { transform: translateY(-4px); border-color: #d4e3ef; box-shadow: 0 14px 28px rgba(7, 94, 163, .13); }
.card-head { margin-bottom: 14px; }
.icon-chip { display: inline-flex; align-items: center; justify-content: center; width: 44px; height: 44px; border-radius: 12px; background: #e8f4fc; color: #0870bc; }
.profile-tracks strong { color: #17384d; font-size: 17px; }
.profile-tracks p { margin: 0; color: #5f7487; line-height: 1.8; }
.profile-actions { display: flex; flex-wrap: wrap; gap: 12px; }
.profile-actions button { padding: 11px 18px; color: #fff; background: #0870bc; border: 0; border-radius: 4px; font-weight: 800; transition: transform 180ms ease; }
.profile-actions button.is-quiet { color: #075a9d; background: #e8f4fc; }
.profile-actions button:hover { transform: translateY(-2px); }
@media (prefers-reduced-motion: no-preference) {
  .profile-tracks article { animation: cardIn 360ms ease both; }
}
@keyframes cardIn { from { opacity: 0; } to { opacity: 1; } }
</style>
