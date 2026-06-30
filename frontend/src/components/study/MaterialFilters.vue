<template>
  <div class="material-filters">
    <el-input :model-value="q" placeholder="搜索标题、关键词、摘要" clearable @update:model-value="$emit('update:q', $event)" />
    <el-select :model-value="status" clearable placeholder="状态" @update:model-value="$emit('update:status', $event)">
      <el-option label="已可提问" value="ready" />
      <el-option label="处理中" value="processing" />
      <el-option label="处理失败" value="failed" />
    </el-select>
    <el-select :model-value="fileType" clearable placeholder="类型" @update:model-value="$emit('update:fileType', $event)">
      <el-option v-for="type in fileTypes" :key="type" :label="type.toUpperCase()" :value="type" />
    </el-select>
    <el-select :model-value="sort" placeholder="排序" @update:model-value="$emit('update:sort', $event)">
      <el-option label="自定义排序" value="custom" />
      <el-option label="最新上传" value="created_desc" />
      <el-option label="标题 A-Z" value="title_asc" />
      <el-option label="状态优先" value="status" />
      <el-option label="资料丰富度" value="richness_desc" />
    </el-select>
    <el-select :model-value="hasVisualAssets" clearable placeholder="视觉资产" @update:model-value="$emit('update:hasVisualAssets', $event)">
      <el-option label="含视觉资产" :value="true" />
      <el-option label="无视觉资产" :value="false" />
    </el-select>
    <el-segmented :model-value="viewMode" :options="viewOptions" @update:model-value="$emit('update:viewMode', $event)" />
  </div>
</template>

<script setup>
defineProps({
  q: { type: String, default: '' },
  status: { type: String, default: '' },
  fileType: { type: String, default: '' },
  sort: { type: String, default: 'created_desc' },
  viewMode: { type: String, default: 'cards' },
  hasVisualAssets: { type: [Boolean, String], default: null },
  fileTypes: { type: Array, default: () => [] }
})
defineEmits(['update:q', 'update:status', 'update:fileType', 'update:sort', 'update:viewMode', 'update:hasVisualAssets'])
const viewOptions = [{ label: '资料库', value: 'cards' }, { label: '管理表格', value: 'table' }]
</script>
