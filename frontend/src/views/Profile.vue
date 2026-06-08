<template>
  <AppLayout>
    <div class="page-heading">
      <div>
        <p class="page-kicker">Profile</p>
        <h1 class="page-title">个人设置</h1>
        <p class="page-subtitle">调整昵称、头像和学习目标，让顶部学习状态更像你的个人空间。</p>
      </div>
    </div>

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
          <el-input
            v-model="form.study_goal"
            type="textarea"
            :rows="4"
            placeholder="例如：本月完成数据库基础和 SQL 练习"
          />
          <p class="panel-subtitle">学习目标会显示在顶部栏，帮助你进入学习状态。</p>
        </el-form-item>
        <el-button type="primary" :loading="saving" @click="save">保存设置</el-button>
      </el-form>
    </div>
  </AppLayout>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { computed, onMounted, reactive, ref, watch } from 'vue'

import { authApi } from '../api/modules'
import AppLayout from '../components/AppLayout.vue'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const saving = ref(false)
const avatarPreviewOk = ref(true)
const form = reactive({ nickname: '', avatar: '', study_goal: '' })
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
