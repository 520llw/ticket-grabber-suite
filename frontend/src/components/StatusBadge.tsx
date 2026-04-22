import type { Task } from '@/services/api'

interface StatusBadgeProps {
  status: Task['status']
  showPulse?: boolean
}

const statusMeta: Record<
  Task['status'],
  { label: string; bg: string; text: string; border: string; dot: string }
> = {
  idle: {
    label: '闲置',
    bg: 'bg-slate-500/10',
    text: 'text-slate-400',
    border: 'border-slate-500/20',
    dot: 'bg-slate-400',
  },
  running: {
    label: '抢票中',
    bg: 'bg-emerald-500/10',
    text: 'text-emerald-400',
    border: 'border-emerald-500/20',
    dot: 'bg-emerald-400',
  },
  success: {
    label: '成功',
    bg: 'bg-emerald-500/10',
    text: 'text-emerald-400',
    border: 'border-emerald-500/20',
    dot: 'bg-emerald-400',
  },
  failed: {
    label: '失败',
    bg: 'bg-red-500/10',
    text: 'text-red-400',
    border: 'border-red-500/20',
    dot: 'bg-red-400',
  },
  stopped: {
    label: '已停止',
    bg: 'bg-amber-500/10',
    text: 'text-amber-400',
    border: 'border-amber-500/20',
    dot: 'bg-amber-400',
  },
}

export default function StatusBadge({ status, showPulse = true }: StatusBadgeProps) {
  const meta = statusMeta[status]
  const isRunning = status === 'running'

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border ${meta.bg} ${meta.text} ${meta.border}`}
    >
      <span className="relative flex h-2 w-2">
        <span
          className={`absolute inline-flex h-full w-full rounded-full opacity-75 ${meta.dot} ${isRunning && showPulse ? 'animate-ping' : ''}`}
        />
        <span className={`relative inline-flex rounded-full h-2 w-2 ${meta.dot}`} />
      </span>
      {meta.label}
    </span>
  )
}
