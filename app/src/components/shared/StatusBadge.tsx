import { cn } from '@/lib/utils'
import type { SessionStatus, AssignmentCategory } from '@/types/api'

// ── Generic status badge (for string statuses like admin views) ──────
const genericStyles: Record<string, string> = {
  active:    'bg-accent-teal/15 text-accent-teal border border-accent-teal/30',
  inactive:  'bg-navy-800/60 text-text-secondary border border-navy-800',
  published: 'bg-accent-teal/15 text-accent-teal border border-accent-teal/30',
  draft:     'bg-status-warning/15 text-status-warning border border-status-warning/30',
  PENDING:   'bg-status-warning/15 text-status-warning border border-status-warning/30',
  APPROVED:  'bg-accent-teal/15 text-accent-teal border border-accent-teal/30',
  REJECTED:  'bg-status-danger/15 text-status-danger border border-status-danger/30',
  STARTED:         'bg-accent-blue/15 text-accent-blue border border-accent-blue/30',
  IN_PROGRESS:     'bg-status-warning/15 text-status-warning border border-status-warning/30',
  COMPLETED:       'bg-accent-teal/15 text-accent-teal border border-accent-teal/30',
  SUBMITTED:       'bg-accent-blue/15 text-accent-blue border border-accent-blue/30',
  VERIFIED:        'bg-accent-teal/15 text-accent-teal border border-accent-teal/30',
  FAILED:          'bg-status-danger/15 text-status-danger border border-status-danger/30',
  ABORTED:         'bg-status-danger/15 text-status-danger border border-status-danger/30',
}

interface StatusBadgeProps { status: string; className?: string }
export const StatusBadge = ({ status, className }: StatusBadgeProps) => (
  <span className={cn(
    'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold tracking-wide',
    genericStyles[status] ?? 'bg-navy-800/60 text-text-secondary',
    className,
  )}>
    {status.replace(/_/g, ' ')}
  </span>
)

// ── Session-specific status badge ────────────────────────────────────
const sessionDot: Record<SessionStatus, string> = {
  STARTED: 'bg-accent-blue', IN_PROGRESS: 'bg-status-warning', COMPLETED: 'bg-accent-teal',
  REJECTED: 'bg-status-danger', SUBMITTED: 'bg-accent-blue', VERIFIED: 'bg-accent-teal',
  FAILED: 'bg-status-danger', ABORTED: 'bg-status-danger',
  CREATED: 'bg-navy-800', CHALLENGE_ISSUED: 'bg-status-warning',
  RUNNING: 'bg-accent-blue', PROOF_GENERATED: 'bg-accent-teal', PROOF_SUBMITTED: 'bg-accent-teal',
}

interface SessionStatusBadgeProps { status: SessionStatus; className?: string }
export const SessionStatusBadge = ({ status, className }: SessionStatusBadgeProps) => (
  <span className={cn(
    'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold tracking-wide',
    genericStyles[status] ?? 'bg-navy-800/60 text-text-secondary',
    className,
  )}>
    <span className={cn('h-1.5 w-1.5 rounded-full', sessionDot[status] ?? 'bg-text-secondary')} />
    {status.replace(/_/g, ' ')}
  </span>
)

// ── Category badge ────────────────────────────────────────────────────
const categoryLabels: Record<AssignmentCategory, string> = {
  artifact_validation: 'Artifact', deterministic_execution: 'Execution',
  filesystem_validation: 'Filesystem', git_validation: 'Git',
  network_validation: 'Network', documentation_review: 'Docs', manual_review: 'Manual',
}

interface CategoryBadgeProps { category: AssignmentCategory | string; className?: string }
export const CategoryBadge = ({ category, className }: CategoryBadgeProps) => (
  <span className={cn(`cat-${category} inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold tracking-wide`, className)}>
    {categoryLabels[category as AssignmentCategory] ?? category}
  </span>
)
