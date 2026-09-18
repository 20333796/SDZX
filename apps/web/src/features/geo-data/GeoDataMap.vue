<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  Activity,
  Database,
  ExternalLink,
  FlaskConical,
  Layers,
  Magnet,
  MapPin,
  Mountain,
  Satellite,
  Waves,
} from '@lucide/vue'
import Feature from 'ol/Feature'
import Map from 'ol/Map'
import View from 'ol/View'
import Point from 'ol/geom/Point'
import TileLayer from 'ol/layer/Tile'
import VectorLayer from 'ol/layer/Vector'
import OSM from 'ol/source/OSM'
import VectorSource from 'ol/source/Vector'
import Overlay from 'ol/Overlay'
import { Circle as CircleStyle, Fill, Stroke, Style } from 'ol/style'
import { fromLonLat } from 'ol/proj'
import 'ol/ol.css'
import DestinationView from '@/features/portal/DestinationView.vue'
import { WELL_LOG_LAB_PATH } from '@/config/destinations'
import { FALLBACK_GEO_DATASETS, GEO_CATEGORY_LABELS, type GeoDatasetItem, type GeoFeature } from '@/config/geoData'

const categoryIcons: Record<string, typeof Layers> = {
  geology: Layers,
  borehole: MapPin,
  logging: Activity,
  seismic: Waves,
  geochemistry: FlaskConical,
  remote_sensing: Satellite,
  terrain: Mountain,
  potential_field: Magnet,
}

const datasets = ref<GeoDatasetItem[]>([])
const usingFallback = ref(false)
const loading = ref(true)
const activeId = ref<string>('')
const detailFeatures = ref<GeoFeature[]>([])

const activeDataset = computed(() => datasets.value.find((item) => item.id === activeId.value))
const categoryCounts = computed(() => {
  const counts: Record<string, number> = {}
  for (const item of datasets.value) counts[item.category] = (counts[item.category] ?? 0) + 1
  return counts
})
const filteredDatasets = computed(() => {
  if (!activeCategory.value) return datasets.value
  return datasets.value.filter((item) => item.category === activeCategory.value)
})

const activeCategory = ref<string>('')
const totalFeatures = computed(() => datasets.value.reduce((sum, item) => sum + item.feature_count, 0))
const totalRegions = computed(() => new Set(datasets.value.map((item) => item.region)).size)

async function loadDatasets() {
  try {
    const response = await fetch('/api/v1/geo-data/datasets')
    if (!response.ok) throw new Error(String(response.status))
    const payload = (await response.json()) as GeoDatasetItem[]
    if (!Array.isArray(payload) || payload.length === 0) throw new Error('empty')
    datasets.value = payload
  } catch {
    datasets.value = FALLBACK_GEO_DATASETS
    usingFallback.value = true
  } finally {
    loading.value = false
    if (!activeId.value && datasets.value.length) selectDataset(datasets.value[0].id)
  }
}

async function selectDataset(id: string) {
  activeId.value = id
  const local = datasets.value.find((item) => item.id === id)
  if (local?.features?.length) {
    detailFeatures.value = local.features
    return
  }
  if (usingFallback.value) {
    detailFeatures.value = []
    return
  }
  try {
    const response = await fetch(`/api/v1/geo-data/datasets/${encodeURIComponent(id)}`)
    if (!response.ok) throw new Error(String(response.status))
    const payload = (await response.json()) as GeoDatasetItem
    detailFeatures.value = payload.features ?? []
    if (local) local.features = detailFeatures.value
  } catch {
    detailFeatures.value = []
  }
}

const mapTarget = ref<HTMLDivElement | null>(null)
const popupRef = ref<HTMLDivElement | null>(null)
const popupPoint = ref<GeoFeature | null>(null)
let map: Map | undefined
let vectorSource: VectorSource | undefined
let popupOverlay: Overlay | undefined
const HOME_CENTER = fromLonLat([105.5, 38.5])

const pointStyle = new Style({
  image: new CircleStyle({
    radius: 8,
    fill: new Fill({ color: '#0e7596' }),
    stroke: new Stroke({ color: '#ffffff', width: 2.5 }),
  }),
})

function renderFeatures(features: GeoFeature[]) {
  if (!map || !vectorSource) return
  vectorSource.clear()
  for (const item of features) {
    if (!Number.isFinite(item.lon) || !Number.isFinite(item.lat)) continue
    const feature = new Feature({ geometry: new Point(fromLonLat([item.lon, item.lat])) })
    feature.set('name', item.name)
    vectorSource.addFeature(feature)
  }
  popupPoint.value = null
  popupOverlay?.setPosition(undefined)
  const extent = vectorSource.getExtent()
  if (features.length && extent) map.getView().fit(extent, { padding: [46, 46, 46, 46], maxZoom: 9, duration: 420 })
}

