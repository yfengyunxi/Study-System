<template>
  <article class="task-board-card">
    <div class="task-card-title">
      <strong>{{ task.title }}</strong>
      <StatusBadge :code="task.status === 'done' ? 'done' : task.is_overdue ? 'overdue' : 'todo'" />
    </div>
    <p class="muted">{{ task.plan_title || '未归属计划' }}</p>
    <p class="muted">{{ dueLabel }}</p>
    <p v-if="task.description" class="muted">{{ task.description }}</p>
    <div class="task-card-actions">
      <el-button v-if="task.status === 'done'" size="small" @click="$emit('undo', task)">撤销完成</el-button>
      <el-button v-else size="small" type="success" @click="$emit('complete', task)">完成</el-button>
      <el-button size="small" type="danger" @click="$emit('remove', task)">删除</el-button>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import StatusBadge from './StatusBadge.vue'
const props = defineProps({ task: { type: Object, required: true } })
defineEmits(['complete', 'undo', 'remove'])
const dueLabel = computed(() => {
  if (!props.task.due_date) return '未安排日期'
  if (props.task.days_until_due === 0) return '今天截止'
  if (props.task.days_until_due === 1) return '明天截止'
  if (props.task.days_until_due < 0) return `已逾期 ${Math.abs(props.task.days_until_due)} 天`
  return props.task.due_date
})
</script>
