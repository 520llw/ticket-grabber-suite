import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Play, Square, Clock, ExternalLink } from 'lucide-react'
import type { Task } from '@/services/api'
import PlatformIcon from './PlatformIcon'
import StatusBadge from './StatusBadge'
import CountdownTimer from './CountdownTimer'
import { taskApi } from '@/services/api'
import { useStore } from '@/store/useStore'

interface TaskCardProps {
  task: Task
  index?: number
}

export default function TaskCard({ task, index = 0 }: TaskCardProps) {
  const navigate = useNavigate()
  const { updateTask } = useStore()
  const isRunning = task.status === 'running'

  const handleStart = async (e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await taskApi.start(task.id)
      const updated = { ...task, status: 'running' as const }
      updateTask(updated)
    } catch (err) {
      console.error('Failed to start task', err)
    }
  }

  const handleStop = async (e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await taskApi.stop(task.id)
      const updated = { ...task, status: 'stopped' as const }
      updateTask(updated)
    } catch (err) {
      console.error('Failed to stop task', err)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      onClick={() => navigate(`/tasks/${task.id}`)}
      className="group relative bg-slate-800 border border-slate-700/50 rounded-xl p-5 cursor-pointer hover:shadow-lg hover:shadow-emerald-900/10 hover:border-slate-600/50 transition-shadow"
    >
      {/* Top row: platform + status */}
      <div className="flex items-center justify-between mb-3">
        <PlatformIcon platform={task.platform} />
        <StatusBadge status={task.status} />
      </div>

      {/* Task name */}
      <h3 className="text-base font-semibold text-slate-100 mb-1 truncate">{task.name}</h3>

      {/* URL */}
      <div className="flex items-center gap-1 text-xs text-slate-500 mb-3 truncate">
        <ExternalLink size={12} />
        <span className="truncate">{task.url}</span>
      </div>

      {/* Countdown */}
      {task.cron_time && task.status === 'idle' && (
        <div className="mb-4">
          <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-2">
            <Clock size={12} />
            <span>距开抢还有</span>
          </div>
          <CountdownTimer target={task.cron_time} />
        </div>
      )}

      {/* Meta info */}
      <div className="flex items-center gap-3 text-xs text-slate-500 mb-4">
        <span>{task.date || '未设置日期'}</span>
        <span className="text-slate-700">|</span>
        <span>{task.ticket_count} 张</span>
        <span className="text-slate-700">|</span>
        <span>{task.price || '未设票价'}</span>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 pt-3 border-t border-slate-700/50">
        {isRunning ? (
          <button
            onClick={handleStop}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-red-600/10 text-red-400 border border-red-600/20 hover:bg-red-600/20 transition-colors"
          >
            <Square size={13} />
            停止
          </button>
        ) : (
          <button
            onClick={handleStart}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-600/10 text-emerald-400 border border-emerald-600/20 hover:bg-emerald-600/20 transition-colors"
          >
            <Play size={13} />
            开始
          </button>
        )}
      </div>
    </motion.div>
  )
}
