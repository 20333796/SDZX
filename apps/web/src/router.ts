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
      path: '/',
      name: 'home',
      component: () => import('@/pages/home')
    },
    {
      // Where the header's 登录 / 注册 entry lands. It is a page of its own rather than a modal because the
      // homepage is a scroll-snapped deck: a dialog there would have to fight the deck for the pointer, and
      // the column pages would each need their own copy of it.
      path: '/login',
      name: 'sign-in',
      component: () => import('@/pages/auth/index.vue'),
      // Someone already signed in has nothing to do here; hand them back rather than stacking a second
      // login form on top of a session that exists.
      beforeEnter: () => (session.isAuthenticated.value ? { name: 'home' } : true)
    },
    {
      path: '/assistant',
      name: 'assistant',
      component: () => import('@/pages/assistant/Bridge.vue')
    },
    {
      // Layout route: the header, hero band, footer and floating assistant live in PortalLayout, and
      // every column renders inside it. The children carry absolute paths (a child path starting with
      // '/' is rooted at the domain), so the layout supplies the chrome without prefixing the URLs —
      // the columns live at /teaching/mentor-graph, not /portal/teaching/mentor-graph.
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
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      redirect: { name: 'home' }
    }
  ]
})
