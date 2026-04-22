import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface Task {
  id: string
  name: string
  platform: 'damai' | 'maoyan' | '12306' | 'custom'
  url: string
  date: string
  session: string
  price: string
  ticket_count: number
  buyers: string[]
  cron_time: string | null
  status: 'idle' | 'running' | 'success' | 'failed' | 'stopped'
  headless: boolean
  created_at: string
  updated_at: string
}

export interface TaskLog {
  task_id: string
  timestamp: string
  level: 'info' | 'warn' | 'error' | 'success'
  message: string
}

export interface SystemStatus {
  version: string
  active_tasks: number
  total_tasks: number
  playwright_ready: boolean
}

export const taskApi = {
  list: () => api.get('/tasks').then(r => r.data.tasks as Task[]),
  get: (id: string) => api.get(`/tasks/${id}`).then(r => r.data.task as Task),
  create: (data: Partial<Task>) => api.post('/tasks', data).then(r => r.data.task as Task),
  update: (id: string, data: Partial<Task>) => api.put(`/tasks/${id}`, data).then(r => r.data.task as Task),
  delete: (id: string) => api.delete(`/tasks/${id}`).then(r => r.data),
  start: (id: string) => api.post(`/tasks/${id}/start`).then(r => r.data),
  stop: (id: string) => api.post(`/tasks/${id}/stop`).then(r => r.data),
  logs: (id: string, limit = 100) => api.get(`/tasks/${id}/logs?limit=${limit}`).then(r => r.data.logs as TaskLog[]),
  logStream: (id: string) => new EventSource(`/api/tasks/${id}/logs/stream`),
}

export const systemApi = {
  status: () => api.get('/status').then(r => r.data as SystemStatus),
  health: () => api.get('/health').then(r => r.data),
}

export default api
