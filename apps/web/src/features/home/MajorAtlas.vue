<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ArrowRight, ChevronLeft, ChevronRight, Pause, Play, RotateCcw, ZoomIn, ZoomOut } from '@lucide/vue'
import { useRouter } from 'vue-router'
import { pathTo } from '@/config/destinations'

type Course = { term: string; title: string; type: string; required: string; credits: string; image: string }

const router = useRouter()
const activeType = ref('全部')
const coursePage = ref(0)
const courseAtlas = ref<HTMLElement | null>(null)
const abilityAtlas = ref<HTMLElement | null>(null)
const courseVisible = ref(false)
const abilityVisible = ref(false)
let sectionObserver: IntersectionObserver | undefined
let spinObserver: IntersectionObserver | undefined
let revealTimer: number | undefined
const courseTypes = [
  { label: '全部', count: 12 },
  { label: '专业基础课', count: 4 },
  { label: '公共基础课', count: 1 },
  { label: '专业必修课', count: 5 },
  { label: '专业选修课', count: 2 }
]
const courses: Course[] = [
  { term: '第八学期', title: '油气田勘探', type: '专业基础课', required: '必学', credits: '2.5学分', image: 'https://images.unsplash.com/photo-1511497584788-876760111969?auto=format&fit=crop&w=960&q=85' },
  { term: '第四学期', title: '油矿地质学', type: '专业基础课', required: '必学', credits: '4学分', image: 'https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=960&q=85' },
  { term: '第三学期', title: '沉积岩石学', type: '专业基础课', required: '必学', credits: '3学分', image: 'https://images.unsplash.com/photo-1499346030926-9a72daac6c63?auto=format&fit=crop&w=960&q=85' },
  { term: '第五学期', title: '地球物理测井', type: '专业必修课', required: '必学', credits: '3学分', image: 'https://images.unsplash.com/photo-1518098268026-4e89f1a2cd8e?auto=format&fit=crop&w=960&q=85' },
  { term: '第二学期', title: '造岩矿物学', type: '专业基础课', required: '必学', credits: '3.5学分', image: 'https://images.unsplash.com/photo-1472396961693-142e6e269027?auto=format&fit=crop&w=960&q=85' },
  { term: '第六学期', title: '储层表征与建模', type: '专业必修课', required: '必学', credits: '2学分', image: 'https://images.unsplash.com/photo-1458966480358-a0ac42de0a7a?auto=format&fit=crop&w=960&q=85' },
  { term: '第七学期', title: '油气地震勘探实践', type: '专业选修课', required: '选学', credits: '2学分', image: 'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=960&q=85' },
  { term: '第一学期', title: '普通地质学', type: '专业基础课', required: '必学', credits: '3学分', image: 'https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=960&q=85' },
  { term: '第一学期', title: '地球科学概论', type: '公共基础课', required: '必学', credits: '2.5学分', image: 'https://images.unsplash.com/photo-1464278533981-50106e6176b1?auto=format&fit=crop&w=960&q=85' },
  { term: '第五学期', title: '石油地质学', type: '专业必修课', required: '必学', credits: '3学分', image: 'https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=960&q=85' },
  { term: '第六学期', title: '储层地质学', type: '专业必修课', required: '必学', credits: '2.5学分', image: 'https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=960&q=85' },
  { term: '第七学期', title: '地质综合实习', type: '专业选修课', required: '选学', credits: '1.5学分', image: 'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=960&q=85' }
]
const visibleCourses = computed(() => activeType.value === '全部' ? courses : courses.filter((course) => course.type === activeType.value))
const pageCount = computed(() => Math.max(1, Math.ceil(visibleCourses.value.length / 4)))
const displayedCourses = computed(() => visibleCourses.value.slice(coursePage.value * 4, coursePage.value * 4 + 4))

type SeedAbility = { name: string; kind: '知识' | '技能' | '素养' }
type MainAbility = { name: string; category: '实战能力' | '通用能力'; seeds: SeedAbility[] }

const activeAbilityCategory = ref('全部')
const hoveredAbility = ref('')
// The twelve main abilities follow the national engineering-education graduation
// requirements; the forty-nine seed abilities carry our own geology content.
const abilities: MainAbility[] = [
  { name: '工程知识', category: '实战能力', seeds: [
    { name: '地质基础理论', kind: '知识' }, { name: '沉积与层序', kind: '知识' }, { name: '矿物岩石鉴定', kind: '知识' },
    { name: '构造与盆地', kind: '知识' }, { name: '成藏地质理论', kind: '知识' }, { name: '物探原理', kind: '知识' },
    { name: '测井解释', kind: '技能' }, { name: '地震解释', kind: '技能' }, { name: '地质图件判读', kind: '技能' }
  ] },
  { name: '问题分析', category: '实战能力', seeds: [
    { name: '成因识别', kind: '知识' }, { name: '岩心与露头', kind: '技能' }, { name: '储层参数评价', kind: '技能' },
    { name: '测井异常识别', kind: '技能' }, { name: '勘探风险分析', kind: '技能' }
  ] },
  { name: '设计/开发解决方案', category: '实战能力', seeds: [
    { name: '方案设计规范', kind: '知识' }, { name: '井位与建模', kind: '技能' }, { name: '方案比选决策', kind: '素养' }
  ] },
  { name: '研究', category: '实战能力', seeds: [
    { name: '成藏机理研究', kind: '知识' }, { name: '实验设计分析', kind: '技能' }, { name: '文献调研综述', kind: '素养' }
  ] },
  { name: '使用现代工具', category: '实战能力', seeds: [
    { name: '地质建模软件', kind: '技能' }, { name: '地震解释软件', kind: '技能' }, { name: '数据处理编程', kind: '技能' },
    { name: '数值模拟AI', kind: '技能' }, { name: '测井解释平台', kind: '技能' }, { name: '智能工具素养', kind: '素养' }
  ] },
  { name: '工程与社会', category: '通用能力', seeds: [
    { name: '能源与社会', kind: '知识' }, { name: '影响评估', kind: '技能' }, { name: '社会责任沟通', kind: '素养' }
  ] },
  { name: '环境与可持续发展', category: '通用能力', seeds: [
    { name: '环境评价', kind: '知识' }, { name: '资源节约减排', kind: '知识' }, { name: '绿色勘探意识', kind: '素养' }
  ] },
  { name: '职业规范', category: '通用能力', seeds: [
    { name: '行业规范标准', kind: '知识' }, { name: '现场安全HSE', kind: '技能' }, { name: '工程伦理操守', kind: '素养' }
  ] },
  { name: '个人和团队', category: '通用能力', seeds: [
    { name: '多学科协同', kind: '技能' }, { name: '项目组织执行', kind: '技能' },
    { name: '跨学科协作', kind: '素养' }, { name: '责任担当', kind: '素养' }
  ] },
  { name: '沟通', category: '通用能力', seeds: [
    { name: '技术报告撰写', kind: '技能' }, { name: '成果汇报交流', kind: '技能' }, { name: '国际视野沟通', kind: '素养' }
  ] },
  { name: '项目管理', category: '通用能力', seeds: [
    { name: '进度与成本', kind: '技能' }, { name: '工程经济评价', kind: '知识' }, { name: '质量与合规', kind: '知识' }
  ] },
  { name: '终身学习', category: '通用能力', seeds: [
    { name: '技术前沿认知', kind: '知识' }, { name: '自主学习更新', kind: '素养' },
    { name: '新技术追踪', kind: '素养' }, { name: '职业规划', kind: '素养' }
  ] }
]
const SEED_COLORS: Record<SeedAbility['kind'], string> = { 知识: '#58a6e8', 技能: '#f0a13a', 素养: '#3fbb87' }
const MAIN_COLORS = { 实战能力: '#1478c2', 通用能力: '#12a4b8' } as const
const abilityCategories = computed(() => [
  { label: '全部', count: abilities.length },
  { label: '实战能力', count: abilities.filter((item) => item.category === '实战能力').length },
  { label: '通用能力', count: abilities.filter((item) => item.category === '通用能力').length }
])
const subAbilityCount = computed(() => abilities.reduce((total, item) => total + item.seeds.length, 0))
const seedKindCount = computed(() => {
  const tally: Record<string, number> = { 知识: 0, 技能: 0, 素养: 0 }
  for (const item of abilities) for (const seed of item.seeds) tally[seed.kind] += 1
  return tally
})
function setAbilityCategory(category: string) { activeAbilityCategory.value = category; hoveredAbility.value = ''; resetGraphView() }

