import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

interface PageHeaderProps {
  title: string
  description?: string
  actions?: ReactNode
  backTo?: string
  backLabel?: string
  className?: string
}

export const PageHeader = ({ title, description, actions, backTo, backLabel, className }: PageHeaderProps) => (
  <div className={cn('mb-6 animate-fade-in-up', className)}>
    {backTo && (
      <Link to={backTo} className="mb-3 inline-flex items-center gap-1 text-xs text-text-secondary hover:text-accent-blue transition-colors">
        <ChevronRight size={12} className="rotate-180" />
        {backLabel ?? 'Back'}
      </Link>
    )}
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div>
        <h2 className="font-display text-2xl font-bold text-text-primary">{title}</h2>
        {description && <p className="mt-1 text-sm text-text-secondary">{description}</p>}
      </div>
      {actions && <div className="shrink-0 flex items-center gap-2">{actions}</div>}
    </div>
  </div>
)
