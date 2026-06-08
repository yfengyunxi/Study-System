<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">学习助手</div>
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
    </aside>
    <main class="main">
      <header class="topbar">
        <div>
          <strong>{{ auth.user?.nickname || auth.user?.username || '学习者' }}</strong>
          <span class="muted"> · {{ auth.user?.study_goal || '设置学习目标后会显示在这里' }}</span>
        </div>
        <el-button :icon="SwitchButton" @click="auth.logout">退出</el-button>
      </header>
      <section class="content">
        <slot />
      </section>
    </main>
  </div>
</template>

<script setup>
import { Calendar, ChatDotRound, FolderOpened, House, SwitchButton, User } from '@element-plus/icons-vue'

import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
</script>
