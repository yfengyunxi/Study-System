<template>
  <AppLayout>
    <PageHeader
      kicker="AI Study Session"
      title="AI 学习会话"
      subtitle="明确选择通用、全部资料、文件夹或单资料范围，回答会把证据和正文分开呈现。"
    >
      <template #actions>
        <el-tag size="large">{{ currentScopeText }}</el-tag>
      </template>
    </PageHeader>

    <div class="chat-layout chat-workbench">
      <aside class="panel chat-sidebar">
        <h3 class="panel-title">历史问答</h3>
        <p class="panel-subtitle">点击历史会话继续学习，旧记录自动迁移。</p>
        <el-button class="full-width" :icon="Plus" @click="createNewConversation">新建会话</el-button>
        <el-empty v-if="!conversations.length" description="暂无历史会话" />
        <el-scrollbar v-else height="480px" class="section-gap">
          <button
            v-for="conv in conversations"
            :key="conv.id"
            type="button"
            :class="['history-item', { active: activeConversation?.id === conv.id }]"
            @click="switchConversation(conv)"
          >
            <strong>{{ conv.title }}</strong>
            <p class="muted">{{ conv.updated_at?.slice(0, 16) || conv.created_at?.slice(0, 16) }}</p>
          </button>
        </el-scrollbar>
      </aside>

      <section class="panel chat-window">
        <div v-if="scopeBanner" class="status-banner warning">{{ scopeBanner }}</div>
        <div class="messages">
          <el-empty v-if="!messages.length && !asking" description="选择范围后开始提问，通用问答不会显示资料引用。" />
          <template v-for="(message, index) in messages" :key="message.id || index">
            <MessageBubble :role="message.role" :content="message.content" :error="message.error" />
            <div v-if="message.role === 'assistant'" class="message-actions">
              <el-button size="small" @click="copyAnswer(message.content)">复制答案</el-button>
              <el-button v-if="message.status === 'failed_timeout' || message.status === 'failed_error'" size="small" type="primary" :loading="retryingId === message.id" @click="retryFailed(message)">重试</el-button>
              <el-button v-if="activeConversation" size="small" type="danger" :icon="Delete" @click="confirmDeleteConversation">删除会话</el-button>
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
          <el-input v-model="question" type="textarea" :rows="2" resize="none" placeholder="请输入学习问题；Ctrl + Enter 发送" @keydown.ctrl.enter.prevent="ask" />
          <el-button type="primary" :loading="asking" :disabled="!canSend" :icon="Promotion" @click="ask">发送</el-button>
        </div>
      </section>

      <aside class="panel chat-context-panel">
        <h3 class="panel-title">学习范围与证据</h3>
        <p class="panel-subtitle">通用问答不会伪装成资料证据；资料问答会显示可用引用。</p>
        <ScopeSelector :scope-type="scopeType" :folder-id="selectedFolder" :material-id="selectedMaterial" :folders="folders" :materials="materials" @update:scope-type="changeScope" @update:folder-id="selectedFolder = $event" @update:material-id="selectedMaterial = $event" />
        <div v-if="!isScopeReady" class="status-banner warning section-gap">请选择完整范围后再提问。</div>
        <div v-else class="status-banner section-gap">当前范围：{{ currentScopeText }}</div>
        <EvidencePanel class="section-gap" :references="activeReferences" />
      </aside>
    </div>
  </AppLayout>
</template>

<script setup>
import { Delete, Plus, Promotion } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { chatApi, folderApi, materialApi } from '../api/modules'
import AppLayout from '../components/AppLayout.vue'
import EvidencePanel from '../components/study/EvidencePanel.vue'
import MessageBubble from '../components/study/MessageBubble.vue'
import PageHeader from '../components/study/PageHeader.vue'
import ScopeSelector from '../components/study/ScopeSelector.vue'

const route = useRoute()
const materials = ref([])
const folders = ref([])
const conversations = ref([])
const activeConversation = ref(null)
const messages = ref([])
const question = ref('')
const scopeType = ref(localStorage.getItem('studyhub.defaultScope') || 'all')
const selectedFolder = ref(null)
const selectedMaterial = ref(null)
const scopeBanner = ref('')
const asking = ref(false)
const retryingId = ref(null)

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
  if (scopeType.value === 'general') return '通用问答'
  if (scopeType.value === 'folder') return selectedFolderName.value ? `文件夹：${selectedFolderName.value}` : '文件夹范围未选择'
  if (scopeType.value === 'material') return selectedMaterialName.value ? `资料：${selectedMaterialName.value}` : '单份资料未选择'
  return '全部已处理资料'
})
const activeReferences = computed(() => [...messages.value].reverse().find((message) => message.references?.length)?.references || [])

function changeScope(value) {
  scopeType.value = value
  selectedFolder.value = null
  selectedMaterial.value = null
  scopeBanner.value = ''
}

async function load() {
  const [folderRows, materialRows] = await Promise.all([
    folderApi.list(),
    materialApi.list()
  ])
  folders.value = folderRows
  materials.value = materialRows
  await loadConversations()
  applyRouteScope()
}

async function loadConversations() {
  try {
    const result = await chatApi.conversations({ page: 1, limit: 50 })
    conversations.value = result.conversations || []
  } catch {
    // fallback: load legacy history as conversation-like items
    try {
      const rows = await chatApi.history()
      conversations.value = rows.map((item) => ({
        id: item.conversation_id || item.id,
        title: item.question?.slice(0, 40) || '历史问答',
        created_at: item.created_at,
        updated_at: item.created_at
      }))
    } catch {
      // silent
    }
  }
}

