<template>
  <div class="evidence-list">
    <el-empty v-if="!references.length" description="本次回答没有资料引用" />
    <article v-for="ref in references" :key="referenceKey(ref)" class="source-card">
      <strong>{{ titleFor(ref) }}</strong>
      <p class="muted">{{ metaFor(ref) }}</p>
      <template v-if="isVisual(ref)">
        <p>{{ ref.caption || ref.content_preview || '视觉证据' }}</p>
        <img v-if="urls[ref.asset_id]" :src="urls[ref.asset_id]" :alt="ref.caption || '视觉证据'" class="reference-image" @error="onImageError(ref)" />
        <p v-else class="muted image-fallback">
          <span>📷 {{ ref.caption || '视觉证据' }}</span>
          <span v-if="ref.material_title">来源：{{ ref.material_title }}</span>
          <span>图片暂不可用，可通过资料详情查看</span>
        </p>
      </template>
      <p v-else>{{ ref.content_preview || ref.content || '暂无片段内容' }}</p>
    </article>
  </div>
</template>

<script setup>
import { onBeforeUnmount, ref, watch } from 'vue'
import { materialApi } from '../../api/modules'

const props = defineProps({ references: { type: Array, default: () => [] } })
const urls = ref({})

function isVisual(ref) {
  return ref.type === 'visual' || ref.type === 'image' || ref.legacy_type === 'image'
}

function titleFor(ref) {
  return ref.material_title || ref.title || `资料 ${ref.material_id || ''}`
}

function metaFor(ref) {
  if (isVisual(ref)) return ref.page_number ? `视觉证据 · 第 ${ref.page_number} 页` : '视觉证据'
  return Number.isInteger(ref.chunk_index) ? `文本片段 ${ref.chunk_index + 1}` : '文本片段'
}

function referenceKey(ref) {
  return isVisual(ref) ? `visual-${ref.asset_id || ref.page_number || ref.caption}` : `text-${ref.material_id}-${ref.chunk_index}-${ref.content_preview}`
}

function revokeAll() {
  Object.values(urls.value).forEach((url) => URL.revokeObjectURL(url))
  urls.value = {}
}

async function loadImages() {
  revokeAll()
  const visualRefs = props.references.filter((ref) => isVisual(ref) && ref.asset_id)
  const entries = await Promise.all(visualRefs.map(async (ref) => {
    try {
      const blob = await materialApi.assetImage(ref.asset_id)
      return [ref.asset_id, URL.createObjectURL(blob)]
    } catch (error) {
      return null
    }
  }))
  urls.value = Object.fromEntries(entries.filter(Boolean))
}

watch(() => props.references, loadImages, { immediate: true, deep: true })
onBeforeUnmount(revokeAll)
</script>
