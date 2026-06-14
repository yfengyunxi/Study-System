<template>
  <AppLayout>
    <PageHeader
      kicker="Profile"
      title="个人设置"
      subtitle="调整昵称、头像、学习目标和本地偏好，让学习工作台更贴近你的习惯。"
    />

    <div class="grid two-col profile-grid">
      <div class="panel profile-card">
        <div class="profile-preview">
          <img
            v-if="avatarSrc"
            :src="avatarSrc"
            alt="头像预览"
            class="profile-avatar"
          />
          <div v-else class="profile-avatar-placeholder" aria-hidden="true">{{ avatarInitial }}</div>
          <div>
            <strong>{{ form.nickname || auth.user?.username || '学习者' }}</strong>
            <p class="panel-subtitle">{{ form.study_goal || '设置一个学习目标，它会显示在顶部栏。' }}</p>
          </div>
        </div>

        <el-form :model="form" label-position="top">
          <el-form-item label="昵称">
            <el-input v-model="form.nickname" placeholder="例如：小林同学" />
          </el-form-item>
          <el-form-item label="头像">
            <div class="avatar-upload">
              <el-upload
                :auto-upload="false"
                :show-file-list="false"
                accept="image/png,image/jpeg,image/gif,image/webp,image/avif"
                :on-change="onAvatarFileChange"
              >
                <el-button :icon="Upload">选择图片</el-button>
              </el-upload>
              <el-button v-if="avatarFile" :icon="Check" type="primary" :loading="uploadingAvatar" @click="uploadAvatar">
                上传头像
              </el-button>
              <span v-if="avatarFile" class="avatar-file-name">{{ avatarFile.name }}</span>
            </div>
            <p class="panel-subtitle">支持 PNG / JPEG / GIF / WebP / AVIF 格式。</p>
          </el-form-item>
          <el-form-item label="学习目标">
            <el-input v-model="form.study_goal" type="textarea" :rows="4" placeholder="例如：本月完成数据库基础和 SQL 练习" />
            <p class="panel-subtitle">学习目标会显示在顶部栏，帮助你进入学习状态。</p>
          </el-form-item>
          <el-button type="primary" :loading="saving" @click="save">保存设置</el-button>
        </el-form>
      </div>

      <WorkbenchPanel title="学习偏好" subtitle="这些偏好先保存在本地浏览器，用于当前学习工作台体验。">
        <el-form label-position="top">
          <el-form-item label="默认问答范围">
            <el-select v-model="defaultScope" class="full-width">
              <el-option label="全部资料" value="all" />
              <el-option label="通用问答" value="general" />
            </el-select>
          </el-form-item>
          <el-form-item label="回答风格">
            <el-select v-model="answerStyle" class="full-width">
              <el-option label="分步骤解释" value="step_by_step" />
              <el-option label="简洁总结" value="concise" />
              <el-option label="考试复习重点" value="exam_review" />
            </el-select>
          </el-form-item>
          <el-form-item label="默认展开证据">
            <el-switch v-model="evidenceExpanded" />
          </el-form-item>
          <el-form-item label="默认任务时长（分钟）">
            <el-input-number v-model="defaultTaskMinutes" :min="10" :max="480" />
          </el-form-item>
          <el-button type="primary" @click="saveLocalPreferences">保存学习偏好</el-button>
        </el-form>
      </WorkbenchPanel>
    </div>

    <WorkbenchPanel title="数据与 AI 说明" subtitle="上传资料仅用于当前账号的知识库检索和个人学习问答。AI 回答会标注可用引用，通用问答不会伪装成资料证据。" class="section-gap" />
  </AppLayout>
</template>

<script setup>
import { Check, Upload } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'

import { authApi } from '../api/modules'
import AppLayout from '../components/AppLayout.vue'
import PageHeader from '../components/study/PageHeader.vue'
import WorkbenchPanel from '../components/study/WorkbenchPanel.vue'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const saving = ref(false)
const uploadingAvatar = ref(false)
const avatarFile = ref(null)
const avatarPreviewUrl = ref(null)
const form = reactive({ nickname: '', study_goal: '' })
const defaultScope = ref(localStorage.getItem('studyhub.defaultScope') || 'all')
const answerStyle = ref(localStorage.getItem('studyhub.answerStyle') || 'step_by_step')
const evidenceExpanded = ref(localStorage.getItem('studyhub.evidenceExpanded') === 'true')
const defaultTaskMinutes = ref(Number(localStorage.getItem('studyhub.defaultTaskMinutes') || 30))
const avatarInitial = computed(() => (form.nickname || auth.user?.username || '学').slice(0, 1).toUpperCase())

// Compute the avatar source: local preview > uploaded path > nothing
const avatarSrc = computed(() => {
  if (avatarPreviewUrl.value) return avatarPreviewUrl.value
  const userAvatar = auth.user?.avatar
  if (userAvatar && userAvatar.startsWith('/api/auth/avatar/')) return userAvatar
  if (userAvatar && (userAvatar.startsWith('http://') || userAvatar.startsWith('https://'))) return userAvatar
  return null
})

onMounted(() => {
  form.nickname = auth.user?.nickname || ''
  form.study_goal = auth.user?.study_goal || ''
})

function onAvatarFileChange(file) {
  // Revoke previous preview URL
  if (avatarPreviewUrl.value) {
    URL.revokeObjectURL(avatarPreviewUrl.value)
  }
  avatarFile.value = file.raw
  avatarPreviewUrl.value = URL.createObjectURL(file.raw)
}

async function uploadAvatar() {
  if (!avatarFile.value) {
    ElMessage.warning('请先选择头像图片')
    return
  }
  uploadingAvatar.value = true
  try {
    const formData = new FormData()
    formData.append('file', avatarFile.value)
    auth.user = await authApi.uploadAvatar(formData)
    localStorage.setItem('user', JSON.stringify(auth.user))
    // Clean up preview
    if (avatarPreviewUrl.value) {
      URL.revokeObjectURL(avatarPreviewUrl.value)
      avatarPreviewUrl.value = null
    }
    avatarFile.value = null
    ElMessage.success('头像已更新')
  } catch {
    // error already toasted
  } finally {
    uploadingAvatar.value = false
  }
}

function saveLocalPreferences() {
  localStorage.setItem('studyhub.defaultScope', defaultScope.value)
  localStorage.setItem('studyhub.answerStyle', answerStyle.value)
  localStorage.setItem('studyhub.evidenceExpanded', String(evidenceExpanded.value))
  localStorage.setItem('studyhub.defaultTaskMinutes', String(defaultTaskMinutes.value || 30))
  ElMessage.success('学习偏好已保存')
}

async function save() {
  saving.value = true
  try {
    const payload = {
      nickname: form.nickname,
      study_goal: form.study_goal
    }
    auth.user = await authApi.updateProfile(payload)
    localStorage.setItem('user', JSON.stringify(auth.user))
    ElMessage.success('设置已保存')
  } finally {
    saving.value = false
  }
}
</script>
