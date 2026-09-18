<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ExternalLink, Search, SlidersHorizontal, UsersRound } from '@lucide/vue'
import * as THREE from 'three'
import { loadOfficialTeacherDirectory, mentors, mentorSourcePages, officialTopLevelUnits, type Mentor, type MentorSchool } from '@/config/mentorGraph'

type Scope = '全部单位' | MentorSchool
type GraphNode = { id: string; name: string; kind: 'teacher' | 'unit' | 'direction' | 'college' | 'university'; school?: MentorSchool; mentor?: Mentor; x?: number; y?: number }
type CampusDepartment = { name: string; teachers: number }
type CampusCollege = { school: MentorSchool; departments: CampusDepartment[] }

const threeTarget = ref<HTMLDivElement | null>(null)
const scope = ref<Scope>('全部单位')
const selectedUnit = ref<string>()
const search = ref('')
const selected = ref<Mentor>(mentors[0])
const directoryMentors = ref<Mentor[]>(mentors.filter((mentor) => mentor.school === '地球物理学院'))
const sourceStatus = ref<'geophysics' | 'ready' | 'fallback'>('geophysics')
let threeFrame: number | undefined
let threeResizeObserver: ResizeObserver | undefined

type MentorGraph3D = {
  renderer: THREE.WebGLRenderer
  scene: THREE.Scene
  camera: THREE.PerspectiveCamera
  root: THREE.Group
  raycaster: THREE.Raycaster
  pointer: THREE.Vector2
  nodes: THREE.Object3D[]
  effects: Array<{ sprite: THREE.Sprite; label?: THREE.Sprite; labelBaseScale?: THREE.Vector3; baseScale: number; phase: number }>
  lines: Array<{ material: THREE.LineBasicMaterial; baseOpacity: number; phase: number }>
  hovered?: THREE.Sprite
  cameraDistance: number
  rotationOffset: number
  pointerState?: { x: number; y: number; rotationOffset: number; pitch: number; moved: boolean }
  pitch: number
  paused: boolean
  abortController: AbortController
}

let mentorGraph3D: MentorGraph3D | undefined

const schools = computed<Scope[]>(() => [
  '全部单位',
  ...[...new Set(directoryMentors.value.map((mentor) => mentor.school))].sort((left, right) => left.localeCompare(right, 'zh-Hans-CN'))
])
const campusUnits = computed<MentorSchool[]>(() => [...new Set(Object.values(officialTopLevelUnits))])
const campusHierarchy = computed<CampusCollege[]>(() => campusUnits.value.map((school, index) => {
  const unitCounts = new Map<string, number>()
  directoryMentors.value
    .filter((mentor) => mentor.school === school && mentor.unit && mentor.unit !== school)
    .forEach((mentor) => unitCounts.set(mentor.unit!, (unitCounts.get(mentor.unit!) ?? 0) + 1))
  const departments = [...unitCounts.entries()]
    .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0], 'zh-Hans-CN'))
    .map(([name, teachers]) => ({ name, teachers }))
  return { school, departments }
}))
const campusDepartmentCount = computed(() => campusHierarchy.value.reduce((total, school) => total + school.departments.length, 0))
const filteredMentors = computed(() => {
  const keyword = search.value.trim().toLowerCase()
  return directoryMentors.value.filter((mentor) => {
    const matchedSchool = scope.value === '全部单位' || mentor.school === scope.value
    const matchedUnit = !selectedUnit.value || mentor.unit === selectedUnit.value
    const matchedKeyword = !keyword || [mentor.name, mentor.school, mentor.unit, mentor.title, mentor.summary, ...mentor.directions, ...(mentor.courses ?? []), ...(mentor.mentorTypes ?? []), ...(mentor.subjects ?? [])]
      .join(' ').toLowerCase().includes(keyword)
    return matchedSchool && matchedUnit && matchedKeyword
  })
})
const relationshipMentors = computed(() => filteredMentors.value.filter((mentor) => mentor.directions.length > 0))
const directions = computed(() => [...new Set(relationshipMentors.value.flatMap((mentor) => mentor.directions))])
const mentorCount = computed(() => filteredMentors.value.filter((mentor) => mentor.mentorTypes?.length).length)

function selectMentor(mentor: Mentor) {
  selected.value = mentor
}

function resetFilters() {
  scope.value = '全部单位'
  selectedUnit.value = undefined
  search.value = ''
}

function clearUnitScope() {
  selectedUnit.value = undefined
}

function openCampusSchool(school: MentorSchool) {
  selectedUnit.value = undefined
  scope.value = school
}

function openCampusDepartment(school: MentorSchool, unit: string) {
  selectedUnit.value = unit
  scope.value = school
}

