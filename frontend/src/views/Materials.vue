<template>
  <AppLayout>
    <PageHeader
      kicker="Knowledge Library"
      title="知识库"
      subtitle="把课程资料按文件夹整理好，之后就能直接向知识库提问。"
    >
      <template #actions>
        <el-button :icon="FolderAdd" @click="openFolderDialog()">新建文件夹</el-button>
        <el-button type="primary" :icon="Upload" :loading="uploading" @click="openUploadDialog">
          上传资料
        </el-button>
      </template>
    </PageHeader>

    <MoveMaterialDialog
      v-model="moveDialog"
      v-model:folder-id="moveTargetFolderId"
      :material="moveTargetMaterial"
      :folders="folders"
      :loading="moving"
      @submit="moveMaterial"
    />

    <div class="material-layout">
      <WorkbenchPanel title="资料文件夹" subtitle="选择范围后右侧列表会自动更新。" class="folder-panel">
        <FolderShelf
          :folders="folders"
          :selected="selectedFolderId"
          :total-count="totalCount"
          :uncategorized-count="uncategorizedCount"
          @select="selectFolder"
          @edit="openFolderDialog"
          @delete="deleteFolder"
        />
      </WorkbenchPanel>

      <WorkbenchPanel :title="currentFolderName" :subtitle="`当前展示 ${visibleMaterials.length} 个资料，已完成处理的资料可用于 AI 问答。`">
        <template #actions>
          <el-button :icon="Refresh" :loading="loading" @click="load">刷新</el-button>
        </template>

        <div v-if="uploadStatus" :class="['status-banner', uploadStatus.type]">
          <span>{{ uploadStatus.message }}</span>
        </div>

        <MaterialFilters
          v-model:q="q"
          v-model:status="statusFilter"
          v-model:file-type="fileTypeFilter"
          v-model:sort="sortKey"
          v-model:view-mode="viewMode"
          v-model:has-visual-assets="hasVisualAssets"
          :file-types="fileTypes"
          class="section-gap"
        />

        <EmptyGuide v-if="!loading && !visibleMaterials.length" class="section-gap" title="这里还没有资料" description="上传第一份课程资料，系统会自动摘要、切片并建立可提问的知识库。">
          <template #action>
            <el-button type="primary" @click="openUploadDialog">上传资料</el-button>
          </template>
        </EmptyGuide>

        <div v-else-if="viewMode === 'cards'" class="material-card-grid section-gap" v-loading="loading">
          <MaterialCard
            v-for="material in visibleMaterials"
            :key="material.id"
            :material="material"
            @view="goDetail"
            @ask="goAsk"
            @move="openMoveDialog"
            @reindex="reindex"
            @remove="removeMaterial"
          />
        </div>
        <div v-else class="table-wrap section-gap">
          <el-table :data="visibleMaterials" v-loading="loading">
            <el-table-column prop="title" label="标题" min-width="180" />
            <el-table-column prop="folder_name" label="文件夹" width="140">
              <template #default="{ row }">{{ row.folder_name || '未分类' }}</template>
            </el-table-column>
            <el-table-column prop="file_type" label="类型" width="90" />
            <el-table-column label="状态" width="120">
              <template #default="{ row }"><StatusBadge :code="row.status" /></template>
            </el-table-column>
            <el-table-column label="知识状态" min-width="150">
              <template #default="{ row }">
                <span>切片 {{ row.chunk_count || 0 }} · 图 {{ row.visual_asset_count || 0 }}</span>
              </template>
            </el-table-column>
            <el-table-column label="关键词" min-width="220">
              <template #default="{ row }">
                <div class="keyword-list">
                  <el-tag v-for="keyword in row.keywords" :key="keyword">{{ keyword }}</el-tag>
                  <span v-if="!row.keywords?.length" class="muted">暂无关键词</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="300">
              <template #default="{ row }">
                <el-button :icon="View" @click="goDetail(row)">查看</el-button>
                <el-button :icon="ChatDotRound" :disabled="row.status !== 'ready'" @click="goAsk(row)">问答</el-button>
                <el-button :icon="Refresh" @click="reindex(row)">重建</el-button>
                <el-button :icon="Delete" type="danger" @click="removeMaterial(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </WorkbenchPanel>
    </div>

    <el-dialog v-model="folderDialog" :title="editingFolder ? '重命名文件夹' : '新建文件夹'" width="420px">
      <el-form :model="folderForm" label-position="top">
        <el-form-item label="文件夹名称" required>
          <el-input v-model="folderForm.name" placeholder="例如：数据库系统" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="folderForm.description" type="textarea" placeholder="可选，用来记录这个文件夹的学习范围" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="folderDialog = false">取消</el-button>
        <el-button type="primary" @click="saveFolder">保存</el-button>
      </template>
    </el-dialog>

    <UploadMaterialDialog
      ref="uploadDialogRef"
      v-model="uploadDialog"
      v-model:folder-id="uploadForm.folder_id"
      :folders="folders"
      :uploading="uploading"
      @select-file="selectFile"
      @clear-file="clearFile"
      @submit="upload"
    />
  </AppLayout>
