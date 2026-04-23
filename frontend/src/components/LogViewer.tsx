import { useEffect, useRef } from 'react';
import { clsx } from 'clsx';
import { TaskLog } from '../services/api';

const levelColors: Record<string, string> = {
  info: 'text-blue-400',
  warn: 'text-amber-400',
  error: 'text-red-400',
  success: 'text-emerald-400',
  debug: 'text-slate-500',
};

const levelBg: Record<string, string> = {
  info: 'border-l-blue-500/50',
  warn: 'border-l-amber-500/50',
  error: 'border-l-red-500/50',
  success: 'border-l-emerald-500/50',
  debug: 'border-l-slate-500/50',
};

export default function LogViewer({ logs, maxHeight = '400px' }: { logs: TaskLog[]; maxHeight?: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const autoScrollRef = useRef(true);

  useEffect(() => {
    if (containerRef.current && autoScrollRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs]);

  const handleScroll = () => {
    if (!containerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    autoScrollRef.current = scrollHeight - scrollTop - clientHeight < 50;
  };

  if (!logs.length) {
    return (
      <div className="flex items-center justify-center h-32 text-sm text-muted-foreground bg-card rounded-lg border border-border">
        暂无日志
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      onScroll={handleScroll}
      className="bg-[hsl(222,47%,5%)] rounded-lg border border-border overflow-y-auto font-mono text-xs"
      style={{ maxHeight }}
    >
      {logs.map((log, i) => (
        <div
          key={`${log.timestamp}-${i}`}
          className={clsx(
            'flex gap-3 px-3 py-1.5 border-l-2 hover:bg-white/[0.02] transition-colors',
            levelBg[log.level] || levelBg.info
          )}
        >
          <span className="text-muted-foreground shrink-0 w-20">
            {new Date(log.timestamp).toLocaleTimeString('zh-CN')}
          </span>
          <span className={clsx('shrink-0 w-12 uppercase font-semibold', levelColors[log.level] || levelColors.info)}>
            {log.level}
          </span>
          <span className="text-foreground/90 break-all">{log.message}</span>
        </div>
      ))}
    </div>
  );
}
