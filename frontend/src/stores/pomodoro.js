import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const usePomodoroStore = defineStore('pomodoro', () => {
  const state = ref('idle') // idle | running | paused
  const plannedSeconds = ref(1500)
  const remainingSeconds = ref(1500)
  const startedAt = ref(null)
  const completed = ref(false)
  const completedVersion = ref(0)

  let endAt = null        // timestamp when timer should end
  let pausedRemaining = 0 // remaining ms when paused
  let displayInterval = null

  const formatted = computed(() => {
    const s = Math.max(0, remainingSeconds.value)
    const mins = Math.floor(s / 60)
    const secs = s % 60
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
  })

  const isActive = computed(() => state.value === 'running' || state.value === 'paused')

  function refreshDisplay() {
    if (state.value !== 'running') return
    const now = Date.now()
    const remaining = Math.max(0, Math.round((endAt - now) / 1000))
    remainingSeconds.value = remaining
    if (remaining <= 0) {
      clearInterval(displayInterval)
      displayInterval = null
      state.value = 'idle'
      remainingSeconds.value = plannedSeconds.value
      completed.value = true
    }
  }

  function setPreset(seconds) {
    if (state.value !== 'idle') return
    plannedSeconds.value = seconds
    remainingSeconds.value = seconds
  }

  function consumeCompleted() {
    const was = completed.value
    completed.value = false
    return was
  }

  function start() {
    state.value = 'running'
    startedAt.value = new Date()
    completed.value = false
    endAt = Date.now() + plannedSeconds.value * 1000
    displayInterval = setInterval(refreshDisplay, 250)
  }

  function pause() {
    state.value = 'paused'
    pausedRemaining = Math.max(0, endAt - Date.now())
    clearInterval(displayInterval)
    displayInterval = null
  }

  function resume() {
    state.value = 'running'
    endAt = Date.now() + pausedRemaining
    displayInterval = setInterval(refreshDisplay, 250)
  }

  function reset() {
    clearInterval(displayInterval)
    displayInterval = null
    const endedAt = new Date()
    const now = Date.now()
    const elapsed = state.value === 'paused'
      ? plannedSeconds.value * 1000 - pausedRemaining
      : plannedSeconds.value * 1000 - Math.max(0, endAt - now)
    const duration = Math.round(elapsed / 1000)
    state.value = 'idle'
    remainingSeconds.value = plannedSeconds.value
    const prevStartedAt = startedAt.value
    startedAt.value = null
    completed.value = false
    return { endedAt, duration, prevStartedAt }
  }

  function $dispose() {
    clearInterval(displayInterval)
    displayInterval = null
  }

  return {
    state,
    plannedSeconds,
    remainingSeconds,
    startedAt,
    completed,
    completedVersion,
    formatted,
    isActive,
    setPreset,
    start,
    pause,
    resume,
    reset,
    consumeCompleted,
    $dispose
  }
})