// The board is a real 3D scene: the twelve main abilities ride one circular backbone ring inside a
// tilted disk that slowly turns around its vertical axis. Every frame the cores are rotated, tilted
// (as if seen from ~26° above) and perspective-projected, so the near side of the ring comes out
// larger and brighter than the far side, and paints over it. See LeafNode for why the seed
// abilities orbit their core in screen space instead of riding the disk.
type GraphLink = { id: string; group: string; x1: number; y1: number; x2: number; y2: number; width: number; opacity: number; z: number; ord: number }
type GraphNode = {
  key: string
  kind: 'main' | 'seed'
  group: string
  name: string
  x: number
  y: number
  w: number
  h: number
  r: number
  font: number
  fill: string
  opacity: number
  z: number
  ord: number
}
// A main ability in disk space: lx/lz lie in the disk plane and therefore spin.
type BoardNode = {
  key: string
  name: string
  lx: number
  lz: number
  w: number
  h: number
  font: number
  fill: string
  ord: number
  leaves: LeafNode[]
}
// A cluster's leaves orbit their core in SCREEN space, with a small depth offset that still lets
// them take part in the depth shading and the occlusion order. Carrying them around the disk with
// the rotation looks more rigid, but any orbit that lies in the disk plane collapses to a line as
// soon as the turn brings it into the depth direction — and then the labels stack on top of each
// other at that angle. A screen-plane orbit never collapses, so the cluster stays readable while
// the board itself keeps turning.
type LeafNode = {
  key: string
  group: string
  name: string
  dx: number
  dy: number
  dz: number
  font: number
  fill: string
  ord: number
}
type BoardFit = { scale: number; ox: number; oy: number; kMin: number; kMax: number }

const GRAPH_W = 2600
const GRAPH_H = 760
const GRAPH_PAD = 34
// The backbone ring must be CIRCULAR inside the disk. An elliptical ring looks tidy while it stands
// still, but its long axis swings into the depth direction as the disk turns, and the envelope that
// has to hold every rotation then ends up nearly square — which shrinks the whole board (and every
// label with it) to fit. A circular ring keeps the same projected footprint at every angle.
const RING_RADIUS = 1000
const RING_TILT = 0.23
const TILT_COS = Math.sqrt(1 - RING_TILT * RING_TILT)
const CAMERA = 4200
const SIZE_GAIN = 0.6
const SEED_ORBIT = 118
// The leaves' orbit is squashed vertically and pushed slightly into depth, so a cluster reads as a
// small tilted orbit around its core rather than a flat ring of dots.
const SEED_SQUASH = 0.5
const SEED_DEPTH = 0.3
const SEED_MIN_DIST = 64
const SPIN_SPEED = 0.05
const MAIN_FONT = 24
const SEED_FONT = 13
// Twelve pills on one circle used to leave a wide blank middle, and the board read as a hollow hoop.
// A hub now occupies that middle, and every main ability is joined to it by a spoke, so the ring
// reads as the rim of a wheel.
//
// The hub's size is measured, not guessed. At this tilt the free middle is a very flat band: sampled
// across a whole revolution the clear space is only ~200 units tall against ~1500 wide, because the
// clusters that pass the depth axis bring their labels to within ~100 units of the middle. The height
// also depends on where in that band the hub sits, and the best spot is NOT the disk's centre:
// perspective scales the near half of the ring up (k > 1) and so drops the ring's own screen envelope
// ~53 units below the board centre. Placing the hub on that envelope midline roughly doubles the
// usable height, which is what makes a hub this size possible at all.
// These numbers are the largest that clear every label at all 720 sampled rotation angles in each of
// the three category filters, with margin left over; the tightest case is 通用能力, whose seven
// abilities sit far enough apart that its clusters reach closer to the middle.
const HUB_HALF_W = 285
const HUB_HALF_H = 78
const HUB_FONT = 56

// A cluster's leaves orbit their core. This pass spreads them apart in screen space, keeps them off
// the core pill and pulls them back towards the orbit, so the core stays the middle of its cluster
// and no two labels collide at any rotation angle.
function relaxCluster(main: BoardNode, orbit: number) {
  const leaves = main.leaves
  const clearX = main.w / 2 + 22
  const clearY = main.h / 2 + 26
  // Depth shifts a leaf vertically by dz * RING_TILT, so the separation is measured there too.
  const gap = (a: LeafNode, b: LeafNode) => {
    const dx = b.dx - a.dx
    const dy = b.dy - a.dy + (b.dz - a.dz) * RING_TILT
    return Math.hypot(dx, dy) || 0.001
  }
  for (let step = 0; step < 120; step += 1) {
    const damping = 0.5 - step / 280
    for (let i = 0; i < leaves.length; i += 1) {
      for (let j = i + 1; j < leaves.length; j += 1) {
        const a = leaves[i]
        const b = leaves[j]
        const distance = gap(a, b)
        if (distance >= SEED_MIN_DIST) continue
        const push = ((SEED_MIN_DIST - distance) / distance) * damping
        const dx = b.dx - a.dx
        const dy = b.dy - a.dy + (b.dz - a.dz) * RING_TILT
        a.dx -= dx * push
        a.dy -= dy * push
        b.dx += dx * push
        b.dy += dy * push
      }
      // A leaf must also clear its own core pill, which is a plain rectangle on screen.
      const leaf = leaves[i]
      const lift = leaf.dy + leaf.dz * RING_TILT
      if (Math.abs(leaf.dx) < clearX && Math.abs(lift) < clearY) {
        leaf.dy += (lift < 0 ? -1 : 1) * (clearY - Math.abs(lift))
      }
    }
    for (const leaf of leaves) {
      const distance = Math.hypot(leaf.dx, leaf.dy) || 0.001
      const limit = orbit + 42
      if (distance <= limit) continue
      const pull = (distance - limit) / distance
      leaf.dx -= leaf.dx * pull
      leaf.dy -= leaf.dy * pull
    }
  }
}

// Spin a disk-plane point around the vertical axis of the board.
function spinDisk(lx: number, lz: number, spin: number) {
  const cos = Math.cos(spin)
  const sin = Math.sin(spin)
  return { rx: lx * cos + lz * sin, rz: -lx * sin + lz * cos }
}

// Tilt the disk towards the viewer, divide by depth, and fit the result into the viewBox.
// rx/rz are already-spun disk coordinates, ly is the height above the disk plane.
function projectPoint(rx: number, ly: number, rz: number, fit: BoardFit) {
  const tiltY = ly * TILT_COS + rz * RING_TILT
  const tiltZ = rz * TILT_COS - ly * RING_TILT
  const k = CAMERA / (CAMERA - tiltZ)
  const grew = 1 + (k - 1) * SIZE_GAIN
  return {
    x: rx * k * fit.scale + fit.ox,
    y: tiltY * k * fit.scale + fit.oy,
    depth: fit.kMax === fit.kMin ? 1 : clamp((grew - fit.kMin) / (fit.kMax - fit.kMin), 0, 1),
    grew,
    z: tiltZ
  }
}

// A leaf hangs off the already-spun core: its screen-plane offset is added to the core's spun
// coordinates, and its own height is what turns that offset into the requested screen y.
function projectLeaf(main: { rx: number; rz: number }, leaf: LeafNode, fit: BoardFit) {
  return projectPoint(main.rx + leaf.dx, leaf.dy / TILT_COS, main.rz + leaf.dz, fit)
}

