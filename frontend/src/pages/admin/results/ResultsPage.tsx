import { useQuery } from '@tanstack/react-query'
import { listAllSessions } from '@/api/admin/admin'
import { PageWrapper } from '@/components/shared/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { SkeletonRow } from '@/components/shared/SkeletonCard'
import { formatDateTime } from '@/lib/utils'
import { useState } from 'react'

export const ResultsPage = () => {
  const [search, setSearch] = useState('')
  const { data: sessionsResponse, isLoading, error } = useQuery({
    queryKey: ['admin-sessions'],
    queryFn: () => listAllSessions(1, 1000),
    retry: false,
  })

  const sessions = sessionsResponse?.data || []
  const completed = sessions.filter((s) => s.status === 'COMPLETED')
  const filtered = completed.filter(
    (s) =>
      (s.student_name?.toLowerCase() || '').includes(search.toLowerCase()) ||
      (s.student_roll?.toLowerCase() || '').includes(search.toLowerCase())
  )

  return (
    <PageWrapper>
      <PageHeader
        title="Results"
        description={`${filtered.length} completed & scored sessions`}
      />
      <div className="mb-4">
        <input
          type="text"
          placeholder="Search by name or roll..."
          className="w-full bg-navy-900 border border-navy-800 rounded px-4 py-2 text-sm text-text-primary"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>
      <div className="card-dark overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-navy-800">
                {['Student', 'Assignment', 'Final Score', 'Status', 'Completed At'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold tracking-widest text-text-secondary uppercase">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => <SkeletonRow key={i} />)
              ) : error ? (
                <tr>
                  <td colSpan={5} className="px-4 py-12 text-center text-text-secondary text-sm">
                    Could not load results — admin API endpoint not yet available.
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-12 text-center text-text-secondary text-sm">
                    No completed sessions yet.
                  </td>
                </tr>
              ) : (
                filtered.map((s) => (
                  <tr key={s.id} className="border-b border-navy-800/50 hover:bg-navy-900/40 transition-colors">
                    <td className="px-4 py-3">
                      <p className="font-medium text-text-primary">{s.student_name}</p>
                      <p className="font-mono text-xs text-text-secondary">{s.student_roll}</p>
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-text-primary">{s.assignment_title}</p>
                      <p className="font-mono text-xs text-text-secondary">{s.assignment_slug}</p>
                    </td>
                    <td className="px-4 py-3 font-mono font-bold text-accent-teal text-base">
                      {s.final_score != null ? s.final_score : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status="completed" />
                    </td>
                    <td className="px-4 py-3 text-text-secondary text-xs">{formatDateTime(s.completed_at || '')}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {!isLoading && !error && (
          <div className="border-t border-navy-800 px-4 py-2 text-xs text-text-secondary">
            {filtered.length} results total
          </div>
        )}
      </div>
    </PageWrapper>
  )
}

export default ResultsPage
