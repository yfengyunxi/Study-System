import http from './http'

export const authApi = {
  register: (data) => http.post('/auth/register', data),
  login: (data) => http.post('/auth/login', data),
  me: () => http.get('/auth/me'),
  updateProfile: (data) => http.put('/auth/profile', data)
}

export const materialApi = {
  list: (params = {}) => http.get('/materials', { params }),
  detail: (id) => http.get(`/materials/${id}`),
  assets: (id) => http.get(`/materials/${id}/assets`),
  assetImage: (assetId) => http.get(`/materials/assets/${assetId}/image`, { responseType: 'blob' }),
  upload: (formData) => http.post('/materials/upload', formData),
  remove: (id) => http.delete(`/materials/${id}`),
  reindex: (id) => http.post(`/materials/${id}/reindex`)
}

export const folderApi = {
  list: () => http.get('/material-folders'),
  create: (data) => http.post('/material-folders', data),
  update: (id, data) => http.put(`/material-folders/${id}`, data),
  remove: (id) => http.delete(`/material-folders/${id}`)
}

export const chatApi = {
  ask: (data) => http.post('/chat', data),
  history: () => http.get('/chat/history')
}

export const planApi = {
  list: () => http.get('/plans'),
  create: (data) => http.post('/plans', data),
  update: (id, data) => http.put(`/plans/${id}`, data),
  remove: (id) => http.delete(`/plans/${id}`)
}

export const taskApi = {
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
  folders: () => http.get('/stats/folders')
}
