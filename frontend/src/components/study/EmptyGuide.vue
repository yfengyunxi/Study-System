<template>
  <div class="empty-guide">
    <div class="empty-guide-icon">{{ icon }}</div>
    <h3>{{ title }}</h3>
    <p>{{ description }}</p>
    <slot name="action" />
  </div>
</template>

<script setup>
defineProps({
  icon: { type: String, default: '学' },
  title: { type: String, required: true },
  description: { type: String, required: true }
})
</script>
