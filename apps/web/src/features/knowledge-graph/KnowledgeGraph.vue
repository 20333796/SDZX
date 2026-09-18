<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { ECharts } from 'echarts/core'
import DestinationView from '@/features/portal/DestinationView.vue'
import { pathTo, WELL_LOG_LAB_PATH } from '@/config/destinations'

type GraphNode = { id: string; name: string; category: string; description: string }
type GraphEdge = { source: string; target: string; relation: string }
type GraphData = { nodes: GraphNode[]; edges: GraphEdge[] }
type Neighbor = { id: string; name: string; category: string; relation: string; direction: 'out' | 'in' }
type ChartEngine = Pick<typeof import('echarts/core'), 'init'>

const CATEGORY_COLORS: Record<string, string> = { 课程: '#0870bc', 知识点: '#d29d48', 能力: '#0e7596' }
const CATEGORY_ORDER = ['课程', '知识点', '能力']

// 后端不可用时的最小兜底图（正式内容见 /api/v1/knowledge-graph）。
const fallbackGraph: GraphData = {
  nodes: [
    { id: 'petroleum-geology', name: '油矿地质学', category: '课程', description: '油气成藏与勘探地质基础。' },
    { id: 'well-log', name: '地球物理测井', category: '课程', description: '测井曲线与地层、储层解释。' },
    { id: 'reservoir', name: '储层', category: '知识点', description: '孔隙度、渗透率与储集空间。' },
    { id: 'logging-interpretation', name: '测井解释', category: '能力', description: '使用曲线证据完成教学判识。' }
  ],
  edges: [
    { source: 'petroleum-geology', target: 'reservoir', relation: '讲授' },
    { source: 'well-log', target: 'reservoir', relation: '识别' },
    { source: 'well-log', target: 'logging-interpretation', relation: '训练' }
  ]
}

const graph = ref<GraphData>(fallbackGraph)
const usingFallback = ref(false)
const loading = ref(true)
const activeCategory = ref<string>('')
const selectedId = ref<string>('')
const target = ref<HTMLDivElement | null>(null)
let chart: ECharts | undefined
let resizeObserver: ResizeObserver | undefined

const categoryCounts = computed(() => {
  const counts: Record<string, number> = {}
  for (const node of graph.value.nodes) counts[node.category] = (counts[node.category] ?? 0) + 1
  return counts
})
const filteredGraph = computed<GraphData>(() => {
  if (!activeCategory.value) return graph.value
  const nodes = graph.value.nodes.filter((node) => node.category === activeCategory.value)
  const allowed = new Set(nodes.map((node) => node.id))
  const edges = graph.value.edges.filter((edge) => allowed.has(edge.source) && allowed.has(edge.target))
  return { nodes, edges }
})
const nodeIndex = computed(() => new Map(graph.value.nodes.map((node) => [node.id, node])))
const selected = computed(() => nodeIndex.value.get(selectedId.value))
const neighbors = computed<Neighbor[]>(() => {
  const id = selectedId.value
  if (!id) return []
  const list: Neighbor[] = []
  for (const edge of graph.value.edges) {
    if (edge.source === id) {
      const node = nodeIndex.value.get(edge.target)
      if (node) list.push({ id: node.id, name: node.name, category: node.category, relation: edge.relation, direction: 'out' })
    } else if (edge.target === id) {
      const node = nodeIndex.value.get(edge.source)
      if (node) list.push({ id: node.id, name: node.name, category: node.category, relation: edge.relation, direction: 'in' })
    }
  }
  return list
})
const outgoing = computed(() => neighbors.value.filter((item) => item.direction === 'out'))
const incoming = computed(() => neighbors.value.filter((item) => item.direction === 'in'))

