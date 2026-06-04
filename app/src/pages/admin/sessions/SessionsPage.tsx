import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search } from 'lucide-react'
import { PageWrapper } from '@/components/shared/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { SkeletonRow } from '@/components/shared/SkeletonCard'
import { listAllSessions } from '@/api/admin/admin'
import { formatDateTime, shortId } from '@/lib/utils'

export const SessionsPage = () => {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('ALL')

  const { data: sessions = [], isLoading, error } = useQuery({
    queryKey: ['admin-sessions'],
    queryFn: listAllSessions,
    retry: false,
  })

  const STATUSES = ['ALL', 'STARTED', 'IN_PROGRESS', 'SUBMITTED', 'COMPLETED', 'REJECTED']

  const filtered = sessions.filter((s) => {
    const matchStatus = statusFilter === 'ALL' || s.status === statusFilter
    const matchSearch =
      s.id.toLowerCase().includes(search.toLowerCase()) ||
      s.student_id.toLowerCase().includes(search.toLowerCase()) ||
      s.assignment_id.toLowerCase().includes(search.toLowerCase())
    return matchStatus && matchSearch
  })

  return (
    <PageWrapper>
      <PageHeader
        title="Sessions & Proofs"
        description={`${sessions.length} total grading sessions`}
      />

      {/* Filters */}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="relative">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search session or student ID…"
            className="input-dark pl-9 w-72"
          />
        </div>
        <div className="flex flex-wrap gap-1">
          {STATUSES.map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1 text-xs font-semibold rounded-lg border transition-colors ${
                statusFilter === s
                  ? 'bg-accent-blue text-white border-accent-blue'
                  : 'text-text-secondary border-navy-800 hover:border-accent-blue hover:text-accent-blue'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <div className="card-dark overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-navy-800">
                {['Session ID', 'Student ID', 'Assignment ID', 'Status', 'Score', 'Started At', 'Completed At'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold tracking-widest text-text-secondary uppercase">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                Array.from({ length: 6 }).map((_, i) => <SkeletonRow key={i} />)
              ) : error ? (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center text-text-secondary text-sm">
                    Could not load sessions — admin API endpoint not yet available.
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center text-text-secondary text-sm">
                    No sessions found.
                  </td>
                </tr>
              ) : (
                filtered.map((session) => (
                  <tr key={session.id} className="border-b border-navy-800/50 hover:bg-navy-900/40 transition-colors">
                    <td className="px-4 py-3 font-mono text-xs text-accent-blue">{shortId(session.id)}</td>
                    <td className="px-4 py-3 font-mono text-xs text-text-secondary">{shortId(session.student_id)}</td>
                    <td className="px-4 py-3 font-mono text-xs text-text-secondary">{shortId(session.assignment_id)}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={session.status.toLowerCase()} />
                    </td>
                    <td className="px-4 py-3 font-mono text-accent-teal font-semibold">
                      {session.final_score != null ? session.final_score : '—'}
                    </td>
                    <td className="px-4 py-3 text-text-secondary text-xs">{formatDateTime(session.started_at)}</td>
                    <td className="px-4 py-3 text-text-secondary text-xs">{formatDateTime(session.completed_at)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {!isLoading && !error && (
          <div className="border-t border-navy-800 px-4 py-2 text-xs text-text-secondary">
            Showing {filtered.length} of {sessions.length} sessions
          </div>
        )}
      </div>
    </PageWrapper>
  )
}

export default SessionsPage
