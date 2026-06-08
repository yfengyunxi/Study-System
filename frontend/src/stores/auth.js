import { defineStore } from 'pinia'

import { authApi } from '../api/modules'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null')
  }),
  actions: {
    async login(payload) {
      const data = await authApi.login(payload)
      this.setSession(data)
    },
    async register(payload) {
      const data = await authApi.register(payload)
      this.setSession(data)
    },
    async fetchMe() {
      this.user = await authApi.me()
      localStorage.setItem('user', JSON.stringify(this.user))
    },
    setSession(data) {
      this.token = data.token
      this.user = data.user
      localStorage.setItem('token', this.token)
      localStorage.setItem('user', JSON.stringify(this.user))
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
  }
})