// 节点 → 平台内相关页面的快捷入口（图谱不只是看，还要能跳去学）。
const LOGGING_NODE_IDS = new Set(['well-log', 'well-log-advanced', 'logging-interpretation', 'archie'])
const quickLinks = computed<{ label: string; to: string }[]>(() => {
  const node = selected.value
  if (!node) return []
  const links: { label: string; to: string }[] = []
  if (node.category === '课程') links.push({ label: '进入相关课程资源', to: pathTo('resources') })
  if (node.category === '能力') links.push({ label: '去能力测评验证', to: pathTo('capability-assessment') })
  if (LOGGING_NODE_IDS.has(node.id)) links.push({ label: '去测井实验室分析曲线', to: WELL_LOG_LAB_PATH })
  if (['trap', 'structural-interpretation', 'seismic-interpretation', 'seismic-waves'].includes(node.id)) links.push({ label: '查看地震勘探虚拟仿真', to: pathTo('practice-simulation') })
  return links
})

function selectNode(id: string) {
  if (!nodeIndex.value.has(id)) return
  selectedId.value = id
  if (!chart) return
  chart.setOption({
    series: [{
      data: filteredGraph.value.nodes.map((node) => ({
        id: node.id,
        name: node.name,
        symbolSize: node.id === selectedId.value ? 60 : node.category === '课程' ? 52 : node.category === '能力' ? 44 : 34,
        itemStyle: node.id === selectedId.value
          ? { color: CATEGORY_COLORS[node.category] ?? '#356c9a', borderColor: '#0b5e63', borderWidth: 3 }
          : { color: CATEGORY_COLORS[node.category] ?? '#356c9a' }
      }))
    }]
  })
  chart.dispatchAction({ type: 'highlight', name: nodeIndex.value.get(id)?.name })
}

function renderChart() {
  if (!target.value) return
  void import('echarts/core').then(async (core) => {
    const [{ GraphChart }, { TooltipComponent }, { CanvasRenderer }] = await Promise.all([
      import('echarts/charts'),
      import('echarts/components'),
      import('echarts/renderers')
    ])
    core.use([GraphChart, TooltipComponent, CanvasRenderer])
    chart?.dispose()
    chart = core.init(target.value!)
    const nodeByName = new Map(filteredGraph.value.nodes.map((node) => [node.name, node]))
    chart.setOption({
      animationDurationUpdate: 380,
      tooltip: {
        confine: true,
        formatter: (item: { dataType: string; data: { name?: string; relation?: string; description?: string } }) => {
          if (item.dataType === 'edge') return item.data.relation ?? ''
          return `<strong>${item.data.name ?? ''}</strong><br/>${item.data.description ?? ''}`
        }
      },
      series: [{
        type: 'graph',
        layout: 'force',
        roam: true,
        draggable: true,
        data: filteredGraph.value.nodes.map((node) => ({
          id: node.id,
          name: node.name,
          symbolSize: node.id === selectedId.value ? 60 : node.category === '课程' ? 52 : node.category === '能力' ? 44 : 34,
          itemStyle: node.id === selectedId.value
            ? { color: CATEGORY_COLORS[node.category] ?? '#356c9a', borderColor: '#0b5e63', borderWidth: 3 }
            : { color: CATEGORY_COLORS[node.category] ?? '#356c9a' }
        })),
        links: filteredGraph.value.edges.map((edge) => ({ source: edge.source, target: edge.target, value: edge.relation })),
        force: { repulsion: 320, edgeLength: [70, 120], gravity: 0.12 },
        edgeSymbol: ['none', 'arrow'],
        edgeSymbolSize: 8,
        label: { show: true, color: '#22384a', fontSize: 11, position: 'bottom' },
        lineStyle: { color: '#9db9c2', curveness: 0.08, width: 1.2 }
      }]
    })
    chart.on('click', (event: { dataType?: string; name?: string }) => {
      const node = event.dataType === 'node' ? nodeByName.get(event.name ?? '') : undefined
      if (node) selectNode(node.id)
    })
    resizeObserver?.disconnect()
    resizeObserver = new ResizeObserver(() => chart?.resize())
    resizeObserver.observe(target.value!)
  })
}

watch(activeCategory, () => {
  if (selectedId.value && !filteredGraph.value.nodes.some((node) => node.id === selectedId.value)) {
    selectedId.value = filteredGraph.value.nodes[0]?.id ?? ''
  }
  renderChart()
})

