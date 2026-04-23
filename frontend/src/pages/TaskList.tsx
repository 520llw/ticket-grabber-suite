import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PlusCircle, Search, Filter, Trash2, Play, Square } from 'lucide-react';
import { useStore } from '../store/useStore';
import TaskCard from '../components/TaskCard';
import { clsx } from 'clsx';

const statusFilters = [
  { value: '', label: '全部' },
  { value: 'running', label: '运行中' },
  { value: 'idle', label: '待运行' },
  { value: 'success', label: '已成功' },
  { value: 'failed', label: '已失败' },
  { value: 'stopped', label: '已停止' },
];

const platformFilters = [
  { value: '', label: '全部平台' },
  { value: 'damai', label: '大麦' },
  { value: 'maoyan', label: '猫眼' },
  { value: '12306', label: '12306' },
];

export default function TaskList() {
  const navigate = useNavigate();
  const { tasks, fetchTasks, removeTask, startTask, stopTask } = useStore();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [platformFilter, setPlatformFilter] = useState('');
  const [selected, setSelected] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetchTasks();
    const timer = setInterval(fetchTasks, 5000);
    return () => clearInterval(timer);
  }, [fetchTasks]);

  const filtered = tasks.filter((t) => {
    if (statusFilter && t.status !== statusFilter) return false;
    if (platformFilter && t.platform !== platformFilter) return false;
    if (search) {
      const q = search.toLowerCase();
      return t.name.toLowerCase().includes(q) || t.url.toLowerCase().includes(q) || t.platform.includes(q);
    }
    return true;
  });

  const toggleSelect = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const selectAll = () => {
    if (selected.size === filtered.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(filtered.map((t) => t.id)));
    }
  };

  const batchAction = async (action: 'start' | 'stop' | 'delete') => {
    const ids = Array.from(selected);
    for (const id of ids) {
      try {
        if (action === 'start') await startTask(id);
        else if (action === 'stop') await stopTask(id);
        else if (action === 'delete') await removeTask(id);
      } catch (e) { /* continue */ }
    }
    setSelected(new Set());
    fetchTasks();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">任务列表</h1>
          <p className="text-sm text-muted-foreground mt-1">共 {tasks.length} 个任务，显示 {filtered.length} 个</p>
        </div>
        <button
          onClick={() => navigate('/tasks/new')}
          className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20"
        >
          <PlusCircle className="w-4 h-4" /> 新建任务
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="搜索任务名称、URL..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-card border border-border rounded-lg text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50"
          />
        </div>
        <div className="flex gap-1 bg-card border border-border rounded-lg p-1">
          {statusFilters.map(({ value, label }) => (
            <button
              key={value}
              onClick={() => setStatusFilter(value)}
              className={clsx(
                'px-3 py-1.5 rounded-md text-xs font-medium transition-colors',
                statusFilter === value ? 'bg-primary/20 text-primary' : 'text-muted-foreground hover:text-foreground'
              )}
            >
              {label}
            </button>
          ))}
        </div>
        <select
          value={platformFilter}
          onChange={(e) => setPlatformFilter(e.target.value)}
          className="px-3 py-2.5 bg-card border border-border rounded-lg text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
        >
          {platformFilters.map(({ value, label }) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </select>
      </div>

      {/* Batch actions */}
      {selected.size > 0 && (
        <div className="flex items-center gap-3 p-3 bg-card border border-primary/30 rounded-lg">
          <span className="text-sm text-foreground">已选择 {selected.size} 个任务</span>
          <div className="flex gap-2 ml-auto">
            <button onClick={() => batchAction('start')} className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-500/15 text-emerald-400 text-xs hover:bg-emerald-500/25">
              <Play className="w-3 h-3" /> 批量开始
            </button>
            <button onClick={() => batchAction('stop')} className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-amber-500/15 text-amber-400 text-xs hover:bg-amber-500/25">
              <Square className="w-3 h-3" /> 批量停止
            </button>
            <button onClick={() => batchAction('delete')} className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-red-500/15 text-red-400 text-xs hover:bg-red-500/25">
              <Trash2 className="w-3 h-3" /> 批量删除
            </button>
          </div>
        </div>
      )}

      {/* Select all */}
      {filtered.length > 0 && (
        <div className="flex items-center gap-2">
          <button onClick={selectAll} className="text-xs text-muted-foreground hover:text-foreground">
            {selected.size === filtered.length ? '取消全选' : '全选'}
          </button>
        </div>
      )}

      {/* Task grid */}
      {filtered.length === 0 ? (
        <div className="bg-card border border-border rounded-xl p-12 text-center">
          <Filter className="w-12 h-12 text-muted-foreground/30 mx-auto mb-3" />
          <p className="text-sm text-muted-foreground">没有匹配的任务</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map((task) => (
            <div key={task.id} className="relative">
              <input
                type="checkbox"
                checked={selected.has(task.id)}
                onChange={() => toggleSelect(task.id)}
                className="absolute top-3 right-3 z-10 w-4 h-4 rounded border-border accent-primary cursor-pointer"
                onClick={(e) => e.stopPropagation()}
              />
              <TaskCard task={task} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
