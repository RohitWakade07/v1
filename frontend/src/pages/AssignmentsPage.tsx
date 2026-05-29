import { PageWrapper } from '@/components/layout/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { useAssignments } from '@/hooks/useAssignments'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'
import { EmptyState } from '@/components/shared/EmptyState'
import { AssignmentTable } from '@/components/assignments/AssignmentTable'

const AssignmentsPage = () => {
  const { data, isLoading } = useAssignments()

  if (isLoading) return <LoadingSpinner />

  const assignments = data ?? []

  return (
    <PageWrapper>
      <PageHeader
        title="Assignments"
        description="Browse and start published assignments."
      />
      {assignments.length === 0 ? (
        <EmptyState
          title="No assignments"
          message="Assignments will appear once they are published."
        />
      ) : (
        <AssignmentTable assignments={assignments} />
      )}
    </PageWrapper>
  )
}

export default AssignmentsPage
