import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Ticket, Film, TrainFront, Zap, Plus, X } from 'lucide-react';
import { useStore } from '../store/useStore';
import { clsx } from 'clsx';

const platforms = [
  { id: 'damai', label: '大麦网', desc: '演唱会、话剧、展览', icon: Ticket, color: 'border-blue-500/50 bg-blue-500/10' },
  { id: 'maoyan', label: '猫眼', desc: '演出、电影', icon: Film, color: 'border-yellow-500/50 bg-yellow-500/10' },
  { id: '12306', label: '12306', desc: '火车票、高铁票', icon: TrainFront, color: 'border-sky-500/50 bg-sky-500/10' },
];

export default function TaskNew() {
  const navigate = useNavigate();
  const { createTask } = useStore();
  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [buyerInput, setBuyerInput] = useState('');

  const [form, setForm] = useState({
    name: '',
    platform: '' as string,
    url: '',
    date: '',
    session: '',
    price: '',
    ticket_count: 1,
    buyers: [] as string[],
    from_station: '',
    to_station: '',
    train_number: '',
    seat_type: '',
    cron_time: '',
    headless: true,
    max_retries: 5,
    retry_interval: 2,
    auto_retry: true,
    notify_on_success: true,
    priority: 5,
  });

  const set = (key: string, value: any) => setForm((prev) => ({ ...prev, [key]: value }));
  const is12306 = form.platform === '12306';

  const addBuyer = () => {
    const name = buyerInput.trim();
    if (name && !form.buyers.includes(name)) {
      set('buyers', [...form.buyers, name]);
      setBuyerInput('');
    }
  };

  const removeBuyer = (name: string) => {
    set('buyers', form.buyers.filter((b) => b !== name));
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const task = await createTask({
        ...form,
        cron_time: form.cron_time || null,
      } as any);
      navigate(`/tasks/${task.id}`);
    } catch (e) {
      console.error(e);
    } finally {
      setSubmitting(false);
    }
  };

  const canProceed = () => {
    if (step === 1) return !!form.platform;
    if (step === 2) {
      if (!form.name) return false;
      if (is12306) return !!form.from_station && !!form.to_station && !!form.date;
      return !!form.url;
    }
    return true;
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="p-2 rounded-lg hover:bg-secondary transition-colors">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-foreground">新建抢票任务</h1>
          <p className="text-sm text-muted-foreground mt-0.5">第 {step} 步 / 共 3 步</p>
        </div>
      </div>

      {/* Progress */}
      <div className="flex gap-2">
        {[1, 2, 3].map((s) => (
          <div
            key={s}
            className={clsx(
              'h-1.5 flex-1 rounded-full transition-colors',
              s <= step ? 'bg-primary' : 'bg-border'
            )}
          />
        ))}
      </div>

      {/* Step 1: Platform */}
      {step === 1 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">选择抢票平台</h2>
          <div className="grid gap-3">
            {platforms.map(({ id, label, desc, icon: Icon, color }) => (
              <button
                key={id}
                onClick={() => set('platform', id)}
                className={clsx(
                  'flex items-center gap-4 p-4 rounded-xl border-2 transition-all text-left',
                  form.platform === id ? color : 'border-border hover:border-muted-foreground/30'
                )}
              >
                <div className={clsx('w-12 h-12 rounded-lg flex items-center justify-center', form.platform === id ? 'bg-white/10' : 'bg-secondary')}>
                  <Icon className="w-6 h-6" />
                </div>
                <div>
                  <p className="font-semibold">{label}</p>
                  <p className="text-xs text-muted-foreground">{desc}</p>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Step 2: Basic Info */}
      {step === 2 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">填写任务信息</h2>

          <div>
            <label className="block text-sm font-medium mb-1.5">任务名称 *</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => set('name', e.target.value)}
              placeholder={is12306 ? '如：春节回家火车票' : '如：周杰伦演唱会北京站'}
              className="w-full px-4 py-2.5 bg-card border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50"
            />
          </div>

          {is12306 ? (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1.5">出发站 *</label>
                  <input
                    type="text"
                    value={form.from_station}
                    onChange={(e) => set('from_station', e.target.value)}
                    placeholder="如：北京"
                    className="w-full px-4 py-2.5 bg-card border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5">到达站 *</label>
                  <input
                    type="text"
                    value={form.to_station}
                    onChange={(e) => set('to_station', e.target.value)}
                    placeholder="如：上海"
                    className="w-full px-4 py-2.5 bg-card border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1.5">出发日期 *</label>
                <input
                  type="date"
                  value={form.date}
                  onChange={(e) => set('date', e.target.value)}
                  className="w-full px-4 py-2.5 bg-card border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1.5">车次号（可选）</label>
                  <input
                    type="text"
                    value={form.train_number}
                    onChange={(e) => set('train_number', e.target.value)}
                    placeholder="如：G1234"
                    className="w-full px-4 py-2.5 bg-card border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5">席别（可选）</label>
                  <select
                    value={form.seat_type}
                    onChange={(e) => set('seat_type', e.target.value)}
                    className="w-full px-4 py-2.5 bg-card border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50"
                  >
                    <option value="">自动选择</option>
                    <option value="商务座">商务座</option>
                    <option value="一等座">一等座</option>
                    <option value="二等座">二等座</option>
                    <option value="硬卧">硬卧</option>
                    <option value="软卧">软卧</option>
                    <option value="硬座">硬座</option>
                    <option value="无座">无座</option>
                  </select>
                </div>
              </div>
            </>
          ) : (
            <>
              <div>
                <label className="block text-sm font-medium mb-1.5">演出链接 *</label>
                <input
                  type="url"
                  value={form.url}
                  onChange={(e) => set('url', e.target.value)}
                  placeholder="粘贴大麦/猫眼演出页面链接"
                  className="w-full px-4 py-2.5 bg-card border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1.5">日期（可选）</label>
                  <input
                    type="text"
                    value={form.date}
                    onChange={(e) => set('date', e.target.value)}
                    placeholder="如：2026-05-01"
                    className="w-full px-4 py-2.5 bg-card border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5">场次（可选）</label>
                  <input
                    type="text"
                    value={form.session}
                    onChange={(e) => set('session', e.target.value)}
                    placeholder="如：19:30"
                    className="w-full px-4 py-2.5 bg-card border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1.5">票价/票档（可选）</label>
                  <input
                    type="text"
                    value={form.price}
                    onChange={(e) => set('price', e.target.value)}
                    placeholder="如：680"
                    className="w-full px-4 py-2.5 bg-card border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5">购票数量</label>
                  <input
                    type="number"
                    min={1}
                    max={10}
                    value={form.ticket_count}
                    onChange={(e) => set('ticket_count', parseInt(e.target.value) || 1)}
                    className="w-full px-4 py-2.5 bg-card border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50"
                  />
                </div>
              </div>
            </>
          )}

          {/* Buyers */}
          <div>
            <label className="block text-sm font-medium mb-1.5">{is12306 ? '乘车人' : '观演人'}（可选）</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={buyerInput}
                onChange={(e) => setBuyerInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addBuyer())}
                placeholder="输入姓名后回车添加"
                className="flex-1 px-4 py-2.5 bg-card border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50"
              />
              <button onClick={addBuyer} className="px-3 py-2.5 bg-primary/15 text-primary rounded-lg hover:bg-primary/25 transition-colors">
                <Plus className="w-4 h-4" />
              </button>
            </div>
            {form.buyers.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {form.buyers.map((name) => (
                  <span key={name} className="flex items-center gap-1 px-2.5 py-1 bg-secondary rounded-full text-xs">
                    {name}
                    <button onClick={() => removeBuyer(name)} className="hover:text-red-400">
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Step 3: Advanced */}
      {step === 3 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">高级设置</h2>

          <div>
            <label className="block text-sm font-medium mb-1.5">定时开抢（可选）</label>
            <input
              type="datetime-local"
              value={form.cron_time}
              onChange={(e) => set('cron_time', e.target.value)}
              className="w-full px-4 py-2.5 bg-card border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50"
            />
            <p className="text-xs text-muted-foreground mt-1">留空则手动开始</p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1.5">最大重试次数</label>
              <input
                type="number"
                min={1}
                max={100}
                value={form.max_retries}
                onChange={(e) => set('max_retries', parseInt(e.target.value) || 5)}
                className="w-full px-4 py-2.5 bg-card border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1.5">重试间隔（秒）</label>
              <input
                type="number"
                min={0.5}
                max={30}
                step={0.5}
                value={form.retry_interval}
                onChange={(e) => set('retry_interval', parseFloat(e.target.value) || 2)}
                className="w-full px-4 py-2.5 bg-card border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1.5">任务优先级</label>
            <input
              type="range"
              min={1}
              max={10}
              value={form.priority}
              onChange={(e) => set('priority', parseInt(e.target.value))}
              className="w-full accent-primary"
            />
            <div className="flex justify-between text-xs text-muted-foreground mt-1">
              <span>低</span>
              <span>当前: {form.priority}</span>
              <span>高</span>
            </div>
          </div>

          <div className="space-y-3">
            {[
              { key: 'auto_retry', label: '自动重试', desc: '失败后自动重新尝试' },
              { key: 'headless', label: '无头模式', desc: '不显示浏览器窗口（更快）' },
              { key: 'notify_on_success', label: '成功通知', desc: '抢票成功后发送通知' },
            ].map(({ key, label, desc }) => (
              <label key={key} className="flex items-center justify-between p-3 bg-card border border-border rounded-lg cursor-pointer hover:border-primary/30 transition-colors">
                <div>
                  <p className="text-sm font-medium">{label}</p>
                  <p className="text-xs text-muted-foreground">{desc}</p>
                </div>
                <input
                  type="checkbox"
                  checked={(form as any)[key]}
                  onChange={(e) => set(key, e.target.checked)}
                  className="w-5 h-5 rounded accent-primary"
                />
              </label>
            ))}
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-between pt-4 border-t border-border">
        <button
          onClick={() => step > 1 ? setStep(step - 1) : navigate(-1)}
          className="px-4 py-2.5 rounded-lg border border-border text-sm hover:bg-secondary transition-colors"
        >
          {step > 1 ? '上一步' : '取消'}
        </button>
        {step < 3 ? (
          <button
            onClick={() => setStep(step + 1)}
            disabled={!canProceed()}
            className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            下一步
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 shadow-lg shadow-primary/20"
          >
            <Zap className="w-4 h-4" />
            {submitting ? '创建中...' : '创建任务'}
          </button>
        )}
      </div>
    </div>
  );
}
