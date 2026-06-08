<template>
  <div class="auth-page">
    <div class="auth-panel">
      <h1 class="auth-title">创建学习账号</h1>
      <p class="auth-subtitle">开始构建你的个人学习知识库</p>
      <el-form :model="form" label-position="top">
        <el-form-item label="用户名">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item label="昵称">
          <el-input v-model="form.nickname" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-button type="primary" :loading="loading" style="width: 100%" @click="submit">
          注册
        </el-button>
      </el-form>
      <p class="muted" style="text-align: center">
        已有账号？
        <router-link to="/login">返回登录</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const form = reactive({ username: '', nickname: '', password: '' })

async function submit() {
  if (!form.username || !form.password) {
    ElMessage.warning('请填写用户名和密码')
    return
  }
  loading.value = true
  try {
    await auth.register(form)
    ElMessage.success('注册成功')
    router.push('/dashboard')
  } finally {
    loading.value = false
  }
}
</script>
