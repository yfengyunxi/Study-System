<template>
  <AppLayout>
    <PageHeader
      kicker="Knowledge Object"
      :title="material?.title || '资料详情'"
      :subtitle="material?.file_name || '查看资料摘要、视觉资产和文本片段。'"
    >
      <template #actions>
        <StatusBadge :code="material?.index_state || material?.status || 'unknown'" size="large" />
        <el-button @click="router.push('/materials')">返回知识库</el-button>
        <el-button :icon="Refresh" :loading="reindexing" @click="reindex">重建索引</el-button>
        <el-button type="primary" :disabled="!canAsk" @click="askWithPrompt()">基于资料提问</el-button>
      </template>
    </PageHeader>

    <div v-if="reindexStatus" :class="['status-banner', reindexStatus.type]">
      <span>{{ reindexStatus.message }}</span>
    </div>

    <div class="grid stats-grid section-gap">
      <MetricCard label="文本切片" :value="material?.chunk_count || chunks.length" icon="文" hint="可被 AI 检索的文本片段" />
      <MetricCard label="视觉资产" :value="material?.visual_asset_count || visualAssets.length" icon="图" hint="图片、页面或图表证据" />
      <MetricCard label="可用视觉资产" :value="material?.ready_visual_asset_count || visualAssets.filter((item) => item.status === 'ready').length" icon="✓" hint="可作为视觉证据" />
      <MetricCard label="失败视觉资产" :value="material?.failed_visual_asset_count || visualAssets.filter((item) => item.status === 'failed').length" icon="!" hint="需要检查或重建索引" />
    </div>

    <div class="grid two-col section-gap">
      <WorkbenchPanel title="资料摘要" subtitle="系统根据内容自动生成的知识对象概览。">
        <p>{{ material.summary || material.error_message || '暂无摘要，资料处理完成后会显示自动摘要。' }}</p>
        <div class="keyword-list">
          <el-tag v-for="keyword in material.keywords" :key="keyword">{{ keyword }}</el-tag>
          <span v-if="!material.keywords?.length" class="muted">暂无关键词</span>
        </div>
      </WorkbenchPanel>
      <WorkbenchPanel title="基础信息" subtitle="用于定位资料来源和处理状态。">
        <dl class="info-list">
          <div><dt>文件名</dt><dd>{{ material.file_name || '未知' }}</dd></div>
          <div><dt>文件夹</dt><dd>{{ material.folder_name || '未分类' }}</dd></div>
          <div><dt>类型</dt><dd>{{ material.file_type || '未知' }}</dd></div>
          <div><dt>状态</dt><dd><StatusBadge :code="material.status" /></dd></div>
          <div><dt>更新时间</dt><dd>{{ material.updated_at || material.created_at || '未知' }}</dd></div>
        </dl>
      </WorkbenchPanel>
    </div>

    <WorkbenchPanel title="推荐提问" subtitle="点击后只会预填问题，不会自动发送。" class="section-gap">
      <el-space wrap>
        <el-button v-for="prompt in recommendedQuestions" :key="prompt" @click="askWithPrompt(prompt)">{{ prompt }}</el-button>
      </el-space>
    </WorkbenchPanel>

    <WorkbenchPanel title="视觉资产" subtitle="系统从资料中提取的页面、图片或图表。" class="section-gap">
      <VisualAssetGrid v-if="visualAssets.length" :assets="visualAssets" />
      <el-empty v-else description="暂无视觉资产" />
    </WorkbenchPanel>

    <WorkbenchPanel title="文本片段" subtitle="默认折叠显示，便于核对 AI 引用。" class="section-gap">
      <el-input v-model="chunkQuery" clearable placeholder="搜索片段内容" />
      <el-empty v-if="!filteredChunks.length" description="暂无匹配片段" />
      <el-collapse v-else class="section-gap">
        <el-collapse-item v-for="chunk in filteredChunks" :key="chunk.id" :title="`片段 ${chunk.chunk_index + 1}`">
          <p class="pre-wrap">{{ chunk.content }}</p>
          <el-button size="small" @click="copyChunk(chunk)">复制片段</el-button>
        </el-collapse-item>
      </el-collapse>
    </WorkbenchPanel>
  </AppLayout>