async function createNewConversation() {
  const scope = scopeType.value === 'uncategorized'
    ? { scope_type: 'uncategorized', folder_id: null }
    : { scope_type: scopeType.value }
  try {
    const result = await chatApi.createConversation({ title: '新会话', default_scope: scope })
    activeConversation.value = result.conversation
    messages.value = []
    conversations.value.unshift(result.conversation)
  } catch {
    ElMessage.error('创建会话失败')
  }
}

async function switchConversation(conv) {
  activeConversation.value = conv
  try {
    const result = await chatApi.messages(conv.id, { page: 1, limit: 50 })
    messages.value = (result.messages || []).map((m) => ({
      id: m.id,
      role: m.role,
      content: m.content,
      status: m.status,
      error_code: m.error_code,
      retryable: m.retryable,
      references: m.citations || m.references || []
    }))
    if (conv.default_scope) {
      scopeType.value = conv.default_scope.scope_type || 'all'
      selectedFolder.value = conv.default_scope.folder_id || null
      selectedMaterial.value = conv.default_scope.material_id || null
    }
  } catch {
    messages.value = []
  }
}

async function confirmDeleteConversation() {
  if (!activeConversation.value) return
  await ElMessageBox.confirm('确认删除此会话？', '删除会话')
  await chatApi.deleteConversation(activeConversation.value.id)
  conversations.value = conversations.value.filter((c) => c.id !== activeConversation.value.id)
  activeConversation.value = null
  messages.value = []
  ElMessage.success('会话已删除')
}

function applyRouteScope() {
  const queryScope = String(route.query.scope_type || '')
  if (['general', 'all', 'folder', 'material', 'uncategorized'].includes(queryScope)) {
    scopeType.value = queryScope
  }
  if (route.query.prompt) {
    question.value = String(route.query.prompt)
  }
  const routeMaterial = Number(route.query.material_id)
  if (scopeType.value === 'material' && routeMaterial) {
    const material = readyMaterials.value.find((item) => item.id === routeMaterial)
    if (material) selectedMaterial.value = routeMaterial
    else setScopeFallback('链接中的资料不存在或尚未处理完成，已切回全部资料范围')
  }
  const routeFolder = Number(route.query.folder_id)
  if (scopeType.value === 'folder' && routeFolder) {
    const folder = folders.value.find((item) => item.id === routeFolder)
    if (folder) selectedFolder.value = routeFolder
    else setScopeFallback('链接中的文件夹不存在，已切回全部资料范围')
  }
}

function setScopeFallback(message) {
  scopeBanner.value = message
  scopeType.value = 'all'
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
  if (!activeConversation.value) {
    await createNewConversation()
    if (!activeConversation.value) return
  }

  const requestId = `req-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
  const scope = { scope_type: scopeType.value }
  if (scopeType.value === 'folder' && selectedFolder.value) scope.folder_id = selectedFolder.value
  if (scopeType.value === 'material' && selectedMaterial.value) scope.material_id = selectedMaterial.value

  messages.value.push({ id: `user-${Date.now()}`, role: 'user', content: text, status: 'succeeded' })
  question.value = ''
  asking.value = true
  try {
    const result = await chatApi.sendMessage(activeConversation.value.id, { content: text, scope, request_id: requestId })
    if (result.assistant_message) {
      messages.value.push({
        id: result.assistant_message.id,
        role: 'assistant',
        content: result.assistant_message.content,
        status: result.assistant_message.status,
        error_code: result.assistant_message.error_code,
        retryable: result.assistant_message.retryable,
        references: result.assistant_message.citations || result.assistant_message.references || []
      })
    }
    activeConversation.value.updated_at = new Date().toISOString()
  } catch (error) {
    const isRetryable = error.retryable || error.apiCode === 'AI_TIMEOUT' || error.apiCode === 'UPSTREAM_AI_ERROR'
    messages.value.push({
      id: error.apiError?.assistant_message?.id || `error-${Date.now()}`,
      role: 'assistant',
      content: error.apiMessage || 'AI 问答失败',
      status: isRetryable ? 'failed_timeout' : 'failed_error',
      error_code: error.apiCode,
      retryable: isRetryable
    })
  } finally {
    asking.value = false
  }
}

async function retryFailed(message) {
  if (!message.id || asking.value) return
  retryingId.value = message.id
  try {
    const result = await chatApi.retryMessage(message.id, { request_id: `retry-${Date.now()}-${Math.random().toString(36).slice(2, 8)}` })
    // Remove the failed message and add the new one
    const idx = messages.value.findIndex((m) => m.id === message.id)
    if (idx > -1) messages.value.splice(idx, 1)
    if (result.assistant_message) {
      messages.value.push({
        id: result.assistant_message.id,
        role: 'assistant',
        content: result.assistant_message.content,
        status: result.assistant_message.status,
        references: result.assistant_message.citations || result.assistant_message.references || []
      })
    }
  } catch {
    // error already toasted
  } finally {
    retryingId.value = null
  }
}

async function copyAnswer(content) {
  try {
    await navigator.clipboard.writeText(content)
    ElMessage.success('答案已复制')
  } catch (error) {
    ElMessage.error('复制失败，请手动选择文本')
  }
}

onMounted(load)
</script>
