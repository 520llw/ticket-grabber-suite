import { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Play, Square, RotateCcw, Trash2, Edit3, Save, X, Calendar, Users, Banknote, Link, TrainFront } from 'lucide-react';
import { useStore } from '../store/useStore';
import { taskApi, TaskLog } from '../services/api';
import StatusBadge from '../components/StatusBadge';
import PlatformIcon, { getPlatformLabel } from '../components/PlatformIcon';
import LogViewer from '../components/LogViewer';
import CountdownTimer from '../components/CountdownTimer';

export default function TaskDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { currentTask, logs, fetchTask, fetchLogs, addLog, startTask, stopTask, restartTask, removeTask, updateTask, clearLogs } = useStore();
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState<Record<string, any>>({});
  const sseRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!id) return;
    fetchTask(id);
    fetchLogs(id);

    const pollTimer = setInterval(() => {
      fetchTask(id);
    }, 3000);

    return () => clearInterval(pollTimer);
  }, [id, fetchTask, fetchLogs]);

  // SSE for live logs
  useEffect(() => {
    if (!id) return;
    const sse = taskApi.logStream(id);
    sseRef.current = sse;

    sse.onmessage = (event) => {
      try {
        const log: TaskLog = JSON.parse(event.data);
        addLog(id, log);
      } catch (e) { /* ignore */ }
    };

    sse.onerror = () => {
      sse.close();
    };

    return () => {
      sse.close();
    };
  }, [id, addLog]);

  if (!currentTask) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-sm text-muted-foreground">加载中...</div>
      </div>
    );
  }

  const task = currentTask;
  const taskLogs = logs[task.id] || [];
  const isRunning = task.status === 'running' || task.status === 'waiting';
  const canStart = task.status === 'idle' || task.status === 'stopped' || task.status === 'failed';
  const is12306 = task.platform === '12306';

  const startEdit = () => {
    setEditForm({
      name: task.name,
      url: task.url,
      date: task.date,
      session: task.session,
      price: task.price,
      ticket_count: task.ticket_count,
      from_station: task.from_station,
      to_station: task.to_station,
      train_number: task.train_number,
      seat_type: task.seat_type,
      max_retries: task.max_retries,
      retry_interval: task.retry_interval,
    });
    setEditing(true);
  };

  const saveEdit = async () => {
    await updateTask(task.id, editForm);
    setEditing(false);
  };

  const handleDelete = async () => {
    if (confirm('确定要删除这个任务吗？')) {
      await removeTask(task.id);
      navigate('/tasks');
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/tasks')} className="p-2 rounded-lg hover:bg-secondary transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <PlatformIcon platform={task.platform} size="lg" />
          <div>
            <h1 className="text-xl font-bold text-foreground">{task.name}</h1>
            <div className="flex items-center gap-3 mt-1">
              <span className="text-xs text-muted-foreground">{getPlatformLabel(task.platform)}</span>
              <StatusBadge status={task.status} />
            </div>
          </div>
        </div>

        <div className="flex gap-2">
          {canStart && (
            <button onClick={() => startTask(task.id)} className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20">
              <Play className="w-4 h-4" /> 开始抢票
            </button>
          )}
          {isRunning && (
            <button onClick={() => stopTask(task.id)} className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-red-500/15 text-red-400 text-sm font-medium hover:bg-red-500/25 transition-colors">
              <Square className="w-4 h-4" /> 停止
            </button>
          )}
          {(task.status === 'failed' || task.status === 'stopped') && (
            <button onClick={() => restartTask(task.id)} className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-amber-500/15 text-amber-400 text-sm font-medium hover:bg-amber-500/25 transition-colors">
              <RotateCcw className="w-4 h-4" /> 重试
            </button>
          )}
          {!editing && !isRunning && (
            <button onClick={startEdit} className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-secondary text-foreground text-sm hover:bg-secondary/80 transition-colors">
              <Edit3 className="w-3.5 h-3.5" /> 编辑
            </button>
          )}
          <button onClick={handleDelete} className="p-2 rounded-lg text-red-400 hover:bg-red-500/15 transition-colors">
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Task Info */}
      <div className="bg-card border border-border rounded-xl p-5">
        <h2 className="text-sm font-semibold mb-4">任务信息</h2>

        {editing ? (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-muted-foreground">任务名称</label>
                <input value={editForm.name} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} className="w-full mt-1 px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30" />
              </div>
              {is12306 ? (
                <>
                  <div>
                    <label className="text-xs text-muted-foreground">出发站</label>
                    <input value={editForm.from_station} onChange={(e) => setEditForm({ ...editForm, from_station: e.target.value })} className="w-full mt-1 px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30" />
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground">到达站</label>
                    <input value={editForm.to_station} onChange={(e) => setEditForm({ ...editForm, to_station: e.target.value })} className="w-full mt-1 px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30" />
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground">车次号</label>
                    <input value={editForm.train_number} onChange={(e) => setEditForm({ ...editForm, train_number: e.target.value })} className="w-full mt-1 px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30" />
                  </div>
                </>
              ) : (
                <div>
                  <label className="text-xs text-muted-foreground">链接</label>
                  <input value={editForm.url} onChange={(e) => setEditForm({ ...editForm, url: e.target.value })} className="w-full mt-1 px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30" />
                </div>
              )}
              <div>
                <label className="text-xs text-muted-foreground">日期</label>
                <input value={editForm.date} onChange={(e) => setEditForm({ ...editForm, date: e.target.value })} className="w-full mt-1 px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30" />
              </div>
              <div>
                <label className="text-xs text-muted-foreground">最大重试</label>
                <input type="number" value={editForm.max_retries} onChange={(e) => setEditForm({ ...editForm, max_retries: parseInt(e.target.value) })} className="w-full mt-1 px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30" />
              </div>
            </div>
            <div className="flex gap-2 justify-end">
              <button onClick={() => setEditing(false)} className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-border text-sm hover:bg-secondary">
                <X className="w-3.5 h-3.5" /> 取消
              </button>
              <button onClick={saveEdit} className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-primary text-primary-foreground text-sm hover:bg-primary/90">
                <Save className="w-3.5 h-3.5" /> 保存
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
            {is12306 ? (
              <>
                <InfoItem icon={TrainFront} label="路线" value={`${task.from_station} → ${task.to_station}`} />
                {task.train_number && <InfoItem icon={TrainFront} label="车次" value={task.train_number} />}
                {task.seat_type && <InfoItem icon={Banknote} label="席别" value={task.seat_type} />}
              </>
            ) : (
              <>
                <InfoItem icon={Link} label="链接" value={task.url} isLink />
                {task.session && <InfoItem icon={Calendar} label="场次" value={task.session} />}
                {task.price && <InfoItem icon={Banknote} label="票档" value={`${task.price} x ${task.ticket_count}张`} />}
              </>
            )}
            <InfoItem icon={Calendar} label="日期" value={task.date || '未设置'} />
            {task.buyers.length > 0 && (
              <InfoItem icon={Users} label={is12306 ? '乘车人' : '观演人'} value={task.buyers.join(', ')} />
            )}
            {task.cron_time && (
              <div className="col-span-full">
                <CountdownTimer targetTime={task.cron_time} />
              </div>
            )}
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-4 gap-3 mt-4 pt-4 border-t border-border">
          <MiniStat label="尝试次数" value={task.attempt_count} />
          <MiniStat label="最大重试" value={task.max_retries} />
          <MiniStat label="重试间隔" value={`${task.retry_interval}s`} />
          <MiniStat label="优先级" value={task.priority} />
        </div>

        {task.last_error && (
          <div className="mt-3 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-xs text-red-400">
            最后错误: {task.last_error}
          </div>
        )}
      </div>

      {/* Logs */}
      <div className="bg-card border border-border rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold">运行日志</h2>
          <div className="flex gap-2">
            <span className="text-xs text-muted-foreground">{taskLogs.length} 条日志</span>
            {taskLogs.length > 0 && (
              <button onClick={() => clearLogs(task.id)} className="text-xs text-red-400 hover:underline">清空</button>
            )}
          </div>
        </div>
        <LogViewer logs={taskLogs} maxHeight="500px" />
      </div>
    </div>
  );
}

function InfoItem({ icon: Icon, label, value, isLink }: { icon: any; label: string; value: string; isLink?: boolean }) {
  return (
    <div className="flex items-start gap-2">
      <Icon className="w-4 h-4 text-muted-foreground mt-0.5 shrink-0" />
      <div className="min-w-0">
        <p className="text-xs text-muted-foreground">{label}</p>
        {isLink ? (
          <a href={value} target="_blank" rel="noopener noreferrer" className="text-sm text-primary hover:underline truncate block">
            {value}
          </a>
        ) : (
          <p className="text-sm font-medium truncate">{value}</p>
        )}
      </div>
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: any }) {
  return (
    <div className="text-center">
      <p className="text-lg font-bold text-foreground">{value}</p>
      <p className="text-[10px] text-muted-foreground">{label}</p>
    </div>
  );
}
