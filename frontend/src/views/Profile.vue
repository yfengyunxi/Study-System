<template>
  <AppLayout>
    <h1 class="page-title">个人设置</h1>
    <div class="panel" style="max-width: 640px">
      <el-form :model="form" label-position="top">
        <el-form-item label="昵称">
          <el-input v-model="form.nickname" />
        </el-form-item>
        <el-form-item label="头像地址">
          <el-input v-model="form.avatar" />
        </el-form-item>
        <el-form-item label="学习目标">
          <el-input
            v-model="form.study_goal"
            type="textarea"
            :rows="4"
            placeholder="例如：本月完成数据库基础和 SQL 练习"
          />
        </el-form-item>
        <el-button type="primary" :loading="saving" @click="save">保存设置</el-button>
      </el-form>
    </div>
  </AppLayout>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'

import { authApi } from '../api/modules'
import AppLayout from '../components/AppLayout.vue'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const saving = ref(false)
const form = reactive({ nickname: '', avatar: '', study_goal: '' })

onMounted(() => {
  form.nickname = auth.user?.nickname || ''
  form.avatar = auth.user?.avatar || ''
  form.study_goal = auth.user?.study_goal || ''
})

async function save() {
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
