<template>
  <AppLayout>
    <PageHeader
      kicker="Today Learning Cockpit"
      title="今日驾驶舱"
      subtitle="先看今天要做什么，再决定从资料、AI 问答还是计划继续。"
    >
      <template #actions>
        <el-button :icon="Refresh" :loading="loading" @click="load">刷新数据</el-button>
      </template>
    </PageHeader>

    <div class="grid two-col">
      <WorkbenchPanel title="今日学习焦点" subtitle="系统根据任务、资料和最近问答给出优先行动。" accent="primary">
        <EmptyGuide v-if="!todayFocus" title="今天还没有学习焦点" description="上传资料或创建任务后，这里会给出下一步建议。">
          <template #action>
            <el-button type="primary" @click="router.push('/materials?upload=1')">上传资料</el-button>
          </template>
        </EmptyGuide>
        <div v-else class="hero-focus-card">
          <el-tag size="large">{{ todayFocus.reason }}</el-tag>
          <h2>{{ todayFocus.title }}</h2>
          <el-button type="primary" @click="router.push(todayFocus.route)">{{ todayFocus.action_label }}</el-button>
        </div>
      </WorkbenchPanel>

      <WorkbenchPanel title="推荐下一步" subtitle="最多展示 5 个可执行学习动作。" accent="ai">
        <div class="action-list">
          <button v-for="action in nextActions" :key="`${action.type}-${action.title}`" type="button" class="action-card" @click="router.push(action.route)">
            <span>
              <strong>{{ action.title }}</strong>
              <p class="muted">{{ action.reason }}</p>
            </span>
            <el-tag>{{ action.action_label }}</el-tag>
          </button>
        </div>
      </WorkbenchPanel>
    </div>

    <div class="grid stats-grid section-gap">
      <MetricCard v-for="card in statCards" :key="card.label" :label="card.label" :value="card.value" :icon="card.icon" :hint="card.hint" />
    </div>

    <div class="grid two-col section-gap">
      <WorkbenchPanel title="番茄钟专注" subtitle="本地计时，完成后自动记录到今日学习时长。" accent="primary">
        <PomodoroTimer @completed="onPomodoroCompleted" />
      </WorkbenchPanel>
      <WorkbenchPanel title="专注时长趋势" subtitle="基于已完成的番茄钟和学习会话统计。">
        <el-skeleton v-if="loading" :rows="5" animated />
        <el-empty v-else-if="!focusTrend.length" description="暂无专注数据，完成一次番茄钟后开始统计。" />
        <StudyDurationChart v-else :data="focusTrend" />
      </WorkbenchPanel>
    </div>

    <div class="grid two-col section-gap">
      <WorkbenchPanel title="最近 7 天完成趋势" subtitle="观察每天完成任务的节奏。">
        <el-skeleton v-if="loading" :rows="5" animated />
        <el-empty v-else-if="!trend.length" description="暂无任务趋势数据" />
        <template v-else>
          <div ref="trendEl" class="chart" role="img" :aria-label="trendSummary"></div>
          <p class="chart-summary">{{ trendSummary }}</p>
        </template>
      </WorkbenchPanel>
      <WorkbenchPanel title="资料类型占比" subtitle="看看你的知识库里哪些类型的资料最多。">
        <el-skeleton v-if="loading" :rows="5" animated />
        <el-empty v-else-if="!types.length" description="暂无资料类型统计" />
        <template v-else>
          <div ref="typeEl" class="chart" role="img" :aria-label="typeSummary"></div>
          <p class="chart-summary">{{ typeSummary }}</p>
        </template>
      </WorkbenchPanel>
    </div>

    <div class="grid two-col section-gap">
      <WorkbenchPanel title="知识库健康度" subtitle="资料是否已经处理完成，决定 AI 能否引用它们。">
        <el-space wrap>
          <el-tag type="success">可问答 {{ knowledgeHealth.ready }}</el-tag>
          <el-tag type="warning">处理中 {{ knowledgeHealth.processing }}</el-tag>
          <el-tag type="danger">失败 {{ knowledgeHealth.failed }}</el-tag>
          <el-tag type="info">未分类 {{ knowledgeHealth.uncategorized }}</el-tag>
          <el-tag>视觉资产 {{ knowledgeHealth.visual_asset_count }}</el-tag>
        </el-space>
      </WorkbenchPanel>

      <WorkbenchPanel title="AI 学习连续性" subtitle="从最近一次问答继续学习。">
        <EmptyGuide v-if="!aiContinuity.recent_item" title="还没有问答记录" description="选择资料或直接进入通用问答，开始第一次学习会话。">
          <template #action>
            <el-button type="primary" @click="router.push('/chat?scope_type=all')">开始提问</el-button>
          </template>
        </EmptyGuide>
        <button v-else type="button" class="action-card" @click="router.push(aiContinuity.route)">
          <span>
            <strong>{{ aiContinuity.recent_item.question }}</strong>
            <p class="muted">{{ aiContinuity.recent_item.answer?.slice(0, 90) }}</p>
          </span>
          <el-tag>继续</el-tag>
        </button>
      </WorkbenchPanel>
    </div>

    <div class="panel section-gap">
      <h3 class="panel-title">文件夹资料分布</h3>
      <p class="panel-subtitle">按文件夹查看你的学习材料积累。</p>
      <el-empty v-if="!folderStats.length" description="暂无文件夹统计" />
      <el-space v-else wrap>
        <el-tag v-for="item in folderStats" :key="item.folder_id || 'none'" size="large">
          {{ item.folder_name }} · {{ item.count }} 份
        </el-tag>
      </el-space>
    </div>

    <div class="grid two-col section-gap">
      <WorkbenchPanel title="最近问答" subtitle="回看最近向资料提出的问题。">
        <el-empty v-if="!stats.recent_chats?.length" description="暂无问答记录" />
        <el-timeline v-else>
          <el-timeline-item v-for="item in stats.recent_chats" :key="item.id">
            <strong>{{ item.question }}</strong>
            <p class="muted">{{ item.answer.slice(0, 80) }}</p>
          </el-timeline-item>
        </el-timeline>
      </WorkbenchPanel>
      <WorkbenchPanel title="高频关键词 / 复习线索" subtitle="这些词常出现在资料或未完成任务中，可作为复习提示。">
        <el-space v-if="stats.weak_points?.length" wrap>
          <el-tag v-for="item in stats.weak_points" :key="item.name" type="warning">
            {{ item.name }} · {{ item.count }}
          </el-tag>
        </el-space>
        <el-empty v-else description="上传资料或创建任务后生成" />
      </WorkbenchPanel>
    </div>
  </AppLayout>
