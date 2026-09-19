<script setup lang="ts">
import { ref } from 'vue'
import type { Component } from 'vue'
import {
  AlertTriangle,
  ArrowRight,
  ArrowUpRight,
  BrainCircuit,
  CloudSun,
  Cpu,
  Gem,
  Layers3,
  LineChart,
  Mountain,
  Radio,
  ScanEye,
  Waves
} from '@lucide/vue'
import { useRouter } from 'vue-router'
import { WELL_LOG_LAB_PATH } from '@/config/destinations'

// 智能应用是入口聚合页：每张卡片 = 顶部主题封面 + 介绍 + 进入动作。
// 已上线与建设中分组展示，各占一组互不混排；封面为自绘 SVG 扁平横幅（品牌蓝/青/沙统一体系）。
const router = useRouter()

interface AppEntry {
  id: string
  title: string
  description: string
  icon: Component
  /** Route path for launched apps; placeholders have none. */
  path?: string
  /** 站外应用：完整 URL，新窗口打开（如高性能计算工作台）。 */
  external?: string
}

const apps: AppEntry[] = [
  {
    id: 'well-log',
    title: '测井曲线智能判识',
    description: '上传测井曲线，自动划分储层候选段并给出可复核的地质依据。',
    icon: LineChart,
    path: WELL_LOG_LAB_PATH
  },
  {
    id: 'hpc',
    title: '智能编程·高性能计算工作台',
    description: '智能编程与高性能计算环境入口，支持在线开展代码开发与作业运行。',
    icon: Cpu,
    external: 'http://10.120.57.231:8890/'
  },
  {
    id: 'seismic',
    title: '地震剖面智能解释',
    description: '识别层位与断层结构，辅助地震资料的解释与圈闭评价。',
    icon: Waves
  },
  {
    id: 'core',
    title: '岩心图像智能识别',
    description: '对岩心照片进行岩性、结构与构造要素的自动标注。',
    icon: Layers3
  },
  {
    id: 'petrophysics',
    title: '岩石物理智能分析',
    description: '由物性实验数据反演孔隙度、渗透率等关键参数。',
    icon: Gem
  },
  {
    id: 'graph-qa',
    title: '地质知识图谱问答',
    description: '围绕地层、岩性与成藏条件进行可溯源的知识问答。',
    icon: BrainCircuit
  },
  {
    id: 'remote-sensing',
    title: '遥感影像地质解译',
    description: '从卫星与航拍影像中提取岩性分区与线性构造信息。',
    icon: ScanEye
  },
  {
    id: 'mineral',
    title: '矿产资源智能预测',
    description: '融合地物化遥多源数据，圈定成矿远景区并排序靶区。',
    icon: Mountain
  },
  {
    id: 'hazard',
    title: '地质灾害智能预警',
    description: '结合降雨、形变与地质条件评估滑坡、泥石流风险。',
    icon: AlertTriangle
  },
  {
    id: 'hydro',
    title: '水文地质智能分析',
    description: '解析水位、水质与补给关系，辅助地下水资源评价。',
    icon: CloudSun
  },
  {
    id: 'paleo',
    title: '古生物化石智能鉴定',
    description: '对化石照片进行属种比对与地史年代提示。',
    icon: Radio
  }
]

/** 已上线 = 有站内路由或站外链接。 */
function isLive(app: AppEntry) {
  return Boolean(app.path || app.external)
}

// 上线状态分组展示：已上线的排前面，未上线的单独一组，互不混排。
const liveApps = apps.filter(isLive)
const buildingApps = apps.filter(app => !isLive(app))

// 卡片封面：自绘 SVG 扁平横幅（品牌蓝/青/沙色统一体系），按应用 id 一一对应。
const COVER_IDS = new Set(['well-log', 'hpc', 'seismic', 'core', 'petrophysics', 'graph-qa', 'remote-sensing', 'mineral', 'hazard', 'hydro', 'paleo'])
function coverFor(app: AppEntry) {
  return COVER_IDS.has(app.id) ? `/images/apps/${app.id}.svg` : `/images/apps/hydro.svg`
}

function openApp(app: AppEntry) {
  if (app.path) {
    void router.push(app.path)
    return
  }
  // 站外应用：新窗口打开，避免把门户会话整个让出去。
  if (app.external) {
    window.open(app.external, '_blank', 'noopener')
    return
  }
  // 占位入口：只提示，不跳转。等对应应用上线后再挂 path。
  placeholderNotice.value = `「${app.title}」正在建设中，敬请期待。`
}

const placeholderNotice = ref('')
</script>

