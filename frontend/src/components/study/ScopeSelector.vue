<template>
  <div class="scope-selector">
    <el-select :model-value="scopeType" placeholder="选择范围" class="full-width" @update:model-value="$emit('update:scopeType', $event)">
      <el-option v-for="opt in scopeOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
    </el-select>
    <el-select v-if="scopeType === 'folder'" :model-value="folderId" clearable placeholder="选择文件夹" class="full-width" @update:model-value="$emit('update:folderId', $event)">
      <el-option v-for="folder in folders" :key="folder.id" :label="folder.name" :value="folder.id" />
    </el-select>
    <el-select v-if="scopeType === 'material'" :model-value="materialId" clearable placeholder="选择资料" class="full-width" @update:model-value="$emit('update:materialId', $event)">
      <el-option v-for="material in readyMaterials" :key="material.id" :label="`${material.folder_name || '未分类'} / ${material.title}`" :value="material.id" />
    </el-select>
  </div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({
  scopeType: { type: String, default: 'all' },
  folderId: { type: [Number, null], default: null },
  materialId: { type: [Number, null], default: null },
  folders: { type: Array, default: () => [] },
  materials: { type: Array, default: () => [] }
})
defineEmits(['update:scopeType', 'update:folderId', 'update:materialId'])
const scopeOptions = [
  { label: '通用问答', value: 'general' },
  { label: '全部资料', value: 'all' },
  { label: '按文件夹', value: 'folder' },
  { label: '单份资料', value: 'material' },
  { label: '未分类', value: 'uncategorized' }
]
const readyMaterials = computed(() => props.materials.filter((item) => item.status === 'ready'))
</script>
