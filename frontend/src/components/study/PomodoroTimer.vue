<template>
  <div class="pomodoro-timer" role="region" :aria-label="'番茄计时器'" :class="{ 'is-active': pomodoro.isActive }">
    <div class="timer-ring" :class="{ running: pomodoro.state === 'running', paused: pomodoro.state === 'paused' }">
      <div class="timer-display" :aria-live="'polite'">{{ pomodoro.formatted }}</div>
    </div>

    <div class="timer-controls">
      <el-button v-if="pomodoro.state === 'idle'" type="primary" size="large" :icon="VideoPlay" @click="start">
        开始专注
      </el-button>
      <template v-else-if="pomodoro.state === 'running'">
        <el-button size="large" :icon="VideoPause" @click="pomodoro.pause()">暂停</el-button>
        <el-button size="large" type="danger" :icon="Close" @click="reset">结束</el-button>
      </template>
      <template v-else-if="pomodoro.state === 'paused'">
        <el-button size="large" type="primary" :icon="VideoPlay" @click="pomodoro.resume()">继续</el-button>
        <el-button size="large" :icon="Close" @click="reset">结束</el-button>
      </template>
    </div>

    <div v-if="pomodoro.state === 'idle'" class="timer-presets">
      <el-button
        v-for="preset in presets"
        :key="preset.seconds"
        :type="pomodoro.plannedSeconds === preset.seconds ? 'primary' : ''"
        size="small"
        @click="pomodoro.setPreset(preset.seconds)"
      >
        {{ preset.label }}
      </el-button>
      <div class="custom-time">
        <el-input-number
          v-model="customMinutes"
          :min="1"
          :max="180"
          size="small"
          controls-position="right"
          style="width: 100px"
        />
        <span class="custom-label">分钟</span>
        <el-button size="small" @click="applyCustom">设置</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Close, VideoPause, VideoPlay } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { ref } from 'vue'

import { focusApi } from '../../api/modules'
import { usePomodoroStore } from '../../stores/pomodoro'

const emit = defineEmits(['completed'])
const pomodoro = usePomodoroStore()
const customMinutes = ref(25)

const presets = [
  { label: '25 分钟', seconds: 1500 },
  { label: '45 分钟', seconds: 2700 },
  { label: '60 分钟', seconds: 3600 }
]

function applyCustom() {
  pomodoro.setPreset(customMinutes.value * 60)
}

function start() {
  pomodoro.start()
}

async function reset() {
  const { endedAt, duration, prevStartedAt } = pomodoro.reset()
  if (duration >= 60 && prevStartedAt) {
    try {
      const studyDate = new Date().toISOString().slice(0, 10)
      const tzOffset = -new Date().getTimezoneOffset()
      await focusApi.createSession({
        client_session_id: `pomo-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        started_at: prevStartedAt?.toISOString(),
        ended_at: endedAt.toISOString(),
        duration_seconds: duration,
        planned_seconds: pomodoro.plannedSeconds,
        study_date: studyDate,
        timezone_offset_minutes: tzOffset,
        source: 'pomodoro'
      })
      ElMessage.success(`专注 ${Math.floor(duration / 60)} 分钟，已记录！`)
      emit('completed')
    } catch {
      // error already toasted
    }
  }
}
</script>
