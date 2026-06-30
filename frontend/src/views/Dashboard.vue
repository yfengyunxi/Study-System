<template>
  <AppLayout>
    <div class="dashboard-hero">
      <div class="dashboard-hero-text">
        <p class="dashboard-greeting">{{ greeting }}</p>
        <h1 class="dashboard-title">{{ heroTitle }}</h1>
        <p class="dashboard-subtitle">{{ heroSubtitle }}</p>
      </div>
      <div class="dashboard-hero-actions">
        <el-button :icon="Refresh" :loading="loading" round @click="load">刷新</el-button>
        <el-button type="primary" :icon="Plus" round @click="router.push('/materials?upload=1')">上传资料</el-button>
      </div>
    </div>

    <!-- Stat cards -->
    <div class="grid stats-grid">
      <MetricCard v-for="card in statCards" :key="card.label" :label="card.label" :value="card.value" :icon="card.icon" :hint="card.hint" />
    </div>

    <!-- Row 2: Task trend + Today's Focus -->
    <div class="grid two-col section-gap">
      <div class="panel chart-panel">
        <h3 class="panel-title">任务完成趋势</h3>
        <p class="panel-subtitle">最近 7 天每天完成的任务数量。</p>
        <el-skeleton v-if="loading" :rows="4" animated />
        <el-empty v-else-if="!trend.length" description="暂无数据" />
        <template v-else>
          <div ref="trendEl" class="chart" role="img"></div>
          <p class="chart-summary">{{ trendSummary }}</p>
        </template>
      </div>

      <div class="panel focus-panel">
        <div class="focus-panel-header">
          <h3 class="panel-title">今日学习焦点</h3>
          <el-tag v-if="todayFocus" size="small" effect="plain">{{ todayFocus.reason }}</el-tag>
        </div>
        <div v-if="todayFocus" class="focus-card">
          <p class="focus-card-title">{{ todayFocus.title }}</p>
          <p class="focus-card-desc">{{ focusDescription }}</p>
          <div class="focus-card-footer">
            <el-button type="primary" @click="router.push(todayFocus.route)">{{ todayFocus.action_label }}</el-button>
            <span class="focus-time" v-if="stats.today_focus_seconds">
              🕐 今日已专注 {{ Math.round(stats.today_focus_seconds / 60) }} 分钟
            </span>
          </div>
        </div>
        <EmptyGuide v-else title="今天还没有学习焦点" description="上传资料或创建任务后，这里会给出下一步建议。">
          <template #action>
            <el-button type="primary" @click="router.push('/materials?upload=1')">上传资料</el-button>
          </template>
        </EmptyGuide>

        <div v-if="nextActions.length > 1" class="next-actions">
          <p class="next-actions-label">更多建议</p>
          <div class="next-actions-list">
            <button v-for="action in nextActions.slice(1, 4)" :key="`${action.type}-${action.title}`" type="button" class="action-chip" @click="router.push(action.route)">
              <span>{{ action.action_label }}</span>
              <span class="muted">{{ action.reason }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Row 3: Pomodoro + Focus Duration -->
    <div class="grid two-col-reverse section-gap">
      <div class="panel pomodoro-panel">
        <h3 class="panel-title">🍅 番茄钟</h3>
        <p class="panel-subtitle">自定义专注时长，开启后右上角持续倒计时。</p>
        <PomodoroTimer @completed="onPomodoroCompleted" />
      </div>

      <div class="panel chart-panel">
        <h3 class="panel-title">专注时长</h3>
        <p class="panel-subtitle">最近 7 天每日专注分钟数。</p>
        <el-skeleton v-if="loading" :rows="4" animated />
        <el-empty v-else-if="!focusTrend.length" description="暂无专注记录" />
        <StudyDurationChart v-else :data="focusTrend" />
      </div>
    </div>

    <!-- Bottom row: Health + Focus trend + Recent -->
    <div class="grid three-col section-gap">
      <div class="panel health-panel">
        <h3 class="panel-title">知识库状态</h3>
        <div class="health-center">
          <div class="health-grid">
            <div class="health-item success">
              <span class="health-value">{{ knowledgeHealth.ready }}</span>
              <span class="health-label">可问答</span>
            </div>
            <div class="health-item warning">
              <span class="health-value">{{ knowledgeHealth.processing }}</span>
              <span class="health-label">处理中</span>
            </div>
            <div class="health-item danger">
              <span class="health-value">{{ knowledgeHealth.failed }}</span>
              <span class="health-label">失败</span>
            </div>
            <div class="health-item info">
              <span class="health-value">{{ knowledgeHealth.uncategorized }}</span>
              <span class="health-label">未分类</span>
            </div>
          </div>
          <p class="health-detail">
            共 {{ knowledgeHealth.total || 0 }} 份资料
            <span v-if="knowledgeHealth.visual_asset_count"> · {{ knowledgeHealth.visual_asset_count }} 视觉资产</span>
          </p>
        </div>
      </div>

      <div class="panel chart-panel">
        <h3 class="panel-title">资料类型分布</h3>
        <p class="panel-subtitle">知识库中各类资料的数量占比。</p>
        <el-skeleton v-if="loading" :rows="3" animated />
        <el-empty v-else-if="!types.length" description="暂无资料" />
        <template v-else>
          <div ref="typeEl" class="chart chart-sm" role="img"></div>
          <p class="chart-summary">{{ typeSummary }}</p>
        </template>
      </div>

      <div class="panel">
        <h3 class="panel-title">最近问答</h3>
        <el-empty v-if="!recentChats.length" description="暂无问答记录" />
        <div v-else class="recent-chats-list">
          <div v-for="item in recentChats.slice(0, 4)" :key="item.id" class="recent-chat-item">
            <strong>{{ item.question }}</strong>
            <p class="muted">{{ (item.answer || '').slice(0, 60) }}{{ (item.answer || '').length > 60 ? '...' : '' }}</p>
          </div>
        </div>
        <el-button v-if="recentChats.length" class="full-width section-gap" @click="router.push('/chat')">进入 AI 会话</el-button>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { Plus, Refresh } from '@element-plus/icons-vue'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { statsApi } from '../api/modules'
import AppLayout from '../components/AppLayout.vue'
import EmptyGuide from '../components/study/EmptyGuide.vue'
import MetricCard from '../components/study/MetricCard.vue'
import PomodoroTimer from '../components/study/PomodoroTimer.vue'
import StudyDurationChart from '../components/study/StudyDurationChart.vue'
import { usePomodoroStore } from '../stores/pomodoro'
import { echarts } from '../utils/chart'

const pomodoroStore = usePomodoroStore()

const router = useRouter()
const stats = ref({})
const loading = ref(false)
const trendEl = ref(null)
const typeEl = ref(null)
let trendChart = null
let typeChart = null

const trend = computed(() => stats.value.task_trend || [])
const types = computed(() => stats.value.material_type_summary || [])
const focusTrend = computed(() => stats.value.focus_duration_trend || [])
const recentChats = computed(() => stats.value.recent_chats || [])
const todayFocus = computed(() => stats.value.today_focus || null)
const nextActions = computed(() => stats.value.next_actions || [])

const focusDescription = computed(() => {
  const f = todayFocus.value
  if (!f) return ''
  const same = nextActions.value.filter(a => a.type === f.type).length
  if (f.type === 'overdue_task') return `还有 ${same} 个逾期任务等待处理`
  if (f.type === 'due_today') return `今天共有 ${same + 1} 个任务待完成`
  if (f.type === 'failed_material') return '资料处理出错，需要重新上传或重建索引'
  if (f.type === 'unclassified_material') return '分类后才能在对应范围中检索到'
  if (f.type === 'recent_chat') return '点击继续上次的 AI 学习对话'
  if (f.type === 'ready_new_material') return '资料已处理完成，可以向它提问'
  if (f.type === 'empty_start') return '先上传资料或创建计划，系统会给出智能建议'
  return ''
})

const knowledgeHealth = computed(() => stats.value.knowledge_health || {
  total: 0, ready: 0, processing: 0, failed: 0, uncategorized: 0, visual_asset_count: 0
})

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return '早上好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

const displayName = computed(() => {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  return user.nickname || user.username || '同学'
})

const todayDone = computed(() => stats.value.today_done_tasks || 0)
const todayDue = computed(() => stats.value.pending_task_count || 0)

const heroTitle = computed(() => {
  if (todayDue.value === 0) return `${greeting.value}，${displayName.value}`
  if (todayDone.value === todayDue.value) return '今日任务全部完成！🎉'
  return `${greeting.value}，${displayName.value}`
})

const heroSubtitle = computed(() => {
  const pending = todayDue.value
  const focus = todayFocus.value
  if (pending === 0) return '今天还没有待处理任务，要开始规划今天的学习吗？'
  if (focus?.type === 'overdue_task') return `${pending} 个任务待处理，其中部分已逾期，尽快完成吧`
  if (pending <= 3) return `${pending} 个任务待完成，加油！`
  return `${pending} 个任务待完成，今天任务不少，一个个来`
})

const statCards = computed(() => [
  { label: '学习资料', value: stats.value.total_materials || 0, icon: '📚', hint: '知识库资料总数' },
  { label: 'AI 问答', value: stats.value.total_chats || 0, icon: '💬', hint: '累计问答次数' },
  { label: '任务完成率', value: `${stats.value.completion_rate || 0}%`, icon: '✅', hint: `${stats.value.done_tasks || 0}/${stats.value.total_tasks || 0} 个任务已完成` },
  { label: '今日专注', value: `${Math.round((stats.value.today_focus_seconds || 0) / 60)}分钟`, icon: '⏱️', hint: '今天累计专注时长' }
])

const trendSummary = computed(() => {
  const total = trend.value.reduce((sum, item) => sum + Number(item.count || 0), 0)
  if (!total) return '最近 7 天暂无完成任务，开始你的第一个任务吧。'
  const best = trend.value.reduce((max, item) => Number(item.count || 0) > Number(max.count || 0) ? item : max, { date: '', count: 0 })
  return `最近 7 天共完成 ${total} 个任务，${best.date} 最多（${best.count} 个）。`
})

const typeSummary = computed(() => {
  const total = types.value.reduce((sum, item) => sum + Number(item.count || 0), 0)
  if (!total) return '暂无资料类型统计。'
  const top = types.value.reduce((max, item) => Number(item.count || 0) > Number(max.count || 0) ? item : max, { type: '暂无', count: 0 })
  return `共 ${total} 份资料，${top.type} 类型最多（${top.count} 份）。`
})

function cssVar(name, fallback) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback
}

