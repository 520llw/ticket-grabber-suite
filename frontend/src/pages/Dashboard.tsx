import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { PlusCircle, Activity, CheckCircle2, XCircle, ListTodo, Cpu, HardDrive, Clock } from 'lucide-react';
import { useStore } from '../store/useStore';
import TaskCard from '../components/TaskCard';

export default function Dashboard() {
  const navigate = useNavigate();
  const { tasks, systemStatus, fetchTasks, fetchStatus } = useStore();

  useEffect(() => {
    fetchTasks();
    fetchStatus();
    const timer = setInterval(() => {
      fetchTasks();
      fetchStatus();
    }, 5000);
    return () => clearInterval(timer);
  }, [fetchTasks, fetchStatus]);

  const running = tasks.filter((t) => t.status === 'running' || t.status === 'waiting').length;
  const success = tasks.filter((t) => t.status === 'success').length;
  const failed = tasks.filter((t) => t.status === 'failed').length;

  const stats = [
    { label: '总任务', value: tasks.length, icon: ListTodo, color: 'text-blue-400', bg: 'bg-blue-500/15' },
    { label: '运行中', value: running, icon: Activity, color: 'text-emerald-400', bg: 'bg-emerald-500/15' },
    { label: '已成功', value: success, icon: CheckCircle2, color: 'text-green-400', bg: 'bg-green-500/15' },
    { label: '已失败', value: failed, icon: XCircle, color: 'text-red-400', bg: 'bg-red-500/15' },
  ];

  const formatUptime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return h > 0 ? `${h}h ${m}m` : `${m}m`;
  };

  const recentTasks = [...tasks].sort((a, b) => b.updated_at.localeCompare(a.updated_at)).slice(0, 6);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">仪表盘</h1>
          <p className="text-sm text-muted-foreground mt-1">抢票系统运行概览</p>
        </div>
        <button
          onClick={() => navigate('/tasks/new')}
          className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20"
        >
          <PlusCircle className="w-4 h-4" /> 新建任务
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map(({ label, value, icon: Icon, color, bg }) => (
          <div key={label} className="bg-card border border-border rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <div className={`w-10 h-10 rounded-lg ${bg} flex items-center justify-center`}>
                <Icon className={`w-5 h-5 ${color}`} />
              </div>
              <span className={`text-2xl font-bold ${color}`}>{value}</span>
            </div>
            <p className="text-xs text-muted-foreground">{label}</p>
          </div>
        ))}
      </div>

      {/* System Status */}
      {systemStatus && (
        <div className="bg-card border border-border rounded-xl p-5">
          <h2 className="text-sm font-semibold text-foreground mb-4">系统状态</h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="flex items-center gap-3">
              <Cpu className="w-4 h-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">CPU 使用率</p>
                <p className="text-sm font-medium">{systemStatus.cpu_percent.toFixed(1)}%</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <HardDrive className="w-4 h-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">内存使用</p>
                <p className="text-sm font-medium">{systemStatus.memory_mb.toFixed(0)} MB</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Clock className="w-4 h-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">运行时间</p>
                <p className="text-sm font-medium">{formatUptime(systemStatus.uptime_seconds)}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Activity className="w-4 h-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">版本</p>
                <p className="text-sm font-medium">v{systemStatus.version}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Recent Tasks */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-foreground">最近任务</h2>
          {tasks.length > 6 && (
            <button onClick={() => navigate('/tasks')} className="text-xs text-primary hover:underline">
              查看全部
            </button>
          )}
        </div>
        {recentTasks.length === 0 ? (
          <div className="bg-card border border-border rounded-xl p-12 text-center">
            <ListTodo className="w-12 h-12 text-muted-foreground/30 mx-auto mb-3" />
            <p className="text-sm text-muted-foreground mb-4">还没有任何任务</p>
            <button
              onClick={() => navigate('/tasks/new')}
              className="px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
            >
              创建第一个任务
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {recentTasks.map((task) => (
              <TaskCard key={task.id} task={task} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