function flyToPoint(point: GeoFeature) {
  popupPoint.value = point
  popupOverlay?.setPosition(fromLonLat([point.lon, point.lat]))
  map?.getView().animate({ center: fromLonLat([point.lon, point.lat]), zoom: 8, duration: 420 })
}

function hidePopup() {
  popupPoint.value = null
  popupOverlay?.setPosition(undefined)
}

/* 切换类别时自动选中该类第一个数据集，地图与详情同步跟随 */
watch(activeCategory, (category) => {
  if (!category) return
  const list = datasets.value.filter((item) => item.category === category)
  if (list.length && !list.some((item) => item.id === activeId.value)) void selectDataset(list[0].id)
})

function resetView() {
  map?.getView().animate({ center: HOME_CENTER, zoom: 4, duration: 420 })
}

watch(detailFeatures, (value) => renderFeatures(value))

onMounted(() => {
  vectorSource = new VectorSource()
  map = new Map({
    target: mapTarget.value ?? undefined,
    layers: [
      new TileLayer({ source: new OSM() }),
      new VectorLayer({ source: vectorSource, style: pointStyle }),
    ],
    view: new View({ center: HOME_CENTER, zoom: 4, minZoom: 3, maxZoom: 13 }),
  })
  popupOverlay = new Overlay({ element: popupRef.value ?? undefined, positioning: 'bottom-center', offset: [0, -14], stopEvent: true })
  map.addOverlay(popupOverlay)
  map.on('singleclick', (event) => {
    const hit = map?.forEachFeatureAtPixel(event.pixel, (feature) => feature)
    const name = hit ? (hit.get('name') as string | undefined) : undefined
    const point = name ? detailFeatures.value.find((item) => item.name === name) : undefined
    if (point) {
      popupPoint.value = point
      popupOverlay?.setPosition(event.coordinate)
    } else {
      hidePopup()
    }
  })
  void loadDatasets()
})

onBeforeUnmount(() => map?.setTarget(undefined))
</script>

