import type { ReactNode } from 'react'

interface EmptyStateProps {
  icon?: ReactNode
  title: string
  message: string
  action?: ReactNode
}

export const EmptyState = ({ icon, title, message, action }: EmptyStateProps) => (
  <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-navy-800 bg-navy-900/30 px-6 py-10 text-center">
    <div className="text-text-secondary">{icon}</div>
    <h3 className="font-display text-lg font-semibold text-text-primary">
      {title}
    </h3>
    <p className="text-sm text-text-secondary">{message}</p>
    {action}
  </div>
)
