import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Play,
  Square,
  Trash2,
  ArrowLeft,
  Calendar,
  Clock,
  Link,
  User,
  Ticket,
  AlertTriangle,
} from 'lucide-react'
import { taskApi } from '@/services/api'
import type { Task, TaskLog } from '@/services/api'
import { useStore } from '@/store/useStore'
import PlatformIcon from '@/components/PlatformIcon'
import StatusBadge from '@/components/StatusBadge'
import LogViewer from '@/components/LogViewer'
import CountdownTimer from '@/components/CountdownTimer'

export default function TaskDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { currentTask, setCurrentTask, logs, addLog } = useStore()
  const [task, setTask] = useState<Task | null>(null)
  const [taskLogs, setTaskLogs] = useState<TaskLog[]>([])
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const esRef = useRef<EventSource | null>(null)

  const displayedTask = task || currentTask

  // Fetch task details
  useEffect(() => {
    if (!id) return
    let mounted = true
    const fetchTask = async () => {
      try {
        const data = await taskApi.get(id)
        if (mounted) {
          setTask(data)
          setCurrentTask(data)
        }
      } catch {
        // ignore
      }
    }
    fetchTask()
    const interval = setInterval(fetchTask, 2000)
    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [id, setCurrentTask])

  // Fetch logs
  useEffect(() => {
    if (!id) return
    let mounted = true
    const fetchLogs = async () => {
      try {
        const data = await taskApi.logs(id, 100)
        if (mounted) setTaskLogs(data)
      } catch {
        // ignore
      }
    }
    fetchLogs()
    const interval = setInterval(fetchLogs, 2000)
    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [id])

  // SSE stream when running
  useEffect(() => {
    if (!id || displayedTask?.status !== 'running') {
      esRef.current?.close()
      esRef.current = null
      return
    }

    const es = taskApi.logStream(id)
    esRef.current = es

    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        if (data.task_id && data.message) {
          addLog(data.task_id, data)
        }
      } catch {
        // ignore
      }
    }

    return () => {
      es.close()
      esRef.current = null
    }
  }, [id, displayedTask?.status, addLog])

  // Merge fetched logs + SSE logs from store
  const mergedLogs = [...taskLogs, ...(id ? logs[id] || [] : [])]
  // Deduplicate by timestamp+message
  const seen = new Set<string>()
  const uniqueLogs = mergedLogs.filter((log) => {
    const key = `${log.timestamp}-${log.message}`
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })

  const handleStart = async () => {
    if (!id) return
    try {
      await taskApi.start(id)
      const updated = await taskApi.get(id)
      setTask(updated)
      setCurrentTask(updated)
    } catch (err) {
      console.error('Failed to start', err)
    }
  }

  const handleStop = async () => {
    if (!id) return
    try {
      await taskApi.stop(id)
      const updated = await taskApi.get(id)
      setTask(updated)
      setCurrentTask(updated)
    } catch (err) {
      console.error('Failed to stop', err)
    }
  }

  const handleDelete = async () => {
    if (!id) return
    try {
      await taskApi.delete(id)
      navigate('/tasks')
    } catch (err) {
      console.error('Failed to delete', err)
    }
  }

  if (!displayedTask) {
    return (
      <div className="flex items-center justify-center py-20 text-slate-500">
        加载任务详情...
      </div>
    )
  }

  const isRunning = displayedTask.status === 'running'

  return (
    <div className="space-y-6">
      {/* Back + title */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate('/tasks')}
          className="p-2 rounded-lg bg-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-700 transition-colors"
        >
          <ArrowLeft size={18} />
        </button>
        <div>
          <h1 className="text-xl font-bold text-slate-100">{displayedTask.name}</h1>
        </div>
      </div>

      {/* Task info card */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-slate-800 border border-slate-700/50 rounded-xl p-5"
      >
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <PlatformIcon platform={displayedTask.platform} />
              <StatusBadge status={displayedTask.status} />
            </div>

            {displayedTask.cron_time && displayedTask.status === 'idle' && (
              <div className="flex items-center gap-2">
                <Clock size={14} className="text-slate-500" />
                <CountdownTimer target={displayedTask.cron_time} />
              </div>
            )}

            <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-400">
              <span className="flex items-center gap-1.5">
                <Calendar size={13} />
                {displayedTask.date || '未设置日期'}
              </span>
              <span className="flex items-center gap-1.5">
                <Ticket size={13} />
                {displayedTask.price || '未设票价'} · {displayedTask.ticket_count} 张
              </span>
              <span className="flex items-center gap-1.5">
                <User size={13} />
                {displayedTask.buyers?.filter(Boolean).join(', ') || '未设置'}
              </span>
            </div>

            <div className="flex items-center gap-1.5 text-xs text-slate-600">
              <Link size={12} />
              <span className="truncate max-w-md">{displayedTask.url}</span>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 shrink-0">
            {isRunning ? (
              <button
                onClick={handleStop}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium bg-red-600/10 text-red-400 border border-red-600/20 hover:bg-red-600/20 transition-colors"
              >
                <Square size={14} />
                停止
              </button>
            ) : (
              <button
                onClick={handleStart}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium bg-emerald-600 hover:bg-emerald-500 text-white transition-colors"
              >
                <Play size={14} />
                开始抢票
              </button>
            )}
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium bg-red-600/10 text-red-400 border border-red-600/20 hover:bg-red-600/20 transition-colors"
            >
              <Trash2 size={14} />
            </button>
          </div>
        </div>
      </motion.div>

      {/* Logs */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-slate-200">实时日志</h2>
          {isRunning && (
            <span className="flex items-center gap-1.5 text-xs text-emerald-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              实时推送中
            </span>
          )}
        </div>
        <LogViewer logs={uniqueLogs} />
      </div>

      {/* Config read-only */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-slate-800 border border-slate-700/50 rounded-xl p-5"
      >
        <h2 className="text-sm font-semibold text-slate-200 mb-4">任务配置</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
          <div className="bg-slate-900/50 rounded-lg p-3">
            <p className="text-xs text-slate-600 mb-1">任务ID</p>
            <p className="text-slate-300 font-mono text-xs">{displayedTask.id}</p>
          </div>
          <div className="bg-slate-900/50 rounded-lg p-3">
            <p className="text-xs text-slate-600 mb-1">平台</p>
            <p className="text-slate-300">{displayedTask.platform}</p>
          </div>
          <div className="bg-slate-900/50 rounded-lg p-3">
            <p className="text-xs text-slate-600 mb-1">场次</p>
            <p className="text-slate-300">{displayedTask.session || '—'}</p>
          </div>
          <div className="bg-slate-900/50 rounded-lg p-3">
            <p className="text-xs text-slate-600 mb-1">定时时间</p>
            <p className="text-slate-300">{displayedTask.cron_time || '—'}</p>
          </div>
          <div className="bg-slate-900/50 rounded-lg p-3">
            <p className="text-xs text-slate-600 mb-1">Headless</p>
            <p className="text-slate-300">{displayedTask.headless ? '是' : '否'}</p>
          </div>
          <div className="bg-slate-900/50 rounded-lg p-3">
            <p className="text-xs text-slate-600 mb-1">创建时间</p>
            <p className="text-slate-300 text-xs">{new Date(displayedTask.created_at).toLocaleString()}</p>
          </div>
        </div>
      </motion.div>

      {/* Delete confirm modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-slate-800 border border-slate-700 rounded-xl p-6 max-w-sm w-full mx-4"
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2 rounded-lg bg-red-500/10 text-red-400">
                <AlertTriangle size={20} />
              </div>
              <h3 className="text-base font-semibold text-slate-100">确认删除</h3>
            </div>
            <p className="text-sm text-slate-400 mb-5">
              删除后任务及其日志将无法恢复，确定继续吗？
            </p>
            <div className="flex items-center justify-end gap-2">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="px-4 py-2 rounded-lg text-sm font-medium bg-slate-700 hover:bg-slate-600 text-slate-200 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleDelete}
                className="px-4 py-2 rounded-lg text-sm font-medium bg-red-600 hover:bg-red-500 text-white transition-colors"
              >
                确认删除
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}
