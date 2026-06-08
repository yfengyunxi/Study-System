<template>
  <AppLayout>
    <div class="toolbar">
      <h1 class="page-title" style="margin: 0">学习资料</h1>
      <el-space>
        <el-button :icon="FolderAdd" @click="openFolderDialog()">新建文件夹</el-button>
        <el-button type="primary" :icon="Upload" :loading="uploading" @click="uploadDialog = true">
          上传资料
        </el-button>
      </el-space>
    </div>

    <div class="material-layout">
      <div class="panel folder-panel">
        <div
          :class="['folder-item', selectedFolderId === null ? 'active' : '']"
          @click="selectFolder(null)"
        >
          <span>全部资料</span>
          <el-tag size="small">{{ totalCount }}</el-tag>
        </div>
        <div
          :class="['folder-item', selectedFolderId === 'uncategorized' ? 'active' : '']"
          @click="selectFolder('uncategorized')"
        >
          <span>未分类</span>
        </div>
        <div
          v-for="folder in folders"
          :key="folder.id"
          :class="['folder-item', selectedFolderId === folder.id ? 'active' : '']"
          @click="selectFolder(folder.id)"
        >
          <span>{{ folder.name }}</span>
          <el-dropdown trigger="click" @command="(command) => handleFolderCommand(command, folder)">
            <el-button text :icon="MoreFilled" @click.stop />
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="edit">重命名</el-dropdown-item>
                <el-dropdown-item command="delete">删除</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>

      <div class="panel">
        <div class="toolbar">
          <div>
            <strong>{{ currentFolderName }}</strong>
            <span class="muted"> · {{ materials.length }} 个资料</span>
          </div>
          <el-button :icon="Refresh" @click="loadMaterials">刷新</el-button>
        </div>

        <el-table :data="materials" v-loading="loading">
          <el-table-column prop="title" label="标题" min-width="180" />
          <el-table-column prop="folder_name" label="文件夹" width="140">
            <template #default="{ row }">{{ row.folder_name || '未分类' }}</template>
          </el-table-column>
          <el-table-column prop="file_type" label="类型" width="90" />
          <el-table-column label="状态" width="120">
            <template #default="{ row }">
              <el-tag :type="row.status === 'ready' ? 'success' : row.status === 'failed' ? 'danger' : 'warning'">
                {{ statusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="关键词" min-width="220">
            <template #default="{ row }">
              <el-tag v-for="keyword in row.keywords" :key="keyword" style="margin-right: 6px">
                {{ keyword }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="260">
            <template #default="{ row }">
              <el-button :icon="View" @click="$router.push(`/materials/${row.id}`)">查看</el-button>
              <el-button :icon="ChatDotRound" @click="$router.push(`/chat?material_id=${row.id}`)">问答</el-button>
              <el-button :icon="Delete" type="danger" @click="remove(row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <el-dialog v-model="folderDialog" :title="editingFolder ? '重命名文件夹' : '新建文件夹'" width="420px">
      <el-form :model="folderForm" label-position="top">
        <el-form-item label="文件夹名称">
          <el-input v-model="folderForm.name" placeholder="例如：数据库系统" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="folderForm.description" type="textarea" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="folderDialog = false">取消</el-button>
        <el-button type="primary" @click="saveFolder">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="uploadDialog" title="上传资料" width="480px">
      <el-form label-position="top">
        <el-form-item label="所属文件夹">
          <el-select v-model="uploadForm.folder_id" clearable placeholder="未分类" style="width: 100%">
            <el-option v-for="folder in folders" :key="folder.id" :label="folder.name" :value="folder.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="资料文件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".pdf,.doc,.docx,.txt,.md,.markdown,.pptx,.xlsx"
            :on-change="selectFile"
            :on-remove="clearFile"
          >
            <el-button :icon="Upload">选择资料文件</el-button>
            <template #tip>
              <div class="el-upload__tip">支持 PDF、Word(doc/docx)、TXT、Markdown、PPTX、XLSX</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadDialog = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="upload">上传</el-button>
      </template>
    </el-dialog>
  </AppLayout>
</template>

<script setup>
import {
  ChatDotRound,
  Delete,
  FolderAdd,
  MoreFilled,
  Refresh,
  Upload,
  View
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'

import { folderApi, materialApi } from '../api/modules'
import AppLayout from '../components/AppLayout.vue'

const materials = ref([])
const folders = ref([])
const loading = ref(false)
const uploading = ref(false)
const uploadDialog = ref(false)
const folderDialog = ref(false)
const editingFolder = ref(null)
const selectedFolderId = ref(null)
const uploadRef = ref(null)
const uploadForm = reactive({ file: null, folder_id: null })
const folderForm = reactive({ name: '', description: '' })

const totalCount = computed(() => folders.value.reduce((sum, folder) => sum + (folder.material_count || 0), 0))
const currentFolderName = computed(() => {
  if (selectedFolderId.value === null) return '全部资料'
  if (selectedFolderId.value === 'uncategorized') return '未分类'
  return folders.value.find((folder) => folder.id === selectedFolderId.value)?.name || '当前文件夹'
})

async function loadFolders() {
  folders.value = await folderApi.list()
}

async function loadMaterials() {
  loading.value = true
  try {
    const params = {}
    if (typeof selectedFolderId.value === 'number') {
      params.folder_id = selectedFolderId.value
    }
    const rows = await materialApi.list(params)
    materials.value = selectedFolderId.value === 'uncategorized'
      ? rows.filter((item) => !item.folder_id)
      : rows
  } finally {
    loading.value = false
  }
}

async function load() {
  await loadFolders()
  await loadMaterials()
}

async function selectFolder(folderId) {
  selectedFolderId.value = folderId
  await loadMaterials()
}

function openFolderDialog(folder = null) {
  editingFolder.value = folder
  folderForm.name = folder?.name || ''
  folderForm.description = folder?.description || ''
  folderDialog.value = true
}

async function saveFolder() {
  if (!folderForm.name.trim()) {
    ElMessage.warning('请输入文件夹名称')
    return
  }
  if (editingFolder.value) {
    await folderApi.update(editingFolder.value.id, folderForm)
    ElMessage.success('文件夹已更新')
  } else {
    await folderApi.create(folderForm)
    ElMessage.success('文件夹已创建')
  }
  folderDialog.value = false
  await loadFolders()
}

async function handleFolderCommand(command, folder) {
  if (command === 'edit') {
    openFolderDialog(folder)
    return
  }
  await ElMessageBox.confirm('删除文件夹后，里面的资料会移动到未分类，确认继续？', '删除文件夹')
  await folderApi.remove(folder.id)
  if (selectedFolderId.value === folder.id) {
    selectedFolderId.value = null
  }
  ElMessage.success('文件夹已删除')
  await load()
}

function selectFile(file) {
  uploadForm.file = file.raw
}

function clearFile() {
  uploadForm.file = null
}

async function upload() {
  if (!uploadForm.file) {
    ElMessage.warning('请选择资料文件')
    return
  }
  uploading.value = true
  const form = new FormData()
  form.append('file', uploadForm.file)
  form.append('title', uploadForm.file.name.replace(/\.[^.]+$/, ''))
  if (uploadForm.folder_id) {
    form.append('folder_id', uploadForm.folder_id)
  }
  try {
    await materialApi.upload(form)
    ElMessage.success('上传并处理成功')
    uploadDialog.value = false
    uploadForm.file = null
    uploadRef.value?.clearFiles()
    await load()
  } finally {
    uploading.value = false
  }
}

async function remove(id) {
  await ElMessageBox.confirm('确认删除该资料及其知识库索引？', '删除资料')
  await materialApi.remove(id)
  ElMessage.success('删除成功')
  await load()
}

function statusText(status) {
  return {
    ready: '已完成',
    processing: '处理中',
    failed: '失败'
  }[status] || status
}

onMounted(load)
</script>
