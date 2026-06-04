import { FlaskConical } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { SessionSummary } from '@/types/api'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { formatRelative } from '@/lib/utils'

interface RecentActivityFeedProps {
  sessions: SessionSummary[]
}

export const RecentActivityFeed = ({ sessions }: RecentActivityFeedProps) => (
  <div className="card-dark p-5">
    <div className="mb-4 flex items-center justify-between">
      <h3 className="font-display text-base font-semibold text-text-primary">Active Sessions</h3>
      <Link to="/sessions" className="text-xs text-accent-blue hover:text-accent-teal transition-colors">
        View all →
      </Link>
    </div>
    {sessions.length === 0 ? (
      <p className="text-center text-sm text-text-secondary py-6">No active sessions. Start an assignment to begin.</p>
    ) : (
      <div className="space-y-3">
        {sessions.map((session) => (
          <Link
            key={session.id}
            to={`/sessions/${session.id}`}
            className="flex items-center gap-3 rounded-lg p-2 transition-colors hover:bg-navy-800/40"
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent-blue/10 text-accent-blue">
              <FlaskConical size={15} />
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-text-primary font-mono">
                {session.id?.slice(0, 8) ?? ''}…
              </p>
              <p className="text-xs text-text-secondary">
                {session.started_at ? formatRelative(session.started_at) : 'Just now'}
              </p>
            </div>
            <StatusBadge status={session.status} />
          </Link>
        ))}
      </div>
    )}
  </div>
)
