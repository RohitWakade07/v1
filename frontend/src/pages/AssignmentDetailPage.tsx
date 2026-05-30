import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Loader2, FlaskConical } from 'lucide-react'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { SkeletonCard } from '@/components/shared/SkeletonCard'
import { useAssignment } from '@/hooks/useAssignments'
import { useSessions } from '@/hooks/useSessions'
import { createSession } from '@/api/sessions'
import { AssignmentDetailPanel } from '@/components/assignments/AssignmentDetailPanel'
import { ConfirmDialog } from '@/components/shared/ConfirmDialog'
import { useNotificationStore } from '@/store/notificationStore'

const AssignmentDetailPage = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const { data, isLoading } = useAssignment(id)
  const { data: sessions } = useSessions()
  const addNotification = useNotificationStore((s) => s.addNotification)
  const [showConfirm, setShowConfirm] = useState(false)
  const [starting, setStarting] = useState(false)

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

  const hasActiveSession = (sessions ?? []).some(
    (s) => s.assignment_id === data.id && ['STARTED', 'IN_PROGRESS'].includes(s.status),
  )

  const handleConfirmStart = async () => {
    setShowConfirm(false)
    setStarting(true)
    try {
      const session = await createSession(data.id)
      addNotification({
        type: 'success',
        title: 'Session created',
        message: 'Your evaluation session has started. Download and run the evaluator.',
      })
      navigate(`/sessions/${session.id}`)
    } catch {
      addNotification({
        type: 'error',
        title: 'Failed to start session',
        message: 'Please try again.',
      })
    } finally {
      setStarting(false)
    }
  }

  return (
    <PageWrapper>
      <PageHeader
        title={data.title}
        description="Review assignment details before launching the evaluator."
        backTo="/assignments"
        backLabel="All Assignments"
        action={
          <button
            className="btn-primary"
            onClick={() => setShowConfirm(true)}
            disabled={hasActiveSession || starting}
            aria-label={hasActiveSession ? 'Session already active for this assignment' : 'Start evaluation session'}
          >
            {starting ? (
              <><Loader2 size={15} className="animate-spin" /> Starting…</>
            ) : hasActiveSession ? (
              'Session Active'
            ) : (
              <><FlaskConical size={15} /> Start Evaluation</>
            )}
          </button>
        }
      />

      {hasActiveSession && (
        <div className="mb-5 rounded-lg border border-status-warning/40 bg-status-warning/10 px-4 py-3 text-sm text-status-warning">
          ⚠ You already have an active session for this assignment. Submit your current proof before starting a new one.
        </div>
      )}

      <AssignmentDetailPanel assignment={data} />

      <ConfirmDialog
        open={showConfirm}
        title="Start Evaluation?"
        message={`This will open a new grading session for "${data.title}". Run the evaluator binary and submit the generated proof.json.`}
        confirmLabel="Start Session"
        cancelLabel="Cancel"
        icon={<FlaskConical size={20} />}
        onConfirm={handleConfirmStart}
        onCancel={() => setShowConfirm(false)}
      />
    </PageWrapper>
  )
}

export default AssignmentDetailPage
