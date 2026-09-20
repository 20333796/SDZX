import { createRouter, createWebHistory } from 'vue-router'
import { DESTINATIONS, resolveLegacyDestination, WELL_LOG_LAB_PATH } from '@/config/destinations'
import { session } from '@/session'

// Column -> view. Each portal column is its own page component; this table is what makes them
// independent, instead of one page branching on `/layers/:layer` + a `section` query.
const views: Record<string, () => Promise<unknown>> = {
  resources: () => import('@/features/resources/ResourceCatalog.vue'),
  'knowledge-graph': () => import('@/features/knowledge-graph/KnowledgeGraph.vue'),
  'geo-data': () => import('@/features/geo-data/GeoDataMap.vue'),
  'learning-diagnosis': () => import('@/features/teaching/LearningDiagnosis.vue'),
  'learning-tasks': () => import('@/features/learning/LearningTasks.vue'),
  'mentor-graph': () => import('@/features/teaching/MentorGraph.vue'),
  'practice-simulation': () => import('@/features/practice/PracticeSimulation.vue'),
  'field-training': () => import('@/features/practice/FieldTraining.vue'),
  'case-library': () => import('@/features/practice/CaseLibrary.vue'),
  // 智能应用 is an entry hub over several tools; the well-log lab is the first live tool and
  // lives on its own route below (WELL_LOG_LAB_PATH).
  'geology-design': () => import('@/features/apps/SmartAppsHub.vue'),
  'ability-map': () => import('@/features/capability/AbilityMap.vue'),
  'capability-assessment': () => import('@/features/capability/CapabilityAssessment.vue'),
  'learning-profile': () => import('@/features/capability/LearningProfile.vue')
}

if (import.meta.env.DEV) {
  const missing = DESTINATIONS.filter((d) => !views[d.target]).map((d) => d.target)
  console.assert(missing.length === 0, 'router: destinations without a view:', missing)
}

export const router = createRouter({
  history: createWebHistory(),
  // Every destination is a real page, so a route change starts at the top. This replaces the
  // scrollTo() the single-page version needed in order to fake that.
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    {
      // 站点根 `/`：郭网页静态落地页（public/landing/index.html）的跳转由全局 beforeEach 承接。
      // 必须单独给 `/` 一条记录：若放任它落进 catch-all，redirect 会先于全局守卫解析，
      // 守卫看到的 to.path 已经是 /platform/，落地页跳转就永远不会触发。
      path: '/',
      name: 'site-root',
      component: () => import('@/pages/home')
    },
    {
      path: '/platform/',
      name: 'home',
      component: () => import('@/pages/home')
    },
    {
      // Where the header's 登录 / 注册 entry lands. It is a page of its own rather than a modal because the
      // homepage is a scroll-snapped deck: a dialog there would have to fight the deck for the pointer, and
      // the column pages would each need their own copy of it.
      path: '/platform/login',
      name: 'sign-in',
      component: () => import('@/pages/auth/index.vue'),
      // Someone already signed in has nothing to do here; hand them back rather than stacking a second
      // login form on top of a session that exists.
      beforeEnter: () => (session.isAuthenticated.value ? { name: 'home' } : true)
    },
    {
      path: '/platform/assistant',
      name: 'assistant',
      component: () => import('@/pages/assistant/Bridge.vue')
    },
    {
      // Keep the established public URL while serving the current portal assistant.
      path: '/platform/geochat/agent',
      name: 'geochat-agent',
      component: () => import('@/pages/assistant/index.vue')
    },
    {
      // Layout route: the header, hero band, footer and floating assistant live in PortalLayout, and
      // every column renders inside it. The children carry absolute paths (a child path starting with
      // '/' is rooted at the domain), so the layout supplies the chrome without prefixing the URLs —
      // the columns live at /platform/teaching/mentor-graph, not /portal/teaching/mentor-graph.
      path: '/portal',
      component: () => import('@/pages/portal/PortalLayout.vue'),
      children: [
        { path: '', redirect: { name: 'home' } },
        ...DESTINATIONS.map((destination) => ({
          path: destination.path,
          name: destination.target,
          component: views[destination.target],
          meta: { target: destination.target }
        })),
        {
          // A tool inside the 智能应用 hub rather than a column of its own: it keeps the column's
          // meta.target so the portal header still highlights 智能应用 while it is open.
          path: WELL_LOG_LAB_PATH,
          name: 'well-log-lab',
          component: () => import('@/features/well-log/WellLogLab.vue'),
          meta: { target: 'geology-design' }
        }
      ]
    },
    {
      // The old shape: every column was a query value on four layered URLs. Kept as a redirect so
      // links already in the wild, and browser tabs left open across this refactor, still land right.
      path: '/layers/:layer(source|teaching|practice|capability)',
      name: 'layer-legacy',
      redirect: (to) => {
        const section = typeof to.query.section === 'string' ? to.query.section : ''
        const destination = resolveLegacyDestination(String(to.params.layer), section)
        if (!destination) return { name: 'home' }
        const category = typeof to.query.category === 'string' ? to.query.category : destination.legacyCategory
        return { path: destination.path, query: category ? { category } : undefined }
      }
    },
    {
      // 迁移兼容：旧栏目绝对路径整体搬到 /platform 前缀下（书签、助手消息里的 resource.route 等）。
      // 用记录级 redirect 承接——它在全局守卫之前解析，不依赖守卫顺序，旧链接一定落地。
      path: '/:legacy(source|teaching|practice|capability)/:rest(.*)*',
      redirect: (to) => ({ path: `/platform${to.path}`, query: to.query, hash: to.hash })
    },
    { path: '/login', redirect: '/platform/login' },
    { path: '/assistant', redirect: '/platform/assistant' },
    { path: '/geochat/agent', redirect: '/platform/geochat/agent' },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      redirect: { name: 'home' }
    }
  ]
})

// 站点根 `/` 落地页（public/landing，即桌面“郭网页”静态首页）的整页跳转。
// 旧绝对路径（/source/...、/login、/assistant、/geochat/agent）的兼容重定向已改为上面的
// 记录级 redirect——记录 redirect 先于全局守卫解析，放在守卫里反而永远轮不到。
router.beforeEach((to) => {
  if (to.path === '/') {
    // 整页换到静态落地页（public/landing/index.html）。用显式文件名而非 `/landing/`，
    // 是因为 Vite 的 SPA history fallback 会把目录请求 `/landing/` 改写成平台首页
    // （预览/生产里由 vite.config 的 serve-landing 中间件兜住 `/landing` 与 `/landing/`）。
    window.location.replace('/landing/index.html')
    return false
  }
})
