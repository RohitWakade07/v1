import { useParams, Link } from 'react-router-dom'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'
import { useSession } from '@/hooks/useSessions'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { SessionTimeline } from '@/components/sessions/SessionTimeline'
import { formatScore } from '@/lib/utils'

const SessionDetailPage = () => {
  const { id } = useParams()
  const { data, isLoading } = useSession(id)

  if (isLoading) return <LoadingSpinner />
  if (!data) return null

  return (
    <PageWrapper>
      <PageHeader
        title="Session Detail"
        description="Review the current status and proof submission details."
        action={
          (data.status === 'STARTED' || data.status === 'IN_PROGRESS') && (
            <Link
              to={`/proof/submit?session_id=${data.id}`}
              className="rounded-lg bg-accent-blue px-4 py-2 text-sm font-medium text-white"
            >
              Submit Proof
            </Link>
          )
        }
      />
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-navy-800 bg-navy-900/50 p-5 shadow-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-text-secondary">Session ID</p>
              <p className="font-mono text-sm text-text-primary">{data.id}</p>
            </div>
            <StatusBadge status={data.status} />
          </div>
          <div className="mt-4 text-sm text-text-secondary">
            <p>Assignment ID: {data.assignment_id}</p>
            <p>Final Score: {formatScore(data.final_score, null)}</p>
          </div>
          {data.rejection_reason && (
            <div className="mt-4 rounded-lg border border-status-danger/40 bg-status-danger/10 px-4 py-3 text-sm text-status-danger">
              {data.rejection_reason}
            </div>
          )}
        </div>
        <SessionTimeline session={data} />
      </div>
      {data.score_breakdown && (
        <div className="rounded-xl border border-navy-800 bg-navy-900/50 p-5 text-sm text-text-secondary shadow-card">
          <p className="font-medium text-text-primary">Score Breakdown</p>
          <pre className="mt-3 whitespace-pre-wrap font-mono text-xs">
            {JSON.stringify(data.score_breakdown, null, 2)}
          </pre>
        </div>
      )}
    </PageWrapper>
  )
}

export default SessionDetailPage
