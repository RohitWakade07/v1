import { BookOpen, Globe, Lock, Activity, PlusCircle, ArrowRight, Users } from 'lucide-react'
import { Link } from 'react-router-dom'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { StatCard } from '@/components/dashboard/StatCard'
import { useAssignments } from '@/hooks/useAssignments'
import { useMentorAnalytics } from '@/hooks/useMentor'
import { SkeletonCard, SkeletonStatCard } from '@/components/shared/SkeletonCard'
import { useAuthStore } from '@/store/authStore'
import { formatDate } from '@/lib/utils'

export const DashboardPage = () => {
  const { data: assignments, isLoading: assignmentsLoading } = useAssignments()
  const { data: analytics, isLoading: analyticsLoading } = useMentorAnalytics()
  const { username, role } = useAuthStore()

  const allAssignments = assignments ?? []
  const publishedCount = allAssignments.filter((a) => a.is_published).length
  const draftCount = allAssignments.length - publishedCount
  const recentAssignments = [...allAssignments]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5)

  return (
    <PageWrapper>
      <div className="mb-6 animate-fade-in-up">
        <h1 className="font-display text-3xl font-bold text-text-primary">
          Welcome back, {username || 'Mentor'}
        </h1>
        <p className="mt-1 text-sm text-text-secondary">
          Here's an overview of the platform's current status.
        </p>
      </div>

      <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {assignmentsLoading ? (
          Array.from({ length: 3 }).map((_, i) => <SkeletonStatCard key={i} />)
        ) : (
          <>
            <StatCard
              title="Total Assignments"
              value={allAssignments.length}
              icon={<BookOpen size={18} />}
              accent="blue"
              subtitle="Created across all time"
            />
            <StatCard
              title="Published"
              value={publishedCount}
              icon={<Globe size={18} />}
              accent="teal"
              subtitle="Live for students"
            />
            <StatCard
              title="Drafts"
              value={draftCount}
              icon={<Lock size={18} />}
              accent="warning"
              subtitle="Pending publication"
            />
          </>
        )}
        
        {analyticsLoading ? (
          <SkeletonStatCard />
        ) : (
          <StatCard
            title="Active Students"
            value={analytics?.total_students || 0}
            icon={<Users size={18} />}
            accent="blue"
            subtitle="Participating in assignments"
          />
        )}
      </div>

      <div className="grid gap-5 xl:grid-cols-3">
        <div className="xl:col-span-2">
          {assignmentsLoading ? (
            <SkeletonCard />
          ) : (
            <div className="card-dark h-full p-5 flex flex-col">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="font-display text-base font-semibold text-text-primary">Recent Assignments</h3>
                <Link to="/assignments" className="text-xs text-accent-blue hover:text-accent-teal transition-colors">
                  View all →
                </Link>
              </div>
              <div className="space-y-3 flex-1">
                {recentAssignments.map((a) => (
                  <div key={a.id} className="flex items-center justify-between rounded-lg bg-navy-950/50 p-3 border border-navy-800">
                    <div>
                      <p className="text-sm font-medium text-text-primary">{a.title}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-text-secondary font-mono">{a.slug}</span>
                        <span className="text-xs text-text-secondary">&bull;</span>
                        <span className="text-xs text-text-secondary">{formatDate(a.created_at)}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {a.is_published ? (
                        <span className="text-xs font-semibold text-accent-teal bg-accent-teal/10 px-2 py-0.5 rounded border border-accent-teal/20">Published</span>
                      ) : (
                        <span className="text-xs font-semibold text-status-warning bg-status-warning/10 px-2 py-0.5 rounded border border-status-warning/20">Draft</span>
                      )}
                      <Link to={`/assignments/${a.id}`} className="text-text-secondary hover:text-accent-blue p-1">
                        <ArrowRight size={16} />
                      </Link>
                    </div>
                  </div>
                ))}
                {recentAssignments.length === 0 && (
                  <p className="text-sm text-text-secondary py-4 text-center">No assignments created yet.</p>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="xl:col-span-1">
          <div className="card-dark h-full p-5">
            <h3 className="mb-4 font-display text-base font-semibold text-text-primary">Quick Actions</h3>
            <div className="space-y-3">
              <Link to="/assignments/create" className="btn-primary w-full justify-center">
                <PlusCircle size={16} /> Create New Assignment
              </Link>
              <Link to="/assignments" className="btn-secondary w-full justify-center">
                <BookOpen size={16} /> View All Assignments
              </Link>
              <Link to="/analytics" className="btn-secondary w-full justify-center">
                <Activity size={16} /> Platform Status
              </Link>
            </div>
            
            <div className="mt-8 border-t border-navy-800 pt-4">
              <p className="text-xs text-text-secondary uppercase tracking-wide mb-2">Current Session</p>
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-navy-800 flex items-center justify-center text-text-primary font-bold uppercase">
                  {username ? username.charAt(0) : 'M'}
                </div>
                <div>
                  <p className="text-sm font-medium text-text-primary">{username}</p>
                  <p className="text-xs font-mono text-text-secondary uppercase">{role}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div className="mt-5">
        {assignmentsLoading ? (
          <SkeletonCard />
        ) : (
          <div className="card-dark p-5">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="font-display text-base font-semibold text-text-primary">Platform Activity Feed</h3>
              <button className="text-xs text-text-secondary hover:text-accent-blue flex items-center gap-1">
                <Activity size={14} /> Refresh
              </button>
            </div>
            <div className="space-y-4 relative before:absolute before:inset-0 before:ml-2 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-navy-800 before:to-transparent">
              {recentAssignments.map((a) => (
                <div key={a.id} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                  <div className="flex items-center justify-center w-5 h-5 rounded-full border border-navy-800 bg-navy-900 shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow-card z-10">
                    <div className="w-1.5 h-1.5 rounded-full bg-accent-blue"></div>
                  </div>
                  <div className="w-[calc(100%-2rem)] md:w-[calc(50%-1.5rem)] card-dark p-4 rounded-xl border border-navy-800 shadow-card">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-display text-sm font-semibold text-text-primary">Assignment {a.is_published ? 'Published' : 'Created'}</span>
                      <span className="text-xs text-text-secondary">{formatDate(a.updated_at || a.created_at)}</span>
                    </div>
                    <p className="text-sm text-text-secondary">
                      Assignment <span className="font-mono text-accent-blue">'{a.slug}'</span> was {a.is_published ? 'published' : 'created'} by {a.created_by_id?.substring(0,8) || 'unknown'}.
                    </p>
                  </div>
                </div>
              ))}
              {recentAssignments.length === 0 && (
                <p className="text-sm text-text-secondary text-center py-4 relative z-10 bg-navy-950">No recent activity.</p>
              )}
            </div>
          </div>
        )}
      </div>
    </PageWrapper>
  )
}

export default DashboardPage
