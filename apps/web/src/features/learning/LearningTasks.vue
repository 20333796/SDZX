<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ArrowUpRight, ClipboardCheck, LockKeyhole } from '@lucide/vue'
import type { LearningTask } from '@/types'

const tasks = ref<LearningTask[]>([])
const loading = ref(true)
const loginNotice = ref('')
const usingDemoTasks = ref(false)

const demoTasks: LearningTask[] = [
  {
    id: 'reservoir-evidence',
    course_name: '油矿地质学',
    title: '识别储层的地质依据',
    summary: '根据岩性、物性与成藏条件整理一个可复核的储层判识结论。',
    objective: '建立储层特征与有效储集空间之间的证据链。',
    difficulty: '基础',
    estimated_minutes: 35,
    status: 'published',
    sort_order: 1,
    instructions: ['阅读课程资料中的储层定义与分类。', '列出三项判识依据并说明它们的关系。', '提交结论前标明课程资料或图谱节点。']
  },
  {
    id: 'well-log-reasoning',
    course_name: '地球物理测井',
    title: '从曲线判断候选储层段',
    summary: '使用 GR、RT 与 NPHI 的基础变化特征完成一次教学判识。',
    objective: '说明曲线组合如何支持而非替代地质解释。',
    difficulty: '进阶',
    estimated_minutes: 45,
    status: 'published',
    sort_order: 2,
    instructions: ['进入测井智能解释教学实验。', '记录候选井段和对应曲线特征。', '补充需要岩心或录井资料复核的原因。']
  }
]

async function loadTasks() {
  try {
    const response = await fetch('/api/v1/learning/tasks')
    if (!response.ok) throw new Error('Learning tasks unavailable')
    tasks.value = await response.json() as LearningTask[]
  } catch {
    tasks.value = demoTasks
    usingDemoTasks.value = true
  } finally {
    loading.value = false
  }
}

function requestSubmission(task: LearningTask) {
  loginNotice.value = `“${task.title}”的学习依据提交将在校内统一认证接入后开放。`
}

onMounted(() => {
  void loadTasks()
})
</script>

<template>
  <section id="learning-tasks" class="learning-tasks" aria-label="智能研学任务">
    <div class="tasks-heading">
      <p class="eyebrow">智能研学</p>
      <h2>从问题到可复核的学习依据</h2>
      <p>任务目录对匿名访客开放。提交、个人记录、评分与教师反馈会在校内统一认证完成后启用。</p>
    </div>

    <p v-if="loading" class="task-state">正在加载任务目录...</p>
    <p v-else-if="usingDemoTasks" class="task-state">当前展示内置教学任务，提交和个人记录将在校内统一认证后保存。</p>
    <div v-if="!loading" class="task-list">
      <article v-for="(task, index) in tasks" :key="task.id" class="task-item">
        <div class="task-number">0{{ index + 1 }}</div>
        <div class="task-main">
          <div class="task-meta"><span>{{ task.course_name }}</span><span>{{ task.difficulty }} · {{ task.estimated_minutes }} 分钟</span></div>
          <h3>{{ task.title }}</h3>
          <p>{{ task.summary }}</p>
          <strong>目标：{{ task.objective }}</strong>
          <ol>
            <li v-for="instruction in task.instructions" :key="instruction">{{ instruction }}</li>
          </ol>
        </div>
        <button class="task-action" @click="requestSubmission(task)"><ClipboardCheck :size="17" />提交学习依据 <ArrowUpRight :size="16" /></button>
      </article>
    </div>
    <p v-if="loginNotice" class="login-notice"><LockKeyhole :size="15" />{{ loginNotice }}</p>
  </section>
</template>

<style scoped>
.learning-tasks { padding: 0 0 112px; border-top: 1px solid #d6e0e2; }
.tasks-heading { width: min(620px, 100%); padding-top: 88px; }
.tasks-heading h2 { margin: 0; color: #112a41; font-family: "Alibaba PuHuiTi", "Microsoft YaHei", sans-serif; font-weight: 800; font-size: clamp(32px, 4vw, 48px); line-height: 1.15; }
.tasks-heading > p:last-child { color: #607283; line-height: 1.8; }
.task-list { margin-top: 38px; border-top: 1px solid #cbd8dc; }
.task-item { display: grid; grid-template-columns: 68px minmax(0, 1fr) auto; gap: 25px; padding: 26px 0; border-bottom: 1px solid #d5e0e3; }
.task-number { color: #1c71b3; font-size: 15px; font-weight: 800; }
.task-meta { display: flex; justify-content: space-between; gap: 20px; color: #54718a; font-size: 12px; font-weight: 700; }
.task-main h3 { margin: 12px 0 7px; color: #163b5c; font-size: 22px; }
.task-main p { margin: 0; color: #667c8e; line-height: 1.7; }
.task-main strong { display: block; margin-top: 15px; color: #315c79; font-size: 14px; }
.task-main ol { display: grid; gap: 4px; margin: 12px 0 0; padding-left: 20px; color: #617788; font-size: 13px; line-height: 1.65; }
.task-action { align-self: start; display: inline-flex; align-items: center; gap: 6px; padding: 8px 0; color: #1662a7; background: transparent; border: 0; font-weight: 700; white-space: nowrap; }
.task-action:hover { color: #0c4d8e; }
.task-state, .login-notice { display: inline-flex; align-items: center; gap: 7px; margin: 28px 0 0; color: #607283; font-size: 14px; }
.task-state.error { color: #92442c; }
.login-notice { color: #567088; }
@media (max-width: 760px) { .learning-tasks { padding-bottom: 80px; }.tasks-heading { padding-top: 70px; }.task-item { grid-template-columns: 42px 1fr; gap: 14px; }.task-action { grid-column: 2; justify-self: start; }.task-meta { display: grid; gap: 3px; }.task-main h3 { font-size: 19px; } }
</style>