</template>

<script setup>
import { ChatDotRound, Delete, FolderAdd, Refresh, Upload, View } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { folderApi, materialApi } from '../api/modules'
import AppLayout from '../components/AppLayout.vue'
import EmptyGuide from '../components/study/EmptyGuide.vue'
import FolderShelf from '../components/study/FolderShelf.vue'
import MaterialCard from '../components/study/MaterialCard.vue'
import MaterialFilters from '../components/study/MaterialFilters.vue'
import MoveMaterialDialog from '../components/study/MoveMaterialDialog.vue'
import PageHeader from '../components/study/PageHeader.vue'
import StatusBadge from '../components/study/StatusBadge.vue'
import UploadMaterialDialog from '../components/study/UploadMaterialDialog.vue'
import WorkbenchPanel from '../components/study/WorkbenchPanel.vue'

const route = useRoute()
const router = useRouter()
const allMaterials = ref([])
const folders = ref([])
const loading = ref(false)
const uploading = ref(false)
const uploadDialog = ref(false)
const uploadDialogRef = ref(null)
const folderDialog = ref(false)
const editingFolder = ref(null)
const selectedFolderId = ref(null)
const uploadStatus = ref(null)
const viewMode = ref(localStorage.getItem('studyhub.materialViewMode') || 'cards')
const q = ref(String(route.query.q || ''))
const statusFilter = ref(String(route.query.status || ''))
const fileTypeFilter = ref('')
const sortKey = ref('created_desc')
const hasVisualAssets = ref(null)
const uploadForm = reactive({ file: null, folder_id: null })
const folderForm = reactive({ name: '', description: '' })
const moveDialog = ref(false)
const moveTargetFolderId = ref(null)
const moveTargetMaterial = ref(null)
const moving = ref(false)
const reindexTimers = new Map()

const totalCount = computed(() => allMaterials.value.length || folders.value.reduce((sum, folder) => sum + (folder.material_count || 0), 0))
const uncategorizedCount = computed(() => allMaterials.value.filter((item) => !item.folder_id).length)
const currentFolderName = computed(() => {
  if (selectedFolderId.value === null) return '全部资料'
  if (selectedFolderId.value === 'uncategorized') return '未分类'
  return folders.value.find((folder) => folder.id === selectedFolderId.value)?.name || '当前文件夹'
})
const fileTypes = computed(() => [...new Set(allMaterials.value.map((item) => item.file_type).filter(Boolean))].sort())
const visibleMaterials = computed(() => {
  let rows = [...allMaterials.value]
  if (selectedFolderId.value === 'uncategorized') rows = rows.filter((item) => !item.folder_id)
  if (typeof selectedFolderId.value === 'number') rows = rows.filter((item) => item.folder_id === selectedFolderId.value)
  const needle = q.value.trim().toLowerCase()
  if (needle) {
    rows = rows.filter((item) => [item.title, item.file_name, item.folder_name, item.summary, item.error_message, ...(item.keywords || [])].join(' ').toLowerCase().includes(needle))
  }
  if (statusFilter.value) rows = rows.filter((item) => item.status === statusFilter.value)
  if (fileTypeFilter.value) rows = rows.filter((item) => item.file_type === fileTypeFilter.value)
  if (hasVisualAssets.value === true) rows = rows.filter((item) => (item.visual_asset_count || 0) > 0)
  if (hasVisualAssets.value === false) rows = rows.filter((item) => (item.visual_asset_count || 0) === 0)
  const richness = (item) => (item.chunk_count || 0) + (item.visual_asset_count || 0) * 3 + Math.min((item.keywords || []).length, 5)
  rows.sort((a, b) => {
    if (sortKey.value === 'title_asc') return a.title.localeCompare(b.title, 'zh-CN')
    if (sortKey.value === 'status') return (a.status || '').localeCompare(b.status || '')
    if (sortKey.value === 'richness_desc') return richness(b) - richness(a)
    return new Date(b.updated_at || b.created_at || 0) - new Date(a.updated_at || a.created_at || 0)
  })
  return rows
})

watch(viewMode, (value) => localStorage.setItem('studyhub.materialViewMode', value))

async function loadFolders() {
  folders.value = await folderApi.list()
}

async function loadMaterials() {
  allMaterials.value = await materialApi.list()
}

async function load() {
  loading.value = true
  try {
    await Promise.all([loadFolders(), loadMaterials()])
    if (route.query.upload === '1') openUploadDialog()
  } finally {
    loading.value = false
  }
}

function openUploadDialog() {
  uploadDialog.value = true
}

function selectFolder(folderId) {
  selectedFolderId.value = folderId
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
  await load()
}

