import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface StatCardProps {
  title: string
  value: string | number
  icon: ReactNode
  accent?: 'blue' | 'teal' | 'warning' | 'danger'
  subtitle?: string
}

const accentMap = {
  blue: 'border-b-accent-blue text-accent-blue',
  teal: 'border-b-accent-teal text-accent-teal',
  warning: 'border-b-status-warning text-status-warning',
  danger: 'border-b-status-danger text-status-danger',
}

export const StatCard = ({ title, value, icon, accent = 'blue', subtitle }: StatCardProps) => {
  return (
    <div className={cn(
      'flex flex-col rounded-xl border border-navy-800 bg-navy-900 p-5 shadow-card border-b-4',
      accentMap[accent].split(' ')[0]
    )}>
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-text-secondary">{title}</p>
        <div className={cn("rounded-lg p-2 bg-navy-800/50", accentMap[accent].split(' ')[1])}>
          {icon}
        </div>
      </div>
      <div className="mt-4">
        <h3 className="font-display text-3xl font-bold text-text-primary">{value}</h3>
        {subtitle && <p className="mt-1 text-xs text-text-secondary">{subtitle}</p>}
      </div>
    </div>
  )
}
