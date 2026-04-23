import { useNavigate } from 'react-router-dom';
import { Play, Square, RotateCcw, Calendar, Users, Banknote } from 'lucide-react';
import { Task } from '../services/api';
import { useStore } from '../store/useStore';
import StatusBadge from './StatusBadge';
import PlatformIcon, { getPlatformLabel } from './PlatformIcon';
import CountdownTimer from './CountdownTimer';

export default function TaskCard({ task }: { task: Task }) {
  const navigate = useNavigate();
  const { startTask, stopTask, restartTask } = useStore();

  const handleAction = async (e: React.MouseEvent, action: () => Promise<void>) => {
    e.stopPropagation();
    try {
      await action();
    } catch (err) {
      console.error(err);
    }
  };

  const isRunning = task.status === 'running' || task.status === 'waiting';
  const canStart = task.status === 'idle' || task.status === 'stopped' || task.status === 'failed';

  return (
    <div
      onClick={() => navigate(`/tasks/${task.id}`)}
      className="group bg-card border border-border rounded-xl p-4 hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5 transition-all cursor-pointer"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <PlatformIcon platform={task.platform} />
          <div>
            <h3 className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors line-clamp-1">
              {task.name}
            </h3>
            <span className="text-[10px] text-muted-foreground">{getPlatformLabel(task.platform)}</span>
          </div>
        </div>
        <StatusBadge status={task.status} />
      </div>

      {/* Info */}
      <div className="space-y-1.5 mb-3">
        {task.date && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Calendar className="w-3 h-3" />
            <span>{task.date} {task.session}</span>
          </div>
        )}
        {task.price && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Banknote className="w-3 h-3" />
            <span>{task.price} x {task.ticket_count}张</span>
          </div>
        )}
        {task.buyers.length > 0 && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Users className="w-3 h-3" />
            <span>{task.buyers.join(', ')}</span>
          </div>
        )}
        {task.cron_time && task.status !== 'success' && (
          <CountdownTimer targetTime={task.cron_time} />
        )}
        {task.attempt_count > 0 && (
          <div className="text-[10px] text-muted-foreground">
            已尝试 {task.attempt_count} 次
            {task.last_error && <span className="text-red-400 ml-1">| {task.last_error.slice(0, 40)}</span>}
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        {canStart && (
          <button
            onClick={(e) => handleAction(e, () => startTask(task.id))}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary/15 text-primary text-xs font-medium hover:bg-primary/25 transition-colors"
          >
            <Play className="w-3 h-3" /> 开始
          </button>
        )}
        {isRunning && (
          <button
            onClick={(e) => handleAction(e, () => stopTask(task.id))}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-500/15 text-red-400 text-xs font-medium hover:bg-red-500/25 transition-colors"
          >
            <Square className="w-3 h-3" /> 停止
          </button>
        )}
        {(task.status === 'failed' || task.status === 'stopped') && (
          <button
            onClick={(e) => handleAction(e, () => restartTask(task.id))}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500/15 text-amber-400 text-xs font-medium hover:bg-amber-500/25 transition-colors"
          >
            <RotateCcw className="w-3 h-3" /> 重试
          </button>
        )}
      </div>
    </div>
  );
}
