import type { Component } from 'vue'
import { BookOpen, Compass, MapPinned, Sparkles } from '@lucide/vue'

// One row per portal column. This table is the single source of truth for three things that used to be
// scattered and could disagree with each other:
//   * the header navigation (a destination looked up by `target`, i.e. the id the portal config API sends),
//   * the route each column lives on (`path`), and
//   * the hero band at the top of that page (`title` / `intro`).
// The previous version inferred the layer from the target's spelling (`target.startsWith('learning')`),
// which silently sent 成长画像 into the 因材智教 layer — its content rendered 智能研学's task list while the
// header highlighted 能力智验. Nothing here is inferred: an id maps to a path or it does not exist.
export type DestinationGroupKey = 'source' | 'teaching' | 'practice' | 'capability'

export interface DestinationGroup {
  key: DestinationGroupKey
  label: string
  icon: Component
}

export interface Destination {
  /** Matches `PortalNavigationLink.target` from the portal config API / fallback config. */
  target: string
  group: DestinationGroupKey
  /** Absolute route path. Columns sharing a group share the group's first path segment. */
  path: string
  /** Hero heading. */
  title: string
  /** Hero supporting line. */
  intro: string
  /**
   * Query the old `/layers/...?section=` links used to carry, preserved so the legacy redirect keeps
   * landing on the same view state (only 课程资源 used one: the resource-category filter).
   */
  legacyCategory?: string
}

export const DESTINATION_GROUPS: DestinationGroup[] = [
  { key: 'source', label: '知源智汇', icon: BookOpen },
  { key: 'teaching', label: '因材智教', icon: Sparkles },
  { key: 'practice', label: '实践智导', icon: Compass },
  { key: 'capability', label: '能力智验', icon: MapPinned }
]

export const DESTINATIONS: Destination[] = [
  // 知源智汇
  { target: 'resources', group: 'source', path: '/source/courses', title: 'AI 智慧课程', intro: '从公开课程与校内 AI 课程进入地质学习。', legacyCategory: 'courses' },
  { target: 'knowledge-graph', group: 'source', path: '/source/knowledge-graph', title: '学科知识图谱', intro: '查看课程、知识点与专业能力之间的连接。' },
  { target: 'geo-data', group: 'source', path: '/source/geo-data', title: '地学数据', intro: '浏览经过课程审核的公开教学图层与元数据。' },
  // 因材智教
  { target: 'learning-diagnosis', group: 'teaching', path: '/teaching/learning-diagnosis', title: '学情诊断', intro: '根据学习记录形成可由教师复核的诊断入口。' },
  { target: 'learning-tasks', group: 'teaching', path: '/teaching/learning-tasks', title: '智能研学', intro: '围绕课程目标完成任务、依据和教师反馈。' },
  { target: 'mentor-graph', group: 'teaching', path: '/teaching/mentor-graph', title: '导师图谱', intro: '按研究方向发现可联系的导师与课程关联。' },
  // 实践智导
  { target: 'practice-simulation', group: 'practice', path: '/practice/simulation', title: '虚拟仿真', intro: '从课程目录进入碎屑岩、沉积岩与地震勘探实验。' },
  { target: 'field-training', group: 'practice', path: '/practice/field-training', title: '野外实训', intro: '围绕地层路线、观察点与任务记录组织实训过程。' },
  { target: 'case-library', group: 'practice', path: '/practice/case-library', title: '工程案例', intro: '从资料解释到勘探判断建立案例学习路径。' },
  // 能力智验
  { target: 'geology-design', group: 'capability', path: '/capability/geology-design', title: '智能应用', intro: '汇聚地学各方向的智能应用入口，测井曲线判识为首个上线实验。' },
  { target: 'ability-map', group: 'capability', path: '/capability/ability-map', title: '能力大图谱', intro: '从课程学习、综合判识到实践创新，沿能力路径继续探索。' },
  { target: 'capability-assessment', group: 'capability', path: '/capability/assessment', title: '独立能力测评', intro: '通过课程任务与教师评价形成能力证据。' },
  { target: 'learning-profile', group: 'capability', path: '/capability/profile', title: '成长画像', intro: '聚合学习、实践与评价记录，呈现可追溯的成长轨迹。' }
]

const byTarget = new Map(DESTINATIONS.map((d) => [d.target, d]))
const byPath = new Map(DESTINATIONS.map((d) => [d.path, d]))
const groupByKey = new Map(DESTINATION_GROUPS.map((g) => [g.key, g]))

export function destinationForTarget(target: string): Destination | undefined {
  return byTarget.get(target)
}

export function destinationForPath(path: string): Destination | undefined {
  return byPath.get(path)
}

/** Path for a column id — the only way pages should build links to another column. */
export function pathTo(target: string): string {
  return byTarget.get(target)?.path ?? '/'
}

/**
 * 智能应用 column hosts several tools; the well-log lab is the first one that actually exists.
 * It lives on its own route under the same column so the hub can link to it and the portal
 * chrome still highlights 智能应用 while it is open.
 */
export const WELL_LOG_LAB_PATH = '/capability/well-log'

export function groupOf(destination: Destination): DestinationGroup {
  // Every destination group has a row in DESTINATION_GROUPS; the non-null assertion is safe and the
  // build-time check below keeps it that way.
  return groupByKey.get(destination.group) as DestinationGroup
}

export function destinationsInGroup(key: DestinationGroupKey): Destination[] {
  return DESTINATIONS.filter((d) => d.group === key)
}

/**
 * Resolve the legacy `/layers/:layer?section=<target>` form onto a destination. Used by the redirect that
 * keeps old links (bookmarks, the browser tabs already open during this refactor) working.
 */
export function resolveLegacyDestination(layer: string, section: string): Destination | undefined {
  return destinationForTarget(section) ?? destinationsInGroup(layer as DestinationGroupKey)[0]
}

if (import.meta.env.DEV) {
  // Catch drift at dev time: a new column added to the portal config API without a row here would
  // otherwise become an unclickable nav entry.
  const known = new Set(DESTINATIONS.map((d) => d.target))
  console.assert(
    DESTINATION_GROUPS.every((g) => destinationsInGroup(g.key).length > 0),
    'destinations: every group needs at least one destination'
  )
  console.assert(known.size === DESTINATIONS.length, 'destinations: duplicate target id')
}