async function loadGraph() {
  try {
    const response = await fetch('/api/v1/knowledge-graph')
    if (!response.ok) throw new Error(String(response.status))
    const payload = (await response.json()) as GraphData
    if (!payload.nodes?.length) throw new Error('empty')
    graph.value = payload
  } catch {
    graph.value = fallbackGraph
    usingFallback.value = true
  } finally {
    loading.value = false
    selectedId.value = graph.value.nodes[0]?.id ?? ''
    await nextTick()
    renderChart()
  }
}

onMounted(() => void loadGraph())
onBeforeUnmount(() => { resizeObserver?.disconnect(); chart?.dispose() })
</script>

<template>
  <section id="knowledge-graph" class="knowledge-graph" aria-label="学科知识图谱">
    <DestinationView
      eyebrow="学科知识图谱"
      title="课程如何连接能力"
      intro="三层图谱把主干课程、核心知识点与教学能力连接成网：课程讲授知识点，知识点支撑能力，课程通过项目训练能力。点击节点查看它的关系。"
    >
      <p v-if="usingFallback" class="fallback-note">后端服务未连接，当前展示精简示例图谱；数据以接口恢复后的版本为准。</p>

      <div class="stats-strip">
        <div><strong>{{ loading ? '—' : graph.nodes.length }}</strong><span>知识节点</span></div>
        <div><strong>{{ loading ? '—' : graph.edges.length }}</strong><span>教学关系</span></div>
        <div><strong>{{ loading ? '—' : categoryCounts['课程'] ?? 0 }}</strong><span>主干课程</span></div>
        <div><strong>{{ loading ? '—' : categoryCounts['能力'] ?? 0 }}</strong><span>核心能力</span></div>
      </div>

      <div class="filter-chips" role="tablist" aria-label="按层级筛选">
        <button :class="{ selected: activeCategory === '' }" @click="activeCategory = ''">全部（{{ graph.nodes.length }}）</button>
        <button
          v-for="category in CATEGORY_ORDER.filter((key) => categoryCounts[key])"
          :key="category"
          :class="{ selected: activeCategory === category }"
          @click="activeCategory = activeCategory === category ? '' : category"
        >
          <i class="dot" :style="{ background: CATEGORY_COLORS[category] }"></i>
          {{ category }}（{{ categoryCounts[category] }}）
        </button>
      </div>

      <div class="graph-layout">
        <div class="graph-wrap">
          <div ref="target" class="graph-canvas" aria-label="学科知识图谱交互视图"></div>
          <div class="graph-legend">
            <span v-for="(color, category) in CATEGORY_COLORS" :key="category"><i :style="{ background: color }"></i>{{ category }}</span>
          </div>
        </div>

        <aside class="detail-panel">
          <template v-if="selected">
            <p class="detail-tag" :style="{ color: CATEGORY_COLORS[selected.category] }">{{ selected.category }}</p>
            <h4>{{ selected.name }}</h4>
            <p class="detail-desc">{{ selected.description }}</p>

            <div v-if="outgoing.length" class="relation-group">
              <p>指向（{{ outgoing.length }}）</p>
              <ul>
                <li v-for="item in outgoing" :key="`out-${item.id}`" role="button" tabindex="0" @click="selectNode(item.id)" @keydown.enter.prevent="selectNode(item.id)">
                  <strong>{{ item.name }}</strong>
                  <span>{{ item.relation }} →</span>
                </li>
              </ul>
            </div>
            <div v-if="incoming.length" class="relation-group">
              <p>来源（{{ incoming.length }}）</p>
              <ul>
                <li v-for="item in incoming" :key="`in-${item.id}`" role="button" tabindex="0" @click="selectNode(item.id)" @keydown.enter.prevent="selectNode(item.id)">
                  <strong>{{ item.name }}</strong>
                  <span>← {{ item.relation }}</span>
                </li>
              </ul>
            </div>

            <div v-if="quickLinks.length" class="quick-links">
              <RouterLink v-for="link in quickLinks" :key="link.to + link.label" :to="link.to">{{ link.label }} →</RouterLink>
            </div>
          </template>
        </aside>
      </div>
    </DestinationView>
  </section>
</template>

