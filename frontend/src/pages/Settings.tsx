import { useEffect } from 'react';
import { useStore } from '../store/useStore';
import { Cpu, HardDrive, Clock, Activity, Shield, Zap, Globe } from 'lucide-react';

export default function Settings() {
  const { systemStatus, fetchStatus } = useStore();

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const formatUptime = (seconds: number) => {
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    if (d > 0) return `${d}天 ${h}小时 ${m}分钟`;
    if (h > 0) return `${h}小时 ${m}分钟`;
    return `${m}分钟`;
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">系统设置</h1>
        <p className="text-sm text-muted-foreground mt-1">查看系统状态和配置信息</p>
      </div>

      {/* System Status */}
      <div className="bg-card border border-border rounded-xl p-5">
        <h2 className="text-sm font-semibold mb-4 flex items-center gap-2">
          <Activity className="w-4 h-4 text-primary" /> 系统状态
        </h2>
        {systemStatus ? (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatusItem icon={Cpu} label="CPU 使用率" value={`${systemStatus.cpu_percent.toFixed(1)}%`} />
            <StatusItem icon={HardDrive} label="内存使用" value={`${systemStatus.memory_mb.toFixed(0)} MB`} />
            <StatusItem icon={Clock} label="运行时间" value={formatUptime(systemStatus.uptime_seconds)} />
            <StatusItem icon={Globe} label="版本" value={`v${systemStatus.version}`} />
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">加载中...</p>
        )}
      </div>

      {/* Feature Info */}
      <div className="bg-card border border-border rounded-xl p-5">
        <h2 className="text-sm font-semibold mb-4 flex items-center gap-2">
          <Zap className="w-4 h-4 text-primary" /> 功能特性
        </h2>
        <div className="grid gap-3">
          {[
            { title: '多平台支持', desc: '支持大麦网、猫眼、12306 三大平台' },
            { title: '智能重试', desc: '失败后自动重试，可配置重试次数和间隔' },
            { title: '定时抢票', desc: '设置开抢时间，到点自动执行' },
            { title: '反检测', desc: '模拟真人操作，随机延迟，浏览器指纹伪装' },
            { title: '实时日志', desc: 'SSE 实时推送日志，掌握抢票全过程' },
            { title: '数据持久化', desc: '任务数据自动保存，重启不丢失' },
            { title: '批量操作', desc: '支持批量开始、停止、删除任务' },
            { title: '并发控制', desc: '智能控制并发数，避免资源耗尽' },
          ].map(({ title, desc }) => (
            <div key={title} className="flex items-start gap-3 p-3 bg-background rounded-lg">
              <div className="w-2 h-2 rounded-full bg-primary mt-1.5 shrink-0" />
              <div>
                <p className="text-sm font-medium">{title}</p>
                <p className="text-xs text-muted-foreground">{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Disclaimer */}
      <div className="bg-card border border-amber-500/30 rounded-xl p-5">
        <h2 className="text-sm font-semibold mb-3 flex items-center gap-2 text-amber-400">
          <Shield className="w-4 h-4" /> 免责声明
        </h2>
        <div className="text-xs text-muted-foreground space-y-2">
          <p>本工具仅供学习研究使用，禁止用于商业用途或黄牛行为。</p>
          <p>用户需自行承担使用风险，开发者不对任何因使用本工具造成的损失负责。</p>
          <p>请遵守相关平台的服务条款和法律法规。</p>
        </div>
      </div>
    </div>
  );
}

function StatusItem({ icon: Icon, label, value }: { icon: any; label: string; value: string }) {
  return (
    <div className="flex items-center gap-3 p-3 bg-background rounded-lg">
      <Icon className="w-5 h-5 text-muted-foreground" />
      <div>
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-sm font-semibold">{value}</p>
      </div>
    </div>
  );
}
