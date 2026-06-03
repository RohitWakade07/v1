import { useParams } from 'react-router-dom'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { SkeletonCard } from '@/components/shared/SkeletonCard'
import { useAssignment } from '@/hooks/useAssignments'
import { AssignmentDetailPanel } from '@/components/assignments/AssignmentDetailPanel'

const AssignmentDetailPage = () => {
  const { id } = useParams()
  const { data, isLoading } = useAssignment(id)

  if (isLoading) {
    return (
      <PageWrapper>
        <div className="space-y-4">
          <SkeletonCard showHeader={false} rows={2} />
          <SkeletonCard rows={4} />
        </div>
      </PageWrapper>
    )
  }

  if (!data) return null

  return (
    <PageWrapper>
      <PageHeader
        title={data.title}
        description="Review assignment details. Launch the evaluator CLI tool to start this assignment."
        backTo="/assignments"
        backLabel="All Assignments"
      />

      <AssignmentDetailPanel assignment={data} />
    </PageWrapper>
  )
}

export default AssignmentDetailPage
