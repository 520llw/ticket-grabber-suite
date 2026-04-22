import { useState, useEffect, useCallback } from 'react'

interface CountdownTimerProps {
  target: string
  onComplete?: () => void
}

interface TimeLeft {
  days: number
  hours: number
  minutes: number
  seconds: number
}

function parseTimeLeft(targetDate: Date): TimeLeft {
  const now = new Date().getTime()
  const target = targetDate.getTime()
  const diff = target - now

  if (diff <= 0) {
    return { days: 0, hours: 0, minutes: 0, seconds: 0 }
  }

  return {
    days: Math.floor(diff / (1000 * 60 * 60 * 24)),
    hours: Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)),
    minutes: Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60)),
    seconds: Math.floor((diff % (1000 * 60)) / 1000),
  }
}

function TimeUnit({ value, label }: { value: number; label: string }) {
  return (
    <div className="flex flex-col items-center">
      <div className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 min-w-[56px] text-center">
        <span className="text-xl font-mono font-bold text-slate-100 tabular-nums">
          {String(value).padStart(2, '0')}
        </span>
      </div>
      <span className="text-[10px] text-slate-500 mt-1 uppercase tracking-wider">{label}</span>
    </div>
  )
}

export default function CountdownTimer({ target, onComplete }: CountdownTimerProps) {
  const [timeLeft, setTimeLeft] = useState<TimeLeft>({ days: 0, hours: 0, minutes: 0, seconds: 0 })
  const [isComplete, setIsComplete] = useState(false)

  const update = useCallback(() => {
    const targetDate = new Date(target)
    const left = parseTimeLeft(targetDate)
    setTimeLeft(left)

    if (left.days === 0 && left.hours === 0 && left.minutes === 0 && left.seconds === 0 && !isComplete) {
      setIsComplete(true)
      onComplete?.()
    }
  }, [target, onComplete, isComplete])

  useEffect(() => {
    update()
    const timer = setInterval(update, 1000)
    return () => clearInterval(timer)
  }, [update])

  if (isComplete) {
    return (
      <div className="text-sm font-medium text-emerald-400 animate-pulse">
        开抢时间到！
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2">
      {timeLeft.days > 0 && <TimeUnit value={timeLeft.days} label="天" />}
      <TimeUnit value={timeLeft.hours} label="时" />
      <span className="text-slate-600 text-lg font-bold -mt-4">:</span>
      <TimeUnit value={timeLeft.minutes} label="分" />
      <span className="text-slate-600 text-lg font-bold -mt-4">:</span>
      <TimeUnit value={timeLeft.seconds} label="秒" />
    </div>
  )
}
