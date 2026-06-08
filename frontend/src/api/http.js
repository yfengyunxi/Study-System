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
    const message = error.response?.data?.message || '请求失败，请稍后重试'
    ElMessage.error(message)
    if (error.response?.status === 401) {
      const auth = useAuthStore()
      auth.logout()
    }
    return Promise.reject(error)
  }
)

export default http
