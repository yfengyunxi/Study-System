<template>
  <div class="pomodoro-timer" role="region" :aria-label="'番茄计时器'">
    <div class="timer-display" :aria-live="'polite'">{{ formatted }}</div>
    <div class="timer-controls">
      <el-button v-if="state === 'idle'" type="primary" :icon="VideoPlay" @click="start">开始专注</el-button>
      <template v-else-if="state === 'running'">
        <el-button :icon="VideoPause" @click="pause">暂停</el-button>
        <el-button type="danger" :icon="Close" @click="reset">结束</el-button>
      </template>
      <template v-else-if="state === 'paused'">
        <el-button type="primary" :icon="VideoPlay" @click="resume">继续</el-button>
        <el-button :icon="Close" @click="reset">结束</el-button>
      </template>
    </div>
    <div class="timer-presets">
      <el-button v-for="preset in presets" :key="preset.seconds" size="small" :disabled="state !== 'idle'" @click="setPreset(preset.seconds)">{{ preset.label }}</el-button>
    </div>
  </div>
</template>

<script setup>
import { Close, VideoPause, VideoPlay } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onBeforeUnmount, ref } from 'vue'

import { focusApi } from '../../api/modules'

const emit = defineEmits(['completed'])

const presets = [
  { label: '25 分钟', seconds: 1500 },
  { label: '45 分钟', seconds: 2700 },
  { label: '60 分钟', seconds: 3600 }
]

const state = ref('idle')
const plannedSeconds = ref(1500)
const remainingSeconds = ref(1500)
const startedAt = ref(null)
let timerInterval = null

const formatted = computed(() => {
  const mins = Math.floor(remainingSeconds.value / 60)
  const secs = remainingSeconds.value % 60
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
})

function setPreset(seconds) {
  plannedSeconds.value = seconds
  remainingSeconds.value = seconds
}

function tick() {
  remainingSeconds.value -= 1
  if (remainingSeconds.value <= 0) {
    complete()
  }
}

function start() {
  state.value = 'running'
  startedAt.value = new Date()
  timerInterval = setInterval(tick, 1000)
}

function pause() {
  state.value = 'paused'
  clearInterval(timerInterval)
  timerInterval = null
}

function resume() {
  state.value = 'running'
  timerInterval = setInterval(tick, 1000)
}

async function reset() {
  clearInterval(timerInterval)
  timerInterval = null
  const endedAt = new Date()
  const duration = plannedSeconds.value - remainingSeconds.value
  if (duration >= 60 && startedAt.value) {
    try {
      await persistCompleted(endedAt, duration)
    } catch {
      // local error is already toasted by http interceptor
    }
  }
  state.value = 'idle'
  remainingSeconds.value = plannedSeconds.value
  startedAt.value = null
}

async function complete() {
  clearInterval(timerInterval)
  timerInterval = null
  const endedAt = new Date()
  try {
    await persistCompleted(endedAt, plannedSeconds.value)
    emit('completed')
  } catch {
    // local error already toasted
  }
  state.value = 'idle'
  remainingSeconds.value = plannedSeconds.value
  startedAt.value = null
}

async function persistCompleted(endedAt, duration) {
  const studyDate = new Date().toISOString().slice(0, 10)
  const tzOffset = -new Date().getTimezoneOffset()
  const clientSessionId = `pomo-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
  await focusApi.createSession({
    client_session_id: clientSessionId,
    started_at: startedAt.value?.toISOString(),
    ended_at: endedAt.toISOString(),
    duration_seconds: duration,
    planned_seconds: plannedSeconds.value,
    study_date: studyDate,
    timezone_offset_minutes: tzOffset,
    source: 'pomodoro'
  })
  ElMessage.success(`专注 ${Math.floor(duration / 60)} 分钟，已记录！`)
}

onBeforeUnmount(() => {
  clearInterval(timerInterval)
})
</script>
