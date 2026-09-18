<script setup lang="ts">
import { computed } from 'vue'
import { ExternalLink } from '@lucide/vue'
import { fallbackResources } from '@/config/resources'
import { resourceCover, resourceIcon } from '@/config/resourceIcons'
import DestinationView from '@/features/portal/DestinationView.vue'
import DestinationNote from '@/features/portal/DestinationNote.vue'

// This column has real content: the catalog already carries the virtual-lab experiments. It used to be
// one of three cards on a shared page, so the experiments themselves were never listed here.
const experiments = computed(() => fallbackResources.filter((resource) => resource.category === 'practice'))
</script>

<template>
  <DestinationView eyebrow="虚拟仿真" title="进入虚拟仿真实验" intro="实验由各校内外平台承载，实验账号、学时与考核规则由原平台负责。">
    <div class="simulation-grid">
      <article v-for="experiment in experiments" :key="experiment.id">
        <div v-if="resourceCover(experiment.id)" class="card-cover">
          <img :src="resourceCover(experiment.id)" :alt="experiment.title" loading="lazy" />
          <span class="level-badge is-practice">{{ experiment.course_level }}</span>
        </div>
        <div v-else class="card-head">
          <span class="icon-chip" :class="{ 'is-practice': experiment.category === 'practice' }"><component :is="resourceIcon(experiment)" :size="20" /></span>
          <span class="level-badge" :class="{ 'is-graduate': experiment.course_level === '研究生', 'is-practice': experiment.category === 'practice' }">{{ experiment.course_level }}</span>
        </div>
        <h3>{{ experiment.title }}</h3>
        <p>{{ experiment.description }}</p>
        <footer>
          <small>
            <span class="provider">{{ experiment.provider }}</span>
            {{ experiment.audience }}
          </small>
          <a v-if="experiment.status === 'active' && experiment.url" :href="experiment.url" target="_blank" rel="noopener noreferrer">前往实验 <ExternalLink :size="14" /></a>
          <em v-else>链接待补充</em>
        </footer>
      </article>
    </div>
    <DestinationNote title="打开实验平台需要相应权限">虚拟仿真平台通常要求选课名单或校内账号，未登录时会跳转到平台自身的登录页。</DestinationNote>
  </DestinationView>
</template>

<style scoped>
/* 与 AI 智慧课程页（ResourceCatalog）共用同一套卡片语言，仅数据来源不同。 */
.simulation-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
.simulation-grid article {
  display: flex; flex-direction: column;
  padding: 22px 24px 20px;
  background: #fff;
  border: 1px solid #e6ecf2;
  border-radius: 14px;
  box-shadow: 0 1px 2px rgba(16, 52, 84, .05);
  transition: transform .22s ease, box-shadow .22s ease, border-color .22s ease;
}
.simulation-grid article:hover { transform: translateY(-4px); border-color: #d4e3ef; box-shadow: 0 14px 28px rgba(7, 94, 163, .13); }
.card-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.card-cover { position: relative; margin-bottom: 16px; }
.card-cover img { display: block; width: 100%; height: 132px; object-fit: cover; border-radius: 10px; background: #f2f7f7; }
.card-cover .level-badge { position: absolute; top: 10px; right: 10px; background: rgba(255, 255, 255, .92); box-shadow: 0 1px 4px rgba(16, 52, 84, .14); }
.icon-chip {
  display: inline-flex; align-items: center; justify-content: center;
  width: 44px; height: 44px; border-radius: 12px;
  background: #e8f4fc; color: #0870bc;
}
/* 仿真/实践域用站点既有的青色次级色，与课程页的蓝形成两色区分（站点 geo/data 页也用此青色）。 */
.icon-chip.is-practice { background: #e6f4f1; color: #0e7596; }
.level-badge {
  display: inline-flex; align-items: center;
  padding: 5px 12px; border-radius: 999px;
  color: #0870bc; background: #e8f4fc;
  font-size: 12px; font-weight: 800; line-height: 1; letter-spacing: .02em;
}
.level-badge.is-graduate { color: #4a4fb5; background: #eef0fb; }
.level-badge.is-practice { color: #0e7596; background: #e6f4f1; }
.level-badge.is-graduate.is-practice { color: #0b5e63; background: #e3eef0; }
.simulation-grid h3 { margin: 0 0 10px; color: #17384d; font-size: 19px; font-weight: 700; line-height: 1.4; }
.simulation-grid p { flex: 1; margin: 0; color: #5f7487; line-height: 1.75; }
.simulation-grid footer {
  display: flex; align-items: flex-end; justify-content: space-between; gap: 12px;
  margin-top: 18px; padding-top: 16px;
  border-top: 1px solid #eef2f6;
}
.simulation-grid small { color: #8a98a6; line-height: 1.6; }
.simulation-grid .provider { display: block; margin-bottom: 4px; color: #7b8fa0; font-weight: 700; }
.simulation-grid a {
  display: inline-flex; align-items: center; gap: 5px;
  color: #0e7596; font-weight: 800; white-space: nowrap; text-decoration: none;
}
.simulation-grid a:hover { text-decoration: underline; }
.simulation-grid em { color: #98a9b6; font-style: normal; }
@media (max-width: 600px) { .simulation-grid { grid-template-columns: 1fr; } }
@media (prefers-reduced-motion: no-preference) {
  .simulation-grid article { animation: cardIn 360ms ease both; }
}
@keyframes cardIn { from { opacity: 0; } to { opacity: 1; } }
</style>
