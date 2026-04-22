import { useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { TaskLog } from '@/services/api'
import { format } from 'date-fns'

interface LogViewerProps {
  logs: TaskLog[]
  autoScroll?: boolean
}

const levelColors: Record<TaskLog['level'], string> = {
  info: 'text-slate-300',
  warn: 'text-amber-400',
  error: 'text-red-400',
  success: 'text-emerald-400',
}

const levelBg: Record<TaskLog['level'], string> = {
  info: 'bg-slate-800/30',
  warn: 'bg-amber-500/5',
  error: 'bg-red-500/5',
  success: 'bg-emerald-500/5',
}

const levelBorder: Record<TaskLog['level'], string> = {
  info: 'border-l-slate-600',
  warn: 'border-l-amber-500',
  error: 'border-l-red-500',
  success: 'border-l-emerald-500',
}

export default function LogViewer({ logs, autoScroll = true }: LogViewerProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [logs, autoScroll])

  if (logs.length === 0) {
    return (
      <div className="flex items-center justify-center h-40 text-sm text-slate-500">
        暂无日志
      </div>
    )
  }

  return (
    <div
      ref={scrollRef}
      className="h-96 overflow-y-auto rounded-xl bg-slate-950 border border-slate-800 p-3 font-mono text-xs"
    >
      <AnimatePresence initial={false}>
        {logs.map((log, i) => {
          const ts = log.timestamp ? new Date(log.timestamp) : new Date()
          return (
            <motion.div
              key={`${log.timestamp}-${i}`}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.2 }}
              className={`flex items-start gap-2 px-2 py-1.5 rounded border-l-2 ${levelBorder[log.level]} ${levelBg[log.level]} mb-0.5`}
            >
              <span className="shrink-0 text-slate-600 tabular-nums">
                {format(ts, 'HH:mm:ss')}
              </span>
              <span
                className={`shrink-0 px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${levelColors[log.level]} bg-slate-900/50`}
              >
                {log.level}
              </span>
              <span className={`break-all ${levelColors[log.level]}`}>{log.message}</span>
            </motion.div>
          )
        })}
      </AnimatePresence>
    </div>
  )
}
