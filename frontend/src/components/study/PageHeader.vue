<template>
  <div class="page-heading study-page-header">
    <div>
      <p v-if="kicker" class="page-kicker">{{ kicker }}</p>
      <h1 class="page-title">{{ title }}</h1>
      <p v-if="subtitle" class="page-subtitle">{{ subtitle }}</p>
    </div>
    <div v-if="$slots.actions" class="toolbar-actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  kicker: { type: String, default: '' },
  title: { type: String, required: true },
  subtitle: { type: String, default: '' }
})
</script>
