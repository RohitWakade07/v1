import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { PageWrapper } from '@/components/shared/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { SkeletonCard } from '@/components/shared/SkeletonCard'
import { useAssignment } from '@/hooks/student/useAssignments'
import { AssignmentDetailPanel } from '@/components/student/assignments/AssignmentDetailPanel'
import { useSessions, useCreateSession } from '@/hooks/student/useSessions'
import { useProofSubmit, useEepProofSubmit } from '@/hooks/student/useProofSubmit'
import { ProofDropZone } from '@/components/student/proof/ProofDropZone'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { formatDate, formatScore } from '@/lib/utils'
import { Play, FileCheck2, Loader2, CheckCircle2, XCircle, Trophy, Activity } from 'lucide-react'
import { proofFileSchema } from '@/lib/schemas'
import { useNotificationStore } from '@/store/notificationStore'
import type { ProofSubmitRequest } from '@/types/api'

type SubmitStatus = 'idle' | 'uploading' | 'success' | 'error'

const AssignmentDetailPage = () => {
  const { id } = useParams<{ id: string }>()
  const { data: assignment, isLoading: assignmentLoading } = useAssignment(id)
  const { data: allSessions, isLoading: sessionsLoading } = useSessions({
    refetchInterval: 3000,
  })
  const createSessionMutation = useCreateSession()
  const proofSubmit = useProofSubmit()
  const eepProofSubmit = useEepProofSubmit()
  const addNotification = useNotificationStore((s) => s.addNotification)

  const [fileName, setFileName] = useState('')
  const [fileSize, setFileSize] = useState<number | undefined>()
  const [isEepFile, setIsEepFile] = useState(false)
  const [eepFile, setEepFile] = useState<File | null>(null)
  const [eepSessionId, setEepSessionId] = useState('')
  const [parsedProof, setParsedProof] = useState<ProofSubmitRequest | null>(null)
  const [parseError, setParseError] = useState('')
  const [submitStatus, setSubmitStatus] = useState<SubmitStatus>('idle')
  const [submitMessage, setSubmitMessage] = useState('')
  const [submitScore, setSubmitScore] = useState<number | null>(null)

  const assignmentSessions = (allSessions ?? []).filter(
    (s) => s.assignment_id?.toLowerCase() === id?.toLowerCase()
  )

  const submittableSessions = assignmentSessions.filter((s) =>
    ['CREATED', 'CHALLENGE_ISSUED', 'RUNNING', 'PROOF_GENERATED', 'STARTED', 'IN_PROGRESS'].includes(s.status)
  )

  // Auto-select session if there is only one submittable session
  useEffect(() => {
    if (submittableSessions.length === 1) {
      const singleId = submittableSessions[0].id
      if (isEepFile) {
        if (eepSessionId !== singleId) setEepSessionId(singleId)
      } else if (parsedProof) {
        if (parsedProof.session_id !== singleId) {
          setParsedProof({ ...parsedProof, session_id: singleId })
        }
      }
    }
  }, [submittableSessions, isEepFile, eepSessionId, parsedProof])

  const handleStartSession = async () => {
    if (!id) return
    try {
      await createSessionMutation.mutateAsync(id)
      addNotification({
        type: 'success',
        title: 'Session created',
        message: 'A new grading session has been bootstrapped. Run the verifier CLI on your machine.',
      })
    } catch (err) {
      // Handled globally
    }
  }

  const handleFileSelected = (file: File, eep: boolean) => {
    setParseError('')
    setParsedProof(null)
    setEepFile(null)
    setIsEepFile(eep)
    setFileName(file.name)
    setFileSize(file.size)

    if (file.size > 5 * 1024 * 1024) {
      setParseError('File exceeds the 5 MB size limit.')
      return
    }

    if (eep) {
      setEepFile(file)
      return
    }

    const reader = new FileReader()
    reader.onload = () => {
      try {
        const json = JSON.parse(reader.result as string)
        const result = proofFileSchema.safeParse(json)
        if (!result.success) {
          const firstError = result.error.issues[0]
          const path = firstError.path.join('.')
          setParseError(`Invalid proof file structure: "${path}" - ${firstError.message}`)
          return
        }
        setParsedProof(result.data as ProofSubmitRequest)
      } catch {
        setParseError('Unable to parse JSON. Ensure the file is valid JSON.')
      }
    }
    reader.readAsText(file)
  }

  const handleSubmit = async () => {
    setSubmitStatus('uploading')
    setSubmitMessage('Submitting proof to the verification backend…')
    setSubmitScore(null)

    const targetSessionId = isEepFile ? eepSessionId : parsedProof?.session_id

    if (!targetSessionId) {
      setSubmitStatus('error')
      setSubmitMessage('Please select a grading session before submitting.')
      return
    }

    try {
      if (isEepFile && eepFile) {
        const response = await eepProofSubmit.mutateAsync({
          sessionId: targetSessionId,
          file: eepFile,
        })
        applySubmitResult(response.status, response.message, response.final_score)
        return
      }

      if (!parsedProof) return
      const response = await proofSubmit.mutateAsync({
        ...parsedProof,
        session_id: targetSessionId,
      })
      applySubmitResult(response.status, response.message, response.final_score)
    } catch (error: unknown) {
      setSubmitStatus('error')
      const errMsg = extractErrorMessage(error)
      setSubmitMessage(errMsg)
    }
  }

  const applySubmitResult = (
    status: string,
    message: string,
    finalScore?: number | null,
  ) => {
    const isSuccess = status === 'VERIFIED' || status === 'COMPLETED'
    setSubmitStatus(isSuccess ? 'success' : 'error')
    setSubmitMessage(message)
    if (finalScore !== null && finalScore !== undefined) {
      setSubmitScore(finalScore)
    }
  }

  const canSubmit = isEepFile
    ? Boolean(eepFile && eepSessionId)
    : Boolean(parsedProof && parsedProof.session_id)

  const isPending = proofSubmit.isPending || eepProofSubmit.isPending

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
        description="Review assignment details, manage sessions, and submit evaluation proofs."
        backTo="/student/assignments"
        backLabel="All Assignments"
      />

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left column: details (2/3 width) */}
        <div className="lg:col-span-2 space-y-6">
          <AssignmentDetailPanel assignment={assignment} />
        </div>

        {/* Right column: sessions and submission (1/3 width) */}
        <div className="lg:col-span-1 space-y-6">
          {/* Card 1: Grading Sessions */}
          <div className="card-dark p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-display text-base font-semibold text-text-primary flex items-center gap-2">
                <Activity size={18} className="text-accent-blue animate-pulse" />
                Sessions
              </h3>
              <button
                onClick={handleStartSession}
                disabled={createSessionMutation.isPending}
                className="btn-primary py-1 px-3 text-xs flex items-center gap-1 bg-accent-blue hover:bg-[#1f75cb] text-white"
              >
                {createSessionMutation.isPending ? (
                  <Loader2 size={12} className="animate-spin" />
                ) : (
                  <Play size={12} />
                )}
                New Session
              </button>
            </div>

            {sessionsLoading ? (
              <div className="animate-pulse space-y-3">
                <div className="h-10 bg-navy-900 rounded" />
                <div className="h-10 bg-navy-900 rounded" />
              </div>
            ) : assignmentSessions.length === 0 ? (
              <div className="text-center py-6 border border-dashed border-navy-800 rounded-lg bg-navy-950/40">
                <p className="text-sm text-text-secondary">No sessions started yet.</p>
                <p className="text-xs text-text-muted mt-1">Click "New Session" to bootstrap one.</p>
              </div>
            ) : (
              <div className="space-y-2.5 max-h-[300px] overflow-y-auto pr-1">
                {assignmentSessions.map((session) => (
                  <div key={session.id} className="flex items-center justify-between p-3 rounded-lg border border-navy-800 bg-navy-950/40 hover:border-navy-700 transition-colors">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs text-text-primary font-bold">
                          {session.id.slice(0, 8)}…
                        </span>
                        <StatusBadge status={session.status} className="scale-75 origin-left" />
                      </div>
                      <p className="text-[10px] text-text-muted mt-1">
                        Started: {formatDate(session.started_at)}
                      </p>
                    </div>
                    <div className="flex items-center gap-2.5 shrink-0">
                      {session.final_score !== null && session.final_score !== undefined && (
                        <span className="text-xs font-semibold text-accent-teal font-display">
                          {formatScore(session.final_score, null)}
                        </span>
                      )}
                      <Link
                        to={`/student/sessions/${session.id}`}
                        className="text-xs text-accent-blue hover:text-accent-teal transition-colors"
                      >
                        Timeline →
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Card 2: Submit Proof */}
          <div className="card-dark p-5">
            <h3 className="font-display text-base font-semibold text-text-primary flex items-center gap-2 mb-4">
              <FileCheck2 size={18} className="text-accent-teal" />
              Submit Proof
            </h3>

            <div className="space-y-4">
              <ProofDropZone
                onFileSelected={handleFileSelected}
                fileName={fileName}
                isEepFile={isEepFile}
                fileSize={fileSize}
                hasError={Boolean(parseError)}
              />

              {parseError && (
                <div className="flex items-center gap-3 rounded-lg border border-status-danger/30 bg-status-danger/10 px-4 py-3 text-sm text-status-danger">
                  <XCircle size={16} className="shrink-0" />
                  {parseError}
                </div>
              )}

              {/* Session Selector */}
              {fileName && (
                <div className="space-y-2">
                  <label htmlFor="detail-session-select" className="block text-xs font-semibold text-text-secondary uppercase tracking-wider">
                    Verify against session
                  </label>
                  <select
                    id="detail-session-select"
                    className="input-dark w-full text-sm"
                    value={isEepFile ? eepSessionId : parsedProof?.session_id || ''}
                    onChange={(e) => {
                      if (isEepFile) {
                        setEepSessionId(e.target.value)
                      } else if (parsedProof) {
                        setParsedProof({ ...parsedProof, session_id: e.target.value })
                      }
                    }}
                  >
                    <option value="">Choose a session…</option>
                    {submittableSessions.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.id.slice(0, 8)}… ({s.status.replace('_', ' ')})
                      </option>
                    ))}
                  </select>
                  {submittableSessions.length === 0 && (
                    <p className="text-[10px] text-status-warning">
                      No active sessions found. Start a new session above first.
                    </p>
                  )}
                </div>
              )}

              <button
                className="btn-primary w-full justify-center"
                onClick={handleSubmit}
                disabled={!canSubmit || isPending}
              >
                {isPending ? (
                  <><Loader2 size={15} className="animate-spin mr-1.5" /> Verifying…</>
                ) : (
                  <><FileCheck2 size={15} className="mr-1.5" /> Submit & Verify Proof</>
                )}
              </button>

              {submitStatus !== 'idle' && (
                <div className={`rounded-xl border p-4 text-sm animate-fade-in ${
                  submitStatus === 'success'
                    ? 'border-accent-teal/30 bg-accent-teal/10 text-accent-teal'
                    : submitStatus === 'error'
                    ? 'border-status-danger/30 bg-status-danger/10 text-status-danger'
                    : 'border-accent-blue/30 bg-accent-blue/10 text-accent-blue'
                }`}>
                  <div className="flex items-start gap-2.5">
                    {submitStatus === 'success' ? (
                      <CheckCircle2 size={18} className="shrink-0 mt-0.5" />
                    ) : submitStatus === 'error' ? (
                      <XCircle size={18} className="shrink-0 mt-0.5" />
                    ) : (
                      <Loader2 size={18} className="shrink-0 mt-0.5 animate-spin" />
                    )}
                    <div>
                      <p className="font-semibold">
                        {submitStatus === 'success' ? 'Verification Success' : submitStatus === 'error' ? 'Verification Failed' : 'Processing…'}
                      </p>
                      <p className="mt-1 text-xs text-text-secondary">{submitMessage}</p>
                      {submitScore !== null && (
                        <p className="mt-1.5 font-display text-lg font-bold text-accent-teal">
                          Earned Score: {submitScore.toFixed(1)} / {assignment.max_score}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Card 3: Verified Results */}
          <div className="card-dark p-5">
            <h3 className="font-display text-base font-semibold text-text-primary flex items-center gap-2 mb-4">
              <Trophy size={18} className="text-accent-teal" />
              Verified Results
            </h3>

            {sessionsLoading ? (
              <div className="animate-pulse h-12 bg-navy-900 rounded" />
            ) : assignmentSessions.filter(s => ['VERIFIED', 'COMPLETED', 'FAILED', 'REJECTED'].includes(s.status)).length === 0 ? (
              <div className="text-center py-4 text-xs text-text-secondary">
                No verified results yet. Submit a proof package to grade this assignment.
              </div>
            ) : (
              <div className="space-y-3">
                {assignmentSessions
                  .filter(s => ['VERIFIED', 'COMPLETED', 'FAILED', 'REJECTED'].includes(s.status))
                  .map((session) => (
                    <div
                      key={session.id}
                      className={`p-3 rounded-lg border ${
                        ['VERIFIED', 'COMPLETED'].includes(session.status)
                          ? 'border-accent-teal/20 bg-navy-950/60'
                          : 'border-status-danger/20 bg-navy-950/60'
                      } flex items-center justify-between`}
                    >
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-semibold text-text-primary">
                          Session {session.id.slice(0, 8)}…
                        </p>
                        <p className="text-[10px] text-text-secondary mt-0.5">
                          Date: {formatDate(session.completed_at || session.submitted_at || session.started_at)}
                        </p>
                        {session.rejection_reason && (
                          <p className="text-[10px] text-status-danger truncate mt-1" title={session.rejection_reason}>
                            {session.rejection_reason}
                          </p>
                        )}
                      </div>
                      <div className="text-right ml-2 shrink-0">
                        {session.final_score !== null && session.final_score !== undefined ? (
                          <p className="text-base font-bold text-accent-teal font-display">
                            {session.final_score.toFixed(1)} / {assignment.max_score}
                          </p>
                        ) : (
                          <p className="text-xs font-semibold text-status-danger">
                            Failed
                          </p>
                        )}
                        <Link
                          to={`/student/sessions/${session.id}`}
                          className="text-[10px] text-accent-blue hover:underline mt-0.5 block"
                        >
                          View Breakdown
                        </Link>
                      </div>
                    </div>
                  ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </PageWrapper>
  )
}

function extractErrorMessage(error: unknown): string {
  const responseData = (error as { response?: { data?: { detail?: unknown; message?: string } } })
    ?.response?.data
  if (responseData?.detail) {
    if (typeof responseData.detail === 'string') return responseData.detail
    if (Array.isArray(responseData.detail)) {
      return responseData.detail
        .map((err: { loc?: string[]; msg?: string }) => {
          const field = err.loc?.length ? err.loc[err.loc.length - 1] : 'field'
          return `"${field}" ${err.msg ?? 'invalid'}`
        })
        .join(', ')
    }
  }
  if (responseData?.message) return responseData.message
  if (error instanceof Error) return error.message
  return 'Submission failed. Please check your connection and try again.'
}

export default AssignmentDetailPage
