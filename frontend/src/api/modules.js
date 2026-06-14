import http from './http'

export const authApi = {
  register: (data) => http.post('/auth/register', data),
  login: (data) => http.post('/auth/login', data),
  me: () => http.get('/auth/me'),
  updateProfile: (data) => http.put('/auth/profile', data),
  uploadAvatar: (formData) => http.post('/auth/avatar', formData)
}

export const materialApi = {
  list: (params = {}) => http.get('/materials', { params }),
  detail: (id) => http.get(`/materials/${id}`),
  assets: (id) => http.get(`/materials/${id}/assets`),
  assetImage: (assetId, config = {}) => http.get(`/materials/assets/${assetId}/image`, { responseType: 'blob', ...config }),
  upload: (formData) => http.post('/materials/upload', formData),
  remove: (id) => http.delete(`/materials/${id}`),
  moveFolder: (id, data) => http.patch(`/materials/${id}/folder`, data),
  reindex: (id, data = {}) => http.post(`/materials/${id}/reindex`, data),
  indexStatus: (id) => http.get(`/materials/${id}/index-status`)
}

export const folderApi = {
  list: () => http.get('/material-folders'),
  create: (data) => http.post('/material-folders', data),
  update: (id, data) => http.put(`/material-folders/${id}`, data),
  remove: (id) => http.delete(`/material-folders/${id}`)
}

export const chatApi = {
  ask: (data) => http.post('/chat', data),
  history: () => http.get('/chat/history'),
  conversations: (params = {}) => http.get('/chat/conversations', { params }),
  createConversation: (data) => http.post('/chat/conversations', data),
  deleteConversation: (id) => http.delete(`/chat/conversations/${id}`),
  messages: (id, params = {}) => http.get(`/chat/conversations/${id}/messages`, { params }),
  sendMessage: (id, data) => http.post(`/chat/conversations/${id}/messages`, data),
  retryMessage: (id, data) => http.post(`/chat/messages/${id}/retry`, data)
}

export const planApi = {
  list: (params = {}) => http.get('/plans', { params }),
  create: (data) => http.post('/plans', data),
  update: (id, data) => http.put(`/plans/${id}`, data),
  remove: (id) => http.delete(`/plans/${id}`),
  aiPreview: (data) => http.post('/plans/ai-preview', data),
  createFromPreview: (data) => http.post('/plans/from-preview', data)
}

export const taskApi = {
  list: (params = {}) => http.get('/tasks', { params }),
  today: () => http.get('/tasks/today'),
  create: (data) => http.post('/tasks', data),
  update: (id, data) => http.put(`/tasks/${id}`, data),
  remove: (id) => http.delete(`/tasks/${id}`),
  complete: (id) => http.post(`/tasks/${id}/complete`),
  undo: (id) => http.post(`/tasks/${id}/undo`)
}

export const statsApi = {
  dashboard: () => http.get('/stats/dashboard'),
  taskTrend: () => http.get('/stats/task-trend'),
  materialTypes: () => http.get('/stats/material-types'),
  folders: () => http.get('/stats/folders'),
  focusDurationTrend: (params = {}) => http.get('/stats/focus-duration-trend', { params })
}

export const focusApi = {
  createSession: (data) => http.post('/focus-sessions', data)
}
