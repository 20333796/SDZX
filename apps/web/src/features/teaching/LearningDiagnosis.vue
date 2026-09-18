<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { BookOpen, FileSearch, UserCheck } from '@lucide/vue'
import { pathTo } from '@/config/destinations'
import { session } from '@/session'
import DestinationView from '@/features/portal/DestinationView.vue'
import DestinationNote from '@/features/portal/DestinationNote.vue'

const router = useRouter()

// What a diagnosis actually needs, stated as data requirements rather than as a fake report: the
// numbers do not exist yet because they all come from records that require campus sign-on.
const dimensions = [
  { name: '学习记录', detail: '任务完成情况、投入时长与知识点覆盖，来自智能研学任务的提交记录。', icon: BookOpen },
  { name: '任务依据', detail: '学员提交的判识结论与引用来源，用于判断结论是否可复核。', icon: FileSearch },
  { name: '教师复核', detail: '教师对结论的确认与批注，决定该记录是否进入能力证据。', icon: UserCheck }
]

type TaskCohortStat = { task_id: string; title: string; course_name: string; difficulty: string; submissions: number; reviewed: number; avg_score: number | null }
type DiagnosisOverview = { tasks_total: number; submissions_total: number; reviewed_total: number; avg_score: number | null; per_task: TaskCohortStat[] }
type CourseDiagnosis = { course_name: string; attempts: number; reviewed: number; avg_score: number | null; level: '扎实' | '待巩固' | '需加强' }
type LearnerDiagnosis = { learner_id: string; published_tasks: number; attempts: number; reviewed: number; avg_score: number | null; coverage: number; courses: CourseDiagnosis[]; strengths: string[]; focus: string[]; suggestions: string[] }

const overview = ref<DiagnosisOverview | null>(null)
const overviewLoading = ref(true)
const overviewError = ref(false)

const report = ref<LearnerDiagnosis | null>(null)
const reportLoading = ref(false)
const reportError = ref('')

const authenticated = computed(() => session.isAuthenticated.value)

async function loadOverview() {
  try {
    const response = await fetch('/api/v1/learning/diagnosis/overview')
    if (!response.ok) throw new Error(String(response.status))
    overview.value = (await response.json()) as DiagnosisOverview
  } catch {
    overviewError.value = true
  } finally {
    overviewLoading.value = false
  }
}

