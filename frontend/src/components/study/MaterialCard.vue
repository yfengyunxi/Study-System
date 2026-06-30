<template>
  <article class="material-card">
    <div class="material-card-head">
      <div class="material-card-head-left">
        <el-tag>{{ material.file_type?.toUpperCase() || 'FILE' }}</el-tag>
        <StatusBadge :code="material.status" />
        <span v-if="isReindexing" class="reindexing-badge">
          <el-icon class="reindexing-spin"><Refresh /></el-icon>
          重建中
        </span>
      </div>
      <el-icon v-if="sortable" class="drag-handle" title="拖拽排序"><Rank /></el-icon>
    </div>
    <h3>{{ material.title }}</h3>
    <p class="muted">{{ material.folder_name || '未分类' }}</p>
    <p class="material-summary">{{ material.summary || material.error_message || '暂无摘要' }}</p>
    <div class="keyword-list">
      <el-tag v-for="keyword in visibleKeywords" :key="keyword">{{ keyword }}</el-tag>
      <span v-if="extraKeywordCount" class="muted">+{{ extraKeywordCount }}</span>
    </div>
    <div class="material-meta-row">
      <span>切片 {{ material.chunk_count || 0 }}</span>
      <span>视觉资产 {{ material.visual_asset_count || 0 }}</span>
    </div>
    <div class="material-card-actions">
      <el-button @click="$emit('view', material)">查看详情</el-button>
      <el-button type="primary" :disabled="material.status !== 'ready'" @click="$emit('ask', material)">
        {{ material.status === 'ready' ? '向 AI 提问' : '暂不可问答' }}
      </el-button>
      <el-dropdown trigger="click" @command="(command) => $emit(command, material)">
        <el-button>更多</el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="move">移动资料</el-dropdown-item>
            <el-dropdown-item command="reindex">重建索引</el-dropdown-item>
            <el-dropdown-item command="remove">删除</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </article>
</template>

<script setup>
import { Rank, Refresh } from '@element-plus/icons-vue'
import { computed } from 'vue'
import StatusBadge from './StatusBadge.vue'

const props = defineProps({
  material: { type: Object, required: true },
  sortable: { type: Boolean, default: false }
})
defineEmits(['view', 'ask', 'move', 'reindex', 'remove'])

const visibleKeywords = computed(() => (props.material.keywords || []).slice(0, 4))
const extraKeywordCount = computed(() => Math.max((props.material.keywords || []).length - 4, 0))
const isReindexing = computed(() => {
  return props.material.index_state === 'queued' || props.material.index_state === 'running' || props.material.status === 'processing'
})
</script>
