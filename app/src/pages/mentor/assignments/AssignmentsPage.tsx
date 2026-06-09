import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { PlusCircle, Eye, Send, Pencil, Globe, Lock, BookOpen } from 'lucide-react'
import { PageWrapper } from '@/components/shared/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { DataTable } from '@/components/shared/DataTable'
import { EmptyState } from '@/components/shared/EmptyState'
import { useAssignments } from '@/hooks/mentor/useAssignments'
import { usePublishAssignment } from '@/hooks/mentor/usePublishAssignment'
import { formatDate } from '@/lib/utils'


// Simple helper to check if deadline is past or within 7 days
const getDeadlineColor = (deadline: string | null) => {
  if (!deadline) return 'text-text-secondary'
  const date = new Date(deadline).getTime()
  const now = new Date().getTime()
  if (date < now) return 'text-status-danger'
  if (date - now < 7 * 24 * 60 * 60 * 1000) return 'text-status-warning'
  return 'text-text-secondary'
}

export const AssignmentsPage = () => {
  const { data: assignments, isLoading } = useAssignments()
  const publishMutation = usePublishAssignment()
  
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'published' | 'draft'>('all')

  const filteredData = useMemo(() => {
    if (!assignments) return []
    return assignments.filter((a) => {
      const matchesSearch = 
        a.title.toLowerCase().includes(searchTerm.toLowerCase()) || 
        a.slug.toLowerCase().includes(searchTerm.toLowerCase())
      
      const matchesStatus = 
        statusFilter === 'all' ? true :
        statusFilter === 'published' ? a.is_published :
        !a.is_published

      return matchesSearch && matchesStatus
    })
  }, [assignments, searchTerm, statusFilter])

  const headers = ['Title', 'Slug', 'Category', 'Status', 'Deadline', 'Created', '']

  const rows = useMemo(() => {
    return filteredData.map((a) => [
      <span key="title" className="font-medium text-text-primary">{a.title}</span>,
      <span key="slug" className="font-mono text-xs text-text-secondary">{a.slug}</span>,
      <span key="category" className="rounded-full bg-navy-800 px-2 py-0.5 text-xs font-medium text-text-secondary">
        {a.category.replace('_', ' ')}
      </span>,
      a.is_published ? (
        <span key="status" className="inline-flex items-center gap-1 rounded bg-accent-teal/10 px-2 py-0.5 text-xs font-semibold border border-accent-teal/20 text-accent-teal">
          <Globe size={12} /> Published
        </span>
      ) : (
        <span key="status" className="inline-flex items-center gap-1 rounded bg-status-warning/10 px-2 py-0.5 text-xs font-semibold border border-status-warning/20 text-status-warning">
          <Lock size={12} /> Draft
        </span>
      ),
      <span key="deadline" className={`text-xs ${getDeadlineColor(a.deadline ?? null)}`}>
        {a.deadline ? formatDate(a.deadline) : 'No deadline'}
      </span>,
      <span key="created" className="text-xs text-text-secondary">{formatDate(a.created_at)}</span>,
      <div key="actions" className="flex items-center justify-end gap-2">
        <Link
          to={`/mentor/assignments/${a.id}`}
          className="flex items-center gap-1 rounded p-1 text-xs text-text-secondary transition-colors hover:bg-navy-800 hover:text-accent-blue"
          title="View Details"
        >
          <Eye size={16} />
        </Link>
        
        {!a.is_published && (
          <button
            onClick={() => publishMutation.mutate(a.id)}
            disabled={publishMutation.isPending}
            className="flex items-center gap-1 rounded p-1 text-xs text-text-secondary transition-colors hover:bg-accent-teal/10 hover:text-accent-teal"
            title="Publish"
          >
            <Send size={16} />
          </button>
        )}
        
        <button
          disabled
          title="Coming in Phase 2"
          className="flex cursor-not-allowed items-center gap-1 rounded p-1 text-xs text-text-secondary/50 opacity-50"
        >
          <Pencil size={16} />
        </button>
      </div>
    ])
  }, [filteredData, publishMutation])

  return (
    <PageWrapper>
      <PageHeader
        title="Assignments"
        description="Manage platform assignments, drafts, and publication status."
        actions={
          <Link to="/mentor/assignments/create" className="btn-primary">
            <PlusCircle size={16} /> Create Assignment
          </Link>
        }
      />

      <div className="card-dark p-5">
        <div className="mb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-1 items-center gap-4">
            <input
              type="text"
              placeholder="Search by title or slug..."
              className="input-dark max-w-xs"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <select
              className="input-dark max-w-[150px]"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as 'all' | 'published' | 'draft')}
            >
              <option value="all">All Status</option>
              <option value="published">Published</option>
              <option value="draft">Drafts</option>
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
            icon={<BookOpen size={24} />}
            title="No assignments found"
            message={searchTerm ? "Try adjusting your search or filters." : "Create your first assignment to get started."}
            action={!searchTerm && <Link to="/mentor/assignments/create" className="btn-primary mt-4">Create Assignment</Link>}
          />
        ) : (
          <DataTable headers={headers} rows={rows} />
        )}
      </div>
    </PageWrapper>
  )
}

export default AssignmentsPage
