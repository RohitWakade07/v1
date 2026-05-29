import type { ReactNode } from 'react'

interface PageHeaderProps {
  title: string
  description?: string
  action?: ReactNode
}

export const PageHeader = ({ title, description, action }: PageHeaderProps) => (
  <div className="flex flex-wrap items-center justify-between gap-4">
    <div>
      <h2 className="font-display text-2xl font-semibold text-text-primary">
        {title}
      </h2>
      {description && (
        <p className="text-sm text-text-secondary">{description}</p>
      )}
    </div>
    {action}
  </div>
)
