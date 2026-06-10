<template>
  <div class="task-board">
    <section v-for="column in columns" :key="column.key" class="task-column">
      <h3>{{ column.title }} <span class="muted">{{ column.items.length }}</span></h3>
      <el-empty v-if="!column.items.length" :description="column.empty" />
      <TaskCard v-for="task in column.items" :key="task.id" :task="task" @complete="$emit('complete', $event)" @undo="$emit('undo', $event)" @remove="$emit('remove', $event)" />
    </section>
  </div>
</template>

<script setup>
import TaskCard from './TaskCard.vue'
defineProps({ columns: { type: Array, default: () => [] } })
defineEmits(['complete', 'undo', 'remove'])
</script>
