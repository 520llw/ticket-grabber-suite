import type { Task['platform'] } from '@/services/api'
import { Ticket, Train, ShoppingBag, Globe } from 'lucide-react'

interface PlatformIconProps {
  platform: Task['platform']
  size?: number
  showLabel?: boolean
}

const platformMeta: Record<
  Task['platform'],
  { icon: React.ReactNode; label: string; bg: string; text: string; border: string }
> = {
  damai: {
    icon: <Ticket size={16} />,
    label: '大麦',
    bg: 'bg-red-500/10',
    text: 'text-red-400',
    border: 'border-red-500/20',
  },
  maoyan: {
    icon: <ShoppingBag size={16} />,
    label: '猫眼',
    bg: 'bg-orange-500/10',
    text: 'text-orange-400',
    border: 'border-orange-500/20',
  },
  '12306': {
    icon: <Train size={16} />,
    label: '12306',
    bg: 'bg-blue-500/10',
    text: 'text-blue-400',
    border: 'border-blue-500/20',
  },
  custom: {
    icon: <Globe size={16} />,
    label: '自定义',
    bg: 'bg-slate-500/10',
    text: 'text-slate-400',
    border: 'border-slate-500/20',
  },
}

export default function PlatformIcon({ platform, size = 16, showLabel = true }: PlatformIconProps) {
  const meta = platformMeta[platform]
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border ${meta.bg} ${meta.text} ${meta.border}`}
    >
      <span style={{ width: size, height: size, display: 'inline-flex', alignItems: 'center' }}>
        {meta.icon}
      </span>
      {showLabel && <span>{meta.label}</span>}
    </span>
  )
}
