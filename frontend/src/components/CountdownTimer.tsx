import { useState, useEffect } from 'react';
import { Timer } from 'lucide-react';

export default function CountdownTimer({ targetTime }: { targetTime: string }) {
  const [remaining, setRemaining] = useState('');

  useEffect(() => {
    const update = () => {
      const target = new Date(targetTime).getTime();
      const now = Date.now();
      const diff = target - now;

      if (diff <= 0) {
        setRemaining('已到时间');
        return;
      }

      const hours = Math.floor(diff / 3600000);
      const minutes = Math.floor((diff % 3600000) / 60000);
      const seconds = Math.floor((diff % 60000) / 1000);

      if (hours > 0) {
        setRemaining(`${hours}时${minutes}分${seconds}秒`);
      } else if (minutes > 0) {
        setRemaining(`${minutes}分${seconds}秒`);
      } else {
        setRemaining(`${seconds}秒`);
      }
    };

    update();
    const timer = setInterval(update, 1000);
    return () => clearInterval(timer);
  }, [targetTime]);

  return (
    <div className="flex items-center gap-1.5 text-xs text-amber-400">
      <Timer className="w-3.5 h-3.5" />
      <span>{remaining}</span>
    </div>
  );
}
