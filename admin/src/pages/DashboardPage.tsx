import { useQuery } from '@tanstack/react-query'
import {
  Users, UserCheck, BookOpen, Globe, Activity, FileText, HeartPulse,
} from 'lucide-react'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { StatCard } from '@/components/shared/StatCard'
import { SkeletonStatCard, SkeletonCard } from '@/components/shared/SkeletonCard'
import { useAuthStore } from '@/store/authStore'
import { listAllAssignments } from '@/api/assignments'
import { listStudents, listMentors } from '@/api/users'
import { listAllSessions } from '@/api/sessions'
import { getHealth } from '@/api/health'
import { greeting, formatDate, shortId } from '@/lib/utils'

export const DashboardPage = () => {
  const { username } = useAuthStore()

  const { data: assignments = [], isLoading: aLoad } = useQuery({
    queryKey: ['admin-assignments'],
    queryFn: listAllAssignments,
    retry: false,
  })

  const { data: students = [], isLoading: sLoad } = useQuery({
    queryKey: ['admin-students'],
    queryFn: listStudents,
    retry: false,
  })

  const { data: mentors = [], isLoading: mLoad } = useQuery({
    queryKey: ['admin-mentors'],
    queryFn: listMentors,
    retry: false,
  })

  const { data: sessions = [], isLoading: sessLoad } = useQuery({
    queryKey: ['admin-sessions'],
    queryFn: listAllSessions,
    retry: false,
  })

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: getHealth,
    retry: false,
  })

  const published = assignments.filter((a) => a.is_published).length
  const drafts = assignments.length - published
  const recentAssignments = [...assignments]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 6)

  return (
    <PageWrapper>
      {/* Header */}
      <div className="mb-6 animate-fade-in-up">
        <h1 className="font-display text-3xl font-bold text-text-primary">
          {greeting()}, {username || 'Admin'} 👋
        </h1>
        <p className="mt-1 text-sm text-text-secondary">
          Platform-wide overview — E-Yantra EEP Admin Control Center
        </p>
      </div>

      {/* Stat grid */}
      <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {sLoad ? <SkeletonStatCard /> : (
          <StatCard title="Total Students" value={students.length} icon={<Users size={18} />} accent="blue" subtitle="Registered learners" />
        )}
        {mLoad ? <SkeletonStatCard /> : (
          <StatCard title="Total Mentors" value={mentors.length} icon={<UserCheck size={18} />} accent="teal" subtitle="Active instructors" />
        )}
        {aLoad ? (
          <>
            <SkeletonStatCard />
            <SkeletonStatCard />
          </>
        ) : (
          <>
            <StatCard title="Published" value={published} icon={<Globe size={18} />} accent="teal" subtitle="Live assignments" />
            <StatCard title="Drafts" value={drafts} icon={<BookOpen size={18} />} accent="warning" subtitle="Pending publication" />
          </>
        )}
      </div>

      <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {sessLoad ? <SkeletonStatCard /> : (
          <StatCard title="Total Sessions" value={sessions.length} icon={<Activity size={18} />} accent="blue" subtitle="All grading sessions" />
        )}
        {sessLoad ? <SkeletonStatCard /> : (
          <StatCard
            title="Completed Sessions"
            value={sessions.filter((s) => s.status === 'COMPLETED').length}
            icon={<FileText size={18} />}
            accent="teal"
            subtitle="Verified & scored"
          />
        )}
        <StatCard
          title="Platform Health"
          value={health?.status === 'ok' ? 'Operational' : (health ? 'Degraded' : 'Unknown')}
          icon={<HeartPulse size={18} />}
          accent={health?.status === 'ok' ? 'teal' : 'danger'}
          subtitle={health?.database === 'ok' ? 'DB connected' : 'Check health page'}
        />
      </div>

      {/* Recent assignments timeline + quick stats */}
      <div className="grid gap-5 xl:grid-cols-3">
        {/* Timeline */}
        <div className="xl:col-span-2">
          {aLoad ? <SkeletonCard /> : (
            <div className="card-dark p-5">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="font-display text-base font-semibold text-text-primary">Recent Assignments</h3>
                <a href="/assignments" className="text-xs text-accent-blue hover:text-accent-teal transition-colors">
                  View all →
                </a>
              </div>
              <div className="space-y-4 relative before:absolute before:inset-0 before:ml-2 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-navy-800 before:to-transparent">
                {recentAssignments.map((a) => (
                  <div key={a.id} className="relative flex items-start gap-4 pl-6">
                    <div className="absolute left-0 top-2 flex h-4 w-4 items-center justify-center rounded-full border border-navy-800 bg-navy-900 z-10">
                      <div className="h-1.5 w-1.5 rounded-full bg-accent-blue" />
                    </div>
                    <div className="flex-1 rounded-xl bg-navy-950/50 border border-navy-800 p-3">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-display text-sm font-semibold text-text-primary">{a.title}</span>
                        <span className={`text-xs font-semibold px-2 py-0.5 rounded ${a.is_published ? 'text-accent-teal bg-accent-teal/10 border border-accent-teal/20' : 'text-status-warning bg-status-warning/10 border border-status-warning/20'}`}>
                          {a.is_published ? 'Published' : 'Draft'}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-text-secondary">
                        <span className="font-mono">{a.slug}</span>
                        <span>•</span>
                        <span>{formatDate(a.created_at)}</span>
                        <span>•</span>
                        <span>by {shortId(a.created_by_id)}</span>
                      </div>
                    </div>
                  </div>
                ))}
                {recentAssignments.length === 0 && (
                  <p className="text-sm text-text-secondary py-4 text-center relative z-10">No assignments yet.</p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Quick stats */}
        <div className="xl:col-span-1">
          <div className="card-dark p-5 h-full">
            <h3 className="mb-4 font-display text-base font-semibold text-text-primary">Session Breakdown</h3>
            {sessLoad ? (
              <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, i) => <div key={i} className="skeleton h-8 w-full" />)}
              </div>
            ) : (
              <div className="space-y-2">
                {[
                  { label: 'Started', status: 'STARTED', cls: 'bg-navy-800 text-text-secondary' },
                  { label: 'In Progress', status: 'IN_PROGRESS', cls: 'bg-accent-blue/10 text-accent-blue' },
                  { label: 'Submitted', status: 'SUBMITTED', cls: 'bg-accent-blue/10 text-accent-blue' },
                  { label: 'Completed', status: 'COMPLETED', cls: 'bg-accent-teal/10 text-accent-teal' },
                  { label: 'Rejected', status: 'REJECTED', cls: 'bg-status-danger/10 text-status-danger' },
                ].map(({ label, status, cls }) => {
                  const count = sessions.filter((s) => s.status === status).length
                  return (
                    <div key={status} className="flex items-center justify-between rounded-lg border border-navy-800 p-3">
                      <span className="text-sm text-text-secondary">{label}</span>
                      <span className={`font-display text-lg font-bold ${cls.split(' ')[1]}`}>{count}</span>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </PageWrapper>
  )
}

export default DashboardPage
