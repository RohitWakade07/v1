import { FlaskConical, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { SessionSummary } from '@/types/api'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { formatDate, formatScore } from '@/lib/utils'

interface SessionCardProps {
  session: SessionSummary
  assignmentTitle?: string
}

export const SessionCard = ({ session, assignmentTitle }: SessionCardProps) => (
  <div className="card-dark transition-card p-5">
    <div className="flex items-start justify-between gap-3">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-accent-blue/10 text-accent-blue">
          <FlaskConical size={16} />
        </div>
        <div>
          <p className="text-sm font-medium text-text-primary">
            {assignmentTitle ?? 'Session'}
          </p>
          <p className="font-mono text-xs text-text-secondary">{session.id.slice(0, 8)}…</p>
        </div>
      </div>
      <StatusBadge status={session.status} />
    </div>

    <div className="mt-4 grid grid-cols-2 gap-3 text-xs text-text-secondary">
      <div>
        <p className="uppercase tracking-wide">Started</p>
        <p className="mt-0.5 text-text-primary">{formatDate(session.started_at)}</p>
      </div>
      <div>
        <p className="uppercase tracking-wide">Completed</p>
        <p className="mt-0.5 text-text-primary">{formatDate(session.completed_at)}</p>
      </div>
    </div>

    {session.final_score !== null && session.final_score !== undefined && (
      <div className="mt-3 rounded-lg bg-accent-teal/10 px-3 py-2 text-sm font-semibold text-accent-teal">
        Score: {formatScore(session.final_score, null)}
      </div>
    )}

    <div className="mt-4 flex justify-end">
      <Link
        to={`/sessions/${session.id}`}
        className="inline-flex items-center gap-1 text-sm font-medium text-accent-blue hover:text-accent-teal transition-colors"
      >
        View Details <ArrowRight size={14} />
      </Link>
    </div>
  </div>
)
