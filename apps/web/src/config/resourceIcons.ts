import type { Component } from 'vue'
import {
  BookOpen,
  Boxes,
  Compass,
  Droplets,
  FlaskConical,
  GraduationCap,
  Layers,
  Microscope,
  Mountain,
  Radar,
  Radio,
  Waves
} from '@lucide/vue'

// 按资源 id 选一个能代表其主题的图标；缺省按分类回退。两页（AI 智慧课程 / 仿真模拟）
// 共用这一份映射，保证同一资源在两处图标一致。
const byId: Record<string, Component> = {
  'petroleum-geology-ai': Droplets,
  'petroleum-geology-ai-foundation': Mountain,
  'reservoir-characterization': Boxes,
  'oil-gas-exploration-graduate': Compass,
  'clastic-rock-vr': Microscope,
  'sedimentary-rock-vr': Layers,
  'seismic-exploration-vr': Waves,
  'radioactive-logging-vr': Radio,
  'geophysical-logging': Radio,
  'elastic-wave-dynamics': Waves,
  'seismic-wave-dynamics': Waves,
  'seismic-exploration-principles': Radar
}

const fallback: Record<string, Component> = {
  courses: GraduationCap,
  practice: FlaskConical
}

export function resourceIcon(resource: { id: string; category: string }): Component {
  return byId[resource.id] ?? fallback[resource.category] ?? BookOpen
}

// 卡片封面图：与图标同一套 id 映射，静态资源位于 public/images/resources（构建时原样拷贝）。
// 没有配图的资源返回 undefined，卡片回退到图标芯片。
const coverIds = new Set(Object.keys(byId))

export function resourceCover(id: string): string | undefined {
  return coverIds.has(id) ? `/images/resources/${id}.png` : undefined
}
