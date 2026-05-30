import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { FileCheck2, Loader2, CheckCircle2, XCircle, AlertCircle } from 'lucide-react'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { ProofDropZone } from '@/components/proof/ProofDropZone'
import { ProofHistoryTable } from '@/components/proof/ProofHistoryTable'
import { useSessions } from '@/hooks/useSessions'
import { useProofSubmit } from '@/hooks/useProofSubmit'
import { useAssignments } from '@/hooks/useAssignments'
import { proofFileSchema } from '@/lib/schemas'
import type { ProofSubmitRequest } from '@/types/api'
import { useNotificationStore } from '@/store/notificationStore'
import { SkeletonCard } from '@/components/shared/SkeletonCard'
import { truncateHash } from '@/lib/utils'

type SubmitStatus = 'idle' | 'uploading' | 'success' | 'error'

const ProofSubmitPage = () => {
  const { data: sessions, isLoading } = useSessions()
  const { data: assignments } = useAssignments()
  const [selectedSessionId, setSelectedSessionId] = useState('')
  const [fileName, setFileName] = useState('')
  const [parsedProof, setParsedProof] = useState<ProofSubmitRequest | null>(null)
  const [parseError, setParseError] = useState('')
  const [submitStatus, setSubmitStatus] = useState<SubmitStatus>('idle')
  const [submitMessage, setSubmitMessage] = useState('')
  const [submitScore, setSubmitScore] = useState<number | null>(null)
  const proofSubmit = useProofSubmit()
  const addNotification = useNotificationStore((s) => s.addNotification)
  const location = useLocation()

  const activeSessions = (sessions ?? []).filter((s) =>
    ['STARTED', 'IN_PROGRESS'].includes(s.status),
  )

  const assignmentMap = Object.fromEntries(
    (assignments ?? []).map((a) => [a.id, a.title]),
  )

  useEffect(() => {
    const sessionId = new URLSearchParams(location.search).get('session_id')
    if (sessionId) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setSelectedSessionId(sessionId)
    }
  }, [location.search])

  const handleFileSelected = (file: File) => {
    setParseError('')
    setParsedProof(null)
    if (file.size > 5 * 1024 * 1024) {
      setParseError('File exceeds the 5 MB size limit.')
      return
    }
    setFileName(file.name)
    const reader = new FileReader()
    reader.onload = () => {
      try {
        const json = JSON.parse(reader.result as string)
        const result = proofFileSchema.safeParse(json)
        if (!result.success) {
          setParseError('Proof file is missing required fields or has invalid structure.')
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
    if (!parsedProof || !selectedSessionId) return
    setSubmitStatus('uploading')
    setSubmitMessage('Submitting proof to the verification backend…')
    setSubmitScore(null)
    try {
      const response = await proofSubmit.mutateAsync(parsedProof)
      setSubmitStatus(response.status === 'COMPLETED' ? 'success' : 'error')
      setSubmitMessage(response.message)
      if (response.final_score !== null && response.final_score !== undefined) {
        setSubmitScore(response.final_score)
      }
      addNotification({
        type: response.status === 'COMPLETED' ? 'success' : 'warning',
        title: response.status === 'COMPLETED' ? 'Proof verified!' : 'Proof rejected',
        message: response.message,
      })
    } catch {
      setSubmitStatus('error')
      setSubmitMessage('Submission failed. Please check your connection and try again.')
      addNotification({ type: 'error', title: 'Submission failed', message: 'Check your connection.' })
    }
  }

  return (
    <PageWrapper>
      <PageHeader
        title="Submit Proof"
        description="Upload your signed proof.json file for cryptographic verification."
      />

      {isLoading ? (
        <div className="space-y-4">
          <SkeletonCard rows={2} />
          <SkeletonCard rows={3} />
        </div>
      ) : (
        <div className="space-y-5">
          {/* Session selector */}
          <div className="card-dark p-5">
            <label htmlFor="session-select" className="mb-2 block text-sm font-medium text-text-secondary">
              Select Session
            </label>
            {activeSessions.length === 0 ? (
              <div className="flex items-center gap-2 rounded-lg border border-status-warning/30 bg-status-warning/10 px-4 py-3 text-sm text-status-warning">
                <AlertCircle size={16} />
                No active sessions. Start an assignment first.
              </div>
            ) : (
              <select
                id="session-select"
                className="input-dark"
                value={selectedSessionId}
                onChange={(e) => setSelectedSessionId(e.target.value)}
                aria-label="Select an active session"
              >
                <option value="">Select an active session…</option>
                {activeSessions.map((s) => (
                  <option key={s.id} value={s.id}>
                    {assignmentMap[s.assignment_id] ?? 'Unknown Assignment'} — {s.id.slice(0, 12)}… ({s.status})
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Drop zone */}
          <ProofDropZone
            onFileSelected={handleFileSelected}
            fileName={fileName}
            hasError={Boolean(parseError)}
          />

          {/* Parse error */}
          {parseError && (
            <div className="flex items-center gap-3 rounded-lg border border-status-danger/30 bg-status-danger/10 px-4 py-3 text-sm text-status-danger">
              <XCircle size={16} />
              {parseError}
            </div>
          )}

          {/* Proof preview */}
          {parsedProof && (
            <div className="card-dark p-5 animate-fade-in">
              <div className="mb-4 flex items-center gap-2">
                <FileCheck2 size={16} className="text-accent-teal" />
                <h3 className="font-display text-base font-semibold text-text-primary">
                  Proof Preview
                </h3>
              </div>
              <div className="grid gap-2.5 sm:grid-cols-2">
                {[
                  { label: 'Session ID', value: truncateHash(parsedProof.session_id) },
                  { label: 'Assignment ID', value: truncateHash(parsedProof.assignment_id) },
                  { label: 'Student ID', value: truncateHash(parsedProof.student_id) },
                  { label: 'Nonce', value: truncateHash(parsedProof.nonce) },
                  { label: 'Grader Hash', value: truncateHash(parsedProof.grader_binary_hash) },
                  { label: 'Timestamp', value: parsedProof.timestamp },
                  { label: 'Test Results', value: `${Object.keys(parsedProof.results).length} tests` },
                  { label: 'Artifact Hashes', value: `${Object.keys(parsedProof.artifact_hashes).length} files` },
                ].map(({ label, value }) => (
                  <div key={label} className="rounded-lg bg-navy-950/80 px-3 py-2">
                    <p className="text-xs text-text-secondary">{label}</p>
                    <p className="mt-0.5 font-mono text-xs text-text-primary break-all">{value}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Submit button + status */}
          <div className="flex flex-wrap items-center gap-4">
            <button
              className="btn-primary"
              onClick={handleSubmit}
              disabled={!parsedProof || !selectedSessionId || proofSubmit.isPending}
              aria-label="Submit proof for verification"
            >
              {proofSubmit.isPending ? (
                <><Loader2 size={15} className="animate-spin" /> Submitting…</>
              ) : (
                <><FileCheck2 size={15} /> Submit Proof</>
              )}
            </button>
          </div>

          {/* Result feedback */}
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

          {/* Proof history */}
          <div className="card-dark p-5">
            <h3 className="mb-4 font-display text-base font-semibold text-text-primary">
              Proof History
            </h3>
            <ProofHistoryTable
              sessions={(sessions ?? []).filter(
                (s) => s.id === selectedSessionId || s.status === 'COMPLETED' || s.status === 'REJECTED',
              )}
            />
          </div>
        </div>
      )}
    </PageWrapper>
  )
}

export default ProofSubmitPage
