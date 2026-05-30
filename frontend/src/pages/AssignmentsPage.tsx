import { useState } from 'react'
import { GraduationCap, LayoutGrid, List } from 'lucide-react'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { useAssignments } from '@/hooks/useAssignments'
import { EmptyState } from '@/components/shared/EmptyState'
import { AssignmentTable } from '@/components/assignments/AssignmentTable'
import { AssignmentCard } from '@/components/assignments/AssignmentCard'
import { SkeletonCard } from '@/components/shared/SkeletonCard'

const AssignmentsPage = () => {
  const { data, isLoading } = useAssignments()
  const [view, setView] = useState<'grid' | 'table'>('grid')

  const assignments = data ?? []

  return (
    <PageWrapper>
      <PageHeader
        title="Assignments"
        description="Browse and start published assignments."
        action={
          <div className="flex items-center gap-1 rounded-lg border border-navy-800 bg-navy-900 p-1">
            <button
              aria-label="Grid view"
              onClick={() => setView('grid')}
              className={`rounded p-1.5 transition-colors ${view === 'grid' ? 'bg-accent-blue/20 text-accent-blue' : 'text-text-secondary hover:text-text-primary'}`}
            >
              <LayoutGrid size={15} />
            </button>
            <button
              aria-label="Table view"
              onClick={() => setView('table')}
              className={`rounded p-1.5 transition-colors ${view === 'table' ? 'bg-accent-blue/20 text-accent-blue' : 'text-text-secondary hover:text-text-primary'}`}
            >
              <List size={15} />
            </button>
          </div>
        }
      />

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : assignments.length === 0 ? (
        <EmptyState
          icon={<GraduationCap size={28} />}
          title="No assignments published"
          message="Assignments will appear here once they are published by your program administrators."
        />
      ) : view === 'grid' ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {assignments.map((a) => <AssignmentCard key={a.id} assignment={a} />)}
        </div>
      ) : (
        <AssignmentTable assignments={assignments} />
      )}
    </PageWrapper>
  )
}

export default AssignmentsPage
