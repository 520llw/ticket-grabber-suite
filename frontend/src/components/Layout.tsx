import type { ReactNode } from 'react'
import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Activity } from 'lucide-react'
import Sidebar from './Sidebar'
import { systemApi } from '@/services/api'
import { useStore } from '@/store/useStore'

export default function Layout({ children }: { children: ReactNode }) {
  const location = useLocation()
  const { systemStatus, setSystemStatus } = useStore()

  useEffect(() => {
    let mounted = true
    const fetchStatus = async () => {
      try {
        const status = await systemApi.status()
        if (mounted) setSystemStatus(status)
      } catch {
        if (mounted)
          setSystemStatus({
            version: 'unknown',
            active_tasks: 0,
            total_tasks: 0,
            playwright_ready: false,
          })
      }
    }
    fetchStatus()
    const interval = setInterval(fetchStatus, 10000)
    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [setSystemStatus])

  const isOnline = !!systemStatus?.playwright_ready

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-900">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="h-16 flex items-center justify-between px-6 border-b border-slate-800 bg-slate-900/80 backdrop-blur shrink-0 z-10">
          <h1 className="text-sm font-medium text-slate-400" />
          <div className="flex items-center gap-2">
            <Activity size={14} className={isOnline ? 'text-emerald-400' : 'text-red-400'} />
            <span className={`text-xs font-medium ${isOnline ? 'text-emerald-400' : 'text-red-400'}`}>
              {isOnline ? '系统在线' : '系统离线'}
            </span>
            <span
              className={`inline-block w-2 h-2 rounded-full ${isOnline ? 'bg-emerald-400 animate-pulse' : 'bg-red-400'}`}
            />
          </div>
        </header>

        {/* Main content */}
        <main className="flex-1 overflow-y-auto p-6">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25 }}
            className="max-w-7xl mx-auto"
          >
            {children}
          </motion.div>
        </main>
      </div>
    </div>
  )
}
