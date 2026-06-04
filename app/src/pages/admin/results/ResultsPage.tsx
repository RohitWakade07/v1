import { useQuery } from '@tanstack/react-query'
import { listAllSessions } from '@/api/admin/admin'
import { PageWrapper } from '@/components/shared/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { SkeletonRow } from '@/components/shared/SkeletonCard'
import { formatDateTime, shortId } from '@/lib/utils'

export const ResultsPage = () => {
  const { data: sessions = [], isLoading, error } = useQuery({
    queryKey: ['admin-sessions'],
    queryFn: listAllSessions,
    retry: false,
  })

  const completed = sessions.filter((s) => s.status === 'COMPLETED')

  return (
    <PageWrapper>
      <PageHeader
        title="Results"
        description={`${completed.length} completed & scored sessions`}
      />
      <div className="card-dark overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-navy-800">
                {['Session ID', 'Student ID', 'Assignment ID', 'Final Score', 'Status', 'Completed At'].map((h) => (
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
                  <td colSpan={6} className="px-4 py-12 text-center text-text-secondary text-sm">
                    Could not load results — admin API endpoint not yet available.
                  </td>
                </tr>
              ) : completed.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-text-secondary text-sm">
                    No completed sessions yet.
                  </td>
                </tr>
              ) : (
                completed.map((s) => (
                  <tr key={s.id} className="border-b border-navy-800/50 hover:bg-navy-900/40 transition-colors">
                    <td className="px-4 py-3 font-mono text-xs text-accent-blue">{shortId(s.id)}</td>
                    <td className="px-4 py-3 font-mono text-xs text-text-secondary">{shortId(s.student_id)}</td>
                    <td className="px-4 py-3 font-mono text-xs text-text-secondary">{shortId(s.assignment_id)}</td>
                    <td className="px-4 py-3 font-mono font-bold text-accent-teal text-base">
                      {s.final_score != null ? s.final_score : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status="completed" />
                    </td>
                    <td className="px-4 py-3 text-text-secondary text-xs">{formatDateTime(s.completed_at)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {!isLoading && !error && (
          <div className="border-t border-navy-800 px-4 py-2 text-xs text-text-secondary">
            {completed.length} results total
          </div>
        )}
      </div>
    </PageWrapper>
  )
}

export default ResultsPage