</template>

<script setup>
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { materialApi } from '../api/modules'
import AppLayout from '../components/AppLayout.vue'
import MetricCard from '../components/study/MetricCard.vue'
import PageHeader from '../components/study/PageHeader.vue'
import StatusBadge from '../components/study/StatusBadge.vue'
import VisualAssetGrid from '../components/study/VisualAssetGrid.vue'
import WorkbenchPanel from '../components/study/WorkbenchPanel.vue'

const route = useRoute()
const router = useRouter()
const material = ref({})
const reindexing = ref(false)
const reindexStatus = ref(null)
const chunkQuery = ref('')
let reindexTimer = null

const canAsk = computed(() => {
  return material.value?.status === 'ready' || (material.value?.active_index_generation > 0)
})

const visualAssets = computed(() => material.value?.visual_assets || [])
const chunks = computed(() => material.value?.chunks || [])
const recommendedQuestions = computed(() => {
  const title = material.value?.title || '这份资料'
  const keywords = (material.value?.keywords || []).slice(0, 3)
  return [
    `请总结《${title}》的核心内容`,
    `列出《${title}》的考试重点`,
    ...keywords.map((keyword) => `请解释 ${keyword} 这个知识点`)
  ].slice(0, 5)
})
const filteredChunks = computed(() => {
  const needle = chunkQuery.value.trim().toLowerCase()
  if (!needle) return chunks.value
  return chunks.value.filter((chunk) => chunk.content.toLowerCase().includes(needle))
})

async function load() {
  material.value = await materialApi.detail(route.params.id)
}

async function reindex() {
  reindexing.value = true
  reindexStatus.value = { type: 'warning', message: '正在重建索引，请稍候。' }
  try {
    const result = await materialApi.reindex(route.params.id)
    if (result.material) material.value = result.material
    startDetailReindexPolling()
    ElMessage.info('索引重建已开始')
  } finally {
    reindexing.value = false
  }
}

function startDetailReindexPolling() {
  stopDetailReindexPolling()
  let elapsed = 0
  reindexTimer = setInterval(async () => {
    elapsed += 2000
    if (elapsed > 300000) {
      stopDetailReindexPolling()
      return
    }
    try {
      const status = await materialApi.indexStatus(route.params.id)
      if (material.value) {
        material.value.index_state = status.index_state
        material.value.status = status.status
        material.value.active_index_generation = status.active_index_generation
      }
      if (['succeeded', 'failed', 'cancelled', 'stale'].includes(status.job?.status)) {
        stopDetailReindexPolling()
        if (status.job?.status === 'succeeded') {
          reindexStatus.value = { type: '', message: '索引已重建，可以继续基于该资料提问。' }
          ElMessage.success('索引已重建')
        } else {
          reindexStatus.value = { type: 'danger', message: `索引重建失败：${status.job?.last_error || '未知错误'}` }
        }
        await load()
      }
    } catch {
      stopDetailReindexPolling()
    }
  }, 2000)
}

function stopDetailReindexPolling() {
  if (reindexTimer) {
    clearInterval(reindexTimer)
    reindexTimer = null
  }
}

function askWithPrompt(prompt = '') {
  const query = new URLSearchParams({ scope_type: 'material', material_id: String(material.value.id) })
  if (prompt) query.set('prompt', prompt)
  router.push(`/chat?${query.toString()}`)
}

async function copyChunk(chunk) {
  await navigator.clipboard.writeText(chunk.content)
  ElMessage.success('片段已复制')
}

onMounted(load)
onBeforeUnmount(() => {
  stopDetailReindexPolling()
})
</script>
