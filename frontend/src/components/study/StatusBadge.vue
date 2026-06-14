<template>
  <el-tag :type="tagType" :size="size">{{ label }}</el-tag>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  code: { type: String, default: 'unknown' },
  size: { type: String, default: 'small' }
})

const STATUS_MAP = {
  ready: { label: '已可提问', type: 'success' },
  processing: { label: '处理中', type: 'warning' },
  failed: { label: '处理失败', type: 'danger' },
  not_indexed: { label: '未索引', type: 'info' },
  queued: { label: '排队中', type: '' },
  running: { label: '重建中', type: 'warning' },
  stale: { label: '已过时', type: 'warning' },
  sync_failed: { label: '同步失败', type: 'danger' },
  sync_pending: { label: '待同步', type: 'warning' },
  failed_timeout: { label: '超时', type: 'danger' },
  failed_error: { label: '服务错误', type: 'danger' },
  generating: { label: '生成中', type: 'warning' },
  cancelled: { label: '已取消', type: 'info' },
  succeeded: { label: '已完成', type: 'success' },
  todo: { label: '待完成', type: 'info' },
  done: { label: '已完成', type: 'success' },
  overdue: { label: '已逾期', type: 'danger' },
  completed: { label: '已完成', type: 'success' },
  not_started: { label: '未开始', type: 'info' },
  active: { label: '进行中', type: '' },
  empty: { label: '暂无任务', type: 'info' },
  general: { label: '通用问答', type: 'info' },
  unknown: { label: '状态未知', type: 'info' }
}

const current = computed(() => STATUS_MAP[props.code] || STATUS_MAP.unknown)
const label = computed(() => current.value.label)
const tagType = computed(() => current.value.type)
</script>
