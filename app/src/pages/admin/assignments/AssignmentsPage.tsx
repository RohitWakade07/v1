import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Search, Globe, Lock, PenTool, FileText, Plus, Trash2 } from \'lucide-react\'
import { Link } from 'react-router-dom'
import { PageWrapper } from '@/components/shared/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { SkeletonRow } from '@/components/shared/SkeletonCard'
import { listAllAssignments, publishAssignment, unpublishAssignment, deleteAssignment } from \'@/api/admin/admin\'
import { formatDate, shortId } from '@/lib/utils'
import { EditAssignmentModal } from './EditAssignmentModal'
import { CreateAssignmentModal } from './CreateAssignmentModal'
import { Assignment } from '@/types/api'

const CATEGORY_LABELS: Record<string, string> = {
  artifact_validation: 'Artifact',
  deterministic_execution: 'Deterministic',
  filesystem_validation: 'Filesystem',
  git_validation: 'Git',
  network_validation: 'Network',
  documentation_review: 'Docs',
  manual_review: 'Manual',
}

export const AssignmentsPage = () => {
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<'all' | 'published' | 'draft'>('all')
  const [editingAssignment, setEditingAssignment] = useState<Assignment | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const qc = useQueryClient()
  const deleteMut = useMutation({
    mutationFn: deleteAssignment,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-assignments'] })
    },
  })

  const { data: assignments = [], isLoading, error } = useQuery({
    queryKey: ['admin-assignments'],
    queryFn: listAllAssignments,
    retry: false,
  })

  const publishMut = useMutation({
    mutationFn: publishAssignment,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin-assignments'] }),
  })
  const unpublishMut = useMutation({
    mutationFn: unpublishAssignment,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin-assignments'] }),
  })

  const filtered = assignments
    .filter((a) => {
      if (filter === 'published') return a.is_published
      if (filter === 'draft') return !a.is_published
      return true
    })
    .filter(
      (a) =>
        a.title.toLowerCase().includes(search.toLowerCase()) ||
        a.slug.toLowerCase().includes(search.toLowerCase())
    )

  return (
    <PageWrapper>
      <PageHeader
        title="Assignments"
        description={`${assignments.length} total assignments`}
        actions={
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-1.5 text-xs font-semibold px-3 py-2 rounded-lg bg-accent-teal text-white hover:bg-accent-teal/80 transition-colors"
          >
            <Plus size={14} /> New Assignment
          </button>
        }
      />

      {/* Filters */}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="relative">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search title or slug…"
            className="input-dark pl-9 w-64"
          />
        </div>
        <div className="flex rounded-lg border border-navy-800 overflow-hidden">
          {(['all', 'published', 'draft'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-2 text-xs font-semibold capitalize transition-colors ${
                filter === f
                  ? 'bg-accent-blue text-white'
                  : 'text-text-secondary hover:text-text-primary hover:bg-navy-900'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      <div className="card-dark overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-navy-800">
                {['Assignment', 'Slug', 'Category', 'Max Score', 'Penalty %', 'Deadline', 'Status', 'Actions'].map((h) => (
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
                  <td colSpan={8} className="px-4 py-12 text-center text-text-secondary text-sm">
                    Could not load assignments.
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-12 text-center text-text-secondary text-sm">
                    No assignments found.
                  </td>
                </tr>
              ) : (
                filtered.map((a) => (
                  <tr key={a.id} className="border-b border-navy-800/50 hover:bg-navy-900/40 transition-colors">
                    <td className="px-4 py-3">
                      <p className="font-medium text-text-primary">{a.title}</p>
                      <p className="text-xs text-text-secondary font-mono">{shortId(a.id)}</p>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-accent-blue">{a.slug}</td>
                    <td className="px-4 py-3">
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded cat-${a.category}`}>
                        {CATEGORY_LABELS[a.category] ?? a.category}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono text-text-primary">{a.max_score}</td>
                    <td className="px-4 py-3 font-mono text-status-warning">{a.late_penalty_pct ?? 0}%</td>
                    <td className="px-4 py-3 text-text-secondary">{formatDate(a.deadline)}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={a.is_published ? 'published' : 'draft'} />
                    </td>
                    <td className="px-4 py-3 flex items-center gap-2">
                      {a.is_published ? (
                        <button
                          onClick={() => unpublishMut.mutate(a.id)}
                          disabled={unpublishMut.isPending}
                          className="flex items-center gap-1 text-xs text-status-warning hover:text-status-warning/80 border border-status-warning/30 rounded px-2 py-1 transition-colors"
                        >
                          <Lock size={11} /> Unpublish
                        </button>
                      ) : (
                        <button
                          onClick={() => publishMut.mutate(a.id)}
                          disabled={publishMut.isPending}
                          className="flex items-center gap-1 text-xs text-accent-teal hover:text-accent-teal/80 border border-accent-teal/30 rounded px-2 py-1 transition-colors"
                        >
                          <Globe size={11} /> Publish
                        </button>
                      )}
                      <button
                        onClick={() => setEditingAssignment(a)}
                        className="flex items-center gap-1 text-xs text-accent-blue hover:text-accent-blue/80 border border-accent-blue/30 rounded px-2 py-1 transition-colors"
                      >
                        <PenTool size={11} /> Edit
                      </button>
                      <Link
                        to={`/admin/assignments/${a.id}/quiz`}
                        className="flex items-center gap-1 text-xs text-purple-400 hover:text-purple-300 border border-purple-400/30 rounded px-2 py-1 transition-colors"
                      >
                        <FileText size={11} /> Quiz
                      </Link>
                        <button
                          onClick={() => {
                            if (window.confirm("Are you sure you want to delete this assignment?")) {
                              deleteMut.mutate(a.id);
                            }
                          }}
                          disabled={deleteMut.isPending}
                          className="flex items-center gap-1 text-xs text-status-error hover:text-status-error/80 border border-status-error/30 rounded px-2 py-1 transition-colors"
                        >
                          <Trash2 size={11} /> Delete
                        </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {!isLoading && !error && (
          <div className="border-t border-navy-800 px-4 py-2 text-xs text-text-secondary">
            Showing {filtered.length} of {assignments.length} assignments
          </div>
        )}
      </div>

      <EditAssignmentModal
        assignment={editingAssignment}
        onClose={() => setEditingAssignment(null)}
      />

      <CreateAssignmentModal
        isOpen={showCreate}
        onClose={() => setShowCreate(false)}
      />
    </PageWrapper>
  )
}

export default AssignmentsPage
