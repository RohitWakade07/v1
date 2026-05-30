import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface StatCardProps {
  title: string
  value: string | number
  icon: ReactNode
  subtitle?: string
  accent?: 'blue' | 'teal' | 'warning' | 'danger'
}

const accentMap = {
  blue: {
    icon: 'bg-accent-blue/15 text-accent-blue',
    value: 'text-accent-blue',
  },
  teal: {
    icon: 'bg-accent-teal/15 text-accent-teal',
    value: 'text-accent-teal',
  },
  warning: {
    icon: 'bg-status-warning/15 text-status-warning',
    value: 'text-status-warning',
  },
  danger: {
    icon: 'bg-status-danger/15 text-status-danger',
    value: 'text-status-danger',
  },
}

export const StatCard = ({ title, value, icon, subtitle, accent = 'blue' }: StatCardProps) => {
  const colors = accentMap[accent]
  return (
    <div className="card-dark transition-card p-5 animate-fade-in-up">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wider text-text-secondary">{title}</p>
        <div className={cn('flex h-9 w-9 items-center justify-center rounded-lg', colors.icon)}>
          {icon}
        </div>
      </div>
      <p className={cn('mt-4 font-display text-3xl font-bold', colors.value)}>{value}</p>
      {subtitle && <p className="mt-1 text-xs text-text-secondary">{subtitle}</p>}
    </div>
  )
}
