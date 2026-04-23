import { useEffect, useState } from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { LayoutDashboard, ListTodo, PlusCircle, Settings, Ticket, Activity, Menu, X } from 'lucide-react';
import { useStore } from '../store/useStore';
import { clsx } from 'clsx';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: '仪表盘' },
  { to: '/tasks', icon: ListTodo, label: '任务列表' },
  { to: '/tasks/new', icon: PlusCircle, label: '新建任务' },
  { to: '/settings', icon: Settings, label: '系统设置' },
];

export default function Layout() {
  const { systemStatus, fetchStatus } = useStore();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    fetchStatus();
    const timer = setInterval(fetchStatus, 10000);
    return () => clearInterval(timer);
  }, [fetchStatus]);

  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);

  const isOnline = systemStatus?.playwright_ready ?? false;

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 bg-black/50 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-50 w-64 bg-card border-r border-border flex flex-col transition-transform duration-300 lg:relative lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-6 py-5 border-b border-border">
          <div className="w-9 h-9 rounded-lg bg-primary/20 flex items-center justify-center">
            <Ticket className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h1 className="text-base font-bold text-foreground">抢票套件</h1>
            <p className="text-[10px] text-muted-foreground">Ticket Grabber v2.0</p>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all',
                  isActive
                    ? 'bg-primary/15 text-primary'
                    : 'text-muted-foreground hover:text-foreground hover:bg-secondary/50'
                )
              }
            >
              <Icon className="w-4 h-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Status */}
        <div className="px-4 py-4 border-t border-border">
          <div className="flex items-center gap-2 text-xs">
            <div className={clsx('w-2 h-2 rounded-full', isOnline ? 'bg-emerald-500 animate-pulse' : 'bg-red-500')} />
            <span className="text-muted-foreground">{isOnline ? '系统在线' : '系统离线'}</span>
          </div>
          {systemStatus && (
            <div className="mt-2 grid grid-cols-2 gap-1 text-[10px] text-muted-foreground">
              <span>运行中: {systemStatus.active_tasks}</span>
              <span>总任务: {systemStatus.total_tasks}</span>
              <span>CPU: {systemStatus.cpu_percent.toFixed(1)}%</span>
              <span>内存: {systemStatus.memory_mb.toFixed(0)}MB</span>
            </div>
          )}
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="h-14 border-b border-border flex items-center justify-between px-4 lg:px-6 bg-card/50 backdrop-blur-sm">
          <button className="lg:hidden p-2 -ml-2 rounded-lg hover:bg-secondary" onClick={() => setSidebarOpen(true)}>
            <Menu className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium">
              {systemStatus ? `${systemStatus.active_tasks} 个任务运行中` : '加载中...'}
            </span>
          </div>
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <span>v{systemStatus?.version || '2.0.0'}</span>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
