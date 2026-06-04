import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Globe, Lock, Pencil, Send, Copy, Calendar, Award, Tag, Clock } from 'lucide-react'
import { PageWrapper } from '@/components/shared/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { SkeletonCard } from '@/components/shared/SkeletonCard'
import { useAssignment } from '@/hooks/mentor/useAssignments'
import { usePublishAssignment, useUnpublishAssignment } from '@/hooks/mentor/usePublishAssignment'
import { formatDate } from '@/lib/utils'

export const AssignmentDetailPage = () => {
  const { id } = useParams<{ id: string }>()
  const { data: assignment, isLoading } = useAssignment(id)
  const publishMutation = usePublishAssignment()
  const unpublishMutation = useUnpublishAssignment()

  if (isLoading) {
    return (
      <PageWrapper>
        <div className="animate-pulse space-y-6">
          <div className="h-12 w-1/3 rounded-lg bg-navy-900" />
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2"><SkeletonCard /></div>
            <div className="lg:col-span-1"><SkeletonCard /></div>
          </div>
        </div>
      </PageWrapper>
    )
  }

  if (!assignment) {
    return (
      <PageWrapper>
        <PageHeader title="Assignment Not Found" />
        <div className="card-dark p-8 text-center text-text-secondary">
          <p>The assignment you are looking for does not exist or you don't have permission to view it.</p>
          <Link to="/assignments" className="btn-primary mt-4 mx-auto w-fit">
            <ArrowLeft size={16} /> Back to Assignments
          </Link>
        </div>
      </PageWrapper>
    )
  }

  return (
    <PageWrapper>
      <PageHeader
        title={assignment.title}
        description={`Manage details and publishing status for this assignment.`}
        backTo="/assignments"
        backLabel="Back to Assignments"
        actions={
          assignment.is_published ? (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-accent-teal/20 bg-accent-teal/10 px-3 py-1.5 text-sm font-semibold text-accent-teal">
              <Globe size={16} /> Published
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-status-warning/20 bg-status-warning/10 px-3 py-1.5 text-sm font-semibold text-status-warning">
              <Lock size={16} /> Draft
            </span>
          )
        }
      />

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column: Metadata */}
        <div className="lg:col-span-2 space-y-6">
          <div className="card-dark p-6">
            <h3 className="mb-4 font-display text-lg font-semibold text-text-primary">Overview</h3>
            <div className="grid gap-6 sm:grid-cols-2">
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-text-secondary flex items-center gap-1">
                  <Tag size={14} /> Slug
                </p>
                <p className="mt-1 font-mono text-sm text-text-primary bg-navy-950 p-2 rounded-md border border-navy-800">
                  {assignment.slug}
                </p>
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-text-secondary flex items-center gap-1">
                  <BookOpenIcon size={14} /> Category
                </p>
                <p className="mt-1 text-sm text-text-primary capitalize bg-navy-950 p-2 rounded-md border border-navy-800 inline-block">
                  {assignment.category.replace('_', ' ')}
                </p>
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-text-secondary flex items-center gap-1">
                  <Award size={14} /> Max Score
                </p>
                <p className="mt-1 text-2xl font-bold text-accent-blue">
                  {assignment.max_score}
                </p>
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-text-secondary flex items-center gap-1">
                  <Calendar size={14} /> Deadline
                </p>
                <p className={`mt-1 font-medium ${assignment.deadline ? 'text-text-primary' : 'text-text-secondary'}`}>
                  {assignment.deadline ? formatDate(assignment.deadline) : 'No deadline set'}
                </p>
              </div>
            </div>
            
            <div className="mt-8 border-t border-navy-800 pt-6">
              <p className="mb-2 text-xs font-medium uppercase tracking-wider text-text-secondary">
                Description
              </p>
              <div className="prose prose-invert max-w-none text-sm text-text-primary whitespace-pre-wrap">
                {assignment.description || <span className="italic text-text-secondary">No description provided.</span>}
              </div>
            </div>
          </div>
          
          <div className="card-dark p-6">
            <h3 className="mb-4 font-display text-lg font-semibold text-text-primary">System Information</h3>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <p className="text-xs text-text-secondary flex items-center gap-1"><Clock size={12} /> Created At</p>
                <p className="text-sm font-medium text-text-primary">{formatDate(assignment.created_at)}</p>
              </div>
              <div>
                <p className="text-xs text-text-secondary flex items-center gap-1"><Clock size={12} /> Last Updated</p>
                <p className="text-sm font-medium text-text-primary">{formatDate(assignment.updated_at || assignment.created_at)}</p>
              </div>
              <div className="sm:col-span-2">
                <p className="text-xs text-text-secondary flex items-center gap-1">Created By</p>
                <p className="text-sm font-mono text-text-primary">{assignment.created_by_id}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Actions */}
        <div className="lg:col-span-1 space-y-6">
          <div className="card-dark p-6 sticky top-6">
            <h3 className="mb-4 font-display text-lg font-semibold text-text-primary">Actions</h3>
            
            <div className="space-y-3">
              {!assignment.is_published ? (
                <button
                  onClick={() => publishMutation.mutate(assignment.id)}
                  disabled={publishMutation.isPending}
                  className="btn-primary w-full justify-center bg-accent-teal hover:bg-[#159e82]"
                >
                  <Send size={16} /> {publishMutation.isPending ? 'Publishing...' : 'Publish Assignment'}
                </button>
              ) : (
                <div className="space-y-3">
                  <div className="rounded-lg border border-accent-teal/20 bg-accent-teal/5 p-4 text-center">
                    <Globe size={24} className="mx-auto mb-2 text-accent-teal" />
                    <p className="text-sm font-medium text-accent-teal">This assignment is live.</p>
                    <p className="mt-1 text-xs text-text-secondary">Students can view and submit proofs for this assignment.</p>
                  </div>
                  <button
                    onClick={() => unpublishMutation.mutate(assignment.id)}
                    disabled={unpublishMutation.isPending}
                    className="btn-secondary w-full justify-center text-status-warning hover:bg-status-warning/10 hover:text-status-warning hover:border-status-warning/20"
                  >
                    <Lock size={16} /> {unpublishMutation.isPending ? 'Unpublishing...' : 'Unpublish Assignment'}
                  </button>
                </div>
              )}

              <div className="my-4 border-b border-navy-800" />

              <button
                disabled
                title="Coming in Phase 2"
                className="btn-secondary w-full justify-start cursor-not-allowed opacity-50"
              >
                <Pencil size={16} /> Edit Assignment <Lock size={12} className="ml-auto" />
              </button>
              
              <button
                disabled
                title="Coming in Phase 2"
                className="btn-secondary w-full justify-start cursor-not-allowed opacity-50"
              >
                <Copy size={16} /> Clone Assignment <Lock size={12} className="ml-auto" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </PageWrapper>
  )
}

function BookOpenIcon({ size }: { size: number }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
      <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
    </svg>
  )
}

export default AssignmentDetailPage
