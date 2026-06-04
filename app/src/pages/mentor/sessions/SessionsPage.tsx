import { useMemo, useState } from 'react'
import { FlaskConical, Search } from 'lucide-react'
import { PageWrapper } from '@/components/shared/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { DataTable } from '@/components/shared/DataTable'
import { EmptyState } from '@/components/shared/EmptyState'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { useMentorSessions } from '@/hooks/mentor/useMentor'
import { formatDate } from '@/lib/utils'

export const SessionsPage = () => {
  const { data: sessions, isLoading } = useMentorSessions()
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('ALL')

  const filteredData = useMemo(() => {
    if (!sessions) return []
    return sessions.filter((s) => {
      const matchesSearch = 
        (s.student_roll?.toLowerCase().includes(searchTerm.toLowerCase()) ?? false) || 
        s.student_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.assignment_title.toLowerCase().includes(searchTerm.toLowerCase())
      
      const matchesStatus = statusFilter === 'ALL' || s.status === statusFilter
      return matchesSearch && matchesStatus
    })
  }, [sessions, searchTerm, statusFilter])

  const headers = ['Session ID', 'Student', 'Assignment', 'Status', 'Started At', 'Score']

  const rows = useMemo(() => {
    return filteredData.map((s) => [
      <span key="id" className="font-mono text-xs text-text-secondary" title={s.id}>{s.id.substring(0, 8)}...</span>,
      <div key="student">
        <p className="font-medium text-sm text-text-primary">{s.student_name}</p>
        <p className="font-mono text-xs text-text-secondary">{s.student_roll ?? ''}</p>
      </div>,
      <span key="assignment" className="text-sm text-text-primary">{s.assignment_title}</span>,
      <StatusBadge key="status" status={s.status} />,
      <span key="started" className="text-xs text-text-secondary">{formatDate(s.started_at)}</span>,
      <span key="score" className="text-sm font-medium text-text-primary">
        {s.final_score !== null && s.final_score !== undefined ? s.final_score.toFixed(1) : '-'}
      </span>,
    ])
  }, [filteredData])

  return (
    <PageWrapper>
      <PageHeader
        title="Grading Sessions"
        description="Monitor ongoing and completed evaluation sessions."
      />

      <div className="card-dark p-5">
        <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-1 items-center gap-4">
            <div className="relative w-full max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary" size={16} />
              <input
                type="text"
                placeholder="Search by student or assignment..."
                className="input-dark w-full pl-9"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <select
              className="input-dark max-w-[150px]"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="ALL">All Statuses</option>
              <option value="STARTED">Started</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="SUBMITTED">Submitted</option>
              <option value="COMPLETED">Completed</option>
              <option value="REJECTED">Rejected</option>
            </select>
          </div>
        </div>

        {isLoading ? (
          <div className="animate-pulse space-y-4">
            <div className="h-10 rounded-lg bg-navy-900" />
            <div className="h-10 rounded-lg bg-navy-900" />
            <div className="h-10 rounded-lg bg-navy-900" />
          </div>
        ) : filteredData.length === 0 ? (
          <EmptyState
            icon={<FlaskConical size={24} />}
            title="No sessions found"
            message={searchTerm ? "Try adjusting your search or filters." : "No active or past sessions available."}
          />
        ) : (
          <DataTable headers={headers} rows={rows} />
        )}
      </div>
    </PageWrapper>
  )
}

export default SessionsPage