</template>

<script setup>
import { Refresh } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { statsApi } from '../api/modules'
import AppLayout from '../components/AppLayout.vue'
import EmptyGuide from '../components/study/EmptyGuide.vue'
import MetricCard from '../components/study/MetricCard.vue'
import PageHeader from '../components/study/PageHeader.vue'
import PomodoroTimer from '../components/study/PomodoroTimer.vue'
import StudyDurationChart from '../components/study/StudyDurationChart.vue'
import WorkbenchPanel from '../components/study/WorkbenchPanel.vue'

const router = useRouter()
const stats = ref({})
const trend = ref([])
const types = ref([])
const folderStats = ref([])
const focusTrend = ref([])
const trendEl = ref(null)
const typeEl = ref(null)
const trendChart = ref(null)
const typeChart = ref(null)
const loading = ref(false)

const knowledgeHealth = computed(() => stats.value.knowledge_health || {
  total: stats.value.total_materials || 0,
  ready: 0,
  processing: 0,
  failed: 0,
  uncategorized: 0,
  visual_asset_count: 0
})

const todayFocus = computed(() => stats.value.today_focus || fallbackActions.value[0] || null)
const nextActions = computed(() => (stats.value.next_actions?.length ? stats.value.next_actions : fallbackActions.value).slice(0, 5))
const aiContinuity = computed(() => stats.value.ai_continuity || {
  recent_item: stats.value.recent_chats?.[0] || null,
  route: '/chat'
})

const fallbackActions = computed(() => {
  const actions = []
  if ((stats.value.today_tasks || 0) > (stats.value.today_done_tasks || 0)) {
    actions.push({ type: 'due_today', title: '完成今日剩余任务', reason: '今天还有任务未完成', priority: 90, route: '/plans?task_scope=today', action_label: '查看今日任务' })
  }
  if (stats.value.recent_chats?.[0]) {
    actions.push({ type: 'recent_chat', title: stats.value.recent_chats[0].question, reason: '继续最近问答', priority: 60, route: '/chat', action_label: '继续追问' })
  }
  if (!actions.length) {
    actions.push({ type: 'empty_start', title: '上传第一份学习资料', reason: '开始建立个人知识库', priority: 40, route: '/materials?upload=1', action_label: '上传资料' })
  }
  return actions.sort((a, b) => b.priority - a.priority)
})