function graphData() {
  if (scope.value === '全部单位') {
    const center: GraphNode = { id: 'university', name: '中国石油大学（北京）', kind: 'university', x: 0, y: 0 }
    const nodes: GraphNode[] = [center]
    const links: Array<{ source: string; target: string }> = []
    campusHierarchy.value.forEach((campus, index) => {
      const angle = (Math.PI * 2 * index) / campusHierarchy.value.length - Math.PI / 2
      const college: GraphNode = {
        id: `college:${campus.school}`,
        name: campus.school,
        kind: 'college',
        school: campus.school,
        x: Math.cos(angle) * 740,
        y: Math.sin(angle) * 410
      }
      nodes.push(college)
      links.push({ source: center.id, target: college.id })
      campus.departments.forEach((department, departmentIndex) => {
        const spread = (departmentIndex - (campus.departments.length - 1) / 2) * .22
        const departmentAngle = angle + spread
        const distance = 1160 + (departmentIndex % 3) * 105
        const departmentNode: GraphNode = {
          id: `unit:${campus.school}:${department.name}`,
          name: department.name,
          kind: 'unit',
          school: campus.school,
          x: Math.cos(departmentAngle) * distance,
          y: Math.sin(departmentAngle) * (650 + (departmentIndex % 2) * 70)
        }
        nodes.push(departmentNode)
        links.push({ source: college.id, target: departmentNode.id })
      })
    })
    return { nodes, links }
  }

  const collegeNode: GraphNode = { id: `college:${scope.value}`, name: scope.value, kind: 'college', school: scope.value, x: 0, y: 0 }
  const unitNodes = new Map<string, GraphNode>()
  const directionNodes = new Map<string, GraphNode>()
  const nodes: GraphNode[] = filteredMentors.value.map((mentor) => ({ id: mentor.id, name: mentor.name, kind: 'teacher', school: mentor.school, mentor }))
  const links: Array<{ source: string; target: string }> = []
  const includeDirections = filteredMentors.value.length <= 24
  filteredMentors.value.forEach((mentor) => {
    const officialUnit = mentor.unit ?? mentor.school
    const unitId = `unit:${officialUnit}`
    const belongsToCollege = officialUnit === mentor.school || officialUnit === scope.value
    if (belongsToCollege) {
      links.push({ source: mentor.id, target: collegeNode.id })
    } else {
      if (!unitNodes.has(unitId)) {
        unitNodes.set(unitId, { id: unitId, name: officialUnit, kind: 'unit', school: mentor.school })
        links.push({ source: unitId, target: collegeNode.id })
      }
      links.push({ source: mentor.id, target: unitId })
    }
    if (includeDirections) mentor.directions.forEach((direction) => {
      const directionId = `direction:${direction}`
      if (!directionNodes.has(directionId)) directionNodes.set(directionId, { id: directionId, name: direction, kind: 'direction', school: mentor.school })
      links.push({ source: mentor.id, target: directionId })
    })
  })
  const unitList = [...unitNodes.values()]
  const directionList = [...directionNodes.values()]
  const unitColumns = Math.max(1, Math.ceil(Math.sqrt(unitList.length)))
  const unitRows = Math.max(1, Math.ceil(unitList.length / unitColumns))
  const unitSpacing = 960
  const centerX = ((unitColumns - 1) * unitSpacing) / 2
  const centerY = ((unitRows - 1) * unitSpacing) / 2
  const unitPositions = new Map<string, { x: number; y: number }>()

  unitList.forEach((unit, index) => {
    const x = (index % unitColumns) * unitSpacing - centerX
    const y = Math.floor(index / unitColumns) * unitSpacing - centerY
    unit.x = x
    unit.y = y
    unitPositions.set(unit.name, { x, y })
  })

  const teachersByUnit = new Map<string, GraphNode[]>()
  nodes.forEach((teacher) => {
    const unit = teacher.mentor?.unit ?? teacher.school ?? ''
    const group = teachersByUnit.get(unit) ?? []
    group.push(teacher)
    teachersByUnit.set(unit, group)
  })
  teachersByUnit.forEach((teachers, school) => {
    const center = unitPositions.get(school) ?? { x: 0, y: 0 }
    const radius = 145 + Math.sqrt(teachers.length) * 34
    teachers.forEach((teacher, index) => {
      const angle = (Math.PI * 2 * index) / teachers.length - Math.PI / 2
      teacher.x = center.x + Math.cos(angle) * radius
      teacher.y = center.y + Math.sin(angle) * radius
    })
  })

  directionList.forEach((node, index) => {
    const relatedTeachers = nodes.filter((teacher) => teacher.mentor?.directions.includes(node.name))
    const average = relatedTeachers.reduce((position, teacher) => ({ x: position.x + (teacher.x ?? 0), y: position.y + (teacher.y ?? 0) }), { x: 0, y: 0 })
    const center = relatedTeachers.length ? { x: average.x / relatedTeachers.length, y: average.y / relatedTeachers.length } : { x: 0, y: 0 }
    const angle = (Math.PI * 2 * index) / Math.max(1, directionList.length) - Math.PI / 2
    node.x = center.x + Math.cos(angle) * 190
    node.y = center.y + Math.sin(angle) * 190
  })
  return { nodes: [collegeNode, ...nodes, ...unitList, ...directionList], links }
}

