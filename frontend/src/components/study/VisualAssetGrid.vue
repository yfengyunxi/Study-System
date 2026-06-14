<template>
  <div class="visual-asset-grid">
    <article v-for="asset in assets" :key="asset.id" class="visual-asset-card">
      <div class="visual-preview">
        <img v-if="urls[asset.id]" :src="urls[asset.id]" :alt="asset.caption || `视觉资产 ${asset.asset_index + 1}`" />
        <span v-else>图片不可用</span>
      </div>
      <strong>{{ asset.caption || `视觉资产 ${asset.asset_index + 1}` }}</strong>
      <p class="muted">{{ asset.page_number ? `第 ${asset.page_number} 页` : '无页码' }}</p>
      <StatusBadge :code="asset.status" />
    </article>
  </div>
</template>

<script setup>
import { onBeforeUnmount, ref, watch } from 'vue'
import { materialApi } from '../../api/modules'
import StatusBadge from './StatusBadge.vue'

const props = defineProps({ assets: { type: Array, default: () => [] } })
const urls = ref({})

function revokeAll() {
  Object.values(urls.value).forEach((url) => URL.revokeObjectURL(url))
  urls.value = {}
}

async function loadImages() {
  revokeAll()
  const entries = await Promise.all(props.assets.map(async (asset) => {
    try {
      const blob = await materialApi.assetImage(asset.id, { silent: true })
      return [asset.id, URL.createObjectURL(blob)]
    } catch (error) {
      return null
    }
  }))
  urls.value = Object.fromEntries(entries.filter(Boolean))
}

watch(() => props.assets, loadImages, { immediate: true, deep: true })
onBeforeUnmount(revokeAll)
</script>
