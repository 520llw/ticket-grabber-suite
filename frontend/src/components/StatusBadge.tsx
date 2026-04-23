import { clsx } from 'clsx';
import { Loader2, CheckCircle2, XCircle, StopCircle, Clock, Pause } from 'lucide-react';

const statusConfig: Record<string, { label: string; color: string; icon: any }> = {
  idle: { label: '待运行', color: 'bg-slate-500/20 text-slate-400 border-slate-500/30', icon: Clock },
  running: { label: '运行中', color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30', icon: Loader2 },
  waiting: { label: '等待中', color: 'bg-amber-500/20 text-amber-400 border-amber-500/30', icon: Pause },
  success: { label: '已成功', color: 'bg-green-500/20 text-green-400 border-green-500/30', icon: CheckCircle2 },
  failed: { label: '已失败', color: 'bg-red-500/20 text-red-400 border-red-500/30', icon: XCircle },
  stopped: { label: '已停止', color: 'bg-orange-500/20 text-orange-400 border-orange-500/30', icon: StopCircle },
};

export default function StatusBadge({ status }: { status: string }) {
  const config = statusConfig[status] || statusConfig.idle;
  const Icon = config.icon;

  return (
    <span className={clsx('inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border', config.color)}>
      <Icon className={clsx('w-3 h-3', status === 'running' && 'animate-spin')} />
      {config.label}
    </span>
  );
}