const schoolColors = ['#2563eb', '#0f766e', '#c2410c', '#7c3aed', '#be123c', '#0369a1', '#4d7c0f', '#a16207', '#0e7490', '#9333ea', '#b45309', '#15803d']
const directionColors = ['#db2777', '#7c3aed', '#0891b2', '#ea580c', '#65a30d', '#c026d3', '#0284c7', '#ca8a04', '#059669', '#e11d48']

function colorIndex(value: string, palette: string[]) {
  return [...value].reduce((hash, character) => ((hash * 31) + character.charCodeAt(0)) >>> 0, 17) % palette.length
}

function tint(color: string, amount: number) {
  const value = new THREE.Color(color)
  value.lerp(new THREE.Color('#ffffff'), amount)
  return `#${value.getHexString()}`
}

function threeNodeColor(node: GraphNode) {
  if (node.kind === 'university') return '#0f3f67'
  if (node.kind === 'college') return schoolColors[colorIndex(node.school ?? node.name, schoolColors)]
  if (node.kind === 'unit') return tint(schoolColors[colorIndex(node.school ?? node.name, schoolColors)], .16)
  const direction = node.kind === 'direction' ? node.name : node.mentor?.directions[0]
  if (direction) return directionColors[colorIndex(direction, directionColors)]
  return '#78909c'
}

function textSprite(text: string, color: string, fontSize: number, prominent = false) {
  const canvas = document.createElement('canvas')
  const context = canvas.getContext('2d')
  if (!context) return new THREE.Sprite()
  context.font = `700 ${fontSize}px Microsoft YaHei, PingFang SC, sans-serif`
  const padding = prominent ? 20 : 14
  canvas.width = Math.ceil(context.measureText(text).width + padding * 2)
  canvas.height = fontSize + padding * 2
  context.font = `700 ${fontSize}px Microsoft YaHei, PingFang SC, sans-serif`
  context.fillStyle = prominent ? 'rgba(10, 65, 99, .92)' : 'rgba(255, 255, 255, .97)'
  context.beginPath()
  context.roundRect(0, 0, canvas.width, canvas.height, canvas.height / 2)
  context.fill()
  if (!prominent) {
    context.lineWidth = 1
    context.strokeStyle = 'rgba(113, 162, 187, .72)'
    context.stroke()
  }
  context.fillStyle = color
  context.textAlign = 'center'
  context.textBaseline = 'middle'
  context.fillText(text, canvas.width / 2, canvas.height / 2)
  const texture = new THREE.CanvasTexture(canvas)
  texture.colorSpace = THREE.SRGBColorSpace
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, transparent: true, depthWrite: false }))
  sprite.scale.set(canvas.width / 110, canvas.height / 110, 1)
  return sprite
}

function nodeComponentSprite(color: string, kind: GraphNode['kind']) {
  const canvas = document.createElement('canvas')
  canvas.width = 240
  canvas.height = 240
  const context = canvas.getContext('2d')
  if (!context) return new THREE.Sprite()
  const center = canvas.width / 2
  const colorValue = new THREE.Color(color)
  const red = Math.round(colorValue.r * 255)
  const green = Math.round(colorValue.g * 255)
  const blue = Math.round(colorValue.b * 255)
  const glow = context.createRadialGradient(center, center, 16, center, center, 82)
  glow.addColorStop(0, `rgba(${red}, ${green}, ${blue}, .78)`)
  glow.addColorStop(.36, `rgba(${red}, ${green}, ${blue}, .36)`)
  glow.addColorStop(.68, `rgba(${red}, ${green}, ${blue}, .08)`)
  glow.addColorStop(1, `rgba(${red}, ${green}, ${blue}, 0)`)
  context.fillStyle = glow
  context.fillRect(0, 0, canvas.width, canvas.height)
  const radius = kind === 'university' ? 65 : kind === 'college' ? 53 : kind === 'unit' ? 40 : kind === 'teacher' ? 25 : 22
  context.beginPath()
  context.arc(center, center, radius, 0, Math.PI * 2)
  context.fillStyle = `rgba(${red}, ${green}, ${blue}, .38)`
  context.fill()
  context.lineWidth = kind === 'teacher' ? 2 : 4
  context.strokeStyle = 'rgba(255, 255, 255, .9)'
  context.stroke()
  const core = context.createRadialGradient(center - radius * .28, center - radius * .34, 2, center, center, radius)
  core.addColorStop(0, 'rgba(255, 255, 255, .96)')
  core.addColorStop(.2, `rgba(${red}, ${green}, ${blue}, .98)`)
  core.addColorStop(1, `rgba(${red}, ${green}, ${blue}, .74)`)
  context.beginPath()
  context.arc(center, center, radius * .66, 0, Math.PI * 2)
  context.fillStyle = core
  context.fill()
  const texture = new THREE.CanvasTexture(canvas)
  texture.colorSpace = THREE.SRGBColorSpace
  return new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, transparent: true, depthWrite: false }))
}

