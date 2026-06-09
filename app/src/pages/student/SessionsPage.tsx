import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FlaskConical } from 'lucide-react'
import { PageWrapper } from '@/components/shared/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { useSessions } from '@/hooks/student/useSessions'
import { useAssignments } from '@/hooks/student/useAssignments'
import { EmptyState } from '@/components/shared/EmptyState'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { SkeletonCard } from '@/components/shared/SkeletonCard'
import { formatDate, formatScore } from '@/lib/utils'
import { cn } from '@/lib/utils'
import type { SessionStatus } from '@/types/api'

const ALL_STATUSES: (SessionStatus | 'ALL')[] = ['ALL', 'STARTED', 'IN_PROGRESS', 'COMPLETED', 'REJECTED']

const SessionsPage = () => {
  const { data: sessions, isLoading } = useSessions()
  const { data: assignments } = useAssignments()
  const navigate = useNavigate()
  const [statusFilter, setStatusFilter] = useState<SessionStatus | 'ALL'>('ALL')

  const assignmentMap = Object.fromEntries((assignments ?? []).map((a) => [a.id, a.title]))

  const filtered = (sessions ?? []).filter(
    (s) => statusFilter === 'ALL' || s.status === statusFilter,
  )

  return (
    <PageWrapper>
      <PageHeader
        title="Sessions"
        description="Track all active and completed evaluation sessions."
      />

      {/* Status filter tabs */}
      <div className="mb-5 flex flex-wrap gap-2">
        {ALL_STATUSES.map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={cn(
              'rounded-full px-3 py-1.5 text-xs font-medium transition-colors',
              statusFilter === s
                ? 'bg-accent-blue text-white'
                : 'bg-navy-900 text-text-secondary border border-navy-800 hover:text-text-primary',
            )}
          >
            {s === 'ALL' ? 'All' : s.replace('_', ' ')}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={<FlaskConical size={28} />}
          title="No sessions found"
          message={
            statusFilter === 'ALL'
              ? 'Start an assignment to generate your first session.'
              : `No sessions with status "${statusFilter.replace('_', ' ')}".`
          }
          actionTo="/student/assignments"
          actionLabel="Browse Assignments"
        />
      ) : (
        <div className="overflow-hidden rounded-xl border border-navy-800">
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-sm">
              <thead className="sticky top-0 bg-navy-900/80">
                <tr>
                  {['Assignment', 'Status', 'Started', 'Submitted', 'Completed', 'Score', ''].map((h) => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-text-secondary">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((session, i) => (
                  <tr
                    key={session.id}
                    className={cn(
                      'cursor-pointer border-t border-navy-800 transition-colors hover:bg-navy-800/60',
                      i % 2 === 0 ? 'bg-navy-950' : 'bg-navy-900/30',
                    )}
                    onClick={() => navigate(`/student/sessions/${session.id}`)}
                  >
                    <td className="px-4 py-3 max-w-[200px]">
                      <p className="truncate font-medium text-text-primary">
                        {assignmentMap[session.assignment_id] ?? '—'}
                      </p>
                      <p className="font-mono text-xs text-text-secondary">{session.id.slice(0, 8)}…</p>
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={session.status} />
                    </td>
                    <td className="px-4 py-3 text-text-secondary text-xs">{formatDate(session.started_at)}</td>
                    <td className="px-4 py-3 text-text-secondary text-xs">{formatDate(session.submitted_at)}</td>
                    <td className="px-4 py-3 text-text-secondary text-xs">{formatDate(session.completed_at)}</td>
                    <td className="px-4 py-3 font-medium text-accent-teal">
                      {formatScore(session.final_score, null)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="text-xs text-accent-blue">View →</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </PageWrapper>
  )
}

export default SessionsPage
