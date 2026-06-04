import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { cn } from '@/lib/utils'

interface EmptyStateProps {
  icon?: ReactNode
  title: string
  message: string
  action?: ReactNode
  actionLabel?: string
  actionTo?: string
  className?: string
}

export const EmptyState = ({ icon, title, message, action, actionLabel, actionTo, className }: EmptyStateProps) => (
  <div className={cn('flex flex-col items-center gap-4 rounded-xl border border-dashed border-navy-800 bg-navy-900/30 px-8 py-14 text-center animate-fade-in', className)}>
    {icon && (
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-navy-800/60 text-text-secondary">
        {icon}
      </div>
    )}
    <div>
      <h3 className="font-display text-lg font-semibold text-text-primary">{title}</h3>
      <p className="mt-1 text-sm text-text-secondary">{message}</p>
    </div>
    {action && <div className="mt-1">{action}</div>}
    {actionLabel && actionTo && !action && (
      <Link to={actionTo} className="btn-primary mt-1 text-sm">{actionLabel}</Link>
    )}
  </div>
)
