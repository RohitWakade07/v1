import { useMemo, useState } from 'react'
import { InboxIcon, Search } from 'lucide-react'
import { DataTable } from '@/components/shared/DataTable'
import { EmptyState } from '@/components/shared/EmptyState'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { useMentorSubmissions } from '@/hooks/mentor/useMentor'
import { formatDateTime } from '@/lib/utils'

const STATUS_OPTIONS = [
  'ALL', 'PENDING', 'QUEUED', 'RUNNING', 'COMPLETED', 'FAILED', 'TIMEOUT', 'CANCELLED', 'VALIDATION_ERROR',
]

export const GlobalQueueView = () => {
  const { data: submissions, isLoading } = useMentorSubmissions()
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('ALL')

  const filteredData = useMemo(() => {
    if (!submissions) return []
    return submissions.filter((s) => {
      const matchesSearch =
        s.student_roll.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.student_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.assignment_title.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesStatus = statusFilter === 'ALL' || s.status === statusFilter
      return matchesSearch && matchesStatus
    })
  }, [submissions, searchTerm, statusFilter])

  const headers = ['Student', 'Assignment', 'Type', 'Attempt', 'Status', 'Score', 'Submitted At']

  const rows = useMemo(() => {
    return filteredData.map((s) => [
      <div key={`student-${s.id}`}>
        <p className="font-medium text-sm text-text-primary">{s.student_name}</p>
        <p className="font-mono text-xs text-text-secondary">{s.student_roll}</p>
      </div>,
      <div key={`assignment-${s.id}`}>
        <p className="text-sm text-text-primary">{s.assignment_title}</p>
        <p className="font-mono text-xs text-text-secondary">{s.assignment_slug}</p>
      </div>,
      <span key={`type-${s.id}`} className="font-mono text-xs uppercase text-text-secondary">
        {s.source_type}
      </span>,
      <span key={`attempt-${s.id}`} className="font-mono text-xs text-text-primary">
        #{s.attempt_number}
      </span>,
      <StatusBadge key={`status-${s.id}`} status={s.status} />,
      <span key={`score-${s.id}`} className="font-mono text-sm font-medium">
        {s.score != null ? (
          <span className={s.passed ? 'text-accent-teal' : 'text-status-warning'}>
            {s.score.toFixed(1)}
            {s.max_score != null && (
              <span className="text-text-secondary text-xs ml-1">/ {s.max_score}</span>
            )}
          </span>
        ) : (
          <span className="text-text-muted">—</span>
        )}
      </span>,
      <span key={`submitted-${s.id}`} className="text-xs text-text-secondary">
        {formatDateTime(s.submitted_at)}
      </span>,
    ])
  }, [filteredData])

  return (
    <div className="card-dark p-5 mt-6">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-1 items-center gap-4 flex-wrap">
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
            className="input-dark max-w-[180px]"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            {STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s === 'ALL' ? 'All Statuses' : s.replace(/_/g, ' ')}
              </option>
            ))}
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
          icon={<InboxIcon size={24} />}
          title="No submissions found"
          message={searchTerm || statusFilter !== 'ALL'
            ? 'Try adjusting your search or filters.'
            : 'No submissions have been made yet.'}
        />
      ) : (
        <DataTable headers={headers} rows={rows} />
      )}
    </div>
  )
}
