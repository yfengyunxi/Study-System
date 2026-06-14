<template>
  <div class="panel stat-card metric-card">
    <div class="stat-head">
      <div class="stat-label">{{ label }}</div>
      <div class="stat-icon">{{ icon }}</div>
    </div>
    <div class="stat-value">{{ value }}</div>
    <p v-if="hint" class="panel-subtitle">{{ hint }}</p>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  icon: { type: String, default: '•' },
  hint: { type: String, default: '' }
})
</script>
