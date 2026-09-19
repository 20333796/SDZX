<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { ExternalLink } from '@lucide/vue'
import { fallbackResources } from '@/config/resources'
import { resourceCover, resourceIcon } from '@/config/resourceIcons'
import DestinationView from '@/features/portal/DestinationView.vue'

// 本页只列课程家族；实践资源在 /practice/simulation，学科知识图谱是独立页面。
const route = useRoute()
const resources = computed(() => {
  const keyword = typeof route.query.q === 'string' ? route.query.q.trim().toLowerCase() : ''
  return fallbackResources
    .filter((resource) => resource.category === 'courses')
    .filter((resource) => !keyword || `${resource.title} ${resource.provider} ${resource.description}`.toLowerCase().includes(keyword))
})
</script>

<template>
  <section id="resources" class="resource-catalog" aria-label="课程资源目录">
    <DestinationView
      eyebrow="课程资源"
      title="从课程家族进入学习"
      intro="课程资源保留来源平台入口，学习规则由原平台负责。"
    >
      <div class="catalog-grid">
        <article v-for="resource in resources" :key="resource.id">
          <div v-if="resourceCover(resource.id)" class="card-cover">
            <img :src="resourceCover(resource.id)" :alt="resource.title" loading="lazy" />
            <span class="level-badge" :class="{ 'is-graduate': resource.course_level === '研究生' }">{{ resource.course_level }}</span>
          </div>
          <div v-else class="card-head">
            <span class="icon-chip"><component :is="resourceIcon(resource)" :size="20" /></span>
            <span class="level-badge" :class="{ 'is-graduate': resource.course_level === '研究生' }">{{ resource.course_level }}</span>
          </div>
          <h3>{{ resource.title }}</h3>
          <p>{{ resource.description }}</p>
          <footer>
            <small>
              <span class="provider">{{ resource.provider }}</span>
              {{ resource.credits ? `${resource.credits} 学分` : '学分待补充' }} · {{ resource.audience }}
            </small>
            <a v-if="resource.status === 'active'" :href="resource.url ?? undefined" target="_blank" rel="noopener noreferrer">前往学习 <ExternalLink :size="14" /></a>
            <em v-else>链接待补充</em>
          </footer>
        </article>
      </div>
    </DestinationView>
  </section>
</template>

<style scoped>
/* 外层仅作 :deep() 锚点（PortalLayout 据此统一蓝色调），不再自带内边距。 */
.resource-catalog { padding: 0; }
.catalog-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
.catalog-grid article {
  display: flex; flex-direction: column;
  padding: 22px 24px 20px;
  background: #fff;
  border: 1px solid #e6ecf2;
  border-radius: 14px;
  box-shadow: 0 1px 2px rgba(16, 52, 84, .05);
  transition: transform .22s ease, box-shadow .22s ease, border-color .22s ease;
}
.catalog-grid article:hover {
  transform: translateY(-4px);
  border-color: #d4e3ef;
  /* 悬停阴影由 PortalLayout 的 :deep 规则统一提供，这里只补位移与描边。 */
}
.card-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.card-cover { position: relative; margin-bottom: 16px; }
.card-cover img { display: block; width: 100%; height: 132px; object-fit: cover; border-radius: 10px; background: #f2f6fa; }
.card-cover .level-badge { position: absolute; top: 10px; right: 10px; background: rgba(255, 255, 255, .92); box-shadow: 0 1px 4px rgba(16, 52, 84, .14); }
.icon-chip {
  display: inline-flex; align-items: center; justify-content: center;
  width: 44px; height: 44px; border-radius: 12px;
  background: #e8f4fc; color: #0870bc;
}
.level-badge {
  display: inline-flex; align-items: center;
  padding: 5px 12px; border-radius: 999px;
  color: #0870bc; background: #e8f4fc;
  font-size: 12px; font-weight: 800; line-height: 1; letter-spacing: .02em;
}
.level-badge.is-graduate { color: #4a4fb5; background: #eef0fb; }
.catalog-grid h3 { margin: 0 0 10px; color: #17384d; font-size: 19px; font-weight: 700; line-height: 1.4; }
.catalog-grid p { flex: 1; margin: 0; color: #5f7487; font-size: 14px; line-height: 1.75; }
.catalog-grid footer {
  display: flex; align-items: flex-end; justify-content: space-between; gap: 14px;
  margin-top: 18px; padding-top: 16px;
  border-top: 1px solid #eef2f6;
}
.catalog-grid small { color: #8a98a6; font-size: 12px; line-height: 1.6; }
.catalog-grid .provider { display: block; margin-bottom: 4px; color: #7b8fa0; font-weight: 700; }
.catalog-grid a {
  display: inline-flex; align-items: center; gap: 5px;
  color: #0870bc; font-size: 13px; font-weight: 800; text-decoration: none; white-space: nowrap;
}
.catalog-grid a:hover { text-decoration: underline; }
.catalog-grid em { color: #98a9b6; font-style: normal; font-size: 12px; white-space: nowrap; }
@media (max-width: 600px) { .catalog-grid { grid-template-columns: 1fr; } }
@media (prefers-reduced-motion: no-preference) {
  .catalog-grid article { animation: cardIn 360ms ease both; }
}
@keyframes cardIn { from { opacity: 0; } to { opacity: 1; } }
</style>
