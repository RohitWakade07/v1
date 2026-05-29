import type { SessionSummary } from '@/types/api'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { formatDate } from '@/lib/utils'
import { Link } from 'react-router-dom'

interface SessionCardProps {
  session: SessionSummary
}

export const SessionCard = ({ session }: SessionCardProps) => (
  <div className="rounded-xl border border-navy-800 bg-navy-900/50 p-5 shadow-card">
    <div className="flex items-center justify-between">
      <StatusBadge status={session.status} />
      <span className="text-xs text-text-secondary">
        Started {formatDate(session.started_at)}
      </span>
    </div>
    <p className="mt-3 text-sm text-text-secondary">Session ID</p>
    <p className="font-mono text-sm text-text-primary">{session.id}</p>
    <div className="mt-4 flex items-center justify-between text-xs text-text-secondary">
      <span>Score: {session.final_score ?? 'N/A'}</span>
      <Link className="text-accent-blue" to={`/sessions/${session.id}`}>
        View Details
      </Link>
    </div>
  </div>
)
