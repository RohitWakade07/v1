import { PageWrapper } from '@/components/layout/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { useSessions } from '@/hooks/useSessions'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'
import { EmptyState } from '@/components/shared/EmptyState'
import { DataTable } from '@/components/shared/DataTable'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { formatDate } from '@/lib/utils'
import { Link } from 'react-router-dom'

const SessionsPage = () => {
  const { data, isLoading } = useSessions()

  if (isLoading) return <LoadingSpinner />

  const sessions = data ?? []

  if (sessions.length === 0) {
    return (
      <PageWrapper>
        <PageHeader
          title="Sessions"
          description="Track all active and completed evaluation sessions."
        />
        <EmptyState
          title="No sessions yet"
          message="Start an assignment to generate your first session."
        />
      </PageWrapper>
    )
  }

  const headers = ['Assignment', 'Status', 'Started', 'Completed', 'Score', '']
  const rows = sessions.map((session) => [
    session.assignment_id,
    <StatusBadge key={`status-${session.id}`} status={session.status} />,
    formatDate(session.started_at),
    formatDate(session.completed_at),
    session.final_score ?? 'N/A',
    <Link key={`view-${session.id}`} to={`/sessions/${session.id}`}>
      View
    </Link>,
  ])

  return (
    <PageWrapper>
      <PageHeader
        title="Sessions"
        description="Track all active and completed evaluation sessions."
      />
      <DataTable headers={headers} rows={rows} />
    </PageWrapper>
  )
}

export default SessionsPage
