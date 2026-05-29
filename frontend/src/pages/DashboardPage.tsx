import { GraduationCap, FlaskConical, Trophy, FileCheck2 } from 'lucide-react'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { useAssignments } from '@/hooks/useAssignments'
import { useSessions } from '@/hooks/useSessions'
import { useResults } from '@/hooks/useResults'
import { StatCard } from '@/components/dashboard/StatCard'
import { AssignmentSummaryWidget } from '@/components/dashboard/AssignmentSummaryWidget'
import { RecentActivityFeed } from '@/components/dashboard/RecentActivityFeed'
import { EmptyState } from '@/components/shared/EmptyState'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'

const DashboardPage = () => {
  const assignmentsQuery = useAssignments()
  const sessionsQuery = useSessions()
  const resultsQuery = useResults()

  if (assignmentsQuery.isLoading || sessionsQuery.isLoading || resultsQuery.isLoading) {
    return <LoadingSpinner />
  }

  const assignments = assignmentsQuery.data ?? []
  const sessions = sessionsQuery.data ?? []
  const results = resultsQuery.data ?? []
  const activeSessions = sessions.filter((session) =>
    ['STARTED', 'IN_PROGRESS'].includes(session.status),
  )
  const totalScore = results.reduce((sum, item) => sum + item.final_score, 0)

  return (
    <PageWrapper>
      <PageHeader
        title="Student Dashboard"
        description="Summary of your assignments and evaluation activity."
      />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Published Assignments"
          value={assignments.length}
          icon={<GraduationCap size={20} />}
        />
        <StatCard
          title="Active Sessions"
          value={activeSessions.length}
          icon={<FlaskConical size={20} />}
        />
        <StatCard
          title="Completed Evaluations"
          value={results.length}
          icon={<Trophy size={20} />}
        />
        <StatCard
          title="Total Score"
          value={totalScore.toFixed(1)}
          icon={<FileCheck2 size={20} />}
        />
      </div>
      <div className="grid gap-6 xl:grid-cols-3">
        <AssignmentSummaryWidget assignments={assignments.slice(0, 3)} />
        <RecentActivityFeed
          items={activeSessions.slice(0, 3).map((session) => ({
            label: `Session ${session.id.slice(0, 6)}...`,
            detail: `Status: ${session.status}`,
          }))}
        />
        <div className="rounded-xl border border-navy-800 bg-navy-900/50 p-5 shadow-card">
          <h3 className="font-display text-lg font-semibold text-text-primary">
            Recent Results
          </h3>
          {results.length === 0 ? (
            <EmptyState
              title="No results yet"
              message="Completed evaluations will appear here."
            />
          ) : (
            <div className="mt-4 space-y-3">
              {results.slice(0, 3).map((result) => (
                <div key={result.id} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-text-primary">
                      {result.assignment_title}
                    </p>
                    <p className="text-xs text-text-secondary">
                      {result.category.replace('_', ' ')}
                    </p>
                  </div>
                  <span className="text-sm text-accent-teal">
                    {result.final_score.toFixed(1)} / {result.max_score.toFixed(1)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </PageWrapper>
  )
}

export default DashboardPage
