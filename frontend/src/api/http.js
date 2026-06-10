import axios from 'axios'
import { ElMessage } from 'element-plus'

import { useAuthStore } from '../stores/auth'

const http = axios.create({
  baseURL: '/api',
  timeout: 90000
})

http.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const body = error.response?.data || {}
    const apiError = body.error || {}
    const message = body.message || '请求失败，请稍后重试'
    ElMessage.error(message)
    if (error.response?.status === 401) {
      const auth = useAuthStore()
      auth.logout()
    }
    const enriched = new Error(apiError.message || message)
    enriched.apiError = body
    enriched.apiCode = apiError.code || 'UNKNOWN'
    enriched.apiMessage = apiError.message || message
    enriched.retryable = Boolean(apiError.retryable)
    enriched.fieldErrors = apiError.field_errors || {}
    enriched.status = error.response?.status || 0
    return Promise.reject(enriched)
  }
)

export default http
