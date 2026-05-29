import { cn } from '@/lib/utils'
import type { SessionStatus } from '@/types/api'

const statusStyles: Record<SessionStatus, string> = {
  STARTED: 'bg-accent-blue/20 text-accent-blue',
  IN_PROGRESS: 'bg-status-warning/20 text-status-warning',
  COMPLETED: 'bg-accent-teal/20 text-accent-teal',
  REJECTED: 'bg-status-danger/20 text-status-danger',
}

export const StatusBadge = ({ status }: { status: SessionStatus }) => (
  <span
    className={cn(
      'rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide',
      statusStyles[status],
    )}
  >
    {status.replace('_', ' ')}
  </span>
)
