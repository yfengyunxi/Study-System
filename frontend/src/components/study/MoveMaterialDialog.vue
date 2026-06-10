<template>
  <el-dialog
    :model-value="modelValue"
    title="移动资料"
    width="420px"
    :close-on-click-modal="false"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <p>将 <strong>{{ material?.title || '资料' }}</strong> 移动到：</p>
    <el-select
      :model-value="folderId"
      placeholder="选择目标文件夹"
      class="full-width"
      :disabled="loading"
      @update:model-value="$emit('update:folderId', $event)"
    >
      <el-option label="未分类" :value="null" />
      <el-option
        v-for="folder in folders"
        :key="folder.id"
        :label="folder.name"
        :value="folder.id"
      />
    </el-select>
    <template #footer>
      <el-button :disabled="loading" @click="$emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="loading" @click="$emit('submit', folderId)">确定移动</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
defineProps({
  modelValue: { type: Boolean, default: false },
  folderId: { type: [Number, null], default: null },
  material: { type: Object, default: null },
  folders: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false }
})

defineEmits(['update:modelValue', 'update:folderId', 'submit'])
</script>
