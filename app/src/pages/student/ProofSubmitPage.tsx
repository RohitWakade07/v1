import { useState } from 'react'
import { FileCheck2, Loader2, CheckCircle2, XCircle, Lock } from 'lucide-react'
import { PageWrapper } from '@/components/shared/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { ProofDropZone } from '@/components/student/proof/ProofDropZone'
import { ProofHistoryTable } from '@/components/student/proof/ProofHistoryTable'
import { useSessions } from '@/hooks/student/useSessions'
import { useProofSubmit, useEepProofSubmit } from '@/hooks/student/useProofSubmit'
import { proofFileSchema } from '@/lib/schemas'
import type { ProofSubmitRequest, SessionSummary } from '@/types/api'
import { useNotificationStore } from '@/store/notificationStore'
import { SkeletonCard } from '@/components/shared/SkeletonCard'

type SubmitStatus = 'idle' | 'uploading' | 'success' | 'error'

const SUBMITTABLE_STATUSES = [
  'CREATED',
  'CHALLENGE_ISSUED',
  'RUNNING',
  'PROOF_GENERATED',
  'STARTED',
  'IN_PROGRESS',
]

const ProofSubmitPage = () => {
  const { data: sessions, isLoading } = useSessions()
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
  const proofSubmit = useProofSubmit()
  const eepProofSubmit = useEepProofSubmit()
  const addNotification = useNotificationStore((s) => s.addNotification)

  const submittableSessions = (sessions ?? []).filter((s) =>
    SUBMITTABLE_STATUSES.includes(s.status),
  )

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
      if (submittableSessions.length === 1) {
        setEepSessionId(submittableSessions[0].id)
      }
      return
    }

    setEepSessionId('')
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

    try {
      if (isEepFile && eepFile) {
        if (!eepSessionId) {
          setSubmitStatus('error')
          setSubmitMessage('Select a grading session before submitting your EEP file.')
          return
        }
        const response = await eepProofSubmit.mutateAsync({
          sessionId: eepSessionId,
          file: eepFile,
        })
        applySubmitResult(response.status, response.message, response.final_score)
        return
      }

      if (!parsedProof) return
      const response = await proofSubmit.mutateAsync(parsedProof)
      applySubmitResult(response.status, response.message, response.final_score)
    } catch (error: unknown) {
      setSubmitStatus('error')
      const errMsg = extractErrorMessage(error)
      setSubmitMessage(errMsg)
      if (!isEepFile) {
        addNotification({ type: 'error', title: 'Submission failed', message: errMsg })
      }
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
    if (!isEepFile) {
      addNotification({
        type: isSuccess ? 'success' : 'warning',
        title: isSuccess ? 'Proof verified!' : 'Proof rejected',
        message,
      })
    }
  }

  const canSubmit = isEepFile
    ? Boolean(eepFile && eepSessionId)
    : Boolean(parsedProof)

  const isPending = proofSubmit.isPending || eepProofSubmit.isPending

  return (
    <PageWrapper>
      <PageHeader
        title="Submit Proof"
        description="Upload a signed proof.json or an encrypted .eep1/.eep2/.eep3 verifier report."
      />

      {isLoading ? (
        <div className="space-y-4">
          <SkeletonCard rows={2} />
          <SkeletonCard rows={3} />
        </div>
      ) : (
        <div className="space-y-5">
          <ProofDropZone
            onFileSelected={handleFileSelected}
            fileName={fileName}
            isEepFile={isEepFile}
            fileSize={fileSize}
            hasError={Boolean(parseError)}
          />

          {parseError && (
            <div className="flex items-center gap-3 rounded-lg border border-status-danger/30 bg-status-danger/10 px-4 py-3 text-sm text-status-danger">
              <XCircle size={16} />
              {parseError}
            </div>
          )}

          {isEepFile && eepFile && (
            <div className="card-dark p-5 animate-fade-in">
              <div className="mb-4 flex items-center gap-2">
                <Lock size={16} className="text-accent-teal" />
                <h3 className="font-display text-base font-semibold text-text-primary">
                  EEP Submission Preview
                </h3>
              </div>
              <div className="grid gap-2.5 sm:grid-cols-2">
                <div className="rounded-lg bg-navy-950/80 px-3 py-2">
                  <p className="text-xs text-text-secondary">Filename</p>
                  <p className="mt-0.5 font-mono text-xs text-text-primary break-all">{fileName}</p>
                </div>
                <div className="rounded-lg bg-navy-950/80 px-3 py-2">
                  <p className="text-xs text-text-secondary">File size</p>
                  <p className="mt-0.5 text-xs text-text-primary">
                    {((fileSize ?? 0) / 1024).toFixed(1)} KB
                  </p>
                </div>
              </div>
              <p className="mt-3 text-xs text-text-secondary">
                Encrypted EEP submission — contents verified server-side after upload.
              </p>

              <div className="mt-4">
                <label htmlFor="eep-session" className="mb-1.5 block text-sm font-medium text-text-secondary">
                  Grading session
                </label>
                <select
                  id="eep-session"
                  className="input-dark auth-input w-full"
                  value={eepSessionId}
                  onChange={(e) => setEepSessionId(e.target.value)}
                >
                  <option value="">Select an active session…</option>
                  {submittableSessions.map((s: SessionSummary) => (
                    <option key={s.id} value={s.id}>
                      {s.id.slice(0, 8)}… — {s.status}
                    </option>
                  ))}
                </select>
                {submittableSessions.length === 0 && (
                  <p className="mt-1.5 text-xs text-status-warning">
                    No active session found. Start a session for this assignment first.
                  </p>
                )}
              </div>
            </div>
          )}

          {parsedProof && !isEepFile && (
            <div className="card-dark p-5 animate-fade-in">
              <div className="mb-4 flex items-center gap-2">
                <FileCheck2 size={16} className="text-accent-teal" />
                <h3 className="font-display text-base font-semibold text-text-primary">
                  Proof Preview
                </h3>
              </div>
              <div className="grid gap-2.5 sm:grid-cols-2">
                {[
                  { label: 'Session ID', value: parsedProof.session_id },
                  { label: 'Assignment ID', value: parsedProof.assignment_id },
                  { label: 'Student ID', value: parsedProof.student_id },
                  { label: 'Nonce', value: parsedProof.nonce },
                  { label: 'Test Results', value: `${Object.keys(parsedProof.results).length} tests` },
                ].map(({ label, value }) => (
                  <div key={label} className="rounded-lg bg-navy-950/80 px-3 py-2">
                    <p className="text-xs text-text-secondary">{label}</p>
                    <p className="mt-0.5 font-mono text-xs text-text-primary break-all">{value}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex flex-wrap items-center gap-4">
            <button
              className="btn-primary"
              onClick={handleSubmit}
              disabled={!canSubmit || isPending}
              aria-label="Submit proof for verification"
            >
              {isPending ? (
                <><Loader2 size={15} className="animate-spin" /> Submitting…</>
              ) : (
                <><FileCheck2 size={15} /> Submit Proof</>
              )}
            </button>
          </div>

          {submitStatus !== 'idle' && (
            <div className={`animate-fade-in rounded-xl border p-5 ${
              submitStatus === 'success'
                ? 'border-accent-teal/30 bg-accent-teal/10'
                : submitStatus === 'error'
                ? 'border-status-danger/30 bg-status-danger/10'
                : 'border-accent-blue/30 bg-accent-blue/10'
            }`}>
              <div className="flex items-start gap-3">
                {submitStatus === 'success' ? (
                  <CheckCircle2 size={20} className="mt-0.5 shrink-0 text-accent-teal" />
                ) : submitStatus === 'error' ? (
                  <XCircle size={20} className="mt-0.5 shrink-0 text-status-danger" />
                ) : (
                  <Loader2 size={20} className="mt-0.5 shrink-0 animate-spin text-accent-blue" />
                )}
                <div>
                  <p className={`font-semibold ${submitStatus === 'success' ? 'text-accent-teal' : submitStatus === 'error' ? 'text-status-danger' : 'text-accent-blue'}`}>
                    {submitStatus === 'success' ? 'Verification Successful' : submitStatus === 'error' ? 'Verification Failed' : 'Processing…'}
                  </p>
                  <p className="mt-1 text-sm text-text-secondary">{submitMessage}</p>
                  {submitScore !== null && (
                    <p className="mt-2 font-display text-2xl font-bold text-accent-teal">
                      Score: {submitScore.toFixed(1)}
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          <div className="card-dark p-5">
            <h3 className="mb-4 font-display text-base font-semibold text-text-primary">
              Proof History
            </h3>
            <ProofHistoryTable
              sessions={(sessions ?? []).filter(
                (s) =>
                  (parsedProof && s.id === parsedProof.session_id) ||
                  (eepSessionId && s.id === eepSessionId) ||
                  ['COMPLETED', 'VERIFIED', 'REJECTED', 'FAILED', 'ABORTED'].includes(s.status),
              )}
            />
          </div>
        </div>
      )}
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

export default ProofSubmitPage
