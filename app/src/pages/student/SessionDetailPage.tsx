import { useParams, Link } from 'react-router-dom'
import { PageWrapper } from '@/components/shared/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { useSession } from '@/hooks/student/useSessions'
import { useAssignment } from '@/hooks/student/useAssignments'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { SessionTimeline } from '@/components/student/sessions/SessionTimeline'
import { SkeletonCard } from '@/components/shared/SkeletonCard'
import { formatDate, formatScore, truncateHash } from '@/lib/utils'
import { CheckCircle2, XCircle, FileCheck2 } from 'lucide-react'
import type { SessionStatus } from '@/types/api'

const SessionDetailPage = () => {
  const { id } = useParams()
  const { data, isLoading } = useSession(id)
  const { data: assignment } = useAssignment(data?.assignment_id)

  if (isLoading) {
    return (
      <PageWrapper>
        <div className="grid gap-5 lg:grid-cols-2">
          <SkeletonCard rows={5} />
          <SkeletonCard rows={5} />
        </div>
      </PageWrapper>
    )
  }

  if (!data) return null

  const activeStatuses: SessionStatus[] = ['CREATED', 'STARTED', 'CHALLENGE_ISSUED', 'RUNNING', 'IN_PROGRESS', 'PROOF_GENERATED']
  const canSubmit = activeStatuses.includes(data.status)

  return (
    <PageWrapper>
      <PageHeader
        title="Session Detail"
        description={assignment?.title ?? 'Evaluation session details and status.'}
        backTo="/student/sessions"
        backLabel="All Sessions"
        actions={
          canSubmit ? (
            <Link
              to={`/student/proof/submit?session_id=${data.id}`}
              className="btn-primary"
              aria-label="Submit proof for this session"
            >
              <FileCheck2 size={15} /> Submit Proof
            </Link>
          ) : undefined
        }
      />

      <div className="grid gap-5 lg:grid-cols-2">
        {/* Session info card */}
        <div className="card-dark p-5">
          <div className="flex items-center justify-between">
            <p className="text-xs font-medium uppercase tracking-wider text-text-secondary">
              Session ID
            </p>
            <StatusBadge status={data.status} />
          </div>
          <p className="mt-2 font-mono text-sm text-text-primary break-all">{data.id}</p>

          <div className="mt-5 space-y-4 text-sm">
            {assignment && (
              <div>
                <p className="text-xs text-text-secondary uppercase tracking-wide">Assignment</p>
                <Link
                  to={`/student/assignments/${data.assignment_id}`}
                  className="mt-0.5 font-medium text-accent-blue hover:text-accent-teal transition-colors"
                >
                  {assignment.title}
                </Link>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-text-secondary uppercase tracking-wide">Started</p>
                <p className="mt-0.5 text-text-primary">{formatDate(data.started_at)}</p>
              </div>
              <div>
                <p className="text-xs text-text-secondary uppercase tracking-wide">Completed</p>
                <p className="mt-0.5 text-text-primary">{formatDate(data.completed_at)}</p>
              </div>
            </div>

            {(data.final_score !== null && data.final_score !== undefined) && (
              <div className="rounded-lg border border-accent-teal/30 bg-accent-teal/10 px-4 py-3">
                <p className="text-xs text-text-secondary">Final Score</p>
                <p className="mt-1 font-display text-2xl font-bold text-accent-teal">
                  {formatScore(data.final_score, null)}
                </p>
              </div>
            )}

            {data.proof_nonce && (data.status === 'COMPLETED' || data.status === 'VERIFIED') && (
              <div>
                <p className="text-xs text-text-secondary uppercase tracking-wide">Proof Nonce</p>
                <p className="mt-0.5 font-mono text-xs text-text-primary break-all">
                  {truncateHash(data.proof_nonce)}
                </p>
              </div>
            )}

            {/* Status-specific messaging */}
            {(data.status === 'COMPLETED' || data.status === 'VERIFIED') && (
              <div className="flex items-start gap-3 rounded-lg border border-accent-teal/30 bg-accent-teal/10 px-4 py-3">
                <CheckCircle2 size={16} className="mt-0.5 shrink-0 text-accent-teal" />
                <p className="text-sm text-accent-teal">
                  Your proof was verified successfully. Results are now available.
                </p>
              </div>
            )}

            {(data.status === 'REJECTED' || data.status === 'FAILED') && (
              <div className="flex items-start gap-3 rounded-lg border border-status-danger/30 bg-status-danger/10 px-4 py-3">
                <XCircle size={16} className="mt-0.5 shrink-0 text-status-danger" />
                <div>
                  <p className="text-sm font-medium text-status-danger">Verification Failed</p>
                  {data.rejection_reason && (
                    <p className="mt-1 text-xs text-status-danger/80">{data.rejection_reason}</p>
                  )}
                </div>
              </div>
            )}

            {data.status === 'ABORTED' && (
              <div className="flex items-start gap-3 rounded-lg border border-navy-700/30 bg-navy-950 px-4 py-3">
                <XCircle size={16} className="mt-0.5 shrink-0 text-text-secondary" />
                <div>
                  <p className="text-sm font-medium text-text-secondary">Session Aborted</p>
                  <p className="mt-1 text-xs text-text-secondary">
                    This evaluation session was aborted by the student and is now terminated. No proof can be submitted.
                  </p>
                </div>
              </div>
            )}

            {canSubmit && (
              <div className="flex flex-col gap-3">
                <div className="rounded-lg border border-accent-blue/30 bg-accent-blue/10 px-4 py-3">
                  <p className="text-sm text-accent-blue">
                    This session is active. Run the evaluator CLI on your machine to start/continue the challenge, and submit the generated proof package here when complete.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Timeline */}
        <SessionTimeline session={data} />
      </div>

      {/* Score breakdown */}
      {data.score_breakdown && (
        <div className="mt-5 overflow-hidden rounded-xl border border-navy-800">
          <div className="bg-navy-900/80 px-4 py-3">
            <p className="text-sm font-semibold text-text-primary">Score Breakdown</p>
          </div>
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-t border-navy-800 bg-navy-950">
                <th className="px-4 py-2 text-left text-xs text-text-secondary">Test</th>
                <th className="px-4 py-2 text-left text-xs text-text-secondary">Status</th>
                <th className="px-4 py-2 text-left text-xs text-text-secondary">Score</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(data.score_breakdown as Record<string, { passed: boolean; score: number }>).map(([testId, result], i) => (
                <tr key={testId} className={`border-t border-navy-800 ${i % 2 === 0 ? 'bg-navy-950' : 'bg-navy-900/30'}`}>
                  <td className="px-4 py-2 font-mono text-xs text-text-primary">{testId}</td>
                  <td className="px-4 py-2">
                    {result.passed ? (
                      <span className="inline-flex items-center gap-1 text-xs text-accent-teal">
                        <CheckCircle2 size={12} /> Passed
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-xs text-status-danger">
                        <XCircle size={12} /> Failed
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-2 text-xs text-text-primary">{result.score.toFixed(1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </PageWrapper>
  )
}

export default SessionDetailPage
