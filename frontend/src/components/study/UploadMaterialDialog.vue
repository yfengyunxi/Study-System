<template>
  <el-dialog :model-value="modelValue" title="上传资料" width="480px" @update:model-value="$emit('update:modelValue', $event)">
    <div class="status-banner warning dialog-tip">
      上传后会同步解析、切片并建立索引。大文件可能需要等待；默认建议不超过 30MB。
    </div>
    <el-form label-position="top">
      <el-form-item label="所属文件夹">
        <el-select :model-value="folderId" clearable placeholder="未分类" class="full-width" @update:model-value="$emit('update:folderId', $event)">
          <el-option v-for="folder in folders" :key="folder.id" :label="folder.name" :value="folder.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="资料文件" required>
        <el-upload ref="uploadRef" :auto-upload="false" :limit="1" accept=".pdf,.doc,.docx,.txt,.md,.markdown,.pptx,.xlsx" :on-change="selectFile" :on-remove="clearFile">
          <el-button>选择资料文件</el-button>
          <template #tip>
            <div class="el-upload__tip">支持 PDF、Word、TXT、Markdown、PPTX、XLSX。</div>
          </template>
        </el-upload>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="uploading" @click="$emit('submit')">上传并处理</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  modelValue: { type: Boolean, default: false },
  folders: { type: Array, default: () => [] },
  folderId: { type: [Number, null], default: null },
  uploading: { type: Boolean, default: false }
})
const emit = defineEmits(['update:modelValue', 'update:folderId', 'selectFile', 'clearFile', 'submit'])
const uploadRef = ref(null)

function selectFile(file) {
  emit('selectFile', file.raw)
}

function clearFile() {
  emit('clearFile')
}

defineExpose({ clearFiles: () => uploadRef.value?.clearFiles() })
</script>
