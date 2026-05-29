import type { SessionSummary } from '@/types/api'
import { formatDate } from '@/lib/utils'

interface SessionTimelineProps {
  session: SessionSummary
}

export const SessionTimeline = ({ session }: SessionTimelineProps) => (
  <div className="grid gap-3 rounded-xl border border-navy-800 bg-navy-900/50 p-4 text-sm text-text-secondary">
    <div className="flex justify-between">
      <span>Started</span>
      <span>{formatDate(session.started_at)}</span>
    </div>
    <div className="flex justify-between">
      <span>Submitted</span>
      <span>{formatDate(session.submitted_at)}</span>
    </div>
    <div className="flex justify-between">
      <span>Completed</span>
      <span>{formatDate(session.completed_at)}</span>
    </div>
  </div>
)
