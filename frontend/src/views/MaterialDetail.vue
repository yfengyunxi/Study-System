<template>
  <AppLayout>
    <div class="toolbar">
      <h1 class="page-title" style="margin: 0">{{ material.title || '资料详情' }}</h1>
      <el-space>
        <el-button :icon="Refresh" @click="reindex">重建索引</el-button>
        <el-button type="primary" :icon="ChatDotRound" @click="$router.push(`/chat?material_id=${material.id}`)">
          基于资料提问
        </el-button>
      </el-space>
    </div>

    <div class="grid two-col">
      <div class="panel">
        <h3 style="margin-top: 0">资料摘要</h3>
        <p>{{ material.summary }}</p>
        <el-space wrap>
          <el-tag v-for="keyword in material.keywords" :key="keyword">{{ keyword }}</el-tag>
        </el-space>
      </div>
      <div class="panel">
        <h3 style="margin-top: 0">基础信息</h3>
        <p>文件名：{{ material.file_name }}</p>
        <p>文件夹：{{ material.folder_name || '未分类' }}</p>
        <p>类型：{{ material.file_type }}</p>
        <p>状态：{{ material.status }}</p>
        <p>切片数量：{{ material.chunks?.length || 0 }}</p>
        <p>视觉资料：{{ material.visual_assets?.length || 0 }}</p>
      </div>
    </div>

    <div class="panel" style="margin-top: 16px">
      <h3 style="margin-top: 0">视觉资料</h3>
      <el-empty v-if="!material.visual_assets?.length" description="该资料暂无视觉索引" />
      <div v-else class="asset-grid">
        <div v-for="asset in material.visual_assets" :key="asset.id" class="asset-card">
          <img
            v-if="assetImageUrls[asset.id]"
            :src="assetImageUrls[asset.id]"
            :alt="asset.caption"
            class="asset-image"
          />
          <div class="asset-meta">
            <strong>{{ asset.caption }}</strong>
            <p class="muted">
              {{ asset.asset_type }}
              <span v-if="asset.page_number"> · 第 {{ asset.page_number }} 页</span>
              · {{ statusText(asset.status) }}
            </p>
            <p v-if="asset.error_message" class="muted">{{ asset.error_message }}</p>
          </div>
        </div>
      </div>
    </div>

    <div class="panel" style="margin-top: 16px">
      <h3 style="margin-top: 0">文本切片</h3>
      <el-collapse>
        <el-collapse-item
          v-for="chunk in material.chunks"
          :key="chunk.id"
          :title="`片段 ${chunk.chunk_index + 1}`"
        >
          <p style="white-space: pre-wrap">{{ chunk.content }}</p>
        </el-collapse-item>
      </el-collapse>
    </div>
  </AppLayout>
</template>

<script setup>
import { ChatDotRound, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { materialApi } from '../api/modules'
import AppLayout from '../components/AppLayout.vue'

const route = useRoute()
const material = ref({})
const assetImageUrls = ref({})

async function load() {
  releaseAssetUrls()
  material.value = await materialApi.detail(route.params.id)
  await loadAssetImages()
}

async function reindex() {
  material.value = await materialApi.reindex(route.params.id)
  ElMessage.success('索引已重建')
  await load()
}

async function loadAssetImages() {
  const assets = material.value.visual_assets || []
  const entries = await Promise.all(
    assets
      .filter((asset) => asset.status === 'ready')
      .map(async (asset) => {
        const blob = await materialApi.assetImage(asset.id)
        return [asset.id, URL.createObjectURL(blob)]
      })
  )
  assetImageUrls.value = Object.fromEntries(entries)
}

function releaseAssetUrls() {
  Object.values(assetImageUrls.value).forEach((url) => URL.revokeObjectURL(url))
  assetImageUrls.value = {}
}

function statusText(status) {
  return {
    ready: '已完成',
    processing: '处理中',
    failed: '失败'
  }[status] || status
}

onMounted(load)
onBeforeUnmount(releaseAssetUrls)
</script>
