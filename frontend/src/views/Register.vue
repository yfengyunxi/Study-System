<template>
  <div class="auth-page">
    <div class="auth-shell">
      <section class="auth-story" aria-label="系统介绍">
        <div>
          <div class="auth-badge">开启学习手账</div>
          <h1 class="auth-story-title">创建你的个人知识库，从第一份资料开始。</h1>
          <p class="auth-story-text">
            注册后可以把课程文档、笔记和计划集中管理，让 AI 帮你回顾重点、追踪任务、整理薄弱点。
          </p>
        </div>
        <ul class="auth-feature-list">
          <li>上传资料</li>
          <li>生成摘要</li>
          <li>制定计划</li>
        </ul>
      </section>

      <section class="auth-panel" aria-label="注册表单">
        <h2 class="auth-title">创建学习账号</h2>
        <p class="auth-subtitle">开始构建你的个人学习知识库。昵称可稍后在个人设置中修改。</p>
        <el-form :model="form" label-position="top" @submit.prevent="submit">
          <el-form-item label="用户名" required>
            <el-input v-model="form.username" autocomplete="username" placeholder="用于登录的用户名" />
          </el-form-item>
          <el-form-item label="昵称">
            <el-input v-model="form.nickname" autocomplete="nickname" placeholder="例如：小林同学" />
          </el-form-item>
          <el-form-item label="密码" required>
            <el-input
              v-model="form.password"
              type="password"
              show-password
              autocomplete="new-password"
              placeholder="至少 6 位密码"
            />
            <p class="panel-subtitle">密码至少 6 位，建议包含字母和数字。</p>
          </el-form-item>
          <el-button type="primary" native-type="submit" :loading="loading" class="full-width">
            创建账号
          </el-button>
        </el-form>
        <p class="muted auth-switch">
          已有账号？
          <router-link to="/login">返回登录</router-link>
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
const form = reactive({ username: '', nickname: '', password: '' })

async function submit() {
  if (!form.username || !form.password) {
    ElMessage.warning('请填写用户名和密码')
    return
  }
  if (form.password.length < 6) {
    ElMessage.warning('密码至少需要 6 位')
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
