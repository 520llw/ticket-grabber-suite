import { create } from 'zustand';
import { Task, TaskLog, SystemStatus, taskApi, systemApi } from '../services/api';

interface AppState {
  // 数据
  tasks: Task[];
  currentTask: Task | null;
  logs: Record<string, TaskLog[]>;
  systemStatus: SystemStatus | null;
  isLoading: boolean;

  // 任务操作
  fetchTasks: (params?: { status?: string; platform?: string; search?: string }) => Promise<void>;
  fetchTask: (id: string) => Promise<void>;
  createTask: (data: Partial<Task>) => Promise<Task>;
  updateTask: (id: string, data: Partial<Task>) => Promise<void>;
  removeTask: (id: string) => Promise<void>;
  startTask: (id: string) => Promise<void>;
  stopTask: (id: string) => Promise<void>;
  restartTask: (id: string) => Promise<void>;

  // 日志
  fetchLogs: (taskId: string) => Promise<void>;
  addLog: (taskId: string, log: TaskLog) => void;
  clearLogs: (taskId: string) => Promise<void>;

  // 系统
  fetchStatus: () => Promise<void>;

  // 本地状态
  setTasks: (tasks: Task[]) => void;
  setCurrentTask: (task: Task | null) => void;
  setLoading: (loading: boolean) => void;
}

export const useStore = create<AppState>((set, get) => ({
  tasks: [],
  currentTask: null,
  logs: {},
  systemStatus: null,
  isLoading: false,

  fetchTasks: async (params) => {
    try {
      const data = await taskApi.list(params);
      set({ tasks: data.tasks });
    } catch (e) {
      console.error('fetchTasks error', e);
    }
  },

  fetchTask: async (id) => {
    try {
      const task = await taskApi.get(id);
      set({ currentTask: task });
      // 同步更新列表中的对应任务
      set((state) => ({
        tasks: state.tasks.map((t) => (t.id === id ? task : t)),
      }));
    } catch (e) {
      console.error('fetchTask error', e);
    }
  },

  createTask: async (data) => {
    const task = await taskApi.create(data);
    set((state) => ({ tasks: [task, ...state.tasks] }));
    return task;
  },

  updateTask: async (id, data) => {
    const task = await taskApi.update(id, data);
    set((state) => ({
      tasks: state.tasks.map((t) => (t.id === id ? task : t)),
      currentTask: state.currentTask?.id === id ? task : state.currentTask,
    }));
  },

  removeTask: async (id) => {
    await taskApi.delete(id);
    set((state) => ({
      tasks: state.tasks.filter((t) => t.id !== id),
      currentTask: state.currentTask?.id === id ? null : state.currentTask,
    }));
  },

  startTask: async (id) => {
    await taskApi.start(id);
    await get().fetchTask(id);
  },

  stopTask: async (id) => {
    await taskApi.stop(id);
    await get().fetchTask(id);
  },

  restartTask: async (id) => {
    await taskApi.restart(id);
    await get().fetchTask(id);
  },

  fetchLogs: async (taskId) => {
    try {
      const logs = await taskApi.logs(taskId);
      set((state) => ({ logs: { ...state.logs, [taskId]: logs } }));
    } catch (e) {
      console.error('fetchLogs error', e);
    }
  },

  addLog: (taskId, log) => {
    set((state) => {
      const existing = state.logs[taskId] || [];
      // 去重
      const isDup = existing.some(
        (l) => l.timestamp === log.timestamp && l.message === log.message
      );
      if (isDup) return state;
      const updated = [...existing, log].slice(-500);
      return { logs: { ...state.logs, [taskId]: updated } };
    });
  },

  clearLogs: async (taskId) => {
    await taskApi.clearLogs(taskId);
    set((state) => ({ logs: { ...state.logs, [taskId]: [] } }));
  },

  fetchStatus: async () => {
    try {
      const status = await systemApi.status();
      set({ systemStatus: status });
    } catch (e) {
      set({
        systemStatus: {
          version: 'unknown',
          active_tasks: 0,
          total_tasks: 0,
          success_tasks: 0,
          failed_tasks: 0,
          playwright_ready: false,
          uptime_seconds: 0,
          cpu_percent: 0,
          memory_mb: 0,
        },
      });
    }
  },

  setTasks: (tasks) => set({ tasks }),
  setCurrentTask: (task) => set({ currentTask: task }),
  setLoading: (loading) => set({ isLoading: loading }),
}));
