<template>
  <article :class="['plan-card', { active }]">
    <div class="plan-card-head">
      <h3>{{ plan.title }}</h3>
      <StatusBadge :code="plan.status || 'unknown'" />
    </div>
    <p class="muted">{{ plan.description || '暂无说明' }}</p>
    <p class="muted">{{ plan.start_date || '未设' }} - {{ plan.end_date || '未设' }}</p>
    <el-progress :percentage="plan.progress_percent || 0" />
    <p class="muted">{{ plan.done_count || 0 }} / {{ plan.task_count || 0 }} 个任务已完成</p>
    <p v-if="plan.next_due_task" class="muted">下一项：{{ plan.next_due_task.title }}</p>
    <div class="plan-card-actions">
      <el-button size="small" @click="$emit('select', plan)">查看任务</el-button>
      <el-button size="small" type="primary" @click="$emit('add-task', plan)">添加任务</el-button>
      <el-button size="small" type="danger" @click="$emit('remove', plan)">删除</el-button>
    </div>
  </article>
</template>

<script setup>
import StatusBadge from './StatusBadge.vue'
defineProps({ plan: { type: Object, required: true }, active: { type: Boolean, default: false } })
defineEmits(['select', 'add-task', 'remove'])
</script>