<template>
  <section id="geo-data" class="geo-data-page" aria-label="地学数据目录">
    <DestinationView
      eyebrow="地学数据"
      title="公开地学数据目录"
      intro="面向教学的公开地学数据集目录：钻孔、测井、地震、化探、遥感与重磁。仅登记元数据与示例点位，不接入企业敏感勘探资料。"
    >
      <p v-if="usingFallback" class="fallback-note">后端服务未连接，当前展示内置教学目录；数据以接口恢复后的版本为准。</p>

      <div class="stats-strip">
        <div><strong>{{ loading ? '—' : datasets.length }}</strong><span>公开数据集</span></div>
        <div><strong>{{ loading ? '—' : Object.keys(categoryCounts).length }}</strong><span>地学类别</span></div>
        <div><strong>{{ loading ? '—' : totalRegions }}</strong><span>覆盖区域</span></div>
        <div><strong>{{ loading ? '—' : totalFeatures }}</strong><span>示例点位</span></div>
      </div>

      <div class="filter-chips" role="tablist" aria-label="按类别筛选">
        <button :class="{ selected: activeCategory === '' }" @click="activeCategory = ''">全部（{{ datasets.length }}）</button>
        <button
          v-for="(count, category) in categoryCounts"
          :key="category"
          :class="{ selected: activeCategory === category }"
          @click="activeCategory = activeCategory === category ? '' : category"
        >
          {{ GEO_CATEGORY_LABELS[category] ?? category }}（{{ count }}）
        </button>
      </div>

      <div class="data-layout">
        <div class="dataset-grid">
          <article
            v-for="item in filteredDatasets"
            :key="item.id"
            :class="{ selected: item.id === activeId }"
            role="button"
            tabindex="0"
            @click="selectDataset(item.id)"
            @keydown.enter.prevent="selectDataset(item.id)"
          >
            <div class="card-head">
              <span class="icon-chip"><component :is="categoryIcons[item.category] ?? Database" :size="20" /></span>
              <span class="category-tag">{{ GEO_CATEGORY_LABELS[item.category] ?? item.category }}</span>
            </div>
            <h3>{{ item.title }}</h3>
            <p>{{ item.description }}</p>
            <footer>
              <small>{{ item.region }} · {{ item.size_label }} · {{ item.data_format }}</small>
              <span class="open-hint">{{ item.id === activeId ? '已在地图定位' : '在地图查看' }}</span>
            </footer>
          </article>
        </div>

        <aside class="map-panel">
          <div class="map-head">
            <strong>示例点位地图</strong>
            <button class="map-reset" @click="resetView">复位视图</button>
          </div>
          <div ref="mapTarget" class="map-canvas" aria-label="公开地学教学地图">
            <div ref="popupRef" class="map-popup" aria-live="polite">
              <template v-if="popupPoint">
                <strong>{{ popupPoint.name }}</strong>
                <span v-if="popupPoint.value">{{ popupPoint.value }}</span>
                <small v-if="popupPoint.note">{{ popupPoint.note }}</small>
              </template>
            </div>
          </div>
          <div v-if="activeDataset" class="detail-card">
            <h4>{{ activeDataset.title }}</h4>
            <dl>
              <div><dt>覆盖区域</dt><dd>{{ activeDataset.region }}</dd></div>
              <div><dt>数据格式</dt><dd>{{ activeDataset.data_format }}</dd></div>
              <div><dt>分辨率 / 精度</dt><dd>{{ activeDataset.resolution }}</dd></div>
              <div><dt>数据规模</dt><dd>{{ activeDataset.size_label }}</dd></div>
              <div><dt>来源</dt><dd>{{ activeDataset.source }}</dd></div>
              <div><dt>使用许可</dt><dd>{{ activeDataset.license }}</dd></div>
            </dl>
            <div v-if="detailFeatures.length" class="feature-list">
              <p>示例点位（{{ detailFeatures.length }}）</p>
              <ul>
                <li
                  v-for="point in detailFeatures"
                  :key="point.name"
                  role="button"
                  tabindex="0"
                  :title="`在地图中定位：${point.name}`"
                  @click="flyToPoint(point)"
                  @keydown.enter.prevent="flyToPoint(point)"
                >
                  <strong>{{ point.name }}</strong>
                  <span v-if="point.value">{{ point.value }}</span>
                  <small v-if="point.note">{{ point.note }}</small>
                </li>
              </ul>
            </div>
            <a v-if="activeDataset.access_url" :href="activeDataset.access_url" target="_blank" rel="noopener noreferrer" class="source-link">
              访问公开数据源 <ExternalLink :size="14" />
            </a>
            <RouterLink v-if="activeDataset.category === 'logging'" :to="WELL_LOG_LAB_PATH" class="source-link lab-link" @click="hidePopup">
              去测井实验室分析曲线 <ExternalLink :size="14" />
            </RouterLink>
          </div>
        </aside>
      </div>
    </DestinationView>
  </section>
</template>

