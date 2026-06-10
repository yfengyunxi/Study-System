<template>
  <section :class="['panel', 'workbench-panel', accent ? `accent-${accent}` : '']">
    <div v-if="title || subtitle || $slots.actions" class="toolbar">
      <div>
        <h3 v-if="title" class="panel-title">{{ title }}</h3>
        <p v-if="subtitle" class="panel-subtitle">{{ subtitle }}</p>
      </div>
      <div v-if="$slots.actions" class="toolbar-actions">
        <slot name="actions" />
      </div>
    </div>
    <slot />
  </section>
</template>

<script setup>
defineProps({
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  accent: { type: String, default: '' }
})
</script>