async function deleteFolder(folder) {
  await ElMessageBox.confirm('删除文件夹后，里面的资料会移动到未分类，确认继续？', '删除文件夹')
  await folderApi.remove(folder.id)
  if (selectedFolderId.value === folder.id) selectedFolderId.value = null
  ElMessage.success('文件夹已删除')
  await load()
}

function selectFile(file) {
  uploadForm.file = file
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
  uploadStatus.value = { type: 'warning', message: '资料正在上传和处理，请不要关闭页面。' }
  const form = new FormData()
  form.append('file', uploadForm.file)
  form.append('title', uploadForm.file.name.replace(/\.[^.]+$/, ''))
  if (uploadForm.folder_id !== null && uploadForm.folder_id !== undefined) {
    form.append('folder_id', uploadForm.folder_id)
  }
  try {
    const result = await materialApi.upload(form)
    showUploadResult(result)
    uploadDialog.value = false
    uploadForm.file = null
    uploadDialogRef.value?.clearFiles()
    await load()
  } finally {
    uploading.value = false
  }
}

function showUploadResult(material) {
  if (material?.status === 'failed') {
    uploadStatus.value = { type: 'danger', message: `“${material.title || '资料'}”上传完成，但处理失败：${material.error_message || '请查看详情或重新上传。'}` }
    ElMessage.error('资料处理失败')
    return
  }
  if (material?.status === 'processing') {
    uploadStatus.value = { type: 'warning', message: `“${material.title || '资料'}”已上传，仍在处理中，稍后刷新查看状态。` }
    ElMessage.warning('资料仍在处理中')
    return
  }
  uploadStatus.value = { type: '', message: `“${material?.title || '资料'}”已上传并处理完成，可以开始问答。` }
  ElMessage.success('上传并处理完成')
}

function goDetail(material) {
  router.push(`/materials/${material.id}`)
}

function goAsk(material) {
  if (material.status !== 'ready') return
  router.push(`/chat?scope_type=material&material_id=${material.id}`)
}

function openMoveDialog(material) {
  moveTargetMaterial.value = material
  moveTargetFolderId.value = material.folder_id
  moveDialog.value = true
}

async function moveMaterial(targetFolderId) {
  moving.value = true
  try {
    const result = await materialApi.moveFolder(moveTargetMaterial.value.id, { folder_id: targetFolderId })
    moveDialog.value = false
    ElMessage.success(result.changed ? result.message : '资料已在目标文件夹')
    mergeMaterial(result.material)
    await loadFolders()
  } catch (error) {
    // error already toasted
  } finally {
    moving.value = false
  }
}

function mergeMaterial(updated) {
  const idx = allMaterials.value.findIndex((m) => m.id === updated.id)
  if (idx > -1) allMaterials.value[idx] = updated
}

async function reindex(material) {
  const result = await materialApi.reindex(material.id)
  mergeMaterial(result.material)
  startReindexPolling(material.id)
  ElMessage.info('索引重建已开始')
}

function startReindexPolling(materialId) {
  stopReindexPolling(materialId)
  let elapsed = 0
  const interval = 2000
  const maxTime = 300000
  reindexTimers.set(
    materialId,
    setInterval(async () => {
      elapsed += interval
      if (elapsed > maxTime) {
        stopReindexPolling(materialId)
        return
      }
      if (elapsed > 60000) {
        // slow down after 60s
        clearInterval(reindexTimers.get(materialId))
        reindexTimers.set(
          materialId,
          setInterval(() => pollReindexStatus(materialId), 5000)
        )
        return
      }
      await pollReindexStatus(materialId)
    }, interval)
  )
}

function stopReindexPolling(materialId) {
  if (reindexTimers.has(materialId)) {
    clearInterval(reindexTimers.get(materialId))
    reindexTimers.delete(materialId)
  }
}

async function pollReindexStatus(materialId) {
  try {
    const status = await materialApi.indexStatus(materialId)
    const material = allMaterials.value.find((m) => m.id === materialId)
    if (material) {
      material.index_state = status.index_state
      material.status = status.status
      material.active_index_generation = status.active_index_generation
      if (['succeeded', 'failed', 'cancelled', 'stale'].includes(status.job?.status)) {
        stopReindexPolling(materialId)
        ElMessage(status.job?.status === 'succeeded' ? '索引重建完成' : '索引重建失败')
        await load()
      }
    }
  } catch {
    stopReindexPolling(materialId)
  }
}

async function removeMaterial(material) {
  await ElMessageBox.confirm('确认删除该资料及其知识库索引？', '删除资料')
  await materialApi.remove(material.id)
  ElMessage.success('删除成功')
  await load()
}

onMounted(load)
onBeforeUnmount(() => {
  reindexTimers.forEach((timer) => clearInterval(timer))
  reindexTimers.clear()
})
</script>
