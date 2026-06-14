<template>
  <div class="layout">
    <a class="skip-link" href="#main-content">跳到主内容</a>
    <aside class="sidebar" aria-label="主导航">
      <div class="brand">
        <div class="brand-mark" aria-hidden="true">学</div>
        <div>
          <span class="brand-name">学习助手</span>
          <span class="brand-subtitle">Personal Study Hub</span>
        </div>
      </div>

      <nav class="nav-list">
        <router-link v-for="item in navItems" :key="item.path" class="nav-link" :to="item.path">
          <el-icon class="nav-icon"><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="sidebar-note">
        把资料、问题和计划放在一起，像整理学习手账一样推进每天的小目标。
      </div>
    </aside>

    <main class="main">
      <header class="topbar">
        <div class="topbar-user">
          <img v-if="avatarSrc" :src="avatarSrc" class="topbar-avatar" alt="" />
          <div v-else class="avatar-bubble" aria-hidden="true">{{ userInitial }}</div>
          <div>
            <strong>{{ displayName }}</strong>
            <p class="topbar-goal">
              {{ auth.user?.study_goal || '设置一个学习目标，让系统更懂你的计划。' }}
            </p>
          </div>
        </div>
        <div class="topbar-actions">
          <div v-if="pomodoro.isActive" class="pomodoro-badge" :class="{ paused: pomodoro.state === 'paused' }">
            <span class="pomodoro-badge-icon">🍅</span>
            <span class="pomodoro-badge-time">{{ pomodoro.formatted }}</span>
          </div>
          <el-button :icon="SwitchButton" @click="auth.logout">退出登录</el-button>
        </div>
      </header>
      <section id="main-content" class="content" tabindex="-1" aria-label="主内容">
        <slot />
      </section>
    </main>
  </div>
</template>

<script setup>
import { ChatDotRound, DataBoard, FolderOpened, List, SwitchButton, User } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, watch } from 'vue'

import { focusApi } from '../api/modules'
import { useAuthStore } from '../stores/auth'
import { usePomodoroStore } from '../stores/pomodoro'

const pomodoro = usePomodoroStore()

const navItems = [
  { path: '/dashboard', label: '今日驾驶舱', icon: DataBoard },
  { path: '/plans', label: '学习计划', icon: List },
  { path: '/materials', label: '知识库', icon: FolderOpened },
  { path: '/chat', label: 'AI 学习会话', icon: ChatDotRound },
  { path: '/profile', label: '个人设置', icon: User }
]

const auth = useAuthStore()
const displayName = computed(() => auth.user?.nickname || auth.user?.username || '学习者')
const userInitial = computed(() => displayName.value.slice(0, 1).toUpperCase())
const avatarSrc = computed(() => {
  const av = auth.user?.avatar
  if (!av) return null
  if (av.startsWith('/api/auth/avatar/')) return av
  if (av.startsWith('http://') || av.startsWith('https://')) return av
  return null
})

// Watch pomodoro completion — works on any page since AppLayout is always mounted
watch(() => pomodoro.completed, async (isCompleted) => {
  if (!isCompleted) return
  pomodoro.consumeCompleted()
  pomodoro.completedVersion++
  const started = pomodoro.startedAt
  const planned = pomodoro.plannedSeconds
  if (!started || !planned) return
  try {
    const now = new Date()
    const studyDate = now.toISOString().slice(0, 10)
    const tzOffset = -now.getTimezoneOffset()
    await focusApi.createSession({
      client_session_id: `pomo-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      started_at: started.toISOString(),
      ended_at: now.toISOString(),
      duration_seconds: planned,
      planned_seconds: planned,
      study_date: studyDate,
      timezone_offset_minutes: tzOffset,
      source: 'pomodoro'
    })
    ElMessage.success(`专注 ${Math.floor(planned / 60)} 分钟，已记录！`)
  } catch (e) {
    ElMessage.error('专注记录保存失败：' + (e?.apiMessage || e?.message || ''))
  } finally {
    pomodoro.startedAt = null
  }
})
</script>
