<template>
  <div>
    <div ref="chartEl" class="chart" role="img" :aria-label="summary"></div>
    <p v-if="data.length" class="chart-summary">{{ summary }}</p>
  </div>
</template>

<script setup>
import * as echarts from 'echarts'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  data: { type: Array, default: () => [] }
})

const chartEl = ref(null)
const chart = ref(null)

const summary = computed(() => {
  const total = props.data.reduce((sum, d) => sum + (d.duration_seconds || 0), 0)
  const minutes = Math.round(total / 60)
  const best = props.data.reduce((max, d) => (d.duration_seconds || 0) > (max.duration_seconds || 0) ? d : max, { date: '暂无', duration_seconds: 0 })
  const bestMin = Math.round((best.duration_seconds || 0) / 60)
  return `过去 ${props.data.length} 天累计专注 ${minutes} 分钟，最多一天 ${bestMin} 分钟（${best.date}）。`
})

function cssVar(name, fallback) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback
}

function render() {
  if (!chartEl.value || !props.data.length) return
  if (!chart.value) chart.value = echarts.init(chartEl.value)
  const minutes = props.data.map((d) => Math.round((d.duration_seconds || 0) / 60))
  chart.value.setOption({
    color: [cssVar('--color-coral', '#ff7a66')],
    tooltip: {
      trigger: 'item',
      formatter: (params) => `${params.name}<br/>专注 <b>${params.value}</b> 分钟`
    },
    grid: { left: 32, right: 18, top: 28, bottom: 32 },
    xAxis: { type: 'category', data: props.data.map((d) => d.date), axisTick: { show: false } },
    yAxis: { type: 'value', minInterval: 1, name: '分钟' },
    series: [
      {
        type: 'bar',
        data: minutes,
        barMaxWidth: 48,
        itemStyle: { borderRadius: [6, 6, 0, 0] }
      }
    ]
  })
}

function handleResize() {
  chart.value?.resize()
}

watch(() => props.data, () => { setTimeout(render, 0) }, { deep: true })

onMounted(() => {
  setTimeout(render, 50)
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chart.value?.dispose()
})
</script>
