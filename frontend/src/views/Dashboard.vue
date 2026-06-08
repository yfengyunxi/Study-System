<template>
  <AppLayout>
    <div class="page-heading">
      <div>
        <p class="page-kicker">Study Dashboard</p>
        <h1 class="page-title">首页仪表盘</h1>
        <p class="page-subtitle">快速查看资料、问答和任务进度，决定今天先学什么。</p>
      </div>
      <el-button :icon="Refresh" :loading="loading" @click="load">刷新数据</el-button>
    </div>

    <div class="grid stats-grid">
      <div v-for="card in statCards" :key="card.label" class="panel stat-card">
        <div class="stat-head">
          <div class="stat-label">{{ card.label }}</div>
          <div class="stat-icon">{{ card.icon }}</div>
        </div>
        <div class="stat-value">{{ card.value }}</div>
        <p class="panel-subtitle">{{ card.hint }}</p>
      </div>
    </div>

    <div class="grid two-col section-gap">
      <div class="panel">
        <div class="toolbar">
          <div>
            <h3 class="panel-title">最近 7 天完成趋势</h3>
            <p class="panel-subtitle">观察每天完成任务的节奏。</p>
          </div>
        </div>
        <el-skeleton v-if="loading" :rows="5" animated />
        <el-empty v-else-if="!trend.length" description="暂无任务趋势数据" />
        <template v-else>
          <div ref="trendEl" class="chart" role="img" :aria-label="trendSummary"></div>
          <p class="chart-summary">{{ trendSummary }}</p>
        </template>
      </div>
      <div class="panel">
        <h3 class="panel-title">资料类型占比</h3>
        <p class="panel-subtitle">看看你的知识库里哪些类型的资料最多。</p>
        <el-skeleton v-if="loading" :rows="5" animated />
        <el-empty v-else-if="!types.length" description="暂无资料类型统计" />
        <template v-else>
          <div ref="typeEl" class="chart" role="img" :aria-label="typeSummary"></div>
          <p class="chart-summary">{{ typeSummary }}</p>
        </template>
      </div>
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
      <div class="panel">
        <h3 class="panel-title">最近问答</h3>
        <p class="panel-subtitle">回看最近向资料提出的问题。</p>
        <el-empty v-if="!stats.recent_chats?.length" description="暂无问答记录" />
        <el-timeline v-else>
          <el-timeline-item v-for="item in stats.recent_chats" :key="item.id">
            <strong>{{ item.question }}</strong>
            <p class="muted">{{ item.answer.slice(0, 80) }}</p>
          </el-timeline-item>
        </el-timeline>
      </div>
      <div class="panel">
        <h3 class="panel-title">高频关键词 / 复习线索</h3>
        <p class="panel-subtitle">这些词常出现在资料或未完成任务中，可作为复习提示。</p>
        <el-space v-if="stats.weak_points?.length" wrap>
          <el-tag v-for="item in stats.weak_points" :key="item.name" type="warning">
            {{ item.name }} · {{ item.count }}
          </el-tag>
        </el-space>
        <el-empty v-else description="上传资料或创建任务后生成" />
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { Refresh } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

import { statsApi } from '../api/modules'
import AppLayout from '../components/AppLayout.vue'

const stats = ref({})
const trend = ref([])
const types = ref([])
const folderStats = ref([])
const trendEl = ref(null)
const typeEl = ref(null)
const trendChart = ref(null)
const typeChart = ref(null)
const loading = ref(false)

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
