import { useState } from 'react'
import { GraduationCap, Copy, Check, Plus, Loader2, Users, CheckCircle2, XCircle, AlertCircle } from 'lucide-react'
import { PageWrapper } from '@/components/shared/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { DataTable } from '@/components/shared/DataTable'
import {
  useClassrooms,
  useClassroomEnrollments,
  useCreateClassroom,
  useApproveEnrollment,
  useRejectEnrollment,
} from '@/hooks/mentor/useMentor'
import { useNotificationStore } from '@/store/notificationStore'
import { formatDate } from '@/lib/utils'

export const ClassroomsPage = () => {
  const addNotification = useNotificationStore((s) => s.addNotification)

  const { data: classrooms, isLoading: isClassroomsLoading } = useClassrooms()
  const [selectedClassroomId, setSelectedClassroomId] = useState<string | null>(null)
  const [newClassName, setNewClassName] = useState('')
  const [copiedCode, setCopiedCode] = useState<string | null>(null)

  const { data: enrollments, isLoading: isEnrollmentsLoading } = useClassroomEnrollments(selectedClassroomId)
  const createClassroomMutation = useCreateClassroom()
  const approveEnrollmentMutation = useApproveEnrollment()
  const rejectEnrollmentMutation = useRejectEnrollment()

  const handleCreateClassroom = async (e: React.FormEvent) => {
    e.preventDefault()
    const nameClean = newClassName.trim()
    if (!nameClean) return

    try {
      await createClassroomMutation.mutateAsync(nameClean)
      setNewClassName('')
      addNotification({
        type: 'success',
        title: 'Classroom created!',
        message: `Classroom '${nameClean}' has been created successfully.`,
      })
    } catch {
      addNotification({
        type: 'error',
        title: 'Failed to create',
        message: 'Could not create classroom. Please try again.',
      })
    }
  }

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code)
    setCopiedCode(code)
    addNotification({
      type: 'success',
      title: 'Class code copied!',
      message: `${code} copied to clipboard.`,
    })
    setTimeout(() => setCopiedCode(null), 2000)
  }

  const handleApprove = async (enrollmentId: string, studentName: string) => {
    try {
      await approveEnrollmentMutation.mutateAsync(enrollmentId)
      addNotification({
        type: 'success',
        title: 'Student approved!',
        message: `${studentName} is now authorized to enter the classroom.`,
      })
    } catch {
      addNotification({
        type: 'error',
        title: 'Approval failed',
        message: 'Failed to approve student. Try again.',
      })
    }
  }

  const handleReject = async (enrollmentId: string, studentName: string) => {
    try {
      await rejectEnrollmentMutation.mutateAsync(enrollmentId)
      addNotification({
        type: 'warning',
        title: 'Student rejected!',
        message: `Classroom access denied for ${studentName}.`,
      })
    } catch {
      addNotification({
        type: 'error',
        title: 'Rejection failed',
        message: 'Failed to reject student. Try again.',
      })
    }
  }

  const enrollmentHeaders = ['Roll Number', 'Student Name', 'Email', 'Joined', 'Status', 'Actions']

  const enrollmentRows = (enrollments ?? []).map((e) => {
    const isPending = e.status === 'PENDING'
    const isApproved = e.status === 'APPROVED'
    const isRejected = e.status === 'REJECTED'

    let statusBadge = (
      <span className="inline-flex items-center gap-1 rounded-full bg-status-warning/15 px-2.5 py-0.5 text-xs font-semibold text-status-warning border border-status-warning/30">
        <AlertCircle size={10} /> Pending
      </span>
    )
    if (isApproved) {
      statusBadge = (
        <span className="inline-flex items-center gap-1 rounded-full bg-accent-teal/15 px-2.5 py-0.5 text-xs font-semibold text-accent-teal border border-accent-teal/30">
          <CheckCircle2 size={10} /> Approved
        </span>
      )
    } else if (isRejected) {
      statusBadge = (
        <span className="inline-flex items-center gap-1 rounded-full bg-status-danger/15 px-2.5 py-0.5 text-xs font-semibold text-status-danger border border-status-danger/30">
          <XCircle size={10} /> Rejected
        </span>
      )
    }

    const actionButtons = isPending ? (
      <div className="flex gap-2">
        <button
          onClick={() => handleApprove(e.enrollment_id, e.student_name)}
          disabled={approveEnrollmentMutation.isPending}
          className="rounded-lg bg-accent-teal/15 px-3 py-1 text-xs font-bold text-accent-teal border border-accent-teal/30 hover:bg-accent-teal/25 transition-colors"
        >
          Approve
        </button>
        <button
          onClick={() => handleReject(e.enrollment_id, e.student_name)}
          disabled={rejectEnrollmentMutation.isPending}
          className="rounded-lg bg-status-danger/15 px-3 py-1 text-xs font-bold text-status-danger border border-status-danger/30 hover:bg-status-danger/25 transition-colors"
        >
          Reject
        </button>
      </div>
    ) : (
      <span className="text-xs text-text-secondary italic">No actions needed</span>
    )

    return [
      <span key="roll" className="font-mono text-xs text-text-primary">{e.student_roll}</span>,
      <span key="name" className="font-semibold text-text-primary">{e.student_name}</span>,
      <span key="email" className="text-xs text-text-secondary">{e.student_email}</span>,
      <span key="joined" className="text-xs text-text-secondary">{formatDate(e.joined_at)}</span>,
      statusBadge,
      actionButtons,
    ]
  })

  const selectedClassroomName = classrooms?.find((c) => c.id === selectedClassroomId)?.name

  return (
    <PageWrapper>
      <PageHeader
        title="Classrooms"
        description="Generate class code tokens and approve student access into your classrooms."
      />

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column: Classroom Creation & List */}
        <div className="space-y-6 lg:col-span-1">
          {/* Create Classroom Card */}
          <div className="card-dark p-5">
            <h3 className="mb-4 flex items-center gap-2 font-display text-base font-bold text-text-primary">
              <Plus size={16} className="text-accent-blue" />
              Create Classroom
            </h3>
            <form onSubmit={handleCreateClassroom} className="space-y-3">
              <div>
                <input
                  type="text"
                  required
                  placeholder="e.g. Computer Networks - Div A"
                  className="input-dark w-full"
                  value={newClassName}
                  onChange={(e) => setNewClassName(e.target.value)}
                />
              </div>
              <button
                type="submit"
                disabled={createClassroomMutation.isPending || !newClassName.trim()}
                className="btn-primary w-full justify-center text-sm font-semibold"
              >
                {createClassroomMutation.isPending ? (
                  <><Loader2 size={14} className="animate-spin" /> Creating…</>
                ) : (
                  'Create Classroom'
                )}
              </button>
            </form>
          </div>

          {/* Classrooms List */}
          <div className="card-dark p-5">
            <h3 className="mb-4 font-display text-base font-bold text-text-primary">
              Your Classrooms
            </h3>

            {isClassroomsLoading ? (
              <div className="animate-pulse space-y-3">
                <div className="h-14 rounded-lg bg-navy-900" />
                <div className="h-14 rounded-lg bg-navy-900" />
              </div>
            ) : !classrooms || classrooms.length === 0 ? (
              <div className="py-6 text-center text-sm text-text-secondary">
                No classrooms created yet. Create one above to get started.
              </div>
            ) : (
              <div className="space-y-2.5">
                {classrooms.map((c) => {
                  const isSelected = c.id === selectedClassroomId
                  return (
                    <div
                      key={c.id}
                      onClick={() => setSelectedClassroomId(c.id)}
                      className={`group flex cursor-pointer flex-col gap-1.5 rounded-xl border p-4 transition-all duration-200 ${
                        isSelected
                          ? 'border-accent-blue bg-navy-900/80 shadow-md'
                          : 'border-navy-800 bg-navy-950 hover:border-navy-700 hover:bg-navy-900/40'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <span className="font-semibold text-sm text-text-primary group-hover:text-accent-blue transition-colors">
                          {c.name}
                        </span>
                      </div>
                      <div className="flex items-center justify-between mt-1 rounded bg-navy-950 px-2.5 py-1.5 border border-navy-800">
                        <span className="font-mono text-xs font-bold text-accent-teal tracking-wider">{c.class_code}</span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleCopyCode(c.class_code)
                          }}
                          className="text-text-secondary hover:text-text-primary transition-colors"
                          aria-label="Copy class code"
                        >
                          {copiedCode === c.class_code ? <Check size={14} className="text-accent-teal" /> : <Copy size={14} />}
                        </button>
                      </div>
                      <span className="text-[10px] text-text-secondary/70 self-end mt-1">
                        Created {formatDate(c.created_at)}
                      </span>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Enrollment Approval Queue */}
        <div className="lg:col-span-2">
          <div className="card-dark p-5 min-h-[400px] flex flex-col">
            <h3 className="mb-4 flex items-center gap-2 font-display text-base font-bold text-text-primary">
              <Users size={16} className="text-accent-blue" />
              Student Verification Queue
            </h3>

            {!selectedClassroomId ? (
              <div className="flex flex-1 flex-col items-center justify-center text-center p-8 border-2 border-dashed border-navy-800 rounded-xl">
                <GraduationCap size={48} className="text-text-secondary/40 mb-3" />
                <p className="font-semibold text-text-primary text-sm">No classroom selected</p>
                <p className="text-xs text-text-secondary max-w-xs mt-1 leading-normal">
                  Select a classroom from the left side panel to manage student enrollment approvals and verify credentials.
                </p>
              </div>
            ) : (
              <div className="flex-1 flex flex-col">
                <div className="mb-4 flex items-center justify-between border-b border-navy-800 pb-3">
                  <div>
                    <h4 className="font-semibold text-sm text-text-primary">{selectedClassroomName}</h4>
                    <p className="text-xs text-text-secondary mt-0.5">Manage students requesting entry.</p>
                  </div>
                </div>

                {isEnrollmentsLoading ? (
                  <div className="animate-pulse space-y-4 py-8">
                    <div className="h-10 rounded bg-navy-900" />
                    <div className="h-10 rounded bg-navy-900" />
                  </div>
                ) : !enrollments || enrollments.length === 0 ? (
                  <div className="flex flex-1 flex-col items-center justify-center text-center py-12">
                    <Users size={32} className="text-text-secondary/40 mb-2" />
                    <p className="font-semibold text-sm text-text-primary">Empty Queue</p>
                    <p className="text-xs text-text-secondary mt-1 max-w-xs leading-normal">
                      No students have requested to join this classroom yet. Share the class code with your students to begin.
                    </p>
                  </div>
                ) : (
                  <div className="flex-1">
                    <DataTable headers={enrollmentHeaders} rows={enrollmentRows} />
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </PageWrapper>
  )
}

export default ClassroomsPage