const statCards = computed(() => [
  {
    label: '学习资料',
    value: stats.value.total_materials || 0,
    icon: '册',
    hint: '已沉淀到知识库的资料'
  },
  {
    label: 'AI 问答',
    value: stats.value.total_chats || 0,
    icon: '问',
    hint: '和资料对话的累计次数'
  },
  {
    label: '任务完成率',
    value: `${stats.value.completion_rate || 0}%`,
    icon: '✓',
    hint: '计划任务的完成情况'
  },
  {
    label: '今日任务',
    value: `${stats.value.today_done_tasks || 0}/${stats.value.today_tasks || 0}`,
    icon: '今',
    hint: '今天已完成 / 待完成'
  }
])

const trendSummary = computed(() => {
  const total = trend.value.reduce((sum, item) => sum + Number(item.count || 0), 0)
  const best = trend.value.reduce((max, item) => Number(item.count || 0) > Number(max.count || 0) ? item : max, { date: '暂无', count: 0 })
  return `最近 7 天共完成 ${total} 个任务，完成最多的是 ${best.date}（${best.count || 0} 个）。`
})

const typeSummary = computed(() => {
  const total = types.value.reduce((sum, item) => sum + Number(item.count || 0), 0)
  const top = types.value.reduce((max, item) => Number(item.count || 0) > Number(max.count || 0) ? item : max, { type: '暂无', count: 0 })
  return `当前共有 ${total} 份资料参与统计，最多的类型是 ${top.type}（${top.count || 0} 份）。`
})

async function fetchFocusTrend() {
  try {
    focusTrend.value = await statsApi.focusDurationTrend({ days: 7 })
  } catch {
    // focus trend is optional
  }
}

async function load() {
  disposeCharts()
  loading.value = true
  try {
    const [dashboard, trendRows, typeRows, folderRows] = await Promise.all([
      statsApi.dashboard(),
      statsApi.taskTrend(),
      statsApi.materialTypes(),
      statsApi.folders()
    ])
    stats.value = dashboard
    trend.value = trendRows
    types.value = typeRows
    folderStats.value = folderRows
    await fetchFocusTrend()
  } finally {
    loading.value = false
  }
  await nextTick()
  renderCharts()
}

function cssVar(name, fallback) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback
}

function renderCharts() {
  if (trendEl.value && trend.value.length) {
    trendChart.value ||= echarts.init(trendEl.value)
    trendChart.value.setOption({
      color: [cssVar('--color-primary', '#2f80ed')],
      tooltip: { trigger: 'axis' },
      grid: { left: 32, right: 18, top: 28, bottom: 32 },
      xAxis: { type: 'category', data: trend.value.map((item) => item.date), axisTick: { show: false } },
      yAxis: { type: 'value', minInterval: 1, splitLine: { lineStyle: { color: '#f0e5d2' } } },
      series: [
        {
          type: 'line',
          smooth: true,
          data: trend.value.map((item) => item.count),
          symbolSize: 8,
          areaStyle: { color: 'rgba(47, 128, 237, 0.12)' },
          lineStyle: { width: 4 }
        }
      ]
    })
  }

  if (typeEl.value && types.value.length) {
    typeChart.value ||= echarts.init(typeEl.value)
    typeChart.value.setOption({
      color: [
        cssVar('--color-primary', '#2f80ed'),
        cssVar('--color-mint', '#2fbf9b'),
        cssVar('--color-coral', '#ff7a66'),
        cssVar('--color-yellow', '#ffca58'),
        '#8b7cf6'
      ],
      tooltip: { trigger: 'item' },
      legend: { bottom: 0, type: 'scroll' },
      series: [
        {
          type: 'pie',
          radius: ['42%', '68%'],
          center: ['50%', '44%'],
          label: { formatter: '{b}: {c}' },
          data: types.value.map((item) => ({ name: item.type, value: item.count }))
        }
      ]
    })
  }
}

function resizeCharts() {
  trendChart.value?.resize()
  typeChart.value?.resize()
}

async function onPomodoroCompleted() {
  await fetchFocusTrend()
  await load()
}

function disposeCharts() {
  trendChart.value?.dispose()
  typeChart.value?.dispose()
  trendChart.value = null
  typeChart.value = null
}

onMounted(() => {
  load()
  window.addEventListener('resize', resizeCharts)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)
  disposeCharts()
})
</script>
