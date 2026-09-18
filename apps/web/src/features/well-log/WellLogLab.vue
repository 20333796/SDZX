<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { AlertCircle, CheckCircle2, FlaskConical, LoaderCircle, Play, RotateCcw } from '@lucide/vue'

type LogPoint = { depth: number; gr: number; rt: number; nphi: number }
type Interval = { top_depth: number; bottom_depth: number; sample_count: number; mean_gr: number; mean_rt: number; confidence: string }
type Analysis = { intervals: Interval[]; interpretation: string; evidence: string[] }

const fallback: LogPoint[] = [
  { depth: 2100, gr: 108, rt: 5, nphi: 0.12 }, { depth: 2100.5, gr: 96, rt: 7, nphi: 0.13 },
  { depth: 2101, gr: 68, rt: 24, nphi: 0.17 }, { depth: 2101.5, gr: 54, rt: 37, nphi: 0.21 },
  { depth: 2102, gr: 49, rt: 42, nphi: 0.23 }, { depth: 2102.5, gr: 62, rt: 31, nphi: 0.19 },
  { depth: 2103, gr: 84, rt: 13, nphi: 0.14 }, { depth: 2103.5, gr: 92, rt: 9, nphi: 0.11 }
]

const log = ref<LogPoint[]>(fallback)
const analysis = ref<Analysis | null>(null)
const working = ref(false)
const error = ref('')
const width = 510
const height = 258
const padding = 26

const plotPoints = computed(() => {
  const minDepth = log.value[0]?.depth ?? 0
  const maxDepth = log.value.at(-1)?.depth ?? 1
  const depthRange = maxDepth - minDepth || 1
  const xFor = (value: number, max: number) => padding + (value / max) * (width - padding * 2)
  const yFor = (depth: number) => padding + ((depth - minDepth) / depthRange) * (height - padding * 2)
  return {
    gr: log.value.map((point) => `${xFor(point.gr, 140)},${yFor(point.depth)}`).join(' '),
    rt: log.value.map((point) => `${xFor(Math.min(point.rt, 60), 60)},${yFor(point.depth)}`).join(' '),
    nphi: log.value.map((point) => `${xFor(point.nphi, 0.45)},${yFor(point.depth)}`).join(' ')
  }
})

function createTeachingAnalysis(points: LogPoint[]): Analysis {
  const candidates = points.filter((point) => point.gr <= 68 && point.rt >= 24 && point.nphi >= 0.17)
  const intervalPoints = candidates.length ? candidates : points
  const total = intervalPoints.reduce((sum, point) => ({ gr: sum.gr + point.gr, rt: sum.rt + point.rt }), { gr: 0, rt: 0 })
  const top = intervalPoints[0]?.depth ?? 0
  const bottom = intervalPoints.at(-1)?.depth ?? top

  return {
    intervals: [{
      top_depth: top,
      bottom_depth: bottom,
      sample_count: intervalPoints.length,
      mean_gr: Number((total.gr / Math.max(intervalPoints.length, 1)).toFixed(1)),
      mean_rt: Number((total.rt / Math.max(intervalPoints.length, 1)).toFixed(1)),
      confidence: candidates.length ? '教学候选段' : '待复核'
    }],
    interpretation: candidates.length ? '识别到教学候选储层段' : '未识别到满足当前教学阈值的候选段',
    evidence: ['低 GR、较高 RT 与合理 NPHI 区间需要共同出现。', '教学判识结果需由岩性和录井资料复核。']
  }
}

async function loadDemo() {
  try {
    const response = await fetch('/api/v1/well-log/demo')
    if (!response.ok) throw new Error('Demo unavailable')
    log.value = await response.json()
  } catch {
    log.value = fallback
  }
}

async function runAnalysis() {
  working.value = true
  error.value = ''
  try {
    const response = await fetch('/api/v1/well-log/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ points: log.value })
    })
    if (!response.ok) throw new Error('Analysis unavailable')
    analysis.value = await response.json()
  } catch {
    analysis.value = createTeachingAnalysis(log.value)
  } finally {
    working.value = false
  }
}

async function uploadTeachingFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  working.value = true
  error.value = ''
  const form = new FormData()
  form.append('file', file)
  try {
    const response = await fetch('/api/v1/well-log/analyze-file', { method: 'POST', body: form })
    if (response.status === 401 || response.status === 503) {
      throw new Error('测井文件处理需通过校内统一认证后使用。')
    }
    if (!response.ok) throw new Error('文件无法按教学 LAS/CSV 格式解析。')
    const result = await response.json() as { points: LogPoint[]; analysis: Analysis }
    log.value = result.points
    analysis.value = result.analysis
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '教学文件处理暂时不可用。'
  } finally {
    input.value = ''
    working.value = false
  }
}

onMounted(async () => {
  await loadDemo()
  await runAnalysis()
})
</script>

