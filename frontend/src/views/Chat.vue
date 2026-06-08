<template>
  <AppLayout>
    <div class="page-heading">
      <div>
        <p class="page-kicker">AI Study Chat</p>
        <h1 class="page-title">AI 问答</h1>
        <p class="page-subtitle">选择资料范围后提问，AI 会结合文本片段和视觉资料给出回答。</p>
      </div>
      <el-tag size="large">{{ currentScopeText }}</el-tag>
    </div>

    <div class="chat-layout">
      <div class="panel chat-sidebar">
        <h3 class="panel-title">问答范围</h3>
        <p class="panel-subtitle">默认会从全部已处理资料中检索，也可以缩小到文件夹或单份资料。</p>
        <el-radio-group v-model="scopeType" class="scope-radios" @change="handleScopeChange">
          <el-radio-button label="all">全部</el-radio-button>
          <el-radio-button label="folder">文件夹</el-radio-button>
          <el-radio-button label="material">单份资料</el-radio-button>
        </el-radio-group>

        <el-select
          v-if="scopeType === 'folder'"
          v-model="selectedFolder"
          clearable
          placeholder="选择文件夹"
          class="full-width"
        >
          <el-option v-for="folder in folders" :key="folder.id" :label="folder.name" :value="folder.id" />
        </el-select>

        <el-select
          v-if="scopeType === 'material'"
          v-model="selectedMaterial"
          clearable
          placeholder="选择资料"
          class="full-width"
        >
          <el-option
            v-for="material in readyMaterials"
            :key="material.id"
            :label="`${material.folder_name || '未分类'} / ${material.title}`"
            :value="material.id"
          />
        </el-select>

        <div v-if="!isScopeReady" class="status-banner warning section-gap">
          {{ scopeType === 'folder' ? '请选择一个文件夹后再提问。' : '请选择一份已完成处理的资料后再提问。' }}
        </div>
        <div v-else class="status-banner section-gap">
          当前范围：{{ currentScopeText }}
        </div>

        <div class="toolbar section-gap">
          <h3 class="panel-title">历史记录</h3>
        </div>
        <el-empty v-if="!history.length" description="暂无历史" />
        <el-scrollbar v-else height="430px">
          <div class="history-list">
            <button
              v-for="item in history"
              :key="item.id"
              type="button"
              class="history-item"
              @click="loadHistory(item)"
            >
              <strong>{{ item.question }}</strong>
              <p class="muted">{{ item.answer.slice(0, 58) }}</p>
            </button>
          </div>
        </el-scrollbar>
      </div>

      <div class="panel chat-window">
        <div class="messages">
          <el-empty
            v-if="!messages.length && !asking"
            description="可以直接向全部资料提问，也可以选择文件夹或单份资料。"
          />
          <template v-for="(message, index) in messages" :key="index">
            <div :class="['message', message.role, { error: message.error }]">{{ message.content }}</div>
            <div v-if="message.role === 'assistant'" class="message-actions">
              <el-button size="small" @click="copyAnswer(message.content)">复制答案</el-button>
              <el-button v-if="message.error && lastFailedQuestion" size="small" type="primary" :loading="asking" @click="retryLastFailed">
                重试问题
              </el-button>
            </div>
            <div v-if="message.references?.length" class="section-gap">
              <el-collapse>
                <el-collapse-item :title="`查看引用来源（${message.references.length}）`">
                  <div
                    v-for="ref in message.references"
                    :key="referenceKey(ref)"
                    class="source-card"
                  >
                    <strong>
                      {{ ref.folder_name || '未分类' }} / {{ ref.title || `资料 ${ref.material_id}` }}
                      <template v-if="ref.type === 'image'">
                        · 视觉资料 {{ ref.page_number ? `第 ${ref.page_number} 页` : ref.asset_index + 1 }}
                      </template>
                      <template v-else>
                        · 片段 {{ ref.chunk_index + 1 }}
                      </template>
                    </strong>
                    <template v-if="ref.type === 'image'">
                      <p>{{ ref.caption }}</p>
                      <img
                        v-if="referenceImageUrls[ref.asset_id]"
                        :src="referenceImageUrls[ref.asset_id]"
                        :alt="ref.caption"
                        class="reference-image"
                      />
                    </template>
                    <p v-else>{{ ref.content }}</p>
                  </div>
                </el-collapse-item>
              </el-collapse>
            </div>
          </template>
          <div v-if="asking" class="message assistant" role="status" aria-live="polite">
            <span class="thinking-message">
              AI 正在整理资料并思考
              <span class="thinking-dot"></span>
              <span class="thinking-dot"></span>
              <span class="thinking-dot"></span>
            </span>
          </div>
        </div>
        <div class="chat-input">
          <el-input
            v-model="question"
            type="textarea"
            :rows="2"
            resize="none"
            placeholder="请输入学习问题，例如：这个文件夹下的资料主要讲了什么？"
            @keydown.ctrl.enter="ask"
          />
          <el-button type="primary" :loading="asking" :disabled="!canSend" :icon="Promotion" @click="ask">发送</el-button>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { Promotion } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { chatApi, folderApi, materialApi } from '../api/modules'
import AppLayout from '../components/AppLayout.vue'

const route = useRoute()
const materials = ref([])
const folders = ref([])
const history = ref([])
const messages = ref([])
const question = ref('')
const scopeType = ref('all')
const selectedFolder = ref(null)
const selectedMaterial = ref(null)
const asking = ref(false)
const referenceImageUrls = ref({})
const lastFailedQuestion = ref('')

