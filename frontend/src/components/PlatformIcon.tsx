import { Ticket, Film, TrainFront, Globe } from 'lucide-react';
import { clsx } from 'clsx';

const platformConfig: Record<string, { icon: any; label: string; color: string; bg: string }> = {
  damai: { icon: Ticket, label: '大麦', color: 'text-blue-400', bg: 'bg-blue-500/15' },
  maoyan: { icon: Film, label: '猫眼', color: 'text-yellow-400', bg: 'bg-yellow-500/15' },
  '12306': { icon: TrainFront, label: '12306', color: 'text-sky-400', bg: 'bg-sky-500/15' },
  custom: { icon: Globe, label: '自定义', color: 'text-purple-400', bg: 'bg-purple-500/15' },
};

export default function PlatformIcon({ platform, size = 'md' }: { platform: string; size?: 'sm' | 'md' | 'lg' }) {
  const config = platformConfig[platform] || platformConfig.custom;
  const Icon = config.icon;
  const sizeMap = { sm: 'w-7 h-7', md: 'w-9 h-9', lg: 'w-12 h-12' };
  const iconSize = { sm: 'w-3.5 h-3.5', md: 'w-4.5 h-4.5', lg: 'w-6 h-6' };

  return (
    <div className={clsx('rounded-lg flex items-center justify-center', sizeMap[size], config.bg)}>
      <Icon className={clsx(iconSize[size], config.color)} />
    </div>
  );
}

export function getPlatformLabel(platform: string) {
  return platformConfig[platform]?.label || platform;
}