function disposeMentorGraph3D() {
  if (!mentorGraph3D) return
  if (threeFrame) cancelAnimationFrame(threeFrame)
  threeResizeObserver?.disconnect()
  mentorGraph3D.abortController.abort()
  const geometries = new Set<THREE.BufferGeometry>()
  const materials = new Set<THREE.Material>()
  mentorGraph3D.scene.traverse((object) => {
    const renderable = object as THREE.Mesh | THREE.Line | THREE.Sprite
    if ('geometry' in renderable && renderable.geometry) geometries.add(renderable.geometry)
    if ('material' in renderable && renderable.material) {
      const materialList = Array.isArray(renderable.material) ? renderable.material : [renderable.material]
      materialList.forEach((material) => materials.add(material))
    }
  })
  geometries.forEach((geometry) => geometry.dispose())
  materials.forEach((material) => {
    const spriteMaterial = material as THREE.SpriteMaterial
    spriteMaterial.map?.dispose()
    material.dispose()
  })
  mentorGraph3D.renderer.dispose()
  mentorGraph3D.renderer.domElement.remove()
  mentorGraph3D = undefined
}

function renderMentorGraph3D() {
  const target = threeTarget.value
  if (!target) return
  disposeMentorGraph3D()
  const { nodes, links } = graphData()
  const scene = new THREE.Scene()
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' })
  renderer.setClearColor(0x000000, 0)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.domElement.style.cursor = 'grab'
  target.replaceChildren(renderer.domElement)
  const camera = new THREE.PerspectiveCamera(42, 1, .1, 100)
  const root = new THREE.Group()
  scene.add(root)
  scene.add(new THREE.HemisphereLight(0xf8fcfe, 0x477d9c, 2.2))
  const keyLight = new THREE.DirectionalLight(0xffffff, 2.4)
  keyLight.position.set(4, 7, 8)
  scene.add(keyLight)
  const state: MentorGraph3D = {
    renderer,
    scene,
    camera,
    root,
    raycaster: new THREE.Raycaster(),
    pointer: new THREE.Vector2(),
    nodes: [],
    effects: [],
    lines: [],
    cameraDistance: scope.value === '全部单位' ? 18 : 15,
    rotationOffset: -.45,
    pitch: -.16,
    paused: false,
    abortController: new AbortController()
  }
  mentorGraph3D = state
  const positions = new Map<string, THREE.Vector3>()
  nodes.forEach((node, index) => {
    const hash = [...node.id].reduce((value, character) => (value * 31 + character.charCodeAt(0)) >>> 0, 17)
    const depth = node.kind === 'college' ? 0 : ((hash % 100) / 100 - .5) * (node.kind === 'unit' ? 2.3 : 3.8)
    const positionScale = scope.value === '全部单位' ? 145 : 170
    const position = new THREE.Vector3((node.x ?? 0) / positionScale, -(node.y ?? 0) / positionScale, depth)
    positions.set(node.id, position)
    const component = nodeComponentSprite(threeNodeColor(node), node.kind)
    const componentScale = node.kind === 'university' ? 1.28 : node.kind === 'college' ? .92 : node.kind === 'unit' ? .62 : node.kind === 'teacher' ? .44 : .38
    component.position.copy(position)
    component.scale.set(componentScale, componentScale, 1)
    component.userData.node = node
    root.add(component)
    state.nodes.push(component)
    const effect: MentorGraph3D['effects'][number] = { sprite: component, baseScale: componentScale, phase: (hash % 360) * Math.PI / 180 }
    state.effects.push(effect)
    const showNodeName = node.kind !== 'direction' || filteredMentors.value.length <= 24
    if (showNodeName) {
      const label = textSprite(node.name, '#143f5a', node.kind === 'teacher' ? 16 : node.kind === 'university' ? 20 : 18, node.kind === 'university')
      label.position.copy(position).add(new THREE.Vector3(0, componentScale * .48 + .065, 0))
      root.add(label)
      effect.label = label
      effect.labelBaseScale = label.scale.clone()
    }
  })
  links.forEach((link) => {
    const source = positions.get(String(link.source))
    const targetPosition = positions.get(String(link.target))
    if (!source || !targetPosition) return
    const hash = [...`${link.source}:${link.target}`].reduce((value, character) => (value * 33 + character.charCodeAt(0)) >>> 0, 19)
    const midpoint = source.clone().lerp(targetPosition, .5)
    midpoint.z += ((hash % 100) / 100 - .5) * 1.8
    midpoint.x += ((hash % 7) - 3) * .08
    const curve = new THREE.CatmullRomCurve3([source, midpoint, targetPosition])
    const geometry = new THREE.BufferGeometry().setFromPoints(curve.getPoints(18))
    const material = new THREE.LineBasicMaterial({ color: 0x79b7d4, transparent: true, opacity: .42 })
    const line = new THREE.Line(geometry, material)
    root.add(line)
    state.lines.push({ material, baseOpacity: .42, phase: (hash % 360) * Math.PI / 180 })
  })

  const resize = () => {
    const bounds = target.getBoundingClientRect()
    renderer.setSize(bounds.width, bounds.height, false)
    camera.aspect = bounds.width / Math.max(1, bounds.height)
    camera.updateProjectionMatrix()
  }
  const hitNode = (event: PointerEvent) => {
    const bounds = renderer.domElement.getBoundingClientRect()
    state.pointer.set(((event.clientX - bounds.left) / bounds.width) * 2 - 1, -((event.clientY - bounds.top) / bounds.height) * 2 + 1)
    state.raycaster.setFromCamera(state.pointer, camera)
    const hitObject = state.raycaster.intersectObjects(state.nodes, false)[0]?.object as THREE.Sprite | undefined
    const hit = hitObject?.userData.node as GraphNode | undefined
    return { hit, hitObject }
  }
  const updateHover = (event: PointerEvent) => {
    const { hit, hitObject } = hitNode(event)
    const isActionable = Boolean(hit?.mentor || hit?.kind === 'college' || hit?.kind === 'unit' || hit?.kind === 'university')
    state.hovered = isActionable ? hitObject : undefined
    renderer.domElement.style.cursor = isActionable ? 'pointer' : 'grab'
  }
  const pick = (event: PointerEvent) => {
    const { hit } = hitNode(event)
    if (hit?.mentor) selectMentor(hit.mentor)
    if (hit?.kind === 'college' && hit.school) openCampusSchool(hit.school)
    if (hit?.kind === 'unit' && hit.school) openCampusDepartment(hit.school, hit.name)
    if (hit?.kind === 'university') resetFilters()
  }
  renderer.domElement.addEventListener('pointerdown', (event) => {
    renderer.domElement.setPointerCapture(event.pointerId)
    state.paused = true
    state.pointerState = { x: event.clientX, y: event.clientY, rotationOffset: state.rotationOffset, pitch: state.pitch, moved: false }
  }, { signal: state.abortController.signal })
  renderer.domElement.addEventListener('pointermove', (event) => {
    const pointerState = state.pointerState
    if (!pointerState) {
      updateHover(event)
      return
    }
    const deltaX = event.clientX - pointerState.x
    const deltaY = event.clientY - pointerState.y
    if (Math.abs(deltaX) + Math.abs(deltaY) > 3) pointerState.moved = true
    state.rotationOffset = pointerState.rotationOffset + deltaX * .009
    state.pitch = Math.max(-.78, Math.min(.38, pointerState.pitch + deltaY * .004))
  }, { signal: state.abortController.signal })
  renderer.domElement.addEventListener('pointerup', (event) => {
    const pointerState = state.pointerState
    state.pointerState = undefined
    state.paused = false
    if (!pointerState?.moved) pick(event)
    updateHover(event)
  }, { signal: state.abortController.signal })
  renderer.domElement.addEventListener('pointercancel', () => { state.pointerState = undefined; state.paused = false }, { signal: state.abortController.signal })
  renderer.domElement.addEventListener('pointerleave', () => { state.hovered = undefined; renderer.domElement.style.cursor = 'grab' }, { signal: state.abortController.signal })
  renderer.domElement.addEventListener('wheel', (event) => {
    event.preventDefault()
    state.cameraDistance = Math.max(7, Math.min(38, state.cameraDistance + event.deltaY * .012))
  }, { passive: false, signal: state.abortController.signal })
  resize()
  threeResizeObserver = new ResizeObserver(resize)
  threeResizeObserver.observe(target)
  let previousTime = performance.now()
  const animate = (time: number) => {
    if (mentorGraph3D !== state) return
    const elapsed = Math.min(48, time - previousTime)
    previousTime = time
    if (!state.paused) state.rotationOffset += elapsed * Math.PI * 2 / 9000
    // Keep the information plane readable while retaining a continuous depth motion.
    root.rotation.set(state.pitch, Math.sin(state.rotationOffset) * .24, 0)
    state.effects.forEach(({ sprite, label, labelBaseScale, baseScale, phase }) => {
      const pulse = 1 + Math.sin(time * .0022 + phase) * .03
      const hoverScale = sprite === state.hovered ? 1.24 : 1
      sprite.scale.set(baseScale * pulse * hoverScale, baseScale * pulse * hoverScale, 1)
      if (label && labelBaseScale) label.scale.copy(labelBaseScale).multiplyScalar(sprite === state.hovered ? 1.18 : 1)
    })
    state.lines.forEach(({ material, baseOpacity, phase }) => {
      material.opacity = baseOpacity + Math.sin(time * .0017 + phase) * .12
    })
    camera.position.set(0, 1.5, state.cameraDistance)
    camera.lookAt(0, 0, 0)
    renderer.render(scene, camera)
    threeFrame = requestAnimationFrame(animate)
  }
  threeFrame = requestAnimationFrame(animate)
}