<style scoped>
.knowledge-graph { padding: 0; }
.fallback-note { margin: 0; padding: 10px 14px; color: #7a5c12; background: #fdf6e3; border: 1px solid #f0e2b6; border-radius: 10px; font-size: 13px; }

.stats-strip { display: flex; align-items: center; gap: 26px; padding: 4px 0 14px; border-bottom: 1px solid #e6ecf2; }
.stats-strip div { display: flex; align-items: baseline; gap: 8px; }
.stats-strip strong { color: #0870bc; font-size: 26px; font-weight: 800; }
.stats-strip span { color: #5f7487; font-size: 13px; }
.stats-strip div + div { padding-left: 26px; border-left: 1px solid #e6ecf2; }

.filter-chips { display: flex; flex-wrap: wrap; gap: 8px; }
.filter-chips button { display: inline-flex; align-items: center; gap: 6px; padding: 7px 13px; color: #3d5464; background: #fff; border: 1px solid #d8e4ea; border-radius: 999px; font-size: 13px; font-weight: 600; transition: color .18s ease, background .18s ease, border-color .18s ease; }
.filter-chips button:hover { color: #0870bc; border-color: #a9cbe2; }
.filter-chips button.selected { color: #fff; background: #0870bc; border-color: #0870bc; }
.filter-chips .dot { width: 8px; height: 8px; border-radius: 50%; }
.filter-chips button.selected .dot { background: rgba(255, 255, 255, .85) !important; }

.graph-layout { display: grid; grid-template-columns: minmax(0, 1fr) 300px; gap: 20px; align-items: start; }
.graph-wrap { position: relative; }
.graph-canvas { height: 520px; border: 1px solid #e6ecf2; border-radius: 14px; background: #f8fbfd; overflow: hidden; }
.graph-legend { position: absolute; top: 12px; left: 14px; display: flex; gap: 14px; padding: 6px 12px; background: rgba(255, 255, 255, .92); border: 1px solid #e6ecf2; border-radius: 999px; font-size: 12px; color: #3d5464; }
.graph-legend i { display: inline-block; width: 9px; height: 9px; margin-right: 5px; border-radius: 50%; }

.detail-panel { position: sticky; top: 20px; display: grid; gap: 10px; align-content: start; padding: 16px 18px; background: #fff; border: 1px solid #e6ecf2; border-radius: 14px; box-shadow: 0 1px 2px rgba(16, 52, 84, .05); }
.detail-panel:empty { display: none; }
.detail-tag { margin: 0; font-size: 11px; font-weight: 800; letter-spacing: .08em; }
.detail-panel h4 { margin: 0; color: #17384d; font-size: 17px; }
.detail-desc { margin: 0; color: #5f7487; font-size: 12.5px; line-height: 1.7; }
.relation-group > p { margin: 6px 0 7px; padding-top: 10px; border-top: 1px solid #eef3f6; color: #0870bc; font-size: 12px; font-weight: 800; }
.relation-group ul { display: grid; gap: 6px; margin: 0; padding: 0; list-style: none; }
.relation-group li { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 8px 10px; background: #f4f9fd; border-radius: 9px; cursor: pointer; transition: background .18s ease; }
.relation-group li:hover { background: #e3f0fa; }
.relation-group li:focus-visible { outline: 2px solid #0870bc; outline-offset: 1px; }
.relation-group strong { color: #22384a; font-size: 12.5px; }
.relation-group span { color: #0870bc; font-size: 11.5px; font-weight: 700; white-space: nowrap; }
.quick-links { display: grid; gap: 6px; margin-top: 4px; padding-top: 10px; border-top: 1px solid #eef3f6; }
.quick-links a { padding: 8px 11px; color: #0b5e63; background: #e6f4f1; border-radius: 9px; font-size: 12.5px; font-weight: 700; text-align: center; transition: background .18s ease, color .18s ease; }
.quick-links a:hover { background: #d3eae5; color: #084d52; }

@media (max-width: 1120px) { .graph-layout { grid-template-columns: 1fr; } .detail-panel { position: static; } }
@media (max-width: 760px) {
  .stats-strip { flex-wrap: wrap; gap: 14px; }
  .stats-strip div + div { padding-left: 14px; }
  .graph-canvas { height: 380px; }
  .graph-legend { top: 8px; left: 8px; gap: 10px; padding: 5px 9px; font-size: 11px; }
}
</style>
