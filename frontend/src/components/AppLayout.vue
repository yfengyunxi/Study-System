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
        <router-link class="nav-link" to="/dashboard">
          <el-icon class="nav-icon"><House /></el-icon>
          <span>首页仪表盘</span>
        </router-link>
        <router-link class="nav-link" to="/materials">
          <el-icon class="nav-icon"><FolderOpened /></el-icon>
          <span>学习资料</span>
        </router-link>
        <router-link class="nav-link" to="/chat">
          <el-icon class="nav-icon"><ChatDotRound /></el-icon>
          <span>AI 问答</span>
        </router-link>
        <router-link class="nav-link" to="/plans">
          <el-icon class="nav-icon"><Calendar /></el-icon>
          <span>学习计划</span>
        </router-link>
        <router-link class="nav-link" to="/profile">
          <el-icon class="nav-icon"><User /></el-icon>
          <span>个人设置</span>
        </router-link>
      </nav>

      <div class="sidebar-note">
        把资料、问题和计划放在一起，像整理学习手账一样推进每天的小目标。
      </div>
    </aside>

    <main class="main">
      <header class="topbar">
        <div class="topbar-user">
          <div class="avatar-bubble" aria-hidden="true">{{ userInitial }}</div>
          <div>
            <strong>{{ displayName }}</strong>
            <span class="user-goal">{{ auth.user?.study_goal || '设置学习目标后会显示在这里' }}</span>
          </div>
        </div>
        <el-button :icon="SwitchButton" @click="auth.logout">退出登录</el-button>
      </header>
      <section id="main-content" class="content" tabindex="-1" aria-label="主内容">
        <slot />
      </section>
    </main>
  </div>
</template>

<script setup>
import { Calendar, ChatDotRound, FolderOpened, House, SwitchButton, User } from '@element-plus/icons-vue'
import { computed } from 'vue'

import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const displayName = computed(() => auth.user?.nickname || auth.user?.username || '学习者')
const userInitial = computed(() => displayName.value.slice(0, 1).toUpperCase())
</script>