<template>
  <section class="apps-hub" aria-label="智能应用入口">
    <p v-if="placeholderNotice" class="apps-notice" role="status">{{ placeholderNotice }}</p>

    <!-- 已上线组 -->
    <div class="app-group">
      <div class="group-head">
        <h2>已上线</h2>
        <span class="group-count">{{ liveApps.length }} 个</span>
      </div>
      <div class="apps-grid">
        <article
          v-for="app in liveApps"
          :key="app.id"
          class="app-card is-ready"
          @click="openApp(app)"
        >
          <div class="app-cover">
            <img :src="coverFor(app)" :alt="`${app.title} 封面`" loading="lazy" />
            <span class="cover-tag">已上线</span>
          </div>
          <div class="app-body">
            <h3>{{ app.title }}</h3>
            <p>{{ app.description }}</p>
            <div class="app-foot">
              <span class="app-action is-live">
                {{ app.external ? '打开工作台' : '进入应用' }}
                <ArrowUpRight v-if="app.external" :size="14" />
                <ArrowRight v-else :size="14" />
              </span>
            </div>
          </div>
        </article>
      </div>
    </div>

    <!-- 建设中组 -->
    <div class="app-group">
      <div class="group-head">
        <h2>建设中</h2>
        <span class="group-count">{{ buildingApps.length }} 个</span>
      </div>
      <div class="apps-grid">
        <article
          v-for="app in buildingApps"
          :key="app.id"
          class="app-card"
          @click="openApp(app)"
        >
          <div class="app-cover">
            <img :src="coverFor(app)" :alt="`${app.title} 封面`" loading="lazy" />
            <span class="cover-tag">建设中</span>
          </div>
          <div class="app-body">
            <h3>{{ app.title }}</h3>
            <p>{{ app.description }}</p>
            <div class="app-foot">
              <span class="app-action">敬请期待 <ArrowRight :size="14" /></span>
            </div>
          </div>
        </article>
      </div>
    </div>
  </section>
</template>

<style scoped>
/* 入口聚合页：白底内容板 + 学情诊断同款卡片语言（白卡、灰边、左侧蓝竖条、图标芯片）。 */
.apps-hub {
  display: grid;
  gap: 20px;
  margin-top: 30px;
  padding: 28px 32px 30px;
  background: #fff;
  border: 1px solid #e6edf5;
  border-radius: 16px;
}
.apps-notice { margin: 0; padding: 10px 14px; color: #5c6d84; background: #eef3fa; border: 1px solid #d8e3ef; border-radius: 8px; font-size: 13px; }

/* 每行固定 3 张：11 张卡平铺时 5 列太挤（用户反馈），3 列给标题和描述留足呼吸感 */
.apps-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 20px; }

/* 分组标题：与卡片同宽排布，数量用浅灰小字缀在右侧。 */
.app-group { display: grid; gap: 14px; }
.group-head { display: flex; align-items: baseline; gap: 10px; }
.group-head h2 { margin: 0; color: #17384d; font-size: 16px; font-weight: 800; }
.group-count { color: #8a97a8; font-size: 12.5px; font-weight: 700; }

/* 卡片 = 顶部全宽封面 + 内容区；封面即视觉主体，去掉竖条语言。 */
.app-card {
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 1px solid #e6ecf2;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(16, 52, 84, .05);
  transition: transform .22s ease, box-shadow .22s ease, border-color .22s ease;
}
.app-card:hover { transform: translateY(-4px); border-color: #d4e3ef; box-shadow: 0 14px 28px rgba(7, 94, 163, .13); }
.app-card.is-ready { cursor: pointer; }

.app-cover { position: relative; background: #eef6fb; }
.app-cover img { display: block; width: 100%; height: 168px; object-fit: cover; }
.cover-tag { position: absolute; top: 10px; right: 10px; padding: 3px 10px; color: #8a97a8; background: rgba(255, 255, 255, .92); border: 1px solid #d8e3ee; border-radius: 999px; font-size: 12px; font-weight: 700; }
.app-card.is-ready .cover-tag { color: #0b6cb8; border-color: #c8e2f6; }

.app-body { display: flex; flex-direction: column; gap: 8px; padding: 16px 20px 14px; }
.app-body h3 { margin: 0; color: #17384d; font-size: 17px; font-weight: 800; }
.app-body p { margin: 0; min-height: 44px; color: #5f7487; font-size: 13px; line-height: 1.8; }

.app-foot { display: flex; align-items: center; justify-content: flex-end; margin-top: auto; padding-top: 10px; border-top: 1px solid #eef3f9; }
.app-action { display: inline-flex; align-items: center; gap: 5px; color: #9aa8ba; font-size: 13px; font-weight: 700; }
.app-action.is-live { color: #0b6cb8; }

@media (max-width: 1100px) { .apps-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 760px) {
  .apps-hub { margin-top: 20px; padding: 20px 16px 22px; }
  .apps-grid { grid-template-columns: 1fr; }
  .app-body p { min-height: 0; }
}
</style>
