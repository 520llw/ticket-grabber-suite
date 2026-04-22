import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { Plus, Ticket, Loader2 } from 'lucide-react'
import { taskApi } from '@/services/api'
import { useStore } from '@/store/useStore'
import TaskCard from '@/components/TaskCard'

export default function TaskList() {
  const navigate = useNavigate()
  const { tasks, setTasks, isLoading, setLoading } = useStore()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true
    const fetch = async () => {
      setLoading(true)
      setError(null)
      try {
        const data = await taskApi.list()
        if (mounted) setTasks(data)
      } catch (err) {
        if (mounted) setError('获取任务列表失败')
      } finally {
        if (mounted) setLoading(false)
      }
    }
    fetch()
    const interval = setInterval(fetch, 5000)
    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [setTasks, setLoading])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">任务管理</h1>
          <p className="text-sm text-slate-500 mt-0.5">管理所有抢票任务</p>
        </div>
        <button
          onClick={() => navigate('/tasks/new')}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium transition-colors shadow-lg shadow-emerald-900/20"
        >
          <Plus size={16} />
          新建任务
        </button>
      </div>

      {/* Loading */}
      {isLoading && tasks.length === 0 && (
        <div className="flex items-center justify-center py-20">
          <Loader2 size={28} className="text-emerald-400 animate-spin" />
          <span className="ml-3 text-sm text-slate-400">加载中...</span>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-500/10 border border-red-600/20 rounded-xl p-4 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Empty state */}
      {!isLoading && tasks.length === 0 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col items-center justify-center py-20 bg-slate-800/50 border border-slate-700/50 rounded-xl"
        >
          <div className="w-16 h-16 rounded-2xl bg-slate-800 flex items-center justify-center mb-4">
            <Ticket size={32} className="text-slate-600" />
          </div>
          <h3 className="text-base font-medium text-slate-300 mb-1">还没有任务</h3>
          <p className="text-sm text-slate-500 mb-5">点击新建任务开始配置抢票</p>
          <button
            onClick={() => navigate('/tasks/new')}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium transition-colors"
          >
            <Plus size={16} />
            新建任务
          </button>
        </motion.div>
      )}

      {/* Task grid */}
      {tasks.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {tasks.map((task, i) => (
            <TaskCard key={task.id} task={task} index={i} />
          ))}
        </div>
      )}
    </div>
  )
}