// This block is spin-independent: the disk-plane layout, plus the constant fit that guarantees the
// spinning board always fills the card without clipping and without pulsing in and out of size.
const boardLayout = computed(() => {
  const mains = activeAbilityCategory.value === '全部' ? abilities : abilities.filter((item) => item.category === activeAbilityCategory.value)
  const total = mains.length
  const mainNodes: BoardNode[] = []

  mains.forEach((item, index) => {
    const angle = -Math.PI / 2 + (index / total) * Math.PI * 2 + Math.sin(index * 12.9898) * 0.055
    const wobble = 1 + Math.cos(index * 78.233) * 0.05
    const node: BoardNode = {
      key: item.name,
      name: item.name,
      lx: Math.cos(angle) * RING_RADIUS * wobble,
      lz: Math.sin(angle) * RING_RADIUS * wobble,
      w: item.name.length * MAIN_FONT + 30,
      h: 42,
      font: MAIN_FONT,
      fill: MAIN_COLORS[item.category],
      ord: index,
      leaves: []
    }
    // A long main name needs a wider orbit, otherwise its leaves would sit inside the pill.
    const orbit = Math.max(SEED_ORBIT, node.w / 2 + 46)
    item.seeds.forEach((seed, position) => {
      // The leaves sit on one screen-space ring around their core, squashed vertically and pushed
      // slightly into depth, so a cluster reads as a small tilted orbit: the core stays the middle
      // of its cluster, and the ring never collapses however the board turns.
      const seedAngle = (position / item.seeds.length) * Math.PI * 2 + index * 0.63
      const radius = orbit * (0.9 + 0.14 * Math.abs(Math.sin(position * 4.7 + index)))
      node.leaves.push({
        key: `${item.name}-${seed.name}`,
        group: item.name,
        name: seed.name,
        dx: Math.cos(seedAngle) * radius,
        dy: Math.sin(seedAngle) * radius * SEED_SQUASH,
        dz: Math.sin(seedAngle) * radius * SEED_DEPTH,
        font: SEED_FONT,
        fill: SEED_COLORS[seed.kind],
        ord: index
      })
    })
    relaxCluster(node, orbit)
    mainNodes.push(node)
  })

  // The fit is measured across a whole revolution, so the board keeps one constant scale while it
  // spins: it fills the card, never clips a label, and never breathes in and out of size.
  let minX = Infinity
  let maxX = -Infinity
  let minY = Infinity
  let maxY = -Infinity
  let kMin = Infinity
  let kMax = -Infinity
  // The ring's own vertical envelope, tracked separately from the labelling envelope above, because
  // the hub is centred on the ring as it appears, not on the disk. See HUB_HALF_W for why.
  let coreMinY = Infinity
  let coreMaxY = -Infinity
  const probe: BoardFit = { scale: 1, ox: 0, oy: 0, kMin: 0, kMax: 1 }
  for (let step = 0; step < 48; step += 1) {
    const spin = (step / 48) * Math.PI * 2
    for (const main of mainNodes) {
      const spun = spinDisk(main.lx, main.lz, spin)
      const core = projectPoint(spun.rx, 0, spun.rz, probe)
      coreMinY = Math.min(coreMinY, core.y)
      coreMaxY = Math.max(coreMaxY, core.y)
      minX = Math.min(minX, core.x - main.w / 2)
      maxX = Math.max(maxX, core.x + main.w / 2)
      minY = Math.min(minY, core.y - main.h / 2 - 8)
      maxY = Math.max(maxY, core.y + main.h / 2 + 10)
      kMin = Math.min(kMin, core.grew)
      kMax = Math.max(kMax, core.grew)
      for (const leaf of main.leaves) {
        const point = projectLeaf(spun, leaf, probe)
        const halfW = Math.max(14, leaf.name.length * leaf.font * 0.5)
        minX = Math.min(minX, point.x - halfW)
        maxX = Math.max(maxX, point.x + halfW)
        minY = Math.min(minY, point.y - 10)
        maxY = Math.max(maxY, point.y + leaf.font + 18)
        kMin = Math.min(kMin, point.grew)
        kMax = Math.max(kMax, point.grew)
      }
    }
  }
  const usableW = GRAPH_W - GRAPH_PAD * 2
  const usableH = GRAPH_H - GRAPH_PAD * 2
  const spanX = Math.max(1, maxX - minX)
  const spanY = Math.max(1, maxY - minY)
  const scale = Math.min(usableW / spanX, usableH / spanY)
  const fit: BoardFit = {
    scale,
    ox: GRAPH_PAD + (usableW - spanX * scale) / 2 - minX * scale,
    oy: GRAPH_PAD + (usableH - spanY * scale) / 2 - minY * scale,
    kMin,
    kMax
  }

  // The hub: one oversized pill on the midline of the ring's screen envelope. Its numbers are in the
  // same units as everything else on the board, so it scales with the depth-sized labels around it.
  const hub = {
    x: fit.ox,
    y: ((coreMinY + coreMaxY) / 2) * scale + fit.oy,
    halfW: HUB_HALF_W * scale,
    halfH: HUB_HALF_H * scale,
    font: HUB_FONT * scale,
    title: activeAbilityCategory.value === '全部' ? '专业能力体系' : activeAbilityCategory.value
  }

  return { mains: mainNodes, fit, hub }
})

// The disk turns by itself, slowly (a full turn in about two minutes). Any interaction — a wheel,
// a drag, hovering a main ability, or leaving the screen — hands control back to the reader.
const graphSpin = ref(0)
const graphSpinning = ref(true)
const abilityOnScreen = ref(false)
let spinFrame = 0
let spinClock = 0
let spinReduced = false

function spinTick(now: number) {
  spinFrame = window.requestAnimationFrame(spinTick)
  if (!spinClock) { spinClock = now; return }
  const delta = Math.min(now - spinClock, 80)
  spinClock = now
  if (!graphSpinning.value || spinReduced || hoveredAbility.value || graphPanning.value || !abilityOnScreen.value) return
  graphSpin.value = (graphSpin.value + (delta / 1000) * SPIN_SPEED) % (Math.PI * 2)
}

function toggleSpin() {
  graphSpinning.value = !graphSpinning.value
  spinClock = 0
}