<style scoped>
.geo-data-page { padding: 0; }
.fallback-note { margin: 0; padding: 10px 14px; color: #7a5c12; background: #fdf6e3; border: 1px solid #f0e2b6; border-radius: 10px; font-size: 13px; }

/* 数字用细分隔线分组，靠字号落差建立层级（不做 N 宫格瓷砖） */
.stats-strip { display: flex; align-items: center; gap: 26px; padding: 4px 0 14px; border-bottom: 1px solid #e6ecf2; }
.stats-strip div { display: flex; align-items: baseline; gap: 8px; }
.stats-strip strong { color: #0b5e63; font-size: 26px; font-weight: 800; }
.stats-strip span { color: #5f7487; font-size: 13px; }
.stats-strip div + div { padding-left: 26px; border-left: 1px solid #e6ecf2; }

.filter-chips { display: flex; flex-wrap: wrap; gap: 8px; }
.filter-chips button { padding: 7px 13px; color: #3d5464; background: #fff; border: 1px solid #d8e4ea; border-radius: 999px; font-size: 13px; font-weight: 600; transition: color .18s ease, background .18s ease, border-color .18s ease; }
.filter-chips button:hover { color: #0e7596; border-color: #9ec9d6; }
.filter-chips button.selected { color: #fff; background: #0e7596; border-color: #0e7596; }

.data-layout { display: grid; grid-template-columns: minmax(0, 1fr) minmax(320px, 400px); gap: 20px; align-items: start; }
.dataset-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; }
.dataset-grid article {
  display: flex; flex-direction: column; gap: 9px;
  padding: 18px 18px 16px;
  background: #fff;
  border: 1px solid #e6ecf2;
  border-radius: 14px;
  box-shadow: 0 1px 2px rgba(16, 52, 84, .05);
  cursor: pointer;
  transition: transform .22s ease, box-shadow .22s ease, border-color .22s ease;
}
.dataset-grid article:hover { transform: translateY(-4px); border-color: #cfe3e9; box-shadow: 0 14px 28px rgba(14, 117, 150, .13); }
.dataset-grid article.selected { border-color: #0e7596; box-shadow: 0 0 0 2px rgba(14, 117, 150, .18), 0 10px 22px rgba(14, 117, 150, .12); }
.card-head { display: flex; align-items: center; justify-content: space-between; }
.icon-chip { display: grid; place-items: center; width: 40px; height: 40px; color: #0b5e63; background: #e6f4f1; border-radius: 11px; }
.category-tag { padding: 3px 9px; color: #0b5e63; background: #e6f4f1; border-radius: 999px; font-size: 11px; font-weight: 700; }
.dataset-grid h3 { margin: 2px 0 0; color: #17384d; font-size: 15px; line-height: 1.45; }
.dataset-grid p { margin: 0; color: #5f7487; font-size: 12.5px; line-height: 1.65; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.dataset-grid footer { margin-top: auto; display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.dataset-grid small { color: #8598a6; font-size: 11.5px; }
.open-hint { color: #0e7596; font-size: 11.5px; font-weight: 700; white-space: nowrap; }

.map-panel { position: sticky; top: 20px; display: grid; gap: 12px; }
.map-head { display: flex; align-items: center; justify-content: space-between; }
.map-head strong { color: #17384d; font-size: 14px; }
.map-reset { padding: 7px 12px; color: #0b5e63; background: #fff; border: 1px solid #cfe0e5; border-radius: 9px; font-size: 12px; font-weight: 700; transition: background .18s ease; }
.map-reset:hover { background: #e6f4f1; }
.map-canvas { height: 250px; border: 1px solid #e6ecf2; border-radius: 14px; overflow: hidden; background: #dce8e3; }
.map-popup { min-width: 140px; max-width: 220px; padding: 9px 12px; color: #22384a; background: #fff; border: 1px solid #cfe0e5; border-radius: 10px; box-shadow: 0 8px 20px rgba(16, 52, 84, .18); font-size: 12px; line-height: 1.5; }
.map-popup strong { display: block; color: #17384d; font-size: 12.5px; }
.map-popup span { color: #0e7596; font-weight: 600; }
.map-popup small { display: block; color: #6b7d89; }

.detail-card { padding: 16px 18px; background: #fff; border: 1px solid #e6ecf2; border-radius: 14px; box-shadow: 0 1px 2px rgba(16, 52, 84, .05); }
.detail-card h4 { margin: 0 0 10px; color: #17384d; font-size: 14.5px; line-height: 1.5; }
.detail-card dl { display: grid; gap: 5px; margin: 0; }
.detail-card dl div { display: flex; gap: 10px; font-size: 12.5px; line-height: 1.55; }
.detail-card dt { flex: 0 0 84px; color: #8598a6; }
.detail-card dd { margin: 0; color: #33495a; }
.feature-list { margin-top: 12px; padding-top: 10px; border-top: 1px solid #eef3f6; }
.feature-list > p { margin: 0 0 7px; color: #0b5e63; font-size: 12px; font-weight: 800; }
.feature-list ul { display: grid; gap: 7px; margin: 0; padding: 0; list-style: none; }
.feature-list li { display: grid; gap: 1px; padding: 8px 10px; background: #f4faf9; border-radius: 9px; cursor: pointer; transition: background .18s ease; }
.feature-list li:hover { background: #e6f4f1; }
.feature-list li:focus-visible { outline: 2px solid #0e7596; outline-offset: 1px; }
.dataset-grid article:focus-visible { outline: 2px solid #0e7596; outline-offset: 2px; }
.feature-list strong { color: #22384a; font-size: 12.5px; }
.feature-list span { color: #0e7596; font-size: 12px; font-weight: 600; }
.feature-list small { color: #6b7d89; font-size: 11.5px; }
.source-link { display: inline-flex; align-items: center; gap: 5px; margin-top: 12px; color: #0e7596; font-size: 12.5px; font-weight: 700; }
.source-link:hover { text-decoration: underline; }
.lab-link { color: #1477f5; }

@media (max-width: 1120px) { .data-layout { grid-template-columns: 1fr; } .map-panel { position: static; } }
@media (max-width: 760px) {
  .stats-strip { flex-wrap: wrap; gap: 14px; }
  .stats-strip div + div { padding-left: 14px; }
  .map-canvas { height: 220px; }
}
</style>
