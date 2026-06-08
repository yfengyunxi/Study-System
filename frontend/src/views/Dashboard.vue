<template>
  <AppLayout>
    <h1 class="page-title">首页仪表盘</h1>
    <div class="grid stats-grid">
      <div class="panel">
        <div class="stat-label">学习资料</div>
        <div class="stat-value">{{ stats.total_materials || 0 }}</div>
      </div>
      <div class="panel">
        <div class="stat-label">AI 问答</div>
        <div class="stat-value">{{ stats.total_chats || 0 }}</div>
      </div>
      <div class="panel">
        <div class="stat-label">任务完成率</div>
        <div class="stat-value">{{ stats.completion_rate || 0 }}%</div>
      </div>
      <div class="panel">
        <div class="stat-label">今日任务</div>
        <div class="stat-value">{{ stats.today_done_tasks || 0 }}/{{ stats.today_tasks || 0 }}</div>
      </div>
    </div>

    <div class="grid two-col" style="margin-top: 16px">
      <div class="panel">
        <div class="toolbar">
          <h3 style="margin: 0">最近 7 天完成趋势</h3>
          <el-button :icon="Refresh" @click="load">刷新</el-button>
        </div>
        <div ref="trendEl" class="chart"></div>
      </div>
      <div class="panel">
        <h3 style="margin-top: 0">资料类型占比</h3>
        <div ref="typeEl" class="chart"></div>
      </div>
    </div>

    <div class="panel" style="margin-top: 16px">
      <h3 style="margin-top: 0">文件夹资料分布</h3>
      <el-empty v-if="!folderStats.length" description="暂无文件夹统计" />
      <el-space v-else wrap>
        <el-tag v-for="item in folderStats" :key="item.folder_id || 'none'" size="large">
          {{ item.folder_name }} · {{ item.count }}
        </el-tag>
      </el-space>
    </div>

    <div class="grid two-col" style="margin-top: 16px">
      <div class="panel">
        <h3 style="margin-top: 0">最近问答</h3>
        <el-empty v-if="!stats.recent_chats?.length" description="暂无问答记录" />
        <el-timeline v-else>
          <el-timeline-item v-for="item in stats.recent_chats" :key="item.id">
            <strong>{{ item.question }}</strong>
            <p class="muted">{{ item.answer.slice(0, 80) }}</p>
          </el-timeline-item>
        </el-timeline>
      </div>
      <div class="panel">
        <h3 style="margin-top: 0">高频关键词 / 薄弱点</h3>
        <el-space wrap>
          <el-tag v-for="item in stats.weak_points" :key="item.name" type="warning">
            {{ item.name }} · {{ item.count }}
          </el-tag>
        </el-space>
        <el-empty v-if="!stats.weak_points?.length" description="上传资料或创建任务后生成" />
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { Refresh } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { nextTick, onMounted, ref } from 'vue'

import { statsApi } from '../api/modules'
import AppLayout from '../components/AppLayout.vue'

const stats = ref({})
const trend = ref([])
const types = ref([])
const folderStats = ref([])
const trendEl = ref(null)
const typeEl = ref(null)

async function load() {
  stats.value = await statsApi.dashboard()
  trend.value = await statsApi.taskTrend()
  types.value = await statsApi.materialTypes()
  folderStats.value = await statsApi.folders()
  await nextTick()
  renderCharts()
}

function renderCharts() {
  const trendChart = echarts.init(trendEl.value)
  trendChart.setOption({
    tooltip: {},
    xAxis: { type: 'category', data: trend.value.map((item) => item.date) },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ type: 'line', smooth: true, data: trend.value.map((item) => item.count), color: '#2563eb' }]
  })

  const typeChart = echarts.init(typeEl.value)
  typeChart.setOption({
    tooltip: {},
    series: [
      {
        type: 'pie',
        radius: ['42%', '70%'],
        data: types.value.map((item) => ({ name: item.type, value: item.count }))
      }
    ]
  })
}

onMounted(load)
</script>