const readyMaterials = computed(() => materials.value.filter((item) => item.status === 'ready'))
const selectedFolderName = computed(() => folders.value.find((folder) => folder.id === selectedFolder.value)?.name)
const selectedMaterialName = computed(() => materials.value.find((material) => material.id === selectedMaterial.value)?.title)
const isScopeReady = computed(() => {
  if (scopeType.value === 'folder') return Boolean(selectedFolder.value)
  if (scopeType.value === 'material') return Boolean(selectedMaterial.value)
  return true
})
const canSend = computed(() => Boolean(question.value.trim()) && isScopeReady.value && !asking.value)
const currentScopeText = computed(() => {
  if (scopeType.value === 'folder') return selectedFolderName.value ? `文件夹：${selectedFolderName.value}` : '文件夹范围未选择'
  if (scopeType.value === 'material') return selectedMaterialName.value ? `资料：${selectedMaterialName.value}` : '单份资料未选择'
  return '全部已处理资料'
})

async function load() {
  folders.value = await folderApi.list()
  materials.value = await materialApi.list()
  history.value = await chatApi.history()

  const routeMaterial = Number(route.query.material_id)
  if (routeMaterial) {
    const material = readyMaterials.value.find((item) => item.id === routeMaterial)
    if (material) {
      scopeType.value = 'material'
      selectedMaterial.value = routeMaterial
    } else {
      ElMessage.warning('链接中的资料不存在或尚未处理完成，已切回全部资料范围')
      scopeType.value = 'all'
      selectedMaterial.value = null
    }
  }

  const routeFolder = Number(route.query.folder_id)
  if (routeFolder) {
    const folder = folders.value.find((item) => item.id === routeFolder)
    if (folder) {
      scopeType.value = 'folder'
      selectedFolder.value = routeFolder
    } else {
      ElMessage.warning('链接中的文件夹不存在，已切回全部资料范围')
      scopeType.value = 'all'
      selectedFolder.value = null
    }
  }
}

function handleScopeChange() {
  selectedFolder.value = null
  selectedMaterial.value = null
}

async function ask() {
  const text = question.value.trim()
  if (!text) {
    ElMessage.warning('请输入问题')
    return
  }
  if (!isScopeReady.value) {
    ElMessage.warning(scopeType.value === 'folder' ? '请选择文件夹' : '请选择资料')
    return
  }

  const conversation = messages.value
    .filter((message) => ['user', 'assistant'].includes(message.role) && !message.error)
    .slice(-8)
    .map((message) => ({ role: message.role, content: message.content }))

  messages.value.push({ role: 'user', content: text })
  question.value = ''
  asking.value = true
  try {
    const payload = { question: text, conversation }
    if (scopeType.value === 'folder') {
      payload.folder_id = selectedFolder.value
    }
    if (scopeType.value === 'material') {
      payload.material_id = selectedMaterial.value
    }
    const result = await chatApi.ask(payload)
    messages.value.push({ role: 'assistant', content: result.answer, references: result.references })
    lastFailedQuestion.value = ''
    await loadReferenceImages(result.references)
    history.value.unshift(result)
  } catch (error) {
    lastFailedQuestion.value = text
    messages.value.push({ role: 'assistant', error: true, content: '这次问答没有成功。可以检查资料范围后重试，或稍后再试。' })
  } finally {
    asking.value = false
  }
}

function retryLastFailed() {
  if (!lastFailedQuestion.value || asking.value) return
  question.value = lastFailedQuestion.value
  ask()
}

async function copyAnswer(content) {
  try {
    await navigator.clipboard.writeText(content)
    ElMessage.success('答案已复制')
  } catch (error) {
    ElMessage.error('复制失败，请手动选择文本')
  }
}

function loadHistory(item) {
  messages.value = [
    { role: 'user', content: item.question },
    { role: 'assistant', content: item.answer, references: item.references }
  ]
  loadReferenceImages(item.references).catch(() => {})
  selectedFolder.value = null
  selectedMaterial.value = null
  if (item.material_id && readyMaterials.value.some((material) => material.id === item.material_id)) {
    scopeType.value = 'material'
    selectedMaterial.value = item.material_id
  } else {
    scopeType.value = 'all'
  }
}

async function loadReferenceImages(references = []) {
  const imageReferences = references.filter((ref) => ref.type === 'image' && ref.asset_id && !referenceImageUrls.value[ref.asset_id])
  const entries = await Promise.all(
    imageReferences.map(async (ref) => {
      try {
        const blob = await materialApi.assetImage(ref.asset_id)
        return [ref.asset_id, URL.createObjectURL(blob)]
      } catch (error) {
        return null
      }
    })
  )
  referenceImageUrls.value = {
    ...referenceImageUrls.value,
    ...Object.fromEntries(entries.filter(Boolean))
  }
}

function referenceKey(ref) {
  return ref.type === 'image'
    ? `image-${ref.asset_id}`
    : `text-${ref.material_id}-${ref.chunk_index}`
}

function releaseReferenceImages() {
  Object.values(referenceImageUrls.value).forEach((url) => URL.revokeObjectURL(url))
  referenceImageUrls.value = {}
}

onMounted(load)
onBeforeUnmount(releaseReferenceImages)
</script>
