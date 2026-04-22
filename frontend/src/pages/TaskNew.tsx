import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ChevronRight,
  ChevronLeft,
  Ticket,
  Link,
  Calendar,
  Clock,
  UserPlus,
  UserMinus,
  Eye,
  EyeOff,
  Check,
  Globe,
  Train,
  ShoppingBag,
} from 'lucide-react'
import { taskApi } from '@/services/api'
import type { Task } from '@/services/api'

const platforms: { value: Task['platform']; label: string; desc: string; icon: React.ElementType; color: string }[] = [
  { value: 'damai', label: '大麦网', desc: '演唱会、话剧、体育赛事', icon: Ticket, color: 'text-red-400' },
  { value: 'maoyan', label: '猫眼', desc: '电影票、演出票务', icon: ShoppingBag, color: 'text-orange-400' },
  { value: '12306', label: '12306', desc: '火车票、候补抢票', icon: Train, color: 'text-blue-400' },
  { value: 'custom', label: '自定义', desc: '其他票务平台', icon: Globe, color: 'text-slate-400' },
]

interface FormData {
  name: string
  platform: Task['platform']
  url: string
  date: string
  session: string
  price: string
  ticket_count: number
  buyers: string[]
  cron_time: string
  headless: boolean
}

const initialForm: FormData = {
  name: '',
  platform: 'damai',
  url: '',
  date: '',
  session: '',
  price: '',
  ticket_count: 1,
  buyers: [''],
  cron_time: '',
  headless: false,
}

