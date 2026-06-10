<template>
  <div :class="['message', role, { error }]">
    <div v-if="role === 'assistant' && !error" class="markdown-body" v-html="renderedContent"></div>
    <div v-else>{{ content }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { renderMarkdown } from '../../utils/renderMarkdown'

const props = defineProps({
  role: { type: String, required: true },
  content: { type: String, default: '' },
  error: { type: Boolean, default: false }
})

const renderedContent = computed(() => renderMarkdown(props.content))
</script>
