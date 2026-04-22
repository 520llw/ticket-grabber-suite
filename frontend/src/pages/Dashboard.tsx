import { useEffect } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import {
  ListChecks,
  Play,
  CheckCircle2,
  XCircle,
  Globe,
  Zap,
  ArrowRight,
  Ticket,
} from 'lucide-react'
import { taskApi } from '@/services/api'
import { useStore } from '@/store/useStore'
import TaskCard from '@/components/TaskCard'

function StatCard({
  icon: Icon,
  label,
  value,
  gradient,
  delay = 0,
}: {
  icon: React.ElementType
  label: string
  value: number | string
  gradient: string
  delay?: number
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay }}
      className={`relative overflow-hidden rounded-xl p-5 border border-slate-700/50 bg-gradient-to-br ${gradient}`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-400 mb-1">{label}</p>
          <p className="text-2xl font-bold text-slate-100">{value}</p>
        </div>
        <div className="p-2.5 rounded-lg bg-white/5 text-slate-300">
          <Icon size={20} />
        </div>
      </div>
    </motion.div>
  )
}

export default function Dashboard() {
  const navigate = useNavigate()
  const { tasks, systemStatus, setTasks, setLoading } = useStore()

  useEffect(() => {
    let mounted = true
    const fetch = async () => {
      setLoading(true)
      try {
        const data = await taskApi.list()
        if (mounted) setTasks(data)
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

  const total = tasks.length
  const running = tasks.filter((t) => t.status === 'running').length
  const success = tasks.filter((t) => t.status === 'success').length
  const failed = tasks.filter((t) => t.status === 'failed').length
  const recentTasks = [...tasks].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()).slice(0, 5)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">仪表盘</h1>
          <p className="text-sm text-slate-500 mt-0.5">任务概览与系统状态</p>
        </div>
        <button
          onClick={() => navigate('/tasks/new')}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium transition-colors"
        >
          <Ticket size={16} />
          新建任务
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={ListChecks} label="总任务" value={total} gradient="from-slate-800 to-slate-900" delay={0} />
        <StatCard icon={Play} label="运行中" value={running} gradient="from-emerald-900/40 to-slate-900" delay={0.05} />
        <StatCard icon={CheckCircle2} label="成功" value={success} gradient="from-emerald-900/30 to-slate-900" delay={0.1} />
        <StatCard icon={XCircle} label="失败" value={failed} gradient="from-red-900/30 to-slate-900" delay={0.15} />
      </div>

      {/* System status + Recent tasks */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* System status */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
          className="lg:col-span-1 bg-slate-800 border border-slate-700/50 rounded-xl p-5"
        >
          <h2 className="text-sm font-semibold text-slate-200 mb-4">系统状态</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between py-2 border-b border-slate-700/50">
              <div className="flex items-center gap-2 text-sm text-slate-400">
                <Zap size={14} />
                Playwright
              </div>
              <span
                className={`text-xs font-medium px-2 py-0.5 rounded ${systemStatus?.playwright_ready ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}
              >
                {systemStatus?.playwright_ready ? '就绪' : '未就绪'}
              </span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-slate-700/50">
              <div className="flex items-center gap-2 text-sm text-slate-400">
                <Globe size={14} />
                API 连接
              </div>
              <span
                className={`text-xs font-medium px-2 py-0.5 rounded ${systemStatus ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}
              >
                {systemStatus ? '正常' : '异常'}
              </span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-slate-700/50">
              <div className="flex items-center gap-2 text-sm text-slate-400">
                <ListChecks size={14} />
                活跃任务
              </div>
              <span className="text-xs font-medium text-slate-300">
                {systemStatus?.active_tasks ?? 0} / {systemStatus?.total_tasks ?? 0}
              </span>
            </div>
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center gap-2 text-sm text-slate-400">版本</div>
              <span className="text-xs font-medium text-slate-300">v1.0.0</span>
            </div>
          </div>
        </motion.div>

        {/* Recent tasks */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.25 }}
          className="lg:col-span-2 bg-slate-800 border border-slate-700/50 rounded-xl p-5"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-200">最近创建的任务</h2>
            <button
              onClick={() => navigate('/tasks')}
              className="flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 transition-colors"
            >
              查看全部
              <ArrowRight size={14} />
            </button>
          </div>

          {recentTasks.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 text-slate-500">
              <Ticket size={32} className="mb-2 opacity-30" />
              <p className="text-sm">暂无任务，创建一个吧</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {recentTasks.map((task, i) => (
                <div key={task.id} className="scale-95 origin-top-left">
                  <TaskCard task={task} index={i} />
                </div>
              ))}
            </div>
          )}
        </motion.div>
      </div>
    </div>
  )
}