<template>
  <section id="well-log-lab" class="well-log-lab" aria-label="测井智能解释教学实验">
    <div class="lab-intro">
      <p class="eyebrow">测井智能解释 · 教学案例</p>
      <h2>从曲线到地质依据</h2>
      <p>本模块使用内置教学井段，按 GR、RT 和 NPHI 的课程阈值完成基础判识。它不替代测井解释软件或生产决策。</p>
      <div class="lab-actions">
        <button class="analysis-button" :disabled="working" @click="runAnalysis"><LoaderCircle v-if="working" :size="17" class="spinning" /><Play v-else :size="17" />{{ working ? '正在判识' : '运行教学判识' }}</button>
        <label class="upload-button"><input type="file" accept=".las,.csv,text/csv" @change="uploadTeachingFile" />导入 LAS/CSV</label>
        <button class="reset-button" @click="loadDemo"><RotateCcw :size="16" />重置案例</button>
      </div>
    </div>
    <div class="lab-workspace">
      <div class="curve-header"><span>GR API</span><span>RT Ω·m</span><span>NPHI</span></div>
      <svg class="curve-plot" :viewBox="`0 0 ${width} ${height}`" role="img" aria-label="教学测井曲线">
        <g v-for="step in 5" :key="step" class="grid-line"><line :x1="padding" :x2="width - padding" :y1="padding + step * 41" :y2="padding + step * 41" /></g>
        <polyline :points="plotPoints.gr" class="curve gr" />
        <polyline :points="plotPoints.rt" class="curve rt" />
        <polyline :points="plotPoints.nphi" class="curve nphi" />
      </svg>
      <div class="curve-legend"><span><i class="gr-dot"></i>GR</span><span><i class="rt-dot"></i>RT</span><span><i class="nphi-dot"></i>NPHI</span></div>
      <div v-if="analysis" class="analysis-result">
        <CheckCircle2 :size="20" />
        <div><strong>{{ analysis.interpretation }}</strong><span v-for="interval in analysis.intervals" :key="interval.top_depth">候选段：{{ interval.top_depth }}–{{ interval.bottom_depth }} m · GR {{ interval.mean_gr }} · RT {{ interval.mean_rt }}</span></div>
      </div>
      <div v-else-if="error" class="analysis-error"><AlertCircle :size="19" />{{ error }}</div>
      <div class="evidence-list"><FlaskConical :size="18" /><span>依据：低 GR、较高 RT 与合理 NPHI 区间需共同出现，并由岩性和录井资料复核。</span></div>
    </div>
  </section>
</template>

<style scoped>
.well-log-lab { display: grid; grid-template-columns: .78fr 1.22fr; gap: 64px; padding: 100px 0; border-top: 1px solid #ccdadd; }
.well-log-lab h2 { margin: 0; color: #112a41; font-family: "Alibaba PuHuiTi", "Microsoft YaHei", "PingFang SC", sans-serif; font-size: clamp(32px, 4vw, 48px); font-weight: 800; line-height: 1.15; letter-spacing: .02em; }
.lab-intro > p:not(.eyebrow) { color: #607283; line-height: 1.8; }
.lab-actions { display: flex; gap: 12px; margin-top: 25px; }
.analysis-button, .reset-button, .upload-button { display: inline-flex; align-items: center; gap: 7px; padding: 11px 15px; border-radius: 3px; font-weight: 800; }
.analysis-button { color: #fff; background: #0d607b; border: 1px solid #0d607b; }
.analysis-button:disabled { opacity: .62; cursor: wait; }
.reset-button { color: #31586d; background: transparent; border: 1px solid #b9cbd0; }
.upload-button { color: #0d607b; background: #e7f0f1; border: 1px solid #b9cbd0; cursor: pointer; }.upload-button input { position: absolute; width: 1px; height: 1px; opacity: 0; pointer-events: none; }
.lab-workspace { padding: 22px; background: #f4f8f7; border: 1px solid #ccdadc; }
.curve-header { display: grid; grid-template-columns: repeat(3, 1fr); color: #66808e; font-size: 11px; font-weight: 800; letter-spacing: .08em; }
.curve-header span:nth-child(2) { text-align: center; }.curve-header span:last-child { text-align: right; }
.curve-plot { width: 100%; height: auto; margin-top: 8px; overflow: visible; }
.grid-line line { stroke: #d8e4e5; stroke-width: 1; }.curve { fill: none; stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; }.gr { stroke: #c68a38; }.rt { stroke: #0c6f9e; }.nphi { stroke: #317c62; }
.curve-legend { display: flex; gap: 17px; padding-top: 4px; color: #5e737f; font-size: 12px; }.curve-legend span { display: inline-flex; align-items: center; gap: 5px; }.curve-legend i { width: 8px; height: 8px; border-radius: 50%; }.gr-dot { background: #c68a38; }.rt-dot { background: #0c6f9e; }.nphi-dot { background: #317c62; }
.analysis-result, .analysis-error, .evidence-list { display: flex; gap: 10px; margin-top: 20px; padding: 13px; font-size: 13px; line-height: 1.6; }.analysis-result { color: #145b4a; background: #e2f0eb; }.analysis-result strong, .analysis-result span { display: block; }.analysis-result span { margin-top: 3px; color: #43776b; }.analysis-error { color: #854530; background: #f8e8e3; }.evidence-list { color: #526d78; background: #e9f0ef; }
.spinning { animation: spin 1s linear infinite; }@keyframes spin { to { transform: rotate(360deg); } }
@media (max-width: 760px) { .well-log-lab { grid-template-columns: 1fr; gap: 34px; padding: 80px 0; }.lab-workspace { padding: 14px; }.lab-actions { flex-wrap: wrap; } }
</style>
