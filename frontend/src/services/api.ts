import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.message || '请求失败';
    console.error('[API Error]', msg);
    return Promise.reject(err);
  }
);

export interface Task {
  id: string;
  name: string;
  platform: 'damai' | 'maoyan' | '12306' | 'custom';
  url: string;
  date: string;
  session: string;
  price: string;
  ticket_count: number;
  buyers: string[];
  from_station: string;
  to_station: string;
  train_number: string;
  seat_type: string;
  cron_time: string | null;
  status: 'idle' | 'running' | 'success' | 'failed' | 'stopped' | 'waiting';
  headless: boolean;
  max_retries: number;
  retry_interval: number;
  auto_retry: boolean;
  multi_buy: boolean;
  notify_on_success: boolean;
  priority: number;
  attempt_count: number;
  last_error: string;
  created_at: string;
  updated_at: string;
}

export interface TaskLog {
  task_id: string;
  timestamp: string;
  level: 'info' | 'warn' | 'error' | 'success' | 'debug';
  message: string;
}

export interface SystemStatus {
  version: string;
  active_tasks: number;
  total_tasks: number;
  success_tasks: number;
  failed_tasks: number;
  playwright_ready: boolean;
  uptime_seconds: number;
  cpu_percent: number;
  memory_mb: number;
}

export interface PlatformInfo {
  id: string;
  name: string;
  description: string;
  icon: string;
  fields: string[];
}

export const taskApi = {
  list: (params?: { status?: string; platform?: string; search?: string }) =>
    api.get<{ tasks: Task[]; total: number }>('/tasks', { params }).then(r => r.data),
  get: (id: string) =>
    api.get<{ task: Task }>(`/tasks/${id}`).then(r => r.data.task),
  create: (data: Partial<Task>) =>
    api.post<{ task: Task }>('/tasks', data).then(r => r.data.task),
  update: (id: string, data: Partial<Task>) =>
    api.put<{ task: Task }>(`/tasks/${id}`, data).then(r => r.data.task),
  delete: (id: string) =>
    api.delete(`/tasks/${id}`).then(r => r.data),
  start: (id: string) =>
    api.post(`/tasks/${id}/start`).then(r => r.data),
  stop: (id: string) =>
    api.post(`/tasks/${id}/stop`).then(r => r.data),
  restart: (id: string) =>
    api.post(`/tasks/${id}/restart`).then(r => r.data),
  logs: (id: string, limit = 200) =>
    api.get<{ logs: TaskLog[] }>(`/tasks/${id}/logs`, { params: { limit } }).then(r => r.data.logs),
  clearLogs: (id: string) =>
    api.delete(`/tasks/${id}/logs`).then(r => r.data),
  logStream: (id: string) =>
    new EventSource(`/api/tasks/${id}/logs/stream`),
  batchStart: (ids: string[]) =>
    api.post('/tasks/batch/start', ids).then(r => r.data),
  batchStop: (ids: string[]) =>
    api.post('/tasks/batch/stop', ids).then(r => r.data),
  batchDelete: (ids: string[]) =>
    api.post('/tasks/batch/delete', ids).then(r => r.data),
};

export const systemApi = {
  status: () =>
    api.get<SystemStatus>('/status').then(r => r.data),
  health: () =>
    api.get('/health').then(r => r.data),
  platforms: () =>
    api.get<{ platforms: PlatformInfo[] }>('/platforms').then(r => r.data.platforms),
};

export default api;