export default function TaskNew() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [form, setForm] = useState<FormData>(initialForm)
  const [submitting, setSubmitting] = useState(false)

  const update = <K extends keyof FormData>(key: K, value: FormData[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const addBuyer = () => setForm((prev) => ({ ...prev, buyers: [...prev.buyers, ''] }))
  const removeBuyer = (i: number) =>
    setForm((prev) => ({ ...prev, buyers: prev.buyers.filter((_, idx) => idx !== i) }))
  const setBuyer = (i: number, val: string) =>
    setForm((prev) => {
      const next = [...prev.buyers]
      next[i] = val
      return { ...prev, buyers: next }
    })

  const handleSubmit = async () => {
    setSubmitting(true)
    try {
      const payload: Partial<Task> = {
        name: form.name,
        platform: form.platform,
        url: form.url,
        date: form.date,
        session: form.session,
        price: form.price,
        ticket_count: form.ticket_count,
        buyers: form.buyers.filter(Boolean),
        cron_time: form.cron_time || null,
        headless: form.headless,
      }
      await taskApi.create(payload)
      navigate('/tasks')
    } catch (err) {
      console.error('Failed to create task', err)
    } finally {
      setSubmitting(false)
    }
  }

  const stepValid = () => {
    if (step === 1) return form.name.trim() && form.url.trim()
    if (step === 2) return form.date.trim() && form.price.trim()
    return true
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-100">新建任务</h1>
        <p className="text-sm text-slate-500 mt-0.5">分步配置抢票任务参数</p>
      </div>

      {/* Step indicator */}
      <div className="flex items-center gap-2">
        {[1, 2, 3].map((s) => (
          <div key={s} className="flex items-center gap-2">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold border transition-colors ${
                s < step
                  ? 'bg-emerald-600 border-emerald-600 text-white'
                  : s === step
                    ? 'bg-emerald-600/20 border-emerald-500 text-emerald-400'
                    : 'bg-slate-800 border-slate-700 text-slate-500'
              }`}
            >
              {s < step ? <Check size={14} /> : s}
            </div>
            <span
              className={`text-xs font-medium ${s <= step ? 'text-slate-300' : 'text-slate-600'}`}
            >
              {s === 1 ? '基本信息' : s === 2 ? '抢票配置' : '高级设置'}
            </span>
            {s < 3 && <div className="w-8 h-px bg-slate-700 mx-1" />}
          </div>
        ))}
      </div>

      {/* Form card */}
      <div className="bg-slate-800 border border-slate-700/50 rounded-xl p-6">
        <AnimatePresence mode="wait">
          {step === 1 && (
            <motion.div
              key="step1"
              initial={{ opacity: 0, x: 16 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -16 }}
              className="space-y-5"
            >
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">任务名称</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => update('name', e.target.value)}
                  placeholder="例如：周杰伦演唱会抢票"
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/20 transition-all"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">选择平台</label>
                <div className="grid grid-cols-2 gap-3">
                  {platforms.map((p) => {
                    const Icon = p.icon
                    const selected = form.platform === p.value
                    return (
                      <button
                        key={p.value}
                        onClick={() => update('platform', p.value)}
                        className={`flex items-start gap-3 p-3 rounded-lg border text-left transition-all ${
                          selected
                            ? 'border-emerald-500/40 bg-emerald-500/5'
                            : 'border-slate-700 bg-slate-900/50 hover:border-slate-600'
                        }`}
                      >
                        <Icon size={18} className={`mt-0.5 shrink-0 ${selected ? p.color : 'text-slate-500'}`} />
                        <div>
                          <p className={`text-sm font-medium ${selected ? 'text-slate-200' : 'text-slate-400'}`}>
                            {p.label}
                          </p>
                          <p className="text-[11px] text-slate-600 mt-0.5">{p.desc}</p>
                        </div>
                      </button>
                    )
                  })}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">目标链接</label>
                <div className="relative">
                  <Link size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600" />
                  <input
                    type="text"
                    value={form.url}
                    onChange={(e) => update('url', e.target.value)}
                    placeholder="粘贴商品页或演出详情页链接"
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-3 py-2.5 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/20 transition-all"
                  />
                </div>
              </div>
            </motion.div>
          )}

          {step === 2 && (
            <motion.div
              key="step2"
              initial={{ opacity: 0, x: 16 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -16 }}
              className="space-y-5"
            >
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">目标日期</label>
                  <div className="relative">
                    <Calendar size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600" />
                    <input
                      type="date"
                      value={form.date}
                      onChange={(e) => update('date', e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-3 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/20 transition-all"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">场次 / 时间</label>
                  <div className="relative">
                    <Clock size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600" />
                    <input
                      type="text"
                      value={form.session}
                      onChange={(e) => update('session', e.target.value)}
                      placeholder="例如：19:30"
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-3 py-2.5 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/20 transition-all"
                    />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">票档 / 价格</label>
                  <input
                    type="text"
                    value={form.price}
                    onChange={(e) => update('price', e.target.value)}
                    placeholder="例如：580 或 二等座"
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/20 transition-all"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">购票数量</label>
                  <input
                    type="number"
                    min={1}
                    max={10}
                    value={form.ticket_count}
                    onChange={(e) => update('ticket_count', parseInt(e.target.value) || 1)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/20 transition-all"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  观演人 / 乘车人
                </label>
                <div className="space-y-2">
                  {form.buyers.map((buyer, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <input
                        type="text"
                        value={buyer}
                        onChange={(e) => setBuyer(i, e.target.value)}
                        placeholder={`姓名 ${i + 1}`}
                        className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/20 transition-all"
                      />
                      {form.buyers.length > 1 && (
                        <button
                          onClick={() => removeBuyer(i)}
                          className="p-2 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                        >
                          <UserMinus size={16} />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
                <button
                  onClick={addBuyer}
                  className="flex items-center gap-1.5 mt-2 text-xs text-emerald-400 hover:text-emerald-300 transition-colors"
                >
                  <UserPlus size={14} />
                  添加观演人
                </button>
              </div>
            </motion.div>
          )}

          {step === 3 && (
            <motion.div
              key="step3"
              initial={{ opacity: 0, x: 16 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -16 }}
              className="space-y-5"
            >
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">定时开抢（可选）</label>
                <input
                  type="datetime-local"
                  value={form.cron_time}
                  onChange={(e) => update('cron_time', e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/20 transition-all"
                />
                <p className="text-[11px] text-slate-600 mt-1.5">设置后将自动倒计时，到点后自动启动抢票</p>
              </div>

              <div>
                <label className="flex items-center justify-between p-3 rounded-lg bg-slate-900/50 border border-slate-700 cursor-pointer hover:border-slate-600 transition-colors">
                  <div>
                    <p className="text-sm font-medium text-slate-300">Headless 模式</p>
                    <p className="text-[11px] text-slate-600 mt-0.5">不显示浏览器窗口，后台运行</p>
                  </div>
                  <button
                    onClick={() => update('headless', !form.headless)}
                    className={`w-11 h-6 rounded-full flex items-center px-0.5 transition-colors ${
                      form.headless ? 'bg-emerald-600' : 'bg-slate-700'
                    }`}
                  >
                    <motion.div
                      animate={{ x: form.headless ? 20 : 0 }}
                      className="w-5 h-5 rounded-full bg-white shadow-sm"
                    />
                  </button>
                </label>
              </div>

              {/* Summary */}
              <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-4 space-y-2">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">配置摘要</p>
                <div className="grid grid-cols-2 gap-y-1.5 text-xs">
                  <span className="text-slate-600">名称</span>
                  <span className="text-slate-300 text-right truncate">{form.name}</span>
                  <span className="text-slate-600">平台</span>
                  <span className="text-slate-300 text-right">{platforms.find((p) => p.value === form.platform)?.label}</span>
                  <span className="text-slate-600">日期</span>
                  <span className="text-slate-300 text-right">{form.date || '—'}</span>
                  <span className="text-slate-600">票价</span>
                  <span className="text-slate-300 text-right">{form.price || '—'}</span>
                  <span className="text-slate-600">数量</span>
                  <span className="text-slate-300 text-right">{form.ticket_count}</span>
                  <span className="text-slate-600">观演人</span>
                  <span className="text-slate-300 text-right">
                    {form.buyers.filter(Boolean).join(', ') || '—'}
                  </span>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Footer actions */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => setStep((s) => Math.max(1, s - 1))}
          disabled={step === 1}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium bg-slate-700 hover:bg-slate-600 text-slate-200 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        >
          <ChevronLeft size={16} />
          上一步
        </button>

        {step < 3 ? (
          <button
            onClick={() => setStep((s) => Math.min(3, s + 1))}
            disabled={!stepValid()}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium bg-emerald-600 hover:bg-emerald-500 text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            下一步
            <ChevronRight size={16} />
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="flex items-center gap-1.5 px-5 py-2 rounded-lg text-sm font-medium bg-emerald-600 hover:bg-emerald-500 text-white disabled:opacity-50 transition-colors"
          >
            {submitting ? (
              <>
                <EyeOff size={16} className="animate-spin" />
                创建中...
              </>
            ) : (
              <>
                <Check size={16} />
                确认并创建
              </>
            )}
          </button>
        )}
      </div>
    </div>
  )
}
