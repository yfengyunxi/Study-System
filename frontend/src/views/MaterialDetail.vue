<template>
  <AppLayout>
    <div class="page-heading">
      <div>
        <p class="page-kicker">Material Detail</p>
        <h1 class="page-title">{{ material.title || '资料详情' }}</h1>
        <p class="page-subtitle">{{ material.folder_name || '未分类' }} / {{ material.file_name || '正在加载资料信息' }}</p>
      </div>
      <div class="toolbar-actions">
        <el-button @click="$router.push('/materials')">返回资料库</el-button>
        <el-button :icon="Refresh" :loading="reindexing" @click="reindex">重建索引</el-button>
        <el-button type="primary" :icon="ChatDotRound" :disabled="material.status !== 'ready'" @click="$router.push(`/chat?material_id=${material.id}`)">
          基于资料提问
        </el-button>
      </div>
    </div>

    <div v-if="reindexStatus" :class="['status-banner', reindexStatus.type]">
      <span>{{ reindexStatus.message }}</span>
    </div>

    <div class="grid two-col section-gap">
      <div class="panel">
        <h3 class="panel-title">资料摘要</h3>
        <p>{{ material.summary || '暂无摘要，资料处理完成后会显示自动摘要。' }}</p>
        <div class="keyword-list">
          <el-tag v-for="keyword in material.keywords" :key="keyword">{{ keyword }}</el-tag>
          <span v-if="!material.keywords?.length" class="muted">暂无关键词</span>
        </div>
      </div>
      <div class="panel">
        <h3 class="panel-title">基础信息</h3>
        <dl class="info-list">
          <div><dt>文件名</dt><dd>{{ material.file_name || '未知' }}</dd></div>
          <div><dt>文件夹</dt><dd>{{ material.folder_name || '未分类' }}</dd></div>
          <div><dt>类型</dt><dd>{{ material.file_type || '未知' }}</dd></div>
          <div><dt>状态</dt><dd><el-tag :type="statusTag(material.status)">{{ statusText(material.status) }}</el-tag></dd></div>
          <div><dt>切片数量</dt><dd>{{ material.chunks?.length || 0 }}</dd></div>
          <div><dt>视觉资料</dt><dd>{{ material.visual_assets?.length || 0 }}</dd></div>
        </dl>
      </div>
    </div>

    <div class="panel section-gap">
      <h3 class="panel-title">视觉资料</h3>
      <p class="panel-subtitle">从 PDF/PPTX 等资料中抽取的页面或图片，可作为问答引用来源。</p>
      <el-empty v-if="!material.visual_assets?.length" description="该资料暂无视觉索引" />
      <div v-else class="asset-grid section-gap">
        <div v-for="asset in material.visual_assets" :key="asset.id" class="asset-card">
          <img
            v-if="assetImageUrls[asset.id]"
            :src="assetImageUrls[asset.id]"
            :alt="asset.caption"
            class="asset-image"
          />
          <div v-else class="asset-image" aria-hidden="true"></div>
          <div class="asset-meta">
            <strong>{{ asset.caption || '未命名视觉资料' }}</strong>
            <p class="muted">
              {{ asset.asset_type }}
              <span v-if="asset.page_number"> · 第 {{ asset.page_number }} 页</span>
            </p>
            <el-tag :type="statusTag(asset.status)" size="small">{{ statusText(asset.status) }}</el-tag>
            <p v-if="asset.error_message" class="status-banner danger">{{ asset.error_message }}</p>
          </div>
        </div>
      </div>
    </div>

    <div class="panel section-gap">
      <h3 class="panel-title">文本切片</h3>
      <p class="panel-subtitle">知识库会基于这些片段进行检索和回答。</p>
      <el-empty v-if="!material.chunks?.length" description="暂无文本切片" />
      <el-collapse v-else class="section-gap">
        <el-collapse-item
          v-for="chunk in material.chunks"
          :key="chunk.id"
          :title="`片段 ${chunk.chunk_index + 1}`"
        >
          <p class="pre-wrap">{{ chunk.content }}</p>
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
const reindexing = ref(false)
const reindexStatus = ref(null)

async function load() {
  releaseAssetUrls()
  material.value = await materialApi.detail(route.params.id)
  await loadAssetImages()
}

async function reindex() {
  reindexing.value = true
  reindexStatus.value = { type: 'warning', message: '正在重建索引，请稍候。' }
  try {
    material.value = await materialApi.reindex(route.params.id)
    showReindexResult(material.value)
    await load()
  } finally {
    reindexing.value = false
  }
}

function showReindexResult(result) {
  if (result?.status === 'failed') {
    reindexStatus.value = { type: 'danger', message: '索引重建失败，请检查资料状态后重试。' }
    ElMessage.error('索引重建失败')
    return
  }
  if (result?.status === 'processing') {
    reindexStatus.value = { type: 'warning', message: '索引仍在处理中，稍后刷新查看状态。' }
    ElMessage.warning('索引仍在处理中')
    return
  }
  reindexStatus.value = { type: '', message: '索引已重建，可以继续基于该资料提问。' }
  ElMessage.success('索引已重建')
}

async function loadAssetImages() {
  const assets = material.value.visual_assets || []
  const entries = await Promise.all(
    assets
      .filter((asset) => asset.status === 'ready')
      .map(async (asset) => {
        try {
          const blob = await materialApi.assetImage(asset.id)
          return [asset.id, URL.createObjectURL(blob)]
        } catch (error) {
          return null
        }
      })
  )
  assetImageUrls.value = Object.fromEntries(entries.filter(Boolean))
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
  }[status] || status || '未知'
}

function statusTag(status) {
  return status === 'ready' ? 'success' : status === 'failed' ? 'danger' : status === 'processing' ? 'warning' : 'info'
}

onMounted(load)
onBeforeUnmount(releaseAssetUrls)
</script>
