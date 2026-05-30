import { cn } from '@/lib/utils'
import type { SessionStatus } from '@/types/api'
import type { AssignmentCategory } from '@/types/api'

/* ── Session status badge ─────────────────────────────────────────── */
const sessionStyles: Record<SessionStatus, { bg: string; dot: string; label: string }> = {
  STARTED: {
    bg: 'bg-accent-blue/15 text-accent-blue border border-accent-blue/30',
    dot: 'bg-accent-blue',
    label: 'Started',
  },
  IN_PROGRESS: {
    bg: 'bg-status-warning/15 text-status-warning border border-status-warning/30',
    dot: 'bg-status-warning',
    label: 'In Progress',
  },
  COMPLETED: {
    bg: 'bg-accent-teal/15 text-accent-teal border border-accent-teal/30',
    dot: 'bg-accent-teal',
    label: 'Completed',
  },
  REJECTED: {
    bg: 'bg-status-danger/15 text-status-danger border border-status-danger/30',
    dot: 'bg-status-danger',
    label: 'Rejected',
  },
}

interface StatusBadgeProps {
  status: SessionStatus
  className?: string
}

export const StatusBadge = ({ status, className }: StatusBadgeProps) => {
  const style = sessionStyles[status]
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold tracking-wide',
        style.bg,
        className,
      )}
    >
      <span className={cn('h-1.5 w-1.5 rounded-full', style.dot)} />
      {style.label}
    </span>
  )
}

/* ── Category badge ───────────────────────────────────────────────── */
const categoryLabels: Record<AssignmentCategory, string> = {
  artifact_validation: 'Artifact',
  deterministic_execution: 'Execution',
  filesystem_validation: 'Filesystem',
  git_validation: 'Git',
  network_validation: 'Network',
  documentation_review: 'Docs',
  manual_review: 'Manual',
}

interface CategoryBadgeProps {
  category: AssignmentCategory
  className?: string
}

export const CategoryBadge = ({ category, className }: CategoryBadgeProps) => (
  <span
    className={cn(
      `cat-${category} inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold tracking-wide`,
      className,
    )}
  >
    {categoryLabels[category]}
  </span>
)