onMounted(async () => {
  await nextTick()
  renderMentorGraph3D()
  try {
    const allTeachers = await loadOfficialTeacherDirectory()
    sourceStatus.value = 'ready'
    directoryMentors.value = allTeachers
  } catch {
    sourceStatus.value = 'fallback'
  }
})
watch(filteredMentors, async () => {
  const visible = filteredMentors.value
  if (visible.length && !visible.some((mentor) => mentor.id === selected.value.id)) selected.value = relationshipMentors.value[0] ?? visible[0]
  await nextTick()
  renderMentorGraph3D()
})
onBeforeUnmount(() => disposeMentorGraph3D())
</script>

<template>
  <section class="mentor-graph" aria-label="导师图谱">
    <header class="mentor-header">
      <div>
        <p class="eyebrow">教师与导师图谱 · 官网公开信息</p>
        <h2>全校教师关系图谱</h2>
        <p>教师与官方所属教学科研单位建立关系；导师类别以节点颜色标识，研究方向连线仅保留个人页已核验信息。</p>
      </div>
      <div class="coverage" aria-label="收录范围"><strong>{{ scope === '全部单位' ? campusUnits.length : filteredMentors.length }}</strong><span>{{ scope === '全部单位' ? '个学院单位' : '位公开教师' }}</span><strong>{{ scope === '全部单位' ? campusDepartmentCount : mentorCount }}</strong><span>{{ scope === '全部单位' ? '个二级单位' : '位公开导师' }}</span></div>
    </header>

    <div class="mentor-controls" aria-label="导师筛选">
      <label class="school-select"><span>所属单位</span><select v-model="scope" @change="clearUnitScope"><option v-for="school in schools" :key="school" :value="school">{{ school }}</option></select></label>
      <label class="mentor-search"><Search :size="17" /><input v-model="search" type="search" placeholder="搜索姓名、单位、学科或研究方向" /></label>
      <button class="reset-button" aria-label="重置筛选" title="重置筛选" @click="resetFilters"><SlidersHorizontal :size="18" /></button>
    </div>

    <div v-if="filteredMentors.length" class="graph-workbench" :class="{ 'campus-workbench': scope === '全部单位' }">
      <div ref="threeTarget" class="mentor-canvas" :aria-label="scope === '全部单位' ? '可拖拽缩放的全校单位关系图' : '可拖拽缩放的导师关系图'"></div>
      <aside v-if="scope !== '全部单位'" class="mentor-inspector" aria-label="导师详情">
        <div class="inspector-kicker"><span :class="selected.school === '地球科学学院' ? 'earth' : 'physics'"></span>{{ selected.school }}</div>
        <h3>{{ selected.name }}</h3><p class="mentor-title">{{ selected.title }}</p><p v-if="selected.unit && selected.unit !== selected.school" class="mentor-unit">{{ selected.unit }}</p><p class="mentor-summary">{{ selected.summary }}</p>
        <div v-if="selected.mentorTypes?.length" class="detail-group"><strong>导师类别</strong><div class="tags mentor-types"><span v-for="type in selected.mentorTypes" :key="type">{{ type }}</span></div></div>
        <div v-if="selected.subjects?.length" class="detail-group"><strong>平台公开学科</strong><div class="tags"><span v-for="subject in selected.subjects" :key="subject">{{ subject }}</span></div></div>
        <div v-if="selected.directions.length" class="detail-group"><strong>研究方向</strong><div class="tags"><span v-for="direction in selected.directions" :key="direction">{{ direction }}</span></div></div>
        <p v-else class="unstructured-note">该教师已纳入官网师资名录；研究方向尚未按本图谱的数据口径结构化。</p>
        <div v-if="selected.courses?.length" class="detail-group"><strong>官网列示课程</strong><div class="tags courses"><span v-for="course in selected.courses" :key="course">{{ course }}</span></div></div>
        <a class="source-link" :href="selected.sourceUrl" target="_blank" rel="noreferrer">查看官网教师页 <ExternalLink :size="15" /></a>
      </aside>
    </div>
    <div v-else class="empty-state"><UsersRound :size="24" /><p>当前筛选范围内没有官方公开教师记录。</p><button @click="resetFilters">清除筛选</button></div>

    <footer class="source-register">
      <div><strong>数据口径</strong><span>{{ sourceStatus === 'ready' ? '已同步官方平台全量公开教师记录。' : sourceStatus === 'geophysics' ? '已优先加载地球物理学院，正在后台同步全校公开教师记录。' : '官方平台暂不可用，显示已收录的来源数据。' }} 所属单位、公开学科与导师类别均直接使用平台字段；研究方向和课程不推断。</span></div>
      <div class="source-actions">
        <a :href="mentorSourcePages.facultyPortal" target="_blank" rel="noreferrer">全校官方教师平台 <ExternalLink :size="14" /></a>
      </div>
    </footer>
  </section>
