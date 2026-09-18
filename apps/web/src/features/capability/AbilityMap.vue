<script setup lang="ts">
import { ArrowRight, BrainCircuit, Compass, FileCheck2, LineChart, MapPinned } from '@lucide/vue'
import { useRouter } from 'vue-router'
import { pathTo } from '@/config/destinations'

const router = useRouter()

const stages = [
  { id: 'geology-design', index: '01', title: '地质认知', description: '从课程图谱中建立地层、岩性与成藏条件的关联。', icon: BrainCircuit, action: '进入智能应用' },
  { id: 'capability-assessment', index: '02', title: '综合判识', description: '通过测井曲线、解释依据与任务反馈形成可复核证据。', icon: LineChart, action: '查看能力测评' },
  { id: 'learning-profile', index: '03', title: '实践创新', description: '把野外观察、案例研判和教师评价汇入成长轨迹。', icon: MapPinned, action: '查看成长画像' }
] as const

function openStage(section: typeof stages[number]['id']) {
  void router.push(pathTo(section))
}
</script>

<template>
  <section id="ability-map" class="ability-map" aria-label="能力大图谱">
    <header class="ability-map-heading">
      <div>
        <p>能力大图谱</p>
        <h2>让每一次学习留下专业能力证据</h2>
      </div>
      <span><FileCheck2 :size="17" /> 课程、任务与实践记录</span>
    </header>

    <div class="ability-map-path">
      <article v-for="(stage, index) in stages" :key="stage.id" class="ability-map-stage" :style="{ '--delay': `${index * 90}ms` }">
        <div class="stage-top"><span>{{ stage.index }}</span><component :is="stage.icon" :size="23" /></div>
        <h3>{{ stage.title }}</h3>
        <p>{{ stage.description }}</p>
        <button @click="openStage(stage.id)">{{ stage.action }} <ArrowRight :size="16" /></button>
      </article>
    </div>

    <footer><Compass :size="16" /> 选择路径后可继续查看该阶段的任务说明、数据范围与开放状态。</footer>
  </section>
</template>

<style scoped>
.ability-map { position: relative; overflow: hidden; margin: 74px 0; padding: 54px; color: #1f2234; background: #fff; border: 1px solid #ececf4; border-radius: 28px; box-shadow: 0 18px 46px rgba(42, 45, 80, .07); isolation: isolate; }
.ability-map::before { content: ""; position: absolute; z-index: -1; top: -184px; right: 4%; width: 430px; height: 430px; border: 1px solid rgba(30, 130, 200, .12); border-radius: 50%; box-shadow: 0 0 0 31px rgba(30, 130, 200, .035), 0 0 0 67px rgba(30, 130, 200, .026), 0 0 0 108px rgba(30, 130, 200, .018); }
.ability-map-heading { display: flex; align-items: end; justify-content: space-between; gap: 22px; }.ability-map-heading p { margin: 0 0 11px; color: #6a57ed; font-size: 13px; font-weight: 800; letter-spacing: .12em; }.ability-map-heading h2 { margin: 0; color: #202237; font-size: clamp(28px, 3.1vw, 43px); letter-spacing: .02em; }.ability-map-heading > span, .ability-map footer { display: inline-flex; align-items: center; gap: 8px; color: #74768b; font-size: 13px; line-height: 1.65; }
.ability-map-path { position: relative; display: grid; grid-template-columns: repeat(3, 1fr); gap: 34px; margin-top: 53px; }.ability-map-path::before { content: ""; position: absolute; top: 42px; right: 13%; left: 13%; height: 1px; background: repeating-linear-gradient(90deg, #b9d4e8 0 8px, transparent 8px 17px); }.ability-map-stage { position: relative; display: grid; min-height: 250px; padding: 25px; background: #f4f8fb; border: 1px solid #dfeaf2; border-radius: 16px; animation: stage-enter 460ms cubic-bezier(.2, .8, .2, 1) var(--delay) both; transition: transform 220ms ease, background 220ms ease, border-color 220ms ease, box-shadow 220ms ease; }.ability-map-stage:hover { background: #f3f1ff; border-color: #c8e2f6; box-shadow: 0 18px 28px rgba(20, 70, 118, .1); transform: translateY(-7px); }.stage-top { display: flex; align-items: center; justify-content: space-between; color: #0b6cb8; }.stage-top span { color: #0d76c4; font-family: Georgia, serif; font-size: 21px; font-style: italic; }.ability-map-stage h3 { margin: 31px 0 10px; color: #25263a; font-size: 25px; }.ability-map-stage p { margin: 0; color: #717386; font-size: 14px; line-height: 1.8; }.ability-map-stage button { display: inline-flex; align-items: center; gap: 7px; justify-self: start; margin-top: auto; padding: 0; color: #6452ed; background: transparent; border: 0; font-weight: 800; }.ability-map-stage button:hover { color: #4d3bd8; }.ability-map footer { margin-top: 31px; color: #73758a; }
@keyframes stage-enter { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
@media (max-width: 760px) { .ability-map { margin: 45px 0; padding: 30px 24px; border-radius: 20px; }.ability-map-heading { align-items: start; flex-direction: column; }.ability-map-path { grid-template-columns: 1fr; gap: 13px; margin-top: 33px; }.ability-map-path::before { display: none; }.ability-map-stage { min-height: 190px; padding-bottom: 72px; }.ability-map-stage h3 { margin-top: 20px; } }
</style>