// One pass of the 3D pipeline: spin the disk, tilt it, project it, then size and shade every label
// by its own depth. Nodes are finally sorted back-to-front, so the near side of the board paints
// over the far side — the cue that makes a flat projection read as a solid scene.
const abilityGraph = computed(() => {
  const board = boardLayout.value
  const spin = graphSpin.value
  const nodes: GraphNode[] = []
  const coreNodes = new Map<string, GraphNode>()
  const leafNodes = new Map<string, GraphNode>()
  // One spoke per main ability, from the hub out to the ability. They are drawn BEFORE the hub, so the
  // hub paints over their inner ends and they appear to start on its rim — which saves having to cut
  // each line at the rim by hand.
  const spokes: GraphLink[] = []

  for (const main of board.mains) {
    const spun = spinDisk(main.lx, main.lz, spin)
    const point = projectPoint(spun.rx, 0, spun.rz, board.fit)
    const grew = point.grew * board.fit.scale
    const core: GraphNode = {
      key: main.key,
      kind: 'main',
      group: main.name,
      name: main.name,
      x: point.x,
      y: point.y,
      w: main.w * grew,
      h: main.h * grew,
      r: 0,
      font: main.font * grew,
      fill: main.fill,
      // Nearer abilities are drawn brighter; the far side of the disk fades into the board.
      opacity: 0.46 + 0.54 * point.depth,
      z: point.z,
      ord: main.ord
    }
    nodes.push(core)
    coreNodes.set(main.key, core)
    const depth = core.opacity
    spokes.push({
      id: `spoke-${main.key}`,
      group: main.name,
      x1: board.hub.x,
      y1: board.hub.y,
      x2: point.x,
      y2: point.y,
      width: (0.8 + 1.4 * depth) * board.fit.scale,
      opacity: 0.12 + 0.34 * depth,
      z: point.z,
      ord: main.ord
    })

    for (const leaf of main.leaves) {
      const spot = projectLeaf(spun, leaf, board.fit)
      const leafGrew = spot.grew * board.fit.scale
      const node: GraphNode = {
        key: leaf.key,
        kind: 'seed',
        group: leaf.group,
        name: leaf.name,
        x: spot.x,
        y: spot.y,
        w: 0,
        h: 0,
        r: 6.6 * leafGrew,
        font: leaf.font * leafGrew,
        fill: leaf.fill,
        opacity: 0.5 + 0.5 * spot.depth,
        z: spot.z,
        ord: leaf.ord
      }
      nodes.push(node)
      leafNodes.set(leaf.key, node)
    }
  }

  const seedLinks: GraphLink[] = []
  let linkCount = 0
  for (const main of board.mains) {
    const from = coreNodes.get(main.key)
    if (!from) continue
    for (const leaf of main.leaves) {
      const to = leafNodes.get(leaf.key)
      if (!to) continue
      const depth = (from.opacity + to.opacity) / 2
      seedLinks.push({
        id: leaf.key,
        group: leaf.group,
        x1: from.x,
        y1: from.y,
        x2: to.x,
        y2: to.y,
        width: (0.6 + 1.2 * depth) * board.fit.scale,
        opacity: 0.15 + 0.45 * depth,
        z: (from.z + to.z) / 2,
        ord: linkCount % 20
      })
      linkCount += 1
    }
  }

  const backboneLinks: GraphLink[] = []
  const total = board.mains.length
  const brace = (id: string, aKey: string, bKey: string, ord: number) => {
    const from = coreNodes.get(aKey)
    const to = coreNodes.get(bKey)
    if (!from || !to) return
    const depth = (from.opacity + to.opacity) / 2
    backboneLinks.push({
      id,
      group: '',
      x1: from.x,
      y1: from.y,
      x2: to.x,
      y2: to.y,
      width: (0.7 + 1.4 * depth) * board.fit.scale,
      opacity: 0.16 + 0.5 * depth,
      z: (from.z + to.z) / 2,
      ord
    })
  }
  if (total > 1) {
    for (let i = 0; i < total; i += 1) {
      brace(`ring-${i}`, board.mains[i].key, board.mains[(i + 1) % total].key, i)
    }
  }

  // Painter's algorithm: the back of the disk is painted first.
  nodes.sort((a, b) => a.z - b.z)

  // The hub is spin-independent (a circle in the disk plane projects to the same ellipse at every
  // angle), so it is computed once by boardLayout and merely passed through here.
  return { width: GRAPH_W, height: GRAPH_H, nodes, seedLinks, backboneLinks, spokes, hub: board.hub }
})

// Zoom / pan, so the dense seed labels can actually be read instead of staying hair-thin.
const MIN_ZOOM = 1
const MAX_ZOOM = 4
const graphWrap = ref<HTMLElement | null>(null)
const graphZoom = ref(1)
const graphPanX = ref(0)
const graphPanY = ref(0)
const graphPanning = ref(false)
let panStart = { x: 0, y: 0, panX: 0, panY: 0 }
let dragged = false

const graphTransform = computed(() => `translate(${graphPanX.value}px, ${graphPanY.value}px) scale(${graphZoom.value})`)
const graphZoomLabel = computed(() => `${Math.round(graphZoom.value * 100)}%`)

function clamp(value: number, min: number, max: number) { return Math.min(Math.max(value, min), max) }

function clampGraphPan() {
  const box = graphWrap.value?.getBoundingClientRect()
  if (!box) return
  graphPanX.value = clamp(graphPanX.value, -box.width * (graphZoom.value - 1), 0)
  graphPanY.value = clamp(graphPanY.value, -box.height * (graphZoom.value - 1), 0)
}

function zoomGraphAt(nextZoom: number, px: number, py: number) {
  const next = clamp(nextZoom, MIN_ZOOM, MAX_ZOOM)
  const ratio = next / graphZoom.value
  graphPanX.value = px - ratio * (px - graphPanX.value)
  graphPanY.value = py - ratio * (py - graphPanY.value)
  graphZoom.value = next
  clampGraphPan()
}

function zoomGraphBy(step: number) {
  const box = graphWrap.value?.getBoundingClientRect()
  if (!box) return
  zoomGraphAt(graphZoom.value * (step > 0 ? 1.25 : 1 / 1.25), box.width / 2, box.height / 2)
}

function resetGraphView() {
  graphZoom.value = 1
  graphPanX.value = 0
  graphPanY.value = 0
}

function onGraphWheel(event: WheelEvent) {
  event.preventDefault()
  graphSpinning.value = false
  const box = graphWrap.value?.getBoundingClientRect()
  if (!box) return
  zoomGraphAt(graphZoom.value * (event.deltaY < 0 ? 1.12 : 1 / 1.12), event.clientX - box.left, event.clientY - box.top)
}

function onGraphPointerDown(event: PointerEvent) {
  graphSpinning.value = false
  if (graphZoom.value === 1) return
  graphPanning.value = true
  dragged = false
  panStart = { x: event.clientX, y: event.clientY, panX: graphPanX.value, panY: graphPanY.value }
  ;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId)
}

function onGraphPointerMove(event: PointerEvent) {
  if (!graphPanning.value) return
  const dx = event.clientX - panStart.x
  const dy = event.clientY - panStart.y
  if (Math.abs(dx) > 3 || Math.abs(dy) > 3) dragged = true
  const box = graphWrap.value?.getBoundingClientRect()
  if (!box) return
  graphPanX.value = clamp(panStart.panX + dx, -box.width * (graphZoom.value - 1), 0)
  graphPanY.value = clamp(panStart.panY + dy, -box.height * (graphZoom.value - 1), 0)
}

function onGraphPointerUp(event: PointerEvent) {
  graphPanning.value = false
  const target = event.currentTarget as HTMLElement
  if (target.hasPointerCapture(event.pointerId)) target.releasePointerCapture(event.pointerId)
}

// Hovering any node focuses its whole cluster (and parks the rotation, so the labels can be read).
function focusCluster(node: GraphNode) { hoveredAbility.value = node.group }
function blurCluster() { hoveredAbility.value = '' }
function clickCluster(node: GraphNode) { if (node.kind === 'main') openAbilityAtlasFromGraph() }

// A drag across a node must not count as navigating into the ability atlas.
function openAbilityAtlasFromGraph() {
  if (dragged) { dragged = false; return }
  openAbilityAtlas()
}

function setType(type: string) { activeType.value = type; coursePage.value = 0 }
function previousCourses() { coursePage.value = (coursePage.value - 1 + pageCount.value) % pageCount.value }
function nextCourses() { coursePage.value = (coursePage.value + 1) % pageCount.value }
function openResources() { void router.push({ path: pathTo('resources'), query: { category: 'courses' } }) }
function openAbilityAtlas() {
  void router.push(pathTo('ability-map'))
}

watch(pageCount, (count) => {
  if (coursePage.value >= count) coursePage.value = 0
})

onMounted(() => {
  sectionObserver = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue
      if (entry.target === courseAtlas.value) courseVisible.value = true
      if (entry.target === abilityAtlas.value) abilityVisible.value = true
      sectionObserver?.unobserve(entry.target)
    }
  }, { threshold: .12 })
  if (courseAtlas.value) sectionObserver.observe(courseAtlas.value)
  if (abilityAtlas.value) sectionObserver.observe(abilityAtlas.value)
  // The 3D board re-projects every node on every frame, so it is only allowed to run while it is
  // actually on screen — and this observer keeps reporting (it is never unobserved).
  spinObserver = new IntersectionObserver((entries) => {
    for (const entry of entries) abilityOnScreen.value = entry.isIntersecting
  }, { threshold: .04 })
  if (abilityAtlas.value) spinObserver.observe(abilityAtlas.value)
  // AOS-style sections must never remain invisible when a browser restores or
  // captures a long page without producing intermediate scroll events.
  revealTimer = window.setTimeout(() => {
    courseVisible.value = true
    abilityVisible.value = true
  }, 640)
  // The 3D disk rotates on its own, unless the reader asked for reduced motion.
  spinReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  if (spinReduced) graphSpinning.value = false
  spinFrame = window.requestAnimationFrame(spinTick)
})