async function loadReport() {
  const principal = session.principal.value
  if (!principal) return
  reportLoading.value = true
  reportError.value = ''
  try {
    const token = window.localStorage.getItem('user_token') ?? ''
    const response = await fetch(`/api/v1/learning/diagnosis/${encodeURIComponent(principal.subject)}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    })
    if (response.status === 401 || response.status === 403) {
      reportError.value = '当前账号暂无查看该诊断报告的权限（需要本人或教师身份）。'
      return
    }
    if (!response.ok) throw new Error(String(response.status))
    report.value = (await response.json()) as LearnerDiagnosis
  } catch {
    reportError.value = '诊断服务暂不可用，请稍后重试。'
  } finally {
    reportLoading.value = false
  }
}

const LEVEL_STYLES: Record<string, string> = { 扎实: 'is-good', 待巩固: 'is-mid', 需加强: 'is-low' }

onMounted(() => {
  void loadOverview()
  if (session.isAuthenticated.value) void loadReport()
})
</script>

<template>
  <DestinationView eyebrow="学情诊断" title="用学习证据定位下一步" intro="把任务提交、判识依据与教师反馈汇到一条线上，形成可由教师复核的诊断入口。">
    <dl class="diagnosis-dimensions">
      <div v-for="dimension in dimensions" :key="dimension.name">
        <div class="card-head"><span class="icon-chip"><component :is="dimension.icon" :size="20" /></span></div>
        <dt>{{ dimension.name }}</dt>
        <dd>{{ dimension.detail }}</dd>
      </div>
    </dl>

    <section class="diagnosis-section" aria-label="班级学情总览">
      <header class="section-head">
        <h3>班级学情总览</h3>
        <span>按任务聚合的匿名统计（当前为教师复核流程的示例数据）。</span>
      </header>
      <p v-if="overviewLoading" class="section-hint">正在读取学情总览…</p>
      <p v-else-if="overviewError" class="section-hint is-error">学情服务暂不可用，请稍后重试。</p>
      <template v-else-if="overview">
        <div class="stats-strip">
          <div><strong>{{ overview.tasks_total }}</strong><span>已发布任务</span></div>
          <div><strong>{{ overview.submissions_total }}</strong><span>提交记录</span></div>
          <div><strong>{{ overview.reviewed_total }}</strong><span>已复核</span></div>
          <div><strong>{{ overview.avg_score ?? '—' }}</strong><span>复核均分</span></div>
        </div>
        <ul class="task-rows">
          <li v-for="task in overview.per_task" :key="task.task_id" role="button" tabindex="0" title="去智能研学查看该任务" @click="router.push(pathTo('learning-tasks'))" @keydown.enter.prevent="router.push(pathTo('learning-tasks'))">
            <div class="task-main">
              <strong>{{ task.title }}</strong>
              <small>{{ task.course_name }} · {{ task.difficulty }}</small>
            </div>
            <div class="task-nums">
              <span>提交 <b>{{ task.submissions }}</b></span>
              <span>复核 <b>{{ task.reviewed }}</b></span>
              <span>均分 <b>{{ task.avg_score ?? '—' }}</b></span>
            </div>
          </li>
        </ul>
      </template>
    </section>

    <section class="diagnosis-section" aria-label="个人学情诊断">
      <header class="section-head">
        <h3>个人学情诊断</h3>
        <span>规则化生成、不虚构结论；复核通过的任务才计入能力证据。</span>
      </header>

      <p v-if="reportLoading" class="section-hint">正在生成个人诊断…</p>
      <p v-else-if="reportError" class="section-hint is-error">{{ reportError }}</p>

      <template v-else-if="authenticated && report">
        <div class="stats-strip">
          <div><strong>{{ report.coverage }}</strong><span>任务覆盖</span></div>
          <div><strong>{{ report.attempts }}</strong><span>我的提交</span></div>
          <div><strong>{{ report.reviewed }}</strong><span>已复核</span></div>
          <div><strong>{{ report.avg_score ?? '—' }}</strong><span>复核均分</span></div>
        </div>

        <ul class="course-rows">
          <li v-for="course in report.courses" :key="course.course_name">
            <div class="task-main">
              <strong>{{ course.course_name }}</strong>
              <small>提交 {{ course.attempts }} · 复核 {{ course.reviewed }} · 均分 {{ course.avg_score ?? '待复核' }}</small>
            </div>
            <span class="level-badge" :class="LEVEL_STYLES[course.level]">{{ course.level }}</span>
          </li>
        </ul>

        <div class="report-grid">
          <div v-if="report.strengths.length" class="report-col">
            <p class="is-good">扎实项</p>
            <ul><li v-for="item in report.strengths" :key="item">{{ item }}</li></ul>
          </div>
          <div v-if="report.focus.length" class="report-col">
            <p class="is-low">待加强项</p>
            <ul><li v-for="item in report.focus" :key="item">{{ item }}</li></ul>
          </div>
          <div class="report-col">
            <p class="is-mid">下一步建议</p>
            <ul><li v-for="item in report.suggestions" :key="item">{{ item }}</li></ul>
          </div>
        </div>

        <div class="diagnosis-actions">
          <button @click="router.push(pathTo('learning-tasks'))">去做研学任务</button>
          <button class="is-quiet" @click="router.push(pathTo('capability-assessment'))">去能力测评验证</button>
        </div>
      </template>

      <template v-else>
        <DestinationNote tone="auth" title="个人学情属校内数据">诊断需要读取学员的学习记录与教师批注，因此不会向匿名访客开放，需在校内统一认证接入后启用。</DestinationNote>
        <div class="diagnosis-actions">
          <button @click="router.push({ name: 'sign-in' })">登录后查看我的诊断</button>
          <button class="is-quiet" @click="router.push(pathTo('learning-tasks'))">先看智能研学任务</button>
        </div>
      </template>
    </section>
  </DestinationView>
</template>

<style scoped>
.diagnosis-dimensions { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 20px; margin: 0; }
.diagnosis-dimensions > div { display: flex; flex-direction: column; gap: 8px; padding: 22px 24px 20px 21px; background: #fff; border: 1px solid #e6ecf2; border-left: 3px solid #0870bc; border-radius: 14px; box-shadow: 0 1px 2px rgba(16, 52, 84, .05); transition: transform .22s ease, box-shadow .22s ease, border-color .22s ease; }
/* 左竖条与智能应用卡同款：hover 时其余边变浅、竖条保持 */
.diagnosis-dimensions > div:hover { transform: translateY(-4px); border-color: #d4e3ef; border-left-color: #0870bc; box-shadow: 0 14px 28px rgba(7, 94, 163, .13); }
.card-head { margin-bottom: 14px; }
.icon-chip { display: inline-flex; align-items: center; justify-content: center; width: 44px; height: 44px; border-radius: 12px; background: #e8f4fc; color: #0870bc; }
.diagnosis-dimensions dt { color: #17384d; font-weight: 800; font-size: 17px; }
.diagnosis-dimensions dd { margin: 0; color: #5f7487; line-height: 1.8; }

.diagnosis-section { display: grid; gap: 14px; padding-top: 6px; }
.section-head { display: grid; gap: 4px; }
.section-head h3 { margin: 0; color: #17384d; font-size: 17px; font-weight: 800; }
.section-head span { color: #8598a6; font-size: 12.5px; }
.section-hint { margin: 0; color: #8598a6; font-size: 13px; }
.section-hint.is-error { color: #b3562e; }

.stats-strip { display: flex; align-items: center; gap: 24px; padding: 12px 16px; background: #f8fbfd; border: 1px solid #e6ecf2; border-radius: 12px; }
.stats-strip div { display: flex; align-items: baseline; gap: 7px; }
.stats-strip strong { color: #0870bc; font-size: 22px; font-weight: 800; }
.stats-strip span { color: #5f7487; font-size: 12.5px; }
.stats-strip div + div { padding-left: 24px; border-left: 1px solid #e6ecf2; }

.task-rows, .course-rows { display: grid; gap: 8px; margin: 0; padding: 0; list-style: none; }
.task-rows li, .course-rows li { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 12px 14px; background: #fff; border: 1px solid #e6ecf2; border-radius: 12px; }
.task-rows li { cursor: pointer; transition: transform .2s ease, border-color .2s ease, box-shadow .2s ease; }
.task-rows li:hover { transform: translateY(-2px); border-color: #d4e3ef; box-shadow: 0 8px 18px rgba(7, 94, 163, .1); }
.task-rows li:focus-visible { outline: 2px solid #0870bc; outline-offset: 2px; }
.task-main { display: grid; gap: 2px; }
.task-main strong { color: #22384a; font-size: 13.5px; }
.task-main small { color: #8598a6; font-size: 12px; }
.task-nums { display: flex; gap: 16px; }
.task-nums span { color: #5f7487; font-size: 12px; white-space: nowrap; }
.task-nums b { color: #0870bc; font-size: 13px; }

.level-badge { padding: 3px 10px; border-radius: 999px; font-size: 11.5px; font-weight: 800; white-space: nowrap; }
.level-badge.is-good { color: #0b5e63; background: #e6f4f1; }
.level-badge.is-mid { color: #8a6116; background: #fdf3df; }
.level-badge.is-low { color: #a03d2d; background: #fbe9e4; }

.report-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px; }
.report-col { padding: 14px 16px; background: #f8fbfd; border: 1px solid #e6ecf2; border-radius: 12px; }
.report-col > p { margin: 0 0 8px; font-size: 12.5px; font-weight: 800; }
.report-col > p.is-good { color: #0b5e63; }
.report-col > p.is-mid { color: #8a6116; }
.report-col > p.is-low { color: #a03d2d; }
.report-col ul { display: grid; gap: 6px; margin: 0; padding: 0; list-style: none; }
.report-col li { color: #4c5f70; font-size: 12.5px; line-height: 1.65; }

.diagnosis-actions { display: flex; flex-wrap: wrap; gap: 12px; }
.diagnosis-actions button { padding: 11px 18px; color: #fff; background: #0870bc; border: 0; border-radius: 4px; font-weight: 800; }
.diagnosis-actions button.is-quiet { color: #075a9d; background: #e8f4fc; }
.diagnosis-actions button:hover { transform: translateY(-2px); }
.diagnosis-actions button { transition: transform 180ms ease; }
@media (prefers-reduced-motion: no-preference) {
  .diagnosis-dimensions > div { animation: cardIn 360ms ease both; }
}
@keyframes cardIn { from { opacity: 0; } to { opacity: 1; } }

@media (max-width: 760px) {
  .stats-strip { flex-wrap: wrap; gap: 12px; }
  .stats-strip div + div { padding-left: 12px; }
  .task-rows li, .course-rows li { flex-direction: column; align-items: flex-start; gap: 8px; }
  .task-nums { gap: 12px; }
}
</style>
