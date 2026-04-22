import { create } from 'zustand'
import type { Task, TaskLog, SystemStatus } from '@/services/api'

interface AppState {
  tasks: Task[]
  currentTask: Task | null
  logs: Record<string, TaskLog[]>
  systemStatus: SystemStatus | null
  isLoading: boolean

  setTasks: (tasks: Task[]) => void
  addTask: (task: Task) => void
  updateTask: (task: Task) => void
  removeTask: (id: string) => void
  setCurrentTask: (task: Task | null) => void
  addLog: (taskId: string, log: TaskLog) => void
  setSystemStatus: (status: SystemStatus) => void
  setLoading: (loading: boolean) => void
}

export const useStore = create<AppState>((set, get) => ({
  tasks: [],
  currentTask: null,
  logs: {},
  systemStatus: null,
  isLoading: false,

  setTasks: (tasks) => set({ tasks }),

  addTask: (task) =>
    set((state) => ({
      tasks: [task, ...state.tasks],
    })),

  updateTask: (task) =>
    set((state) => ({
      tasks: state.tasks.map((t) => (t.id === task.id ? task : t)),
      currentTask: state.currentTask?.id === task.id ? task : state.currentTask,
    })),

  removeTask: (id) =>
    set((state) => ({
      tasks: state.tasks.filter((t) => t.id !== id),
      currentTask: state.currentTask?.id === id ? null : state.currentTask,
    })),

  setCurrentTask: (task) => set({ currentTask: task }),

  addLog: (taskId, log) =>
    set((state) => ({
      logs: {
        ...state.logs,
        [taskId]: [...(state.logs[taskId] || []), log],
      },
    })),

  setSystemStatus: (status) => set({ systemStatus: status }),

  setLoading: (loading) => set({ isLoading: loading }),
}))

export default useStore