function renderCharts() {
  if (trendEl.value && trend.value.length) {
    trendChart ||= echarts.init(trendEl.value)
    const color = cssVar('--color-primary', '#2f80ed')
    trendChart.setOption({
      color: [color],
      tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#eadfc8', textStyle: { color: '#243042' } },
      grid: { left: 36, right: 20, top: 24, bottom: 28 },
      xAxis: {
        type: 'category', data: trend.value.map(i => i.date.slice(5)),
        axisTick: { show: false }, axisLine: { lineStyle: { color: '#eadfc8' } },
        axisLabel: { color: '#6b7280' }
      },
      yAxis: {
        type: 'value', minInterval: 1,
        splitLine: { lineStyle: { color: '#f5edd8', type: 'dashed' } },
        axisLabel: { color: '#6b7280' }
      },
      series: [{
        type: 'line', smooth: true, symbol: 'circle', symbolSize: 8,
        data: trend.value.map(i => i.count),
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(47,128,237,0.2)' }, { offset: 1, color: 'rgba(47,128,237,0.02)' }
        ])},
        lineStyle: { width: 3, color },
        itemStyle: { color, borderColor: '#fff', borderWidth: 2 }
      }]
    })
  }

  if (typeEl.value && types.value.length) {
    typeChart ||= echarts.init(typeEl.value)
    const colors = [
      cssVar('--color-primary', '#2f80ed'), cssVar('--color-mint', '#2fbf9b'),
      cssVar('--color-coral', '#ff7a66'), cssVar('--color-yellow', '#ffca58'), '#8b7cf6', '#f0a6ca'
    ]
    typeChart.setOption({
      color: colors,
      tooltip: { trigger: 'item', backgroundColor: '#fff', borderColor: '#eadfc8', textStyle: { color: '#243042' } },
      legend: { bottom: 0, textStyle: { color: '#6b7280' } },
      series: [{
        type: 'pie', radius: ['48%', '74%'], center: ['50%', '46%'],
        label: { formatter: '{b}\n{c} 份', color: '#6b7280' },
        emphasis: { label: { fontSize: 16, fontWeight: 'bold' } },
        data: types.value.map(i => ({ name: i.type, value: i.count })),
        itemStyle: { borderColor: '#fff', borderWidth: 3, borderRadius: 4 }
      }]
    })
  }
}

function resizeCharts() {
  trendChart?.resize()
  typeChart?.resize()
}

function disposeCharts() {
  trendChart?.dispose()
  typeChart?.dispose()
  trendChart = null
  typeChart = null
}

async function load() {
  disposeCharts()
  loading.value = true
  try {
    stats.value = await statsApi.dashboard()
  } finally { loading.value = false }
  await nextTick()
  renderCharts()
}

async function onPomodoroCompleted() {
  await load()
}

// Refresh dashboard when pomodoro completes on any page
watch(() => pomodoroStore.completedVersion, () => {
  if (pomodoroStore.completedVersion > 0) load()
})

onMounted(() => {
  load()
  window.addEventListener('resize', resizeCharts)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)
  disposeCharts()
})
</script>
