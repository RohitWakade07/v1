import { useParams, useNavigate } from 'react-router-dom'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'
import { useAssignment } from '@/hooks/useAssignments'
import { useSessions } from '@/hooks/useSessions'
import { createSession } from '@/api/sessions'
import { AssignmentDetailPanel } from '@/components/assignments/AssignmentDetailPanel'
import { useNotificationStore } from '@/store/notificationStore'

const AssignmentDetailPage = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const { data, isLoading } = useAssignment(id)
  const { data: sessions } = useSessions()
  const addNotification = useNotificationStore((state) => state.addNotification)

  if (isLoading) return <LoadingSpinner />
  if (!data) return null

  const hasActiveSession = (sessions ?? []).some(
    (session) =>
      session.assignment_id === data.id &&
      ['STARTED', 'IN_PROGRESS'].includes(session.status),
  )

  const handleStart = async () => {
    const session = await createSession(data.id)
    addNotification({
      type: 'success',
      title: 'Session created',
      message: 'Your evaluation session is ready to start.',
    })
    navigate(`/sessions/${session.id}`)
  }

  return (
    <PageWrapper>
      <PageHeader
        title="Assignment Details"
        description="Review instructions before you launch the evaluator."
        action={
          <button
            className="rounded-lg bg-accent-blue px-4 py-2 text-sm font-medium text-white"
            onClick={handleStart}
            disabled={hasActiveSession}
          >
            {hasActiveSession ? 'Session Active' : 'Start Evaluation'}
          </button>
        }
      />
      {hasActiveSession && (
        <div className="rounded-lg border border-status-warning/40 bg-status-warning/10 px-4 py-3 text-sm text-status-warning">
          You already have an active session for this assignment.
        </div>
      )}
      <AssignmentDetailPanel assignment={data} />
      <div className="rounded-xl border border-navy-800 bg-navy-900/50 p-5 text-sm text-text-secondary shadow-card">
        <p className="font-medium text-text-primary">Evaluator Download</p>
        <p className="mt-2">
          Evaluator binaries are distributed by your program. Check your course
          resources or contact your mentor to obtain the evaluator package.
        </p>
      </div>
    </PageWrapper>
  )
}

export default AssignmentDetailPage
