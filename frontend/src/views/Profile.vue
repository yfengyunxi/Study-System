<template>
  <AppLayout>
    <PageHeader
      kicker="Profile"
      title="个人设置"
      subtitle="调整昵称、头像、学习目标和本地偏好，让学习工作台更贴近你的习惯。"
    />

    <div class="grid two-col">
      <div class="panel profile-card">
        <div class="profile-preview">
          <img
            v-if="form.avatar && avatarPreviewOk"
            :src="form.avatar"
            alt="头像预览"
            class="profile-avatar"
            @error="avatarPreviewOk = false"
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
          <el-form-item label="头像地址">
            <el-input v-model="form.avatar" placeholder="粘贴图片 URL，保存后继续使用" />
            <p class="panel-subtitle">如果填写有效图片地址，上方会立即显示头像预览。</p>
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
import { ElMessage } from 'element-plus'
import { computed, onMounted, reactive, ref, watch } from 'vue'

import { authApi } from '../api/modules'
import AppLayout from '../components/AppLayout.vue'
import PageHeader from '../components/study/PageHeader.vue'
import WorkbenchPanel from '../components/study/WorkbenchPanel.vue'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const saving = ref(false)
const avatarPreviewOk = ref(true)
const form = reactive({ nickname: '', avatar: '', study_goal: '' })
const defaultScope = ref(localStorage.getItem('studyhub.defaultScope') || 'all')
const answerStyle = ref(localStorage.getItem('studyhub.answerStyle') || 'step_by_step')
const evidenceExpanded = ref(localStorage.getItem('studyhub.evidenceExpanded') === 'true')
const defaultTaskMinutes = ref(Number(localStorage.getItem('studyhub.defaultTaskMinutes') || 30))
const avatarInitial = computed(() => (form.nickname || auth.user?.username || '学').slice(0, 1).toUpperCase())

onMounted(() => {
  form.nickname = auth.user?.nickname || ''
  form.avatar = auth.user?.avatar || ''
  form.study_goal = auth.user?.study_goal || ''
})

watch(() => form.avatar, () => {
  avatarPreviewOk.value = true
})

function isValidImageUrl(url) {
  try {
    const parsed = new URL(url)
    return ['http:', 'https:'].includes(parsed.protocol) && /\.(apng|avif|gif|jpe?g|png|svg|webp)(\?.*)?$/i.test(parsed.href)
  } catch (error) {
    return false
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
  if (form.avatar && !isValidImageUrl(form.avatar)) {
    ElMessage.warning('请输入有效的 http/https 图片地址')
    return
  }
  saving.value = true
  try {
    auth.user = await authApi.updateProfile(form)
    localStorage.setItem('user', JSON.stringify(auth.user))
    ElMessage.success('设置已保存')
  } finally {
    saving.value = false
  }
}
</script>
