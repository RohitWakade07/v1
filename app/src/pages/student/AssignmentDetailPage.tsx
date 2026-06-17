import { useParams, Link } from 'react-router-dom'
import { PageWrapper } from '@/components/shared/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { SkeletonCard } from '@/components/shared/SkeletonCard'
import { useAssignment } from '@/hooks/student/useAssignments'
import { AssignmentDetailPanel } from '@/components/student/assignments/AssignmentDetailPanel'
import { useSubmissions, useSubmitAssignment } from '@/hooks/student/useSubmissions'
import { SubmissionForm } from '@/components/student/submissions/SubmissionForm'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { formatDate } from '@/lib/utils'
import { Activity, UploadCloud, ChevronRight, PenTool } from 'lucide-react'
import type { SubmissionSourceType } from '@/types/api'

const AssignmentDetailPage = () => {
  const { id } = useParams<{ id: string }>()
  const { data: assignment, isLoading: assignmentLoading } = useAssignment(id)
  const { data: allSubmissions, isLoading: submissionsLoading } = useSubmissions({
    refetchInterval: 5000,
  })

  const submitAssignmentMutation = useSubmitAssignment()

  const assignmentSubmissions = (allSubmissions ?? []).filter(
    (s) => s.assignment_id?.toLowerCase() === id?.toLowerCase()
  )

  const handleSubmission = (sourceType: SubmissionSourceType, repoUrl?: string, file?: File) => {
    if (!id) return
    submitAssignmentMutation.mutate({
      assignmentId: id,
      sourceType,
      repoUrl,
      file,
    })
  }

  if (assignmentLoading) {
    return (
      <PageWrapper>
        <div className="space-y-4">
          <SkeletonCard showHeader={false} rows={2} />
          <SkeletonCard rows={4} />
        </div>
      </PageWrapper>
    )
  }

  if (!assignment) return null

  return (
    <PageWrapper>
      <PageHeader
        title={assignment.title}
        description="Review assignment details and submit your work for automated evaluation."
        backTo="/student/assignments"
        backLabel="All Assignments"
      />

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left column: details (2/3 width) */}
        <div className="lg:col-span-2 space-y-6">
          <AssignmentDetailPanel assignment={assignment} />
        </div>

        {/* Right column: submission and history (1/3 width) */}
        <div className="lg:col-span-1 space-y-6">

          {/* Quiz Section */}
          <div className="card-dark p-5">
            <h3 className="font-display text-base font-semibold text-text-primary flex items-center gap-2 mb-2">
              <PenTool size={18} className="text-purple-400" />
              Weekly Quiz
            </h3>
            <p className="text-sm text-text-secondary mb-4">
              Unlock the quiz by submitting your weekly assignment first.
            </p>
            <Link
              to={`/student/assignments/${id}/quiz`}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-navy-800 px-4 py-2.5 text-sm font-medium text-text-primary hover:bg-navy-700 transition-colors"
            >
              Take Quiz
            </Link>
          </div>

          {/* New Submission */}
          <div className="card-dark p-5">
            <h3 className="font-display text-base font-semibold text-text-primary flex items-center gap-2 mb-4">
              <UploadCloud size={18} className="text-accent-teal" />
              New Submission
            </h3>

            <SubmissionForm
              onSubmit={handleSubmission}
              isSubmitting={submitAssignmentMutation.isPending}
              maxFileSizeMB={5}
            />
          </div>

          {/* Submission History */}
          <div className="card-dark p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-display text-base font-semibold text-text-primary flex items-center gap-2">
                <Activity size={18} className="text-accent-blue" />
                History
              </h3>
            </div>

            {submissionsLoading ? (
              <div className="animate-pulse space-y-3">
                <div className="h-10 bg-navy-900 rounded" />
                <div className="h-10 bg-navy-900 rounded" />
              </div>
            ) : assignmentSubmissions.length === 0 ? (
              <div className="text-center py-6 border border-dashed border-navy-800 rounded-lg bg-navy-950/40">
                <p className="text-sm text-text-secondary">No submissions yet.</p>
                <p className="text-xs text-text-muted mt-1">Submit your repository or ZIP above.</p>
              </div>
            ) : (
              <div className="space-y-2.5 max-h-[400px] overflow-y-auto pr-1">
                {assignmentSubmissions.map((submission) => (
                  <Link
                    key={submission.id}
                    to={`/student/submissions/${submission.id}`}
                    className="block p-3 rounded-lg border border-navy-800 bg-navy-950/40 hover:border-navy-600 hover:bg-navy-900/40 transition-colors group"
                  >
                    <div className="flex items-center justify-between">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs text-text-primary font-bold">
                            Attempt {submission.attempt_number}
                          </span>
                          <StatusBadge status={submission.status} className="scale-75 origin-left" />
                        </div>
                        <p className="text-[10px] text-text-muted mt-1">
                          {formatDate(submission.submitted_at)} • {submission.source_type.toUpperCase()}
                        </p>
                      </div>
                      <ChevronRight size={16} className="text-text-muted group-hover:text-accent-blue transition-colors" />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>

        </div>
      </div>
    </PageWrapper>
  )
}

export default AssignmentDetailPage
