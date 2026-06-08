<template>
  <AppLayout>
    <h1 class="page-title">AI 问答</h1>
    <div class="chat-layout">
      <div class="panel">
        <h3 style="margin-top: 0">问答范围</h3>
        <el-radio-group v-model="scopeType" style="margin-bottom: 12px" @change="handleScopeChange">
          <el-radio-button label="all">全部</el-radio-button>
          <el-radio-button label="folder">文件夹</el-radio-button>
          <el-radio-button label="material">单份资料</el-radio-button>
        </el-radio-group>

        <el-select
          v-if="scopeType === 'folder'"
          v-model="selectedFolder"
          clearable
          placeholder="选择文件夹"
          style="width: 100%; margin-bottom: 12px"
        >
          <el-option v-for="folder in folders" :key="folder.id" :label="folder.name" :value="folder.id" />
        </el-select>

        <el-select
          v-if="scopeType === 'material'"
          v-model="selectedMaterial"
          clearable
          placeholder="选择资料"
          style="width: 100%; margin-bottom: 12px"
        >
          <el-option
            v-for="material in readyMaterials"
            :key="material.id"
            :label="`${material.folder_name || '未分类'} / ${material.title}`"
            :value="material.id"
          />
        </el-select>

        <h3>历史记录</h3>
        <el-empty v-if="!history.length" description="暂无历史" />
        <el-scrollbar v-else height="430px">
          <div
            v-for="item in history"
            :key="item.id"
            class="reference"
            style="cursor: pointer"
            @click="loadHistory(item)"
          >
            <strong>{{ item.question }}</strong>
            <p class="muted">{{ item.answer.slice(0, 50) }}</p>
          </div>
        </el-scrollbar>
      </div>

      <div class="panel chat-window">
        <div class="messages">
          <el-empty v-if="!messages.length" description="选择问答范围后开始提问" />
          <template v-for="(message, index) in messages" :key="index">
            <div :class="['message', message.role]">{{ message.content }}</div>
            <div v-if="message.references?.length" style="margin-bottom: 16px">
              <el-collapse>
                <el-collapse-item title="查看引用片段">
                  <div
                    v-for="ref in message.references"
                    :key="referenceKey(ref)"
                    class="reference"
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
          <el-button type="primary" :loading="asking" :icon="Promotion" @click="ask">发送</el-button>
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

const readyMaterials = computed(() => materials.value.filter((item) => item.status === 'ready'))

async function load() {
  folders.value = await folderApi.list()
  materials.value = await materialApi.list()
  history.value = await chatApi.history()

  const routeMaterial = Number(route.query.material_id)
  if (routeMaterial) {
    scopeType.value = 'material'
    selectedMaterial.value = routeMaterial
  }

  const routeFolder = Number(route.query.folder_id)
  if (routeFolder) {
    scopeType.value = 'folder'
    selectedFolder.value = routeFolder
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
  if (scopeType.value === 'folder' && !selectedFolder.value) {
    ElMessage.warning('请选择文件夹')
    return
  }
  if (scopeType.value === 'material' && !selectedMaterial.value) {
    ElMessage.warning('请选择资料')
    return
  }

  const conversation = messages.value
    .filter((message) => ['user', 'assistant'].includes(message.role))
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
    await loadReferenceImages(result.references)
    history.value.unshift(result)
  } finally {
    asking.value = false
  }
}

function loadHistory(item) {
  messages.value = [
    { role: 'user', content: item.question },
    { role: 'assistant', content: item.answer, references: item.references }
  ]
  loadReferenceImages(item.references).catch(() => {})
  if (item.material_id) {
    scopeType.value = 'material'
    selectedMaterial.value = item.material_id
  }
}

async function loadReferenceImages(references = []) {
  const imageReferences = references.filter((ref) => ref.type === 'image' && ref.asset_id && !referenceImageUrls.value[ref.asset_id])
  const entries = await Promise.all(
    imageReferences.map(async (ref) => {
      const blob = await materialApi.assetImage(ref.asset_id)
      return [ref.asset_id, URL.createObjectURL(blob)]
    })
  )
  referenceImageUrls.value = {
    ...referenceImageUrls.value,
    ...Object.fromEntries(entries)
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