onBeforeUnmount(() => {
  sectionObserver?.disconnect()
  spinObserver?.disconnect()
  if (revealTimer !== undefined) window.clearTimeout(revealTimer)
  if (spinFrame) window.cancelAnimationFrame(spinFrame)
})
</script>

<template>
  <section id="slide-course" ref="courseAtlas" :class="['atlas-page', 'deck-slide', 'course-atlas', { 'is-visible': courseVisible }]" aria-label="课程大图谱">
    <div class="atlas-shell">
      <header class="atlas-heading">
        <div class="atlas-title">
          <span class="atlas-ring" aria-hidden="true"></span>
          <h2>课程大图谱</h2>
          <p><b>AI</b> 当前课程家族共 <strong>12</strong> 门课程，其中 <strong>5</strong> 门已建设知识图谱</p>
        </div>
        <button class="atlas-explore" @click="openResources">去探索 <ArrowRight :size="17" /></button>
      </header>
      <div class="atlas-panel">
        <nav class="atlas-tabs" aria-label="课程分类">
          <button v-for="item in courseTypes" :key="item.label" :class="{ active: activeType === item.label }" @click="setType(item.label)">
            {{ item.label }} <b>{{ item.count }}</b>
          </button>
        </nav>
        <div class="course-wall">
          <button class="course-nav course-nav-prev" :disabled="pageCount === 1" aria-label="查看上一组课程" @click="previousCourses"><ChevronLeft :size="23" /></button>
          <article v-for="course in displayedCourses" :key="`${coursePage}-${course.title}`" class="course-card" tabindex="0" @click="openResources" @keydown.enter="openResources">
            <img :src="course.image" :alt="`${course.title}课程封面`" />
            <div class="course-tint"></div>
            <span class="smart-course">智慧课程</span>
            <div class="course-copy"><p>{{ course.term }}</p><h3>{{ course.title }}</h3></div>
            <footer><span>{{ course.type }}</span><span>{{ course.required }}</span><span>{{ course.credits }}</span></footer>
          </article>
          <button class="course-nav course-nav-next" :disabled="pageCount === 1" aria-label="查看下一组课程" @click="nextCourses"><ChevronRight :size="23" /></button>
        </div>
        <p class="course-page-status" :style="{ '--course-progress': `${((coursePage + 1) / pageCount) * 100}%` }" aria-live="polite">第 {{ coursePage + 1 }} / {{ pageCount }} 组课程</p>
      </div>
    </div>
  </section>

  <section id="slide-ability" ref="abilityAtlas" :class="['atlas-page', 'deck-slide', 'ability-atlas', { 'is-visible': abilityVisible }]" aria-label="能力图谱">
    <div class="ability-stage">
      <header class="atlas-heading ability-heading">
        <div class="atlas-title">
          <span class="atlas-ring" aria-hidden="true"></span>
          <h2>能力大图谱</h2>
          <p><b>AI</b> 以下为专业人才培养所需要的 <strong>{{ abilities.length }}</strong> 个主能力，<strong>{{ subAbilityCount }}</strong> 个子能力</p>
        </div>
        <button class="atlas-explore" @click="openAbilityAtlas">去探索 <ArrowRight :size="17" /></button>
      </header>
      <div class="atlas-panel ability-panel">
        <div class="ability-toolbar">
          <nav class="atlas-tabs ability-tabs" aria-label="能力分类">
            <button v-for="item in abilityCategories" :key="item.label" :class="{ active: activeAbilityCategory === item.label }" @click="setAbilityCategory(item.label)">
              {{ item.label }} <b>{{ item.count }}</b>
            </button>
          </nav>
          <div class="graph-tools">
            <button
              type="button"
              class="graph-spin"
              :aria-pressed="graphSpinning"
              :aria-label="graphSpinning ? '暂停三维旋转' : '继续三维旋转'"
              @click="toggleSpin"
            ><Pause v-if="graphSpinning" :size="14" /><Play v-else :size="14" /><span>{{ graphSpinning ? '旋转中' : '已暂停' }}</span></button>
            <div class="graph-zoom" role="group" aria-label="图谱缩放">
              <button type="button" :disabled="graphZoom <= MIN_ZOOM" aria-label="缩小图谱" @click="zoomGraphBy(-1)"><ZoomOut :size="15" /></button>
              <b aria-live="polite">{{ graphZoomLabel }}</b>
              <button type="button" :disabled="graphZoom >= MAX_ZOOM" aria-label="放大图谱" @click="zoomGraphBy(1)"><ZoomIn :size="15" /></button>
              <button type="button" :disabled="graphZoom === 1" aria-label="复位图谱" @click="resetGraphView"><RotateCcw :size="15" /></button>
            </div>
          </div>
        </div>
        <div
          ref="graphWrap"
          class="ability-graph-wrap"
          :class="{ 'is-panning': graphPanning, 'is-zoomed': graphZoom > 1 }"
          @wheel="onGraphWheel"
          @pointerdown="onGraphPointerDown"
          @pointermove="onGraphPointerMove"
          @pointerup="onGraphPointerUp"
          @pointercancel="onGraphPointerUp"
        >
          <svg class="ability-graph" :style="{ transform: graphTransform }" :viewBox="`0 0 ${abilityGraph.width} ${abilityGraph.height}`" preserveAspectRatio="xMidYMid meet" role="img" :aria-label="`专业能力三维图谱，共 ${abilities.length} 个主能力、${subAbilityCount} 个子能力，以能力体系枢纽为中心相互连通，形成一张自动旋转的三维网络，可用滚轮缩放、拖动平移`">
            <defs>
              <radialGradient id="ability-atlas-floor" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stop-color="#1478c2" stop-opacity=".1" />
                <stop offset="62%" stop-color="#1478c2" stop-opacity=".04" />
                <stop offset="100%" stop-color="#1478c2" stop-opacity="0" />
              </radialGradient>
              <radialGradient id="ability-atlas-hub" cx="50%" cy="44%" r="66%">
                <stop offset="0%" stop-color="#1478c2" stop-opacity=".21" />
                <stop offset="68%" stop-color="#1478c2" stop-opacity=".12" />
                <stop offset="100%" stop-color="#1478c2" stop-opacity=".07" />
              </radialGradient>
            </defs>
            <ellipse class="graph-bed" :cx="abilityGraph.width / 2" :cy="abilityGraph.height / 2" :rx="abilityGraph.width / 2 - 12" :ry="abilityGraph.height / 2 - 18" fill="url(#ability-atlas-floor)" />
            <g class="graph-spokes">
              <line v-for="link in abilityGraph.spokes" :key="link.id" class="graph-link spoke" :class="{ dim: hoveredAbility && hoveredAbility !== link.group }" :x1="link.x1" :y1="link.y1" :x2="link.x2" :y2="link.y2" :style="{ '--o': link.opacity, '--sw': link.width, '--d': `${link.ord * 18}ms` }" />
            </g>
            <g class="graph-hub">
              <rect
                :x="abilityGraph.hub.x - abilityGraph.hub.halfW"
                :y="abilityGraph.hub.y - abilityGraph.hub.halfH"
                :width="abilityGraph.hub.halfW * 2"
                :height="abilityGraph.hub.halfH * 2"
                :rx="abilityGraph.hub.halfH"
                fill="url(#ability-atlas-hub)"
              />
              <text :x="abilityGraph.hub.x" :y="abilityGraph.hub.y + abilityGraph.hub.font * 0.35" :font-size="abilityGraph.hub.font">{{ abilityGraph.hub.title }}</text>
            </g>
            <g class="graph-backbone">
              <line v-for="link in abilityGraph.backboneLinks" :key="link.id" class="graph-link backbone" :x1="link.x1" :y1="link.y1" :x2="link.x2" :y2="link.y2" :style="{ '--o': link.opacity, '--sw': link.width, '--d': `${link.ord * 16}ms` }" />
            </g>
            <g class="graph-links">
              <line v-for="link in abilityGraph.seedLinks" :key="link.id" class="graph-link" :class="{ dim: hoveredAbility && hoveredAbility !== link.group }" :x1="link.x1" :y1="link.y1" :x2="link.x2" :y2="link.y2" :style="{ '--o': link.opacity, '--sw': link.width, '--d': `${link.ord * 14}ms` }" />
            </g>
            <g
              v-for="node in abilityGraph.nodes"
              :key="node.key"
              :class="[node.kind === 'main' ? 'graph-main' : 'graph-seed', { dim: hoveredAbility && hoveredAbility !== node.group }]"
              :style="{ '--o': node.opacity, '--d': `${node.ord * 45}ms` }"
              :tabindex="node.kind === 'main' ? 0 : undefined"
              :role="node.kind === 'main' ? 'button' : undefined"
              :aria-label="node.kind === 'main' ? node.name : undefined"
              @mouseenter="focusCluster(node)"
              @mouseleave="blurCluster"
              @focus="focusCluster(node)"
              @blur="blurCluster"
              @click="clickCluster(node)"
              @keydown.enter="clickCluster(node)"
            >
              <template v-if="node.kind === 'main'">
                <rect :x="node.x - node.w / 2" :y="node.y - node.h / 2" :width="node.w" :height="node.h" :rx="node.h / 2" :fill="node.fill" />
                <text :x="node.x" :y="node.y + node.font * 0.35" text-anchor="middle" :font-size="node.font">{{ node.name }}</text>
              </template>
              <template v-else>
                <circle :cx="node.x" :cy="node.y" :r="node.r" :fill="node.fill" />
                <text :x="node.x" :y="node.y + node.r + node.font" text-anchor="middle" :font-size="node.font">{{ node.name }}</text>
              </template>
            </g>
          </svg>
        </div>
        <ul class="ability-legend">
          <li><i style="background: #1478c2"></i>实战能力 {{ abilityCategories[1].count }}</li>
          <li><i style="background: #12a4b8"></i>通用能力 {{ abilityCategories[2].count }}</li>
          <li><i style="background: #58a6e8"></i>知识 {{ seedKindCount['知识'] }}</li>
          <li><i style="background: #f0a13a"></i>技能 {{ seedKindCount['技能'] }}</li>
          <li><i style="background: #3fbb87"></i>素养 {{ seedKindCount['素养'] }}</li>
          <li class="legend-hint">中心枢纽辐射 · 自动旋转 · 滚轮缩放 · 拖动平移 · 悬停聚焦子能力</li>
        </ul>
      </div>
    </div>
  </section>
