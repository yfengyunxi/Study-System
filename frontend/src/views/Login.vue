<template>
  <div class="auth-page">
    <div class="auth-shell">
      <section class="auth-story" aria-label="系统介绍">
        <div>
          <div class="auth-badge">个人学习陪伴系统</div>
          <h1 class="auth-story-title">把资料、计划和 AI 问答整理成你的学习手账。</h1>
          <p class="auth-story-text">
            登录后可以上传课程资料、沉淀知识库、向资料提问，并用任务计划追踪每天的学习进度。
          </p>
        </div>
        <ul class="auth-feature-list">
          <li>资料知识库</li>
          <li>AI 学习问答</li>
          <li>计划与任务</li>
        </ul>
      </section>

      <section class="auth-panel" aria-label="登录表单">
        <h2 class="auth-title">欢迎回来</h2>
        <p class="auth-subtitle">输入账号后继续管理你的学习资料、计划与 AI 问答。</p>
        <el-form :model="form" label-position="top" @submit.prevent="submit">
          <el-form-item label="用户名" required>
            <el-input v-model="form.username" autocomplete="username" placeholder="请输入用户名" />
          </el-form-item>
          <el-form-item label="密码" required>
            <el-input
              v-model="form.password"
              type="password"
              show-password
              autocomplete="current-password"
              placeholder="请输入密码"
            />
          </el-form-item>
          <el-button type="primary" native-type="submit" :loading="loading" class="full-width">
            登录学习空间
          </el-button>
        </el-form>
        <p class="muted auth-switch">
          还没有账号？
          <router-link to="/register">立即注册</router-link>
        </p>
      </section>
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
const form = reactive({ username: '', password: '' })

async function submit() {
  if (!form.username || !form.password) {
    ElMessage.warning('请填写用户名和密码')
    return
  }
  loading.value = true
  try {
    await auth.login(form)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } finally {
    loading.value = false
  }
}
</script>
