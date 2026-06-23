import { useParams } from 'react-router-dom'
import { PageWrapper } from '@/components/shared/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { SkeletonCard } from '@/components/shared/SkeletonCard'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { useSubmission, useSubmissionResult, useSubmissionStatusSSE } from '@/hooks/student/useSubmissions'
import { useAssignment } from '@/hooks/student/useAssignments'
import { formatDate } from '@/lib/utils'
import { Activity, Terminal, AlertTriangle, CheckCircle2, Clock } from 'lucide-react'
import type { CheckResult } from '@/types/api'

export const SubmissionDetailPage = () => {
  const { id } = useParams<{ id: string }>()
  const { data: submission, isLoading: submissionLoading } = useSubmission(id)
  
  // Real-time status
  const liveStatus = useSubmissionStatusSSE(id)
  const currentStatus = liveStatus || submission?.status

  // Only fetch result if status is terminal
  const isTerminal = ['COMPLETED', 'FAILED', 'TIMEOUT', 'VALIDATION_ERROR'].includes(currentStatus || '')
  const { data: result } = useSubmissionResult(id, isTerminal)

  const { data: assignment } = useAssignment(submission?.assignment_id)

  if (submissionLoading) {
    return (
      <PageWrapper>
        <SkeletonCard rows={5} />
      </PageWrapper>
    )
  }

  if (!submission) return null

  let checks: CheckResult[] = []
  try {
    if (result?.checks_json) {
      checks = JSON.parse(result.checks_json)
    }
  } catch (e) {
    console.error('Failed to parse checks_json')
  }

  return (
    <PageWrapper>
      <PageHeader
        title={`Submission Details`}
        description={assignment ? `Attempt ${submission.attempt_number} for ${assignment.title}` : `Attempt ${submission.attempt_number}`}
        backTo={assignment ? `/student/assignments/${assignment.id}` : '/student/assignments'}
        backLabel="Back to Assignment"
      />

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main Content: Execution Logs and Checks (2/3 width) */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Checks / Rubric */}
          {isTerminal && result && checks.length > 0 && (
            <div className="card-dark p-5">
              <h3 className="font-display text-base font-semibold text-text-primary mb-4 flex items-center gap-2">
                <CheckCircle2 size={18} className="text-accent-teal" />
                Rubric Evaluation
              </h3>
              <div className="space-y-4">
                {checks.map((check, i) => (
                  <div key={i} className={`p-4 rounded-lg border ${check.passed ? 'border-accent-teal/30 bg-accent-teal/5' : 'border-status-danger/30 bg-status-danger/5'}`}>
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-semibold text-sm text-text-primary">{check.name}</h4>
                      <span className={`text-xs font-bold ${check.passed ? 'text-accent-teal' : 'text-status-danger'}`}>
                        {check.marks} / {check.max_marks} marks
                      </span>
                    </div>
                    <p className="text-sm text-text-secondary mb-2">{check.reason}</p>
                    {!check.passed && check.hint && (
                      <div className="text-xs text-status-warning bg-status-warning/10 p-2 rounded border border-status-warning/20">
                        <span className="font-semibold">Hint: </span>{check.hint}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Execution Logs */}
          {isTerminal && result && (
            <div className="card-dark p-5">
              <h3 className="font-display text-base font-semibold text-text-primary mb-4 flex items-center gap-2">
                <Terminal size={18} className="text-accent-blue" />
                Execution Output
              </h3>

              {result.grader_logs && (
                <div className="mb-4">
                  <h4 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">Grader Logs</h4>
                  <pre className="bg-navy-950 p-3 rounded-lg overflow-x-auto text-[11px] font-mono text-status-warning border border-navy-800">
                    {result.grader_logs}
                  </pre>
                </div>
              )}

              {result.stdout && (
                <div className="mb-4">
                  <h4 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">Standard Output</h4>
                  <pre className="bg-navy-950 p-3 rounded-lg overflow-x-auto text-[11px] font-mono text-text-primary border border-navy-800 whitespace-pre-wrap">
                    {result.stdout}
                  </pre>
                </div>
              )}

              {result.stderr && (
                <div>
                  <h4 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">Standard Error</h4>
                  <pre className="bg-navy-950 p-3 rounded-lg overflow-x-auto text-[11px] font-mono text-status-danger border border-navy-800 whitespace-pre-wrap">
                    {result.stderr}
                  </pre>
                </div>
              )}
              
              {!result.stdout && !result.stderr && !result.grader_logs && (
                <div className="text-sm text-text-muted italic">No execution output was captured.</div>
              )}
            </div>
          )}

          {!isTerminal && (
            <div className="card-dark p-10 flex flex-col items-center justify-center text-center">
              <Activity size={48} className="text-accent-blue animate-pulse mb-4" />
              <h3 className="text-lg font-semibold text-text-primary mb-2">Evaluating Submission</h3>
              <p className="text-sm text-text-secondary max-w-md">
                Your submission is currently being processed by the grader network. Please wait, this page will automatically update when complete.
              </p>
            </div>
          )}

        </div>

        {/* Sidebar: Metadata (1/3 width) */}
        <div className="lg:col-span-1 space-y-6">
          <div className="card-dark p-5">
            <h3 className="font-display text-base font-semibold text-text-primary mb-4">Metadata</h3>
            <div className="space-y-4 text-sm">
              <div className="flex justify-between items-center border-b border-navy-800 pb-2">
                <span className="text-text-secondary">Status</span>
                <StatusBadge status={currentStatus || ''} />
              </div>
              <div className="flex justify-between items-center border-b border-navy-800 pb-2">
                <span className="text-text-secondary">Submitted At</span>
                <span className="text-text-primary">{formatDate(submission.submitted_at)}</span>
              </div>
              <div className="flex justify-between items-center border-b border-navy-800 pb-2">
                <span className="text-text-secondary">Source Type</span>
                <span className="text-text-primary uppercase">{submission.source_type}</span>
              </div>
              
              {submission.source_type === 'github' && submission.repo_url && (
                <div className="flex justify-between items-center border-b border-navy-800 pb-2">
                  <span className="text-text-secondary">Repository</span>
                  <a href={submission.repo_url} target="_blank" rel="noreferrer" className="text-accent-blue hover:underline truncate max-w-[150px]">
                    {submission.repo_url.replace('https://github.com/', '')}
                  </a>
                </div>
              )}

              {isTerminal && result && (
                <>
                  <div className="flex justify-between items-center border-b border-navy-800 pb-2">
                    <span className="text-text-secondary">Exit Code</span>
                    <span className={`font-mono font-bold ${result.exit_code === 0 ? 'text-accent-teal' : 'text-status-danger'}`}>
                      {result.exit_code !== null ? result.exit_code : 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center border-b border-navy-800 pb-2">
                    <span className="text-text-secondary">Execution Time</span>
                    <span className="text-text-primary flex items-center gap-1">
                      <Clock size={14} className="text-text-muted" />
                      {result.execution_time_ms ? `${(result.execution_time_ms / 1000).toFixed(2)}s` : 'N/A'}
                    </span>
                  </div>
                  {result.timed_out && (
                    <div className="flex items-center gap-2 text-status-warning bg-status-warning/10 p-2 rounded">
                      <AlertTriangle size={16} />
                      <span className="text-xs font-semibold">Execution Timed Out</span>
                    </div>
                  )}
                  {result.oom_killed && (
                    <div className="flex items-center gap-2 text-status-danger bg-status-danger/10 p-2 rounded">
                      <AlertTriangle size={16} />
                      <span className="text-xs font-semibold">Out of Memory (OOM)</span>
                    </div>
                  )}
                  
                  {/* Final Score */}
                  {result.feedback && (
                     <div className="mt-4 p-4 rounded-lg border border-accent-blue/30 bg-accent-blue/5">
                        <p className="text-sm font-semibold text-accent-blue mb-1">Feedback</p>
                        <p className="text-xs text-text-primary">{result.feedback}</p>
                     </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>

      </div>
    </PageWrapper>
  )
}

export default SubmissionDetailPage