</template>

<style scoped>
.atlas-page { position: relative; padding: 76px 0; }.atlas-page .atlas-shell, .atlas-page .ability-stage { opacity: 0; transform: translateY(5.20833vw); transition: opacity 760ms ease, transform 760ms cubic-bezier(.2, .8, .2, 1); }.atlas-page.is-visible .atlas-shell, .atlas-page.is-visible .ability-stage { opacity: 1; transform: translateY(0); }.ability-atlas .ability-stage { transition-delay: 90ms; }
.course-atlas { background: #f4f6fc; }
.atlas-shell { width: min(87.5vw, 1680px); margin: 0 auto; padding: 46px 64px 66px; color: #fff; background: #063f7f; border-radius: 40px; box-shadow: 0 22px 54px rgba(7, 70, 131, .2); }
.atlas-heading { display: flex; align-items: center; justify-content: space-between; gap: 24px; }.atlas-title { display: flex; align-items: center; min-width: 0; gap: 14px; }.atlas-ring { flex: 0 0 auto; display: inline-block; width: 25px; height: 25px; border: 7px solid #fff; border-radius: 50%; box-shadow: inset 0 0 0 3px #063f7f; }h2 { margin: 0; color: inherit; font-size: 30px; line-height: 1; letter-spacing: 0; }.atlas-title p { display: inline-flex; align-items: center; gap: 5px; min-width: 0; margin: 0 0 0 15px; padding: 14px 22px 14px 11px; color: #fff; background: rgba(13, 84, 149, .94); border-radius: 32px; font-size: 16px; font-weight: 600; white-space: nowrap; }.atlas-title p b { display: grid; place-items: center; width: 37px; height: 37px; margin: -10px 2px -10px -18px; color: #fff; background: linear-gradient(135deg, #0875c2, #76d8ff); border: 4px solid #5f9dcc; border-radius: 50%; font-size: 16px; }.atlas-title p strong { font-size: 22px; }
.atlas-explore, .ability-heading button { display: inline-flex; align-items: center; gap: 8px; min-width: 126px; justify-content: center; height: 54px; color: #fff; background: #0b5d9e; border: 1px solid rgba(255,255,255,.24); border-radius: 13px; font-weight: 800; transition: transform .2s ease, background .2s ease; }.atlas-explore:hover, .ability-heading button:hover { background: #147bc1; transform: translateY(-2px); }.atlas-panel { margin-top: 40px; padding: 44px 48px 30px; background: #0b4b84; border-radius: 28px; }.atlas-tabs { display: flex; flex-wrap: wrap; gap: 16px; }.atlas-tabs button { min-width: 150px; padding: 13px 24px; color: #e2f3ff; background: #105e9f; border: 1px solid rgba(255,255,255,.14); border-radius: 28px; font-size: 16px; font-weight: 700; transition: background .2s ease, color .2s ease; }.atlas-tabs button b { margin-left: 13px; font-size: 20px; }.atlas-tabs button.active { color: #076eb9; background: #fff; }.course-wall { position: relative; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 24px; margin-top: 32px; }.course-card { position: relative; min-height: 343px; overflow: hidden; isolation: isolate; cursor: pointer; border: 1px solid rgba(255,255,255,.8); border-radius: 17px; outline: 0; transform: translateZ(0); animation: course-enter 360ms cubic-bezier(.2, .8, .2, 1) both; transition: transform .28s ease, box-shadow .28s ease; }.course-card:hover, .course-card:focus-visible { z-index: 1; box-shadow: 0 22px 35px rgba(0,0,0,.36); transform: translateY(-9px); }.course-card img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; transition: transform .55s ease; }.course-card:hover img { transform: scale(1.07); }.course-tint { position: absolute; inset: 0; z-index: -1; background: linear-gradient(180deg, rgba(0, 24, 51, .06) 30%, rgba(0, 44, 86, .86) 90%); }.smart-course { position: absolute; top: 24px; left: 23px; padding: 8px 12px; color: #087339; background: #f4fff7; border-left: 6px solid #d1df00; border-radius: 4px; font-size: 16px; font-weight: 800; }.course-copy { position: absolute; right: 25px; bottom: 80px; left: 25px; }.course-copy p { margin: 0 0 10px; color: #fff; font-size: 16px; font-weight: 800; }.course-copy h3 { display: -webkit-box; overflow: hidden; margin: 0; color: #fff; font-size: 25px; line-height: 1.15; -webkit-box-orient: vertical; -webkit-line-clamp: 2; }.course-card footer { position: absolute; right: 25px; bottom: 22px; left: 25px; display: flex; gap: 8px; overflow: hidden; }.course-card footer span { padding: 7px 12px; color: #fff; background: rgba(9, 69, 119, .8); border: 1px solid rgba(255,255,255,.3); border-radius: 18px; font-size: 13px; white-space: nowrap; }.course-nav { position: absolute; z-index: 2; top: 50%; display: grid; place-items: center; width: 38px; height: 54px; color: #fff; background: rgba(5, 58, 105, .7); border: 1px solid rgba(255,255,255,.35); opacity: 0; transform: translateY(-50%); transition: opacity 180ms ease, background 180ms ease; }.course-wall:hover .course-nav, .course-nav:focus-visible { opacity: 1; }.course-nav:hover { background: #0b76be; }.course-nav:disabled { cursor: default; opacity: .32; }.course-nav-prev { left: -19px; border-radius: 0 11px 11px 0; }.course-nav-next { right: -19px; border-radius: 11px 0 0 11px; }.course-page-status { margin: 20px 0 0; color: rgba(225, 245, 255, .74); font-size: 13px; text-align: center; }@keyframes course-enter { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
.ability-atlas { padding-top: 0; background: #f4f6fc; }.ability-stage { position: relative; overflow: hidden; width: min(87.5vw, 1680px); min-height: 455px; margin: 0 auto 28px; padding: 62px 64px; color: #fff; background: linear-gradient(124deg, #25315d, #123d78 54%, #096a9e); border-radius: 40px; }.ability-stage::before { content: ""; position: absolute; top: -160px; right: 8%; width: 520px; height: 520px; border: 1px solid rgba(231, 247, 255, .24); border-radius: 50%; box-shadow: 0 0 0 30px rgba(234, 247, 255, .05), 0 0 0 65px rgba(234, 247, 255, .04), 0 0 0 104px rgba(234, 247, 255, .03); }.ability-heading { position: relative; z-index: 1; display: flex; align-items: center; gap: 14px; }.ability-heading p { margin: 0 0 0 15px; color: rgba(255,255,255,.8); font-size: 16px; }.ability-heading button { margin-left: auto; background: rgba(22, 45, 88, .44); }
@media (max-width: 1060px) { .atlas-shell, .ability-stage { width: min(94vw, 1680px); padding: 42px 34px; }.atlas-heading { align-items: flex-start; }.atlas-title { flex-wrap: wrap; }.atlas-title p { margin: 0; }.atlas-panel { padding: 30px; }.course-wall { grid-template-columns: repeat(3, minmax(0, 1fr)); }.course-card { min-height: 310px; } }
@media (max-width: 720px) { .atlas-page { padding: 34px 0; }.atlas-page .atlas-shell, .atlas-page .ability-stage { transform: translateY(52px); }.atlas-shell, .ability-stage { width: calc(100% - 24px); padding: 29px 18px; border-radius: 23px; }/* The deck-framing block in styles.css uses deep selectors on purpose (to outrank this scoped block), but it also carries 60px of side padding — which would spend a third of a phone's width on chrome and leave the graphs unreadably small. Restating the mobile padding behind the same ancestor chain wins it back: the scoped attribute selector adds one more class, so this lands at (0,5,0) against their (0,4,0). */
.deck > .deck-slide.atlas-page .atlas-shell,
.deck > .deck-slide.atlas-page .ability-stage { padding: 29px 18px; }.atlas-heading { gap: 14px; }.atlas-title { gap: 9px; }.atlas-ring { width: 20px; height: 20px; border-width: 5px; } h2 { font-size: 25px; }.atlas-title p { width: 100%; padding: 9px 14px; border-radius: 19px; font-size: 11px; white-space: normal; }.atlas-title p b { width: 28px; height: 28px; margin: -4px 2px -4px -10px; border-width: 2px; font-size: 12px; }.atlas-title p strong { font-size: 15px; }.atlas-explore { min-width: 40px; width: 40px; height: 40px; padding: 0; border-radius: 10px; font-size: 0; }.atlas-explore svg { width: 18px; }.atlas-panel { margin-top: 27px; padding: 20px 14px; border-radius: 18px; }.atlas-tabs { flex-wrap: nowrap; gap: 8px; overflow-x: auto; padding-bottom: 2px; }.atlas-tabs button { min-width: auto; padding: 9px 12px; font-size: 12px; white-space: nowrap; }.atlas-tabs button b { margin-left: 6px; font-size: 14px; }.course-wall { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 11px; margin-top: 21px; }.course-nav { top: auto; bottom: -52px; opacity: 1; transform: none; }.course-nav-prev { left: calc(50% - 46px); border-radius: 8px; }.course-nav-next { right: calc(50% - 46px); border-radius: 8px; }.course-page-status { margin-top: 70px; font-size: 12px; }.course-card { min-height: 245px; border-radius: 11px; }.smart-course { top: 13px; left: 12px; padding: 5px 7px; border-left-width: 4px; font-size: 11px; }.course-copy { right: 13px; bottom: 56px; left: 13px; }.course-copy p { margin-bottom: 6px; font-size: 12px; }.course-copy h3 { font-size: 17px; }.course-card footer { right: 10px; bottom: 12px; left: 10px; gap: 4px; }.course-card footer span { padding: 4px 7px; font-size: 9px; }.ability-stage { min-height: auto; }.ability-heading { flex-wrap: wrap; }.ability-heading p { width: 100%; margin: 0; font-size: 12px; }.ability-heading button { min-width: 100px; height: 40px; margin: 12px 0 0; font-size: 13px; } }




/* Match the reference page's contrast change between the course and ability atlases. */
.course-atlas { background: #f5f6fb; }
.atlas-shell { background: #06294d; box-shadow: none; }
.atlas-title p { background: #2a5f8f; }
.atlas-title p b { background: linear-gradient(135deg, #1272c4, #67d4f5); border-color: #4f86b3; }
.atlas-explore { background: #1c5a92; border-color: rgba(255,255,255,.22); }
.atlas-explore:hover { background: #2672b4; }
.atlas-panel { background: #0b3a63; }
.atlas-tabs button { color: #d7e9f8; background: #1b5c93; border-color: rgba(255,255,255,.12); }
.atlas-tabs button.active { color: #076eb9; background: #fff; }
.course-card { border-color: rgba(255,255,255,.82); }
.course-card footer span { background: rgba(9, 69, 119, .78); }
.course-wall { margin-bottom: 58px; }
.course-nav { top: auto; bottom: -58px; width: 42px; height: 42px; background: rgba(9, 58, 105, .78); border-radius: 50%; opacity: 1; transform: none; }
.course-nav-prev { right: 58px; left: auto; }
.course-nav-next { right: 0; }
.course-nav:hover { background: #0b76be; }
.course-page-status { position: relative; height: 3px; margin: 0 84px 0 0; overflow: hidden; color: transparent; background: rgba(255,255,255,.24); border-radius: 4px; }
.course-page-status::before { content: ""; position: absolute; top: 0; bottom: 0; left: 0; width: var(--course-progress, 17%); background: #46e6e9; border-radius: inherit; transition: width 280ms ease; }

.ability-atlas { background: #f5f6fb; }
.ability-stage { color: #1e2030; background: #fff; box-shadow: 0 16px 44px rgba(20, 60, 95, .07); }
.ability-stage::before { border-color: rgba(30, 130, 200, .12); box-shadow: 0 0 0 30px rgba(30, 130, 200, .035), 0 0 0 65px rgba(30, 130, 200, .026), 0 0 0 104px rgba(30, 130, 200, .018); }
.ability-heading p { color: #5c7f95; }
.ability-heading button { color: #0b6cb8; background: #e9f4fc; border-color: #cfe6f8; }
.ability-heading button:hover { color: #095a9c; background: #d9ecfa; }

.ability-heading p { display: inline-flex; align-items: center; gap: 8px; min-height: 46px; padding: 7px 18px 7px 10px; background: #fff; border-radius: 24px; }.ability-heading p b { display: grid; place-items: center; width: 30px; height: 30px; margin-left: -17px; color: #fff; background: linear-gradient(135deg, #1272c4, #67d4f5); border: 3px solid #d9ecfa; border-radius: 50%; font-size: 13px; }

@media (max-width: 720px) { .course-wall { margin-bottom: 54px; }.course-nav { bottom: -50px; }.course-nav-prev { left: calc(50% - 46px); }.course-nav-next { right: calc(50% - 46px); }.course-page-status { display: none; } }
@media (max-width: 720px) {
  .atlas-heading { position: relative; display: block; }
  .atlas-title { width: 100%; padding-right: 52px; }
  .atlas-title p { width: 100%; min-height: 42px; padding-right: 12px; }
  .atlas-explore { position: absolute; top: 0; right: 0; }
}

/* Ability atlas keeps the reference layout: AI pill heading, category tabs, ability wall. */
.ability-heading .atlas-ring { border-color: #1272c4; box-shadow: inset 0 0 0 3px #fff; }
.ability-heading .atlas-title p { color: #2f516b; background: #eef6fc; box-shadow: none; }
.ability-panel { position: relative; z-index: 1; margin-top: 32px; padding: 34px 32px 28px; background: #f3f8fc; border: 1px solid #dfeaf2; border-radius: 26px; }
.ability-tabs { margin-bottom: 25px; }
.ability-tabs button { min-width: 138px; color: #4a6b82; background: #fff; border-color: #d8e6f0; }
.ability-tabs button.active { color: #0b6cb8; background: #e9f4fc; border-color: #c8e2f6; }
.ability-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 18px; margin-bottom: 16px; }
.ability-toolbar .ability-tabs { margin-bottom: 0; }
.ability-toolbar .graph-zoom { display: inline-flex; align-items: center; gap: 2px; padding: 3px; background: #fff; border: 1px solid #d8e6f0; border-radius: 13px; }
.ability-toolbar .graph-zoom button { display: grid; place-items: center; width: 30px; height: 30px; padding: 0; color: #4a6b82; background: transparent; border: 0; border-radius: 9px; cursor: pointer; transition: color .18s ease, background .18s ease; }
.ability-toolbar .graph-zoom button:hover:not(:disabled) { color: #0b6cb8; background: #e9f4fc; }
.ability-toolbar .graph-zoom button:disabled { color: #b5cbda; cursor: default; }
.ability-toolbar .graph-zoom b { min-width: 46px; color: #4a6b82; font-size: 12px; font-weight: 700; text-align: center; }
.ability-toolbar .graph-tools { display: inline-flex; align-items: center; gap: 8px; }
.ability-toolbar .graph-spin { display: inline-flex; align-items: center; gap: 6px; height: 36px; padding: 0 13px; color: #0b6cb8; background: #fff; border: 1px solid #d8e6f0; border-radius: 13px; font-size: 12px; font-weight: 700; cursor: pointer; transition: color .18s ease, background .18s ease; }
.ability-toolbar .graph-spin:hover { background: #e9f4fc; border-color: #c8e2f6; }
.ability-toolbar .graph-spin[aria-pressed="false"] { color: #8a8ca3; }
/* The board is a pan/zoom viewport: the graph keeps its natural wide aspect and is scaled up on
   demand, instead of being shrunk to fit the card (which made every label unreadable). */
.ability-graph-wrap { position: relative; overflow: hidden; cursor: default; user-select: none; touch-action: none; }
.ability-graph-wrap.is-zoomed { cursor: grab; }
.ability-graph-wrap.is-panning { cursor: grabbing; }
.ability-graph { position: absolute; inset: 0; display: block; width: 100%; height: 100%; transform-origin: 0 0; }
.ability-graph-wrap.is-zoomed .ability-graph { will-change: transform; }
/* The floor is a gradient ellipse, so the disk reads as a plane seen from above at an angle.
   Depth in this board is carried by size, brightness and paint order, all set per frame. */
.graph-bed { pointer-events: none; }
/* The hub carries the board's title, so the middle of the ring reads as a hub rather than as a hole.
   It sits BETWEEN the spokes and the ring links in the paint order: the spokes are drawn first and
   vanish under it, which is what makes them look like they start on its rim. No font-size here — the
   per-frame depth-scaled size comes in as an attribute, and CSS would win over it. */
.graph-hub { pointer-events: none; }
.graph-hub rect { stroke: rgba(106, 90, 224, .32); stroke-width: 1; }
.graph-hub text { fill: #4b3fb4; font-weight: 700; letter-spacing: .08em; text-anchor: middle; }
.graph-link.spoke { stroke: rgba(106, 90, 224, .48); }
.graph-link { stroke: rgba(106, 90, 224, .62); stroke-width: var(--sw, 1.2); stroke-opacity: var(--o, .4); animation: link-in 640ms ease var(--d, 0ms) both; transition: stroke-opacity .26s ease; }
.graph-link.dim { stroke-opacity: .07; }
.graph-link.backbone { stroke: rgba(106, 90, 224, .78); }
.graph-main, .graph-seed { transform-box: fill-box; transform-origin: center; animation: node-in 520ms cubic-bezier(.2, .8, .2, 1) var(--d, 0ms) both; opacity: var(--o, 1); }
.graph-main.dim, .graph-seed.dim { opacity: .12; }
.graph-main { cursor: pointer; outline: 0; }
.graph-main rect { transition: filter .24s ease; }
.graph-main:hover rect, .graph-main:focus-visible rect { filter: brightness(1.1) saturate(1.15); }
/* No font-size here on purpose: the per-frame depth-scaled size is set as an attribute, and CSS
   would otherwise override it. */
.graph-main text { fill: #fff; font-weight: 700; pointer-events: none; }
.graph-seed text { fill: #6f7186; font-weight: 600; pointer-events: none; }
@keyframes node-in { from { transform: scale(.55); } to { transform: scale(1); } }
@keyframes link-in { from { opacity: 0; } to { opacity: 1; } }
.ability-legend { display: flex; flex-wrap: wrap; align-items: center; gap: 10px 20px; margin: 16px 0 0; padding: 15px 0 0; list-style: none; border-top: 1px dashed #e6e6f2; color: #74768b; font-size: 13px; font-weight: 700; }
.ability-legend i { display: inline-block; width: 11px; height: 11px; margin-right: 7px; border-radius: 50%; vertical-align: -1px; }
.ability-legend .legend-hint { margin-left: auto; color: #9a9cb0; font-weight: 600; }
@media (max-width: 1060px) { .ability-legend .legend-hint { display: none; } }
@media (max-width: 720px) { .graph-seed text { display: none; }.ability-legend { gap: 8px 14px; font-size: 12px; } }
/* Phone: the toolbar held the tab strip and the graph controls on one line, and only the strip was
   allowed to shrink — its `overflow-x: auto` cancels the automatic minimum size, so the browser took
   the whole deficit out of the tabs and measured them 0px wide at 360px, i.e. the ability categories
   were invisible. The controls' own min-content width already exceeds the panel at that size, so the
   row cannot hold both: wrap, give the strip its own full-width line and drop the controls below it,
   right-aligned. The 138px per-button floor is a desktop affordance (even pill widths everywhere);
   on a phone it only pads the strip to 430px of content inside a 231px row, so the buttons size to
   their text exactly as the course strip already does. */
@media (max-width: 720px) {
  .ability-toolbar { flex-wrap: wrap; gap: 10px; }
  /* Wrapping is only the backstop; the real fix is that nothing may shrink. The controls used to be
     squeezed to fit one row, which crushed the spin button's label to a 19px box at 320px — a box
     narrower than its own text. `flex: 0 0 auto` plus `flex-end` means the row either fits as is or
     drops its second control to a right-aligned line, never compresses it. */
  .ability-toolbar .graph-tools { flex-wrap: wrap; justify-content: flex-end; margin-left: auto; }
  .ability-toolbar .graph-tools > * { flex: 0 0 auto; }
  /* The play/pause icon already carries the spin state (aria-label carries it for screen readers),
     and the word is what tipped the controls over the row: 242px of controls in a 231px row at 360px. */
  .ability-toolbar .graph-spin span { display: none; }
  .ability-toolbar .ability-tabs button { min-width: auto; }
}
</style>