</template>

<style scoped>
.mentor-graph { padding: 70px 0 36px; border-top: 1px solid #d9eaf3; }.mentor-header { display: flex; align-items: end; justify-content: space-between; gap: 40px; margin-bottom: 30px; }.mentor-header > div:first-child { max-width: 720px; }.mentor-header h2 { margin: 0; color: #123a60; font-family: "Microsoft YaHei", "PingFang SC", sans-serif; font-size: clamp(30px, 3vw, 42px); font-weight: 800; letter-spacing: 0; }.mentor-header p:not(.eyebrow) { margin: 14px 0 0; color: #60788d; line-height: 1.85; }.coverage { display: grid; grid-template-columns: auto auto; gap: 3px 11px; min-width: 178px; padding: 8px 0 8px 23px; border-left: 2px solid #b9ddec; }.coverage strong { color: #0879b8; font-size: 27px; line-height: 1; }.coverage span { align-self: center; color: #6d8495; font-size: 12px; }
.mentor-controls { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; }.school-select { display: flex; align-items: center; gap: 9px; min-width: 244px; padding: 0 12px; color: #59788e; background: #edf7fb; border: 1px solid #c9e3ee; border-radius: 4px; font-size: 12px; font-weight: 700; }.school-select span { flex: 0 0 auto; white-space: nowrap; }.school-select select { width: 100%; height: 38px; min-width: 0; color: #173f5b; background: transparent; border: 0; outline: 0; font: inherit; font-weight: 700; }.mentor-search { display: flex; align-items: center; gap: 8px; min-width: 260px; max-width: 340px; margin-left: auto; padding: 0 11px; color: #6d93a9; background: #fff; border: 1px solid #c9e3ee; border-radius: 4px; }.mentor-search input { width: 100%; height: 38px; min-width: 0; color: #173f5b; background: transparent; border: 0; outline: 0; font-size: 13px; }.reset-button { display: grid; place-items: center; width: 38px; height: 38px; color: #0879b8; background: #edf7fb; border: 1px solid #c9e3ee; border-radius: 4px; }
.graph-workbench { display: grid; grid-template-columns: minmax(0, 1fr) 310px; min-height: 550px; overflow: hidden; background: #f6fbfe; border: 1px solid #bad9e8; box-shadow: 0 16px 36px rgba(38, 94, 122, .08); }.mentor-canvas { min-height: 550px; background: linear-gradient(rgba(70, 142, 177, .08) 1px, transparent 1px), linear-gradient(90deg, rgba(70, 142, 177, .08) 1px, transparent 1px), radial-gradient(circle at 50% 50%, #ffffff 0, #f5fbfe 72%); background-size: 36px 36px, 36px 36px, auto; }.mentor-inspector { display: flex; flex-direction: column; padding: 27px 25px; color: #35566c; background: #ffffff; border-left: 1px solid #c7dfe9; }.inspector-kicker { display: flex; align-items: center; gap: 7px; color: #58798e; font-size: 12px; font-weight: 800; }.inspector-kicker span { width: 8px; height: 8px; border-radius: 50%; }.inspector-kicker .physics { background: #1987c7; }.inspector-kicker .earth { background: #c68839; }.mentor-inspector h3 { margin: 18px 0 3px; color: #173f5b; font-size: 28px; }.mentor-title { margin: 0; color: #0879b8; font-size: 13px; font-weight: 800; }.mentor-unit { margin: 6px 0 0; color: #718692; font-size: 12px; }.mentor-summary { margin: 19px 0 0; color: #5d7283; font-size: 13px; line-height: 1.8; }.detail-group { margin-top: 20px; }.detail-group strong { color: #264b65; font-size: 12px; }.tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 9px; }.tags span { padding: 5px 7px; color: #35566c; background: #e7f1f7; border-radius: 2px; font-size: 11px; line-height: 1.45; }.tags.mentor-types span { color: #075a9d; background: #dceef8; }.tags.courses span { color: #8b5d1e; background: #fff0d8; }.source-link { display: inline-flex; align-items: center; gap: 5px; margin-top: auto; padding-top: 24px; color: #0879b8; font-size: 13px; font-weight: 800; text-decoration: none; }.source-link:hover, .source-register a:hover { color: #075a9d; text-decoration: underline; }
.campus-workbench { display: block; height: clamp(525px, 68.75svh, 650px); min-height: 0; max-height: 650px; }.campus-network { display: block; width: 100%; height: 100%; min-height: 0; max-height: 100%; touch-action: none; cursor: grab; background: linear-gradient(rgba(70, 142, 177, .07) 1px, transparent 1px), linear-gradient(90deg, rgba(70, 142, 177, .07) 1px, transparent 1px), radial-gradient(circle at 50% 50%, #ffffff 0, #f4fbfe 72%); background-size: 36px 36px, 36px 36px, auto; }.campus-network:active { cursor: grabbing; }.campus-link { stroke: #bad9e7; stroke-linecap: round; }.campus-school-link { stroke-width: 1.5; opacity: .82; }.campus-department-link { stroke-width: 1; opacity: .62; }.campus-unit, .campus-department { cursor: pointer; outline: none; }.campus-unit circle { fill: #147aa9; stroke: #ffffff; stroke-width: 2; filter: drop-shadow(0 5px 8px rgba(20, 111, 153, .18)); transition: fill .2s ease, r .2s ease; }.campus-unit text, .campus-department text { fill: #244d69; font-family: "Microsoft YaHei", "PingFang SC", sans-serif; letter-spacing: 0; text-anchor: middle; paint-order: stroke; stroke: #f8fcfe; stroke-width: 4px; stroke-linejoin: round; pointer-events: none; }.campus-unit text { font-size: 12px; font-weight: 800; }.campus-department circle { fill: #62a9c7; stroke: #ffffff; stroke-width: 1.5; filter: drop-shadow(0 3px 5px rgba(35, 111, 145, .14)); transition: fill .2s ease, r .2s ease; }.campus-department text { fill: #6a8798; font-size: 10px; font-weight: 600; }.campus-unit:hover circle, .campus-unit:focus circle { fill: #08689a; r: 30px; }.campus-department:hover circle, .campus-department:focus circle { fill: #2789b5; r: 14px; }.campus-core circle { fill: #123f66; stroke: #ffffff; stroke-width: 2; filter: drop-shadow(0 8px 13px rgba(18, 63, 102, .22)); }.campus-core text { fill: #ffffff; font-family: "Microsoft YaHei", "PingFang SC", sans-serif; font-size: 13px; font-weight: 800; text-anchor: middle; }.campus-core { pointer-events: none; }
.graph-loading, .empty-state { display: grid; justify-items: center; align-content: center; min-height: 320px; gap: 10px; color: #58798e; background: #f7fbfd; border: 1px solid #c8dfeb; }.empty-state p { margin: 0; }.empty-state button { padding: 7px 10px; color: #0870bc; background: transparent; border: 0; font-weight: 800; }.source-register { display: flex; justify-content: space-between; gap: 30px; margin-top: 17px; padding-top: 18px; border-top: 1px solid #d9e7f0; }.source-register > div:first-child { display: grid; flex: 1; grid-template-columns: auto minmax(0, 1fr); gap: 12px; }.source-register strong { color: #274e6b; font-size: 12px; white-space: nowrap; }.source-register span { color: #718692; font-size: 12px; line-height: 1.7; }.source-actions { display: flex; flex-wrap: wrap; align-content: start; justify-content: end; gap: 9px 15px; }.source-register a { display: inline-flex; align-items: center; gap: 4px; color: #0870bc; font-size: 12px; font-weight: 700; text-decoration: none; white-space: nowrap; }
.unstructured-note { margin: 22px 0 0; padding: 11px 12px; color: #677d8c; background: #eef4f7; border-left: 2px solid #9cb7c7; font-size: 12px; line-height: 1.7; }
@media (max-width: 900px) { .mentor-header { align-items: start; flex-direction: column; }.coverage { grid-template-columns: repeat(4, auto); min-width: 0; padding-left: 0; border-top: 1px solid #bfd6e5; border-left: 0; padding-top: 14px; }.graph-workbench { grid-template-columns: 1fr; }.mentor-inspector { min-height: 330px; border-top: 1px solid #b9d3e4; border-left: 0; }.mentor-canvas { min-height: 430px; }.source-register { align-items: start; flex-direction: column; }.source-actions { justify-content: start; } }
@media (max-width: 600px) { .mentor-graph { padding: 48px 0 62px; }.mentor-controls { align-items: stretch; flex-wrap: wrap; }.school-select { width: 100%; }.mentor-search { min-width: 0; max-width: none; flex: 1; margin-left: 0; }.graph-workbench, .mentor-canvas { min-height: 370px; }.mentor-canvas { background-size: 24px 24px; }.source-register > div:first-child { grid-template-columns: 1fr; gap: 6px; } }
</style>
