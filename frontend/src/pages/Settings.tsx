import { useState } from 'react'
import { motion } from 'framer-motion'
import { Settings as SettingsIcon, Globe, Eye, EyeOff, FileText, Github, Info } from 'lucide-react'

const LEGAL_NOTICE = `本软件仅供学习研究使用，禁止用于任何商业目的或黄牛行为。
使用本软件进行抢票操作需自行承担全部风险，开发者不对任何直接或间接损失负责。
本软件模拟人工浏览器操作，不保证 100% 抢票成功率。
请遵守各票务平台的服务条款与相关法律法规。`

export default function Settings() {
  const [headless, setHeadless] = useState(false)
  const [webhook, setWebhook] = useState('')
  const [logDays, setLogDays] = useState(7)

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-100">设置</h1>
        <p className="text-sm text-slate-500 mt-0.5">全局配置与系统信息</p>
      </div>

      {/* Global settings */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-slate-800 border border-slate-700/50 rounded-xl p-5 space-y-5"
      >
        <div className="flex items-center gap-2 mb-1">
          <SettingsIcon size={16} className="text-emerald-400" />
          <h2 className="text-sm font-semibold text-slate-200">全局设置</h2>
        </div>

        {/* Headless toggle */}
        <label className="flex items-center justify-between p-3 rounded-lg bg-slate-900/50 border border-slate-700 cursor-pointer hover:border-slate-600 transition-colors">
          <div>
            <p className="text-sm font-medium text-slate-300">默认 Headless 模式</p>
            <p className="text-[11px] text-slate-600 mt-0.5">新建任务时默认不显示浏览器窗口</p>
          </div>
          <button
            onClick={() => setHeadless(!headless)}
            className={`w-11 h-6 rounded-full flex items-center px-0.5 transition-colors ${headless ? 'bg-emerald-600' : 'bg-slate-700'}`}
          >
            <motion.div
              animate={{ x: headless ? 20 : 0 }}
              className="w-5 h-5 rounded-full bg-white shadow-sm"
            />
          </button>
        </label>

        {/* Webhook */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1.5">
            通知 Webhook URL
          </label>
          <div className="relative">
            <Globe size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600" />
            <input
              type="text"
              value={webhook}
              onChange={(e) => setWebhook(e.target.value)}
              placeholder="https://hooks.example.com/notify"
              className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-3 py-2.5 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/20 transition-all"
            />
          </div>
          <p className="text-[11px] text-slate-600 mt-1.5">抢票成功或失败时将发送 POST 请求至此地址</p>
        </div>

        {/* Log retention */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1.5">
            日志保留天数
          </label>
          <input
            type="number"
            min={1}
            max={90}
            value={logDays}
            onChange={(e) => setLogDays(parseInt(e.target.value) || 7)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/20 transition-all"
          />
        </div>

        <div className="pt-2">
          <button className="px-4 py-2 rounded-lg text-sm font-medium bg-emerald-600 hover:bg-emerald-500 text-white transition-colors">
            保存设置
          </button>
        </div>
      </motion.div>

      {/* Legal notice */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-slate-800 border border-amber-600/20 rounded-xl p-5"
      >
        <div className="flex items-center gap-2 mb-3">
          <FileText size={16} className="text-amber-400" />
          <h2 className="text-sm font-semibold text-amber-400">免责声明</h2>
        </div>
        <div className="bg-amber-500/5 rounded-lg p-3 border border-amber-500/10">
          <p className="text-xs text-amber-200/80 leading-relaxed whitespace-pre-line">
            {LEGAL_NOTICE}
          </p>
        </div>
      </motion.div>

      {/* About */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="bg-slate-800 border border-slate-700/50 rounded-xl p-5"
      >
        <div className="flex items-center gap-2 mb-3">
          <Info size={16} className="text-slate-400" />
          <h2 className="text-sm font-semibold text-slate-200">关于</h2>
        </div>
        <div className="space-y-3 text-sm">
          <div className="flex items-center justify-between py-2 border-b border-slate-700/50">
            <span className="text-slate-500">版本</span>
            <span className="text-slate-300 font-mono">v1.0.0</span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-slate-700/50">
            <span className="text-slate-500">开源参考</span>
            <a
              href="https://github.com/testerSunshine/12306"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-emerald-400 hover:text-emerald-300 transition-colors"
            >
              <Github size={14} />
              testerSunshine/12306
            </a>
          </div>
          <div className="flex items-center justify-between py-2">
            <span className="text-slate-500">技术栈</span>
            <span className="text-slate-400">React 18 + Tailwind CSS + FastAPI + Playwright</span>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
