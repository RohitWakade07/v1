import { GraduationCap, FlaskConical, Trophy, FileCheck2, CheckCircle2 } from 'lucide-react'
import { Link } from 'react-router-dom'
import { PageWrapper } from '@/components/shared/PageWrapper'
import { useAssignments } from '@/hooks/student/useAssignments'
import { useSessions } from '@/hooks/student/useSessions'
import { useResults } from '@/hooks/student/useResults'
import { StatCard } from '@/components/shared/StatCard'
import { AssignmentSummaryWidget } from '@/components/student/dashboard/AssignmentSummaryWidget'
import { RecentActivityFeed } from '@/components/student/dashboard/RecentActivityFeed'
import { QuickActionsPanel } from '@/components/student/dashboard/QuickActionsPanel'
import { EmptyState } from '@/components/shared/EmptyState'
import { SkeletonStatCard, SkeletonCard } from '@/components/shared/SkeletonCard'
import { useAuthStore } from '@/store/authStore'
import { formatDate } from '@/lib/utils'

const getGreeting = () => {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  return 'Good evening'
}

const DashboardPage = () => {
  const profile = useAuthStore((s) => s.profile)
  const assignmentsQuery = useAssignments()
  const sessionsQuery = useSessions()
  const resultsQuery = useResults()

  const isLoading =
    assignmentsQuery.isLoading || sessionsQuery.isLoading || resultsQuery.isLoading

  const assignments = assignmentsQuery.data ?? []
  const sessions = sessionsQuery.data ?? []
  const results = resultsQuery.data ?? []
  const activeSessions = sessions.filter((s) => ['STARTED', 'IN_PROGRESS'].includes(s.status))
  const totalScore = results.reduce((sum, r) => sum + r.final_score, 0)

  return (
    <PageWrapper>
      {/* Welcome banner */}
      <div className="mb-6 animate-fade-in-up">
        <p className="text-sm text-text-secondary">{getGreeting()},</p>
        <h1 className="font-display text-3xl font-bold text-text-primary">
          {profile?.full_name ?? profile?.roll_number ?? 'Student'}
        </h1>
        <p className="mt-1 text-sm text-text-secondary">
          Here's a summary of your academic activity on the E-Yantra EEP Platform.
        </p>
      </div>

      {/* Stat cards */}
      <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => <SkeletonStatCard key={i} />)
        ) : (
          <>
            <StatCard
              title="Published Assignments"
              value={assignments.length}
              icon={<GraduationCap size={18} />}
              accent="blue"
              subtitle="Available to attempt"
            />
            <StatCard
              title="Active Sessions"
              value={activeSessions.length}
              icon={<FlaskConical size={18} />}
              accent="warning"
              subtitle="Started or in progress"
            />
            <StatCard
              title="Completed Evaluations"
              value={results.length}
              icon={<Trophy size={18} />}
              accent="teal"
              subtitle="Verified by backend"
            />
            <StatCard
              title="Total Score Earned"
              value={totalScore.toFixed(1)}
              icon={<FileCheck2 size={18} />}
              accent="blue"
              subtitle="Across all evaluations"
            />
          </>
        )}
      </div>

      {/* Widget grid */}
      <div className="grid gap-5 xl:grid-cols-4">
        {/* Recent assignments (spans 1 col) */}
        {isLoading ? (
          <SkeletonCard className="xl:col-span-1" />
        ) : (
          <div className="xl:col-span-1">
            <AssignmentSummaryWidget assignments={assignments.slice(0, 3)} />
          </div>
        )}

        {/* Active sessions (spans 1 col) */}
        {isLoading ? (
          <SkeletonCard className="xl:col-span-1" />
        ) : (
          <div className="xl:col-span-1">
            <RecentActivityFeed sessions={activeSessions.slice(0, 3)} />
          </div>
        )}

        {/* Recent results (spans 1 col) */}
        <div className="xl:col-span-1">
          {isLoading ? (
            <SkeletonCard />
          ) : (
            <div className="card-dark p-5 h-full">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="font-display text-base font-semibold text-text-primary">Recent Results</h3>
                <Link to="/results" className="text-xs text-accent-blue hover:text-accent-teal transition-colors">
                  View all →
                </Link>
              </div>
              {results.length === 0 ? (
                <EmptyState
                  icon={<Trophy size={24} />}
                  title="No results yet"
                  message="Complete an evaluation to see your scores here."
                />
              ) : (
                <div className="space-y-3">
                  {results.slice(0, 3).map((result) => (
                    <Link
                      key={result.id}
                      to={`/results/${result.id}`}
                      className="flex items-center gap-3 rounded-lg p-2 transition-colors hover:bg-navy-800/40"
                    >
                      <CheckCircle2 size={16} className="shrink-0 text-accent-teal" />
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-text-primary">
                          {result.assignment_title}
                        </p>
                        <p className="text-xs text-text-secondary">
                          {formatDate(result.completed_at)}
                        </p>
                      </div>
                      <span className="shrink-0 text-sm font-semibold text-accent-teal">
                        {result.final_score.toFixed(1)}/{result.max_score}
                      </span>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Quick actions (spans 1 col) */}
        <div className="xl:col-span-1">
          <QuickActionsPanel />
        </div>
      </div>
    </PageWrapper>
  )
}

export default DashboardPage
